import gymnasium as gym
from pettingzoo import ParallelEnv
import numpy as np

class NegotiatorEnv(ParallelEnv):
    metadata = {"render_modes": ["human"], "name": "negotiator_v1"}

    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        self.num_items = self.config.get("num_items", 1)
        self.max_rounds = self.config.get("max_rounds", 20)
        self.history_lag = self.config.get("history_lag", 3)
        
        # N-Agent Support: Allow 2-10 agents
        self._n_agents = self.config.get("num_agents", 2)
        if self._n_agents < 2:
            self._n_agents = 2  # Minimum 2 agents
        elif self._n_agents > 10:
            self._n_agents = 10  # Maximum 10 agents for performance
        
        # Generate agent roles dynamically
        agent_roles = self.config.get("agent_roles", None)
        if agent_roles is None:
            self.possible_agents = self._generate_default_roles()
        else:
            self.possible_agents = agent_roles[:self._n_agents]  # Use custom roles
        
        # Action space: Discrete (0: ACCEPT, 1: COUNTER, 2: QUIT) + Continuous (Proposed Prices)
        self.action_spaces = {
            agent: gym.spaces.Dict({
                "type": gym.spaces.Discrete(3),
                "price": gym.spaces.Box(low=0, high=10000, shape=(self.num_items,), dtype=np.float32)
            }) for agent in self.possible_agents
        }
        
        # Observation space: 
        # [0:num_items]: Normalized Current Prices
        # [num_items:2*num_items]: Normalized My Valuations
        # [2*num_items]: Normalized Time Remaining
        # [2*num_items + 1]: Who is proposing? (1=Me, 0=Opponent)
        # [2*num_items + 2:]: History lag (last N prices)
        obs_size = (self.num_items * 2) + 2 + (self.num_items * self.history_lag)
        self.observation_spaces = {
            agent: gym.spaces.Box(low=0, high=1, shape=(obs_size,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        self.state = None
        self.item_weights = self.config.get("item_weights", [1.0] * self.num_items)
    
    @property
    def agents(self):
        """Return list of active agents. Standard PettingZoo interface."""
        return self.possible_agents
    
    def _generate_default_roles(self):
        """
        Generate default agent roles based on _n_agents.
        For N=2: ["supplier", "retailer"] (backward compatible)
        For N>2: ["supplier_1", "supplier_2", ..., "buyer_1", "buyer_2", ...]
        """
        if self._n_agents == 2:
            return ["supplier", "retailer"]
        
        roles = []
        num_suppliers = self._n_agents // 2
        num_buyers = self._n_agents - num_suppliers
        
        for i in range(num_suppliers):
            roles.append(f"supplier_{i+1}")
        for i in range(num_buyers):
            roles.append(f"buyer_{i+1}")
        
        return roles
    
    def _get_valuation_range(self, agent_role):
        """
        Get valuation range for a specific agent role.
        Suppliers have lower valuations (costs), buyers have higher valuations (willingness to pay).
        """
        if "supplier" in agent_role.lower():
            return (4000, 6000)  # Cost range
        else:  # buyer/retailer
            return (7000, 9000)  # Value range

    def reset(self, seed=None, options=None):
        self.current_round = 0
        
        # 1. Initialize Valuations for all items and all agents
        self.valuations = {}
        for agent in self.possible_agents:
            val_range = self._get_valuation_range(agent)
            self.valuations[agent] = np.random.uniform(val_range[0], val_range[1], size=(self.num_items,))
        
        # Backward compatibility: Keep val_s and val_r for 2-agent mode
        if self._n_agents == 2 and "supplier" in self.possible_agents and "retailer" in self.possible_agents:
            self.val_s = self.valuations["supplier"]
            self.val_r = self.valuations["retailer"]
            
            # Ensure feasible zone for each item
            for i in range(self.num_items):
                if self.val_s[i] > self.val_r[i]:
                    self.val_s[i], self.val_r[i] = self.val_r[i], self.val_s[i]
                    self.valuations["supplier"][i] = self.val_s[i]
                    self.valuations["retailer"][i] = self.val_r[i]
        
        self.max_price = 10000.0
        
        # 2. Initialize State
        self.current_prices = np.zeros(self.num_items, dtype=np.float32)
        self.deal_prices = None
        self.price_history = np.zeros((self.history_lag, self.num_items), dtype=np.float32)
        
        # Round-robin turn assignment for N agents
        self.current_proposer = self.possible_agents[0]
        self.proposal_order = self.possible_agents[:]  # Can be customized for coalitions later
        
        observations = self._get_obs()
        infos = {agent: {} for agent in self.possible_agents}
        return observations, infos

    def step(self, actions):
        if not actions or not self.agents:
            return {}, {}, {}, {}, {}

        # Identiy active agent
        agent_name = self.current_proposer
        
        # If the expected agent didn't send an action (shouldn't happen in standard Env loops), skip or error
        if agent_name not in actions:
            # Fallback: just return current state
            return self._get_obs(), {a:0.0 for a in self.possible_agents}, {a:False for a in self.possible_agents}, {a:False for a in self.possible_agents}, {a:{} for a in self.possible_agents}

        action = actions[agent_name]
        action_type = action["type"] # 0: ACCEPT, 1: COUNTER, 2: QUIT
        proposed_prices = np.array(action["price"], dtype=np.float32)
        
        rewards = {a: 0.0 for a in self.possible_agents}
        terminations = {a: False for a in self.possible_agents}
        truncations = {a: False for a in self.possible_agents}
        infos = {a: {} for a in self.possible_agents}
        
        # --- LOGIC ---
        if action_type == 0: # ACCEPT
            # Agreement reached on PREVIOUS price?
            # If Round 0 (Supplier starts) and says ACCEPT -> Accept what?
            # Typically, Proposer makes an offer. ACCEPT is a response.
            # So Supplier "Proposing ACCEPT" means "I accept your last offer".
            # If Round 0, there is no last offer. Treat as invalid or just stick to price.
            if self.current_round == 0:
                # Invalid accept at start. Penalize or treat as walkaway?
                # Let's treat as "Accepting 0" (bad for supplier) or just Invalid.
                # Simplification: Treat as Quit
                terminations = {a: True for a in self.possible_agents}
                rewards[agent_name] = -0.5
            else:
                self.deal_prices = self.current_prices
                deal_prices = self.deal_prices
                
                # Bundle Profit (weighted sum)
                r_sup_total = 0
                r_ret_total = 0
                for i in range(self.num_items):
                    r_sup_total += self.item_weights[i] * (deal_prices[i] - self.val_s[i]) / self.max_price
                    r_ret_total += self.item_weights[i] * (self.val_r[i] - deal_prices[i]) / self.max_price
                
                # Discount
                discount = 0.99 ** self.current_round
                rewards["supplier"] = r_sup_total * discount
                rewards["retailer"] = r_ret_total * discount
                
                terminations = {a: True for a in self.possible_agents}
                infos["supplier"]["result"] = "deal"
                infos["retailer"]["result"] = "deal"
                infos["deal_prices"] = deal_prices.tolist()

        elif action_type == 2: # QUIT
            rewards = {a: -0.1 for a in self.possible_agents}
            terminations = {a: True for a in self.possible_agents}
            infos = {a: {"result": "quit"} for a in self.possible_agents}
            
        else: # COUNTER (Make a new offer)
            # Update Price
            self.current_prices = np.clip(proposed_prices, 0, self.max_price)
            
            # Update History
            self.price_history = np.roll(self.price_history, 1, axis=0)
            self.price_history[0] = self.current_prices / self.max_price
            
            self.current_round += 1
            
            # Check Timeout
            if self.current_round >= self.max_rounds:
                truncations = {a: True for a in self.possible_agents}
                rewards = {a: -0.05 for a in self.possible_agents}
            else:
                # Switch Turn: Round-robin through all agents
                current_idx = self.proposal_order.index(self.current_proposer)
                next_idx = (current_idx + 1) % len(self.proposal_order)
                self.current_proposer = self.proposal_order[next_idx]

        observations = self._get_obs()
        
        # Note: In PettingZoo ParallelEnv, agents property is read-only
        # No need to manually clear agents list on termination
        
        return observations, rewards, terminations, truncations, infos

    def _get_obs(self):
        obs_dict = {}
        for agent in self.possible_agents:
            # Get this agent's valuation
            my_vals = self.valuations.get(agent, np.zeros(self.num_items))
            is_my_turn = 1.0 if self.current_proposer == agent else 0.0
            
            # Construct flattened observation vector
            obs_parts = [
                self.current_prices / self.max_price,       # num_items
                my_vals / self.max_price,                    # num_items
                np.array([self.current_round / self.max_rounds], dtype=np.float32), # 1
                np.array([is_my_turn], dtype=np.float32),   # 1
                self.price_history.flatten()                 # num_items * history_lag
            ]
            obs_dict[agent] = np.concatenate(obs_parts)
        return obs_dict

    def render(self):
        prices_str = ", ".join([f"{p:.2f}" for p in self.current_prices])
        print(f"Round {self.current_round}: Prices [{prices_str}] (Turn: {self.current_proposer})")

    def close(self):
        pass


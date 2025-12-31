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
        self.possible_agents = ["supplier", "retailer"]
        self.agents = self.possible_agents[:]
        
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

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.current_round = 0
        
        # 1. Initialize Valuations for all items
        # Supplier cost: 4000-6000
        self.val_s = np.random.uniform(4000, 6000, size=(self.num_items,))
        # Retailer resale value: 7000-9000
        self.val_r = np.random.uniform(7000, 9000, size=(self.num_items,))
        
        # Ensure feasible zone for each item (simplification)
        for i in range(self.num_items):
            if self.val_s[i] > self.val_r[i]:
                self.val_s[i], self.val_r[i] = self.val_r[i], self.val_s[i]
        
        self.max_price = 10000.0
        
        # 2. Initialize State
        # Let's start with NO deal price, but the 'current_prices' variable holds the LAST offer.
        self.current_prices = np.zeros(self.num_items, dtype=np.float32)
        self.deal_prices = None
        self.price_history = np.zeros((self.history_lag, self.num_items), dtype=np.float32)
        
        self.current_proposer = "supplier" 
        
        observations = self._get_obs()
        infos = {agent: {} for agent in self.agents}
        return observations, infos

    def step(self, actions):
        if not actions or not self.agents:
            return {}, {}, {}, {}, {}

        # Identiy active agent
        agent_name = self.current_proposer
        
        # If the expected agent didn't send an action (shouldn't happen in standard Env loops), skip or error
        if agent_name not in actions:
            # Fallback: just return current state
            return self._get_obs(), {a:0.0 for a in self.agents}, {a:False for a in self.agents}, {a:False for a in self.agents}, {a:{} for a in self.agents}

        action = actions[agent_name]
        action_type = action["type"] # 0: ACCEPT, 1: COUNTER, 2: QUIT
        proposed_prices = np.array(action["price"], dtype=np.float32)
        
        rewards = {a: 0.0 for a in self.agents}
        terminations = {a: False for a in self.agents}
        truncations = {a: False for a in self.agents}
        infos = {a: {} for a in self.agents}
        
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
                terminations = {a: True for a in self.agents}
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
                
                terminations = {a: True for a in self.agents}
                infos["supplier"]["result"] = "deal"
                infos["retailer"]["result"] = "deal"
                infos["deal_prices"] = deal_prices.tolist()

        elif action_type == 2: # QUIT
            rewards = {a: -0.1 for a in self.agents}
            terminations = {a: True for a in self.agents}
            infos = {a: {"result": "quit"} for a in self.agents}
            
        else: # COUNTER (Make a new offer)
            # Update Price
            self.current_prices = np.clip(proposed_prices, 0, self.max_price)
            
            # Update History
            self.price_history = np.roll(self.price_history, 1, axis=0)
            self.price_history[0] = self.current_prices / self.max_price
            
            self.current_round += 1
            
            # Check Timeout
            if self.current_round >= self.max_rounds:
                truncations = {a: True for a in self.agents}
                rewards = {a: -0.05 for a in self.agents}
            else:
                # Switch Turn
                self.current_proposer = "retailer" if self.current_proposer == "supplier" else "supplier"

        observations = self._get_obs()
        
        if any(terminations.values()) or any(truncations.values()):
            self.agents = []
            
        return observations, rewards, terminations, truncations, infos

    def _get_obs(self):
        obs_dict = {}
        for agent in self.possible_agents:
            my_vals = self.val_s if agent == "supplier" else self.val_r
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

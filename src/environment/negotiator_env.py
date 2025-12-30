import gymnasium as gym
from pettingzoo import ParallelEnv
import numpy as np

class NegotiatorEnv(ParallelEnv):
    metadata = {"render_modes": ["human"], "name": "negotiator_v1"}

    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        self.max_rounds = self.config.get("max_rounds", 20)
        self.possible_agents = ["supplier", "retailer"]
        self.agents = self.possible_agents[:]
        
        # Action space: Discrete (0: ACCEPT, 1: COUNTER, 2: QUIT) + Continuous (Proposed Price)
        self.action_spaces = {
            agent: gym.spaces.Dict({
                "type": gym.spaces.Discrete(3),
                "price": gym.spaces.Box(low=0, high=10000, shape=(1,), dtype=np.float32)
            }) for agent in self.possible_agents
        }
        
        # Observation space: 
        # [0]: Normalized Current Price (0-1)
        # [1]: Normalized My Valuation (0-1)
        # [2]: Normalized Time Remaining (0-1)
        # [3]: Who is proposing? (1=Me, 0=Opponent)
        # [4-9]: History lag (last 6 prices)
        self.observation_spaces = {
            agent: gym.spaces.Box(low=0, high=1, shape=(10,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        self.state = None

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.current_round = 0
        
        # 1. Initialize Valuations (Private Info)
        # Supplier cost: 4000-6000
        self.val_s = np.random.uniform(4000, 6000)
        # Retailer resale value: 7000-9000
        self.val_r = np.random.uniform(7000, 9000)
        
        # Ensure feasible zone (Z > 0)
        if self.val_s > self.val_r:
            self.val_s, self.val_r = self.val_r, self.val_s
        
        self.max_price = 10000.0
        
        # 2. Initialize State
        # Start with a random initial offer from Supplier (~1.1*Val_S is too low, usually Supplier asks High)
        # Standard: Supplier asks high, Retailer offers low.
        # But "Initial State" usually implies "Previous Offer".
        # Let's say initialization: No price on table yet?
        # Or convention: Supplier always starts.
        self.current_price = self.val_r * 0.5 + self.val_s * 0.5 # Midpoint start or random?
        # Paper says: "Proposed price p".
        # Let's start with NO deal price, but the 'current_price' variable holds the LAST offer.
        # Round 0: Supplier makes offer. Last offer is None?
        # Implementation detail: 'current_price' initiates at a neutral value (e.g. 0) or max?
        self.current_price = 0.0
        self.price_history = np.zeros(6, dtype=np.float32)
        
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
        proposed_price = float(action["price"][0])
        
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
                deal_price = self.current_price
                
                # Rewards (Surplus)
                # Supplier: P - Vs
                r_sup = (deal_price - self.val_s) / self.max_price
                # Retailer: Vr - P
                r_ret = (self.val_r - deal_price) / self.max_price
                
                # Discount
                discount = 0.99 ** self.current_round
                rewards["supplier"] = r_sup * discount
                rewards["retailer"] = r_ret * discount
                
                terminations = {a: True for a in self.agents}
                infos["supplier"]["result"] = "deal"
                infos["retailer"]["result"] = "deal"
                infos["deal_price"] = deal_price

        elif action_type == 2: # QUIT
            rewards["supplier"] = -0.1
            rewards["retailer"] = -0.1
            terminations = {a: True for a in self.agents}
            infos["supplier"]["result"] = "quit"
            infos["retailer"]["result"] = "quit"
            
        else: # COUNTER (Make a new offer)
            # Update Price
            self.current_price = np.clip(proposed_price, 0, self.max_price)
            
            # Update History
            self.price_history = np.roll(self.price_history, 1)
            self.price_history[0] = self.current_price / self.max_price
            
            self.current_round += 1
            
            # Check Timeout
            if self.current_round >= self.max_rounds:
                truncations = {a: True for a in self.agents}
                rewards["supplier"] = -0.05
                rewards["retailer"] = -0.05
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
            if agent == "supplier":
                my_val = self.val_s
                is_my_turn = 1.0 if self.current_proposer == "supplier" else 0.0
            else:
                my_val = self.val_r
                is_my_turn = 1.0 if self.current_proposer == "retailer" else 0.0
            
            # [Price, MyVal, Time, Turn, History(6)]
            vec = np.zeros(10, dtype=np.float32)
            vec[0] = self.current_price / self.max_price
            vec[1] = my_val / self.max_price
            vec[2] = self.current_round / self.max_rounds
            vec[3] = is_my_turn
            vec[4:] = self.price_history[:6]
            
            obs_dict[agent] = vec
        return obs_dict

    def render(self):
        print(f"Round {self.current_round}: Price {self.current_price:.2f} (Turn: {self.current_proposer})")

    def close(self):
        pass

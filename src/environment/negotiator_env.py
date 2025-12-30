import gymnasium as gym
from pettingzoo import ParallelEnv
import numpy as np

class NegotiatorEnv(ParallelEnv):
    metadata = {"render_modes": ["human"], "name": "negotiator_v1"}

    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        self.possible_agents = ["supplier", "retailer"]
        self.agents = self.possible_agents[:]
        
        # Action space: Discrete (0: ACCEPT, 1: COUNTER, 2: WALK_AWAY) + Continuous (Proposed Price)
        self.action_spaces = {
            agent: gym.spaces.Dict({
                "type": gym.spaces.Discrete(3),
                "price": gym.spaces.Box(low=0, high=10000, shape=(1,), dtype=np.float32)
            }) for agent in self.possible_agents
        }
        
        # Observation space: Prices, History, Rounds, Beliefs
        self.observation_spaces = {
            agent: gym.spaces.Box(low=0, high=1, shape=(10,), dtype=np.float32)
            for agent in self.possible_agents
        }

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        # Reset internal state logic
        observations = {agent: np.zeros(10, dtype=np.float32) for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        return observations, infos

    def step(self, actions):
        # Process multi-agent concurrent actions
        # Compute rewards based on Eq. 5 & 6 in paper
        rewards = {agent: 0.0 for agent in self.agents}
        terminations = {agent: False for agent in self.agents}
        truncations = {agent: False for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        
        return {}, rewards, terminations, truncations, infos

    def render(self):
        pass

    def close(self):
        pass

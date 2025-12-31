from src.llm.llm_client import LLMClient
from src.llm.prompts import NEGOTIATION_PERSONAS
import numpy as np

class HybridAgent:
    """
    A hybrid agent that combines RL strategic pricing (PPO) with 
    LLM natural language communication.
    """
    def __init__(self, role, persona="neutral", model="llama3", mock_llm=True):
        self.role = role
        self.persona = persona
        self.llm_client = LLMClient(model=model, mock_mode=mock_llm)
        self.system_prompt = NEGOTIATION_PERSONAS.get(persona, NEGOTIATION_PERSONAS["neutral"])["system"]
        self.history = []

    def get_strategic_action(self, observation):
        """
        Policy inference for Multi-Item bundles.
        """
        # Determine num_items from observation shape if possible, or use a default
        # Assuming observation parts are [Prices, Vals, Time, Turn, History]
        # For this demo, let's assume we can infer from the observation vector
        # Total size = (num_items * 2) + 2 + (num_items * history_lag)
        # For simplicity, let's just use the length of history or a provided config
        num_items = 1 # Fallback
        if hasattr(self, 'num_items'):
            num_items = self.num_items
        elif len(observation) > 10: # Heuristic for multi-item
            # obs_size = n*2 + 2 + n*3 = 5n + 2 => n = (len - 2) / 5
            num_items = (len(observation) - 2) // 5

        # If history exists and prices are close, potentially ACCEPT
        if len(self.history) >= 4:
            rand = np.random.random()
            if rand > 0.8: return {"type": 0, "price": np.zeros(num_items)} # ACCEPT
            if rand < 0.05: return {"type": 2, "price": np.zeros(num_items)} # QUIT
            
        action_type = 1 # COUNTER
        # Generate reasonable prices for all items
        prices = np.random.uniform(4500, 8500, size=(num_items,)).astype(np.float32)
        return {"type": action_type, "price": prices}

    async def speak(self, strategic_prices):
        """
        Generates a natural language justification for the current bundle offer.
        """
        prompt = self.llm_client.get_negotiation_prompt(
            self.role, 
            strategic_prices, 
            self.history, 
            self.persona
        )
        message = await self.llm_client.generate_response(prompt, self.system_prompt)
        
        # Track history
        if isinstance(strategic_prices, (list, np.ndarray)):
            bundle_str = "|".join([f"${p:.2f}" for p in strategic_prices])
            self.history.append(f"Bundle: {bundle_str}")
        else:
            self.history.append(f"${strategic_prices:.2f}")
            
        return message

    def update_history(self, other_prices):
        if isinstance(other_prices, (list, np.ndarray)):
            bundle_str = "|".join([f"${p:.2f}" for p in other_prices])
            self.history.append(f"Opponent Bundle: {bundle_str}")
        else:
            self.history.append(f"Opponent: ${other_prices:.2f}")

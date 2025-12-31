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
        Refined placeholder for RL Policy inference for smoother showcase.
        """
        # If history exists and prices are close, potentially ACCEPT
        if len(self.history) >= 4:
            rand = np.random.random()
            if rand > 0.7: return {"type": 0, "price": np.array([0.0])} # ACCEPT
            if rand < 0.1: return {"type": 2, "price": np.array([0.0])} # QUIT
            
        action_type = 1 # COUNTER
        # Simple convergence logic for demo
        price = np.random.uniform(5000, 7000)
        return {"type": action_type, "price": np.array([price], dtype=np.float32)}

    async def speak(self, strategic_price):
        """
        Generates a natural language justification for the current offer.
        """
        prompt = self.llm_client.get_negotiation_prompt(
            self.role, 
            strategic_price, 
            self.history, 
            self.persona
        )
        message = await self.llm_client.generate_response(prompt, self.system_prompt)
        
        # Track history
        self.history.append(f"${strategic_price:.2f}")
        return message

    def update_history(self, other_price):
        self.history.append(f"Opponent: ${other_price:.2f}")

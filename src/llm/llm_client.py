import aiohttp
import json
import logging

class LLMClient:
    """
    Client for interacting with local Ollama API for natural language negotiation.
    """
    def __init__(self, base_url="http://localhost:11434", model="llama3", mock_mode=False):
        self.base_url = base_url
        self.model = model
        self.mock_mode = mock_mode
        self.logger = logging.getLogger(__name__)

    async def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generates a negotiation message based on the strategic offer and persona.
        """
        if self.mock_mode:
            return f"[Mock LLM Response for ${self.model}] Based on our internal valuation, this offer is the best we can do today."

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "").strip()
                    else:
                        error_text = await resp.text()
                        self.logger.error(f"Ollama API Error: {resp.status} - {error_text}")
                        return f"[Error: Ollama status {resp.status}]"
        except Exception as e:
            self.logger.error(f"Failed to connect to Ollama: {e}")
            return f"[Error: Connection failed to local LLM at {self.base_url}]"

    def get_negotiation_prompt(self, agent_role: str, offer_price: float, history: list, persona: str = "professional"):
        """
        Constructs a prompt for the LLM based on the current negotiation state.
        """
        history_str = "\n".join([f"- Offer: {h}" for h in history[-3:]])
        
        prompt = f"""
You are a {agent_role} in a commercial negotiation. 
Your current strategic offer is: ${offer_price:.2f}.
Recent history:
{history_str}

Persona: {persona}

Task: Write a concise message (max 2 sentences) to the other party justifying this offer. 
Do not mention that you are an AI. Be firm but fair.
Message:
"""
        return prompt

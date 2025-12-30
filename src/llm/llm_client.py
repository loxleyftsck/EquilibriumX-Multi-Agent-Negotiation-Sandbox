import os
import requests

class LLMClient:
    def __init__(self, model_name="llama3", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        
    def generate_message(self, prompt, system_prompt=None):
        """
        Generates a negotiation message using the local Ollama instance.
        """
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"Error calling LLM: {e}")
            return "Error: Could not generate message."

if __name__ == "__main__":
    # Smoke test
    client = LLMClient()
    print("Test Response:", client.generate_message("Say hello to the negotiation partner."))

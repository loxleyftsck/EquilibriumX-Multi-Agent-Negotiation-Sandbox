import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.llm_client import LLMClient
from src.llm.prompts import NEGOTIATION_PERSONAS

async def test_llm():
    client = LLMClient(model="llama3") # Assuming user has llama3 or similar
    
    print("Testing LLM Response Generation...")
    
    role = "Supplier"
    price = 5600.50
    history = ["$6000", "$5800"]
    persona_key = "aggressive"
    
    prompt = client.get_negotiation_prompt(role, price, history, persona_key)
    system_prompt = NEGOTIATION_PERSONAS[persona_key]["system"]
    
    print(f"\n--- PROMPT ---\n{prompt}")
    
    response = await client.generate_response(prompt, system_prompt)
    
    print(f"\n--- LLM RESPONSE ---\n{response}")
    print("\nVerification Complete.")

if __name__ == "__main__":
    try:
        asyncio.run(test_llm())
    except Exception as e:
        print(f"FAILED: {e}")

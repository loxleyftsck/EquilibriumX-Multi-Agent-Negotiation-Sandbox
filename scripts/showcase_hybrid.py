import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.hybrid_agent import HybridAgent

async def run_hybrid_showcase():
    print("=== EquilibriumX Hybrid Negotiation Showcase ===")
    
    # 1. Initialize Agents
    supplier = HybridAgent(role="Supplier", persona="aggressive", mock_llm=True)
    retailer = HybridAgent(role="Retailer", persona="cooperative", mock_llm=True)
    
    print(f"\nAgents Initialized:")
    print(f"- Supplier Persona: {supplier.persona}")
    print(f"- Retailer Persona: {retailer.persona}")
    
    # 2. Simulated Multi-Round Negotiation
    print("\n--- Negotiation Start ---")
    
    # Round 1: Supplier offers
    s_offer = supplier.get_strategic_action(None)["price"][0]
    s_msg = await supplier.speak(s_offer)
    print(f"[Supplier] Strategic Price: ${s_offer:.2f}")
    print(f"[Supplier] Message: {s_msg}\n")
    
    # Retailer perceives and responds
    retailer.update_history(s_offer)
    r_offer = retailer.get_strategic_action(None)["price"][0]
    r_msg = await retailer.speak(r_offer)
    print(f"[Retailer] Strategic Price: ${r_offer:.2f}")
    print(f"[Retailer] Message: {r_msg}\n")
    
    # Round 2: Supplier responds
    supplier.update_history(r_offer)
    s_offer_2 = supplier.get_strategic_action(None)["price"][0]
    s_msg_2 = await supplier.speak(s_offer_2)
    print(f"[Supplier] Strategic Price: ${s_offer_2:.2f}")
    print(f"[Supplier] Message: {s_msg_2}\n")
    
    print("--- Negotiation End ---")
    print("\nShowcase Successful: RL Strategy + LLM Communication Integrated.")

if __name__ == "__main__":
    asyncio.run(run_hybrid_showcase())

import asyncio
import os
import sys
import time

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment.negotiator_env import NegotiatorEnv
from src.agents.hybrid_agent import HybridAgent

async def live_battle():
    print("\n" + "="*60)
    print("      🚀 EQUILIBRIUMX: LIVE HYBRID NEGOTIATION BATTLE 🚀      ")
    print("="*60 + "\n")
    
    env = NegotiatorEnv(config={"max_rounds": 10})
    obs, info = env.reset()
    
    # Initialize agents with distinct personalities
    supplier = HybridAgent(role="Supplier", persona="aggressive", mock_llm=True)
    retailer = HybridAgent(role="Retailer", persona="cooperative", mock_llm=True)
    
    agents = {"supplier": supplier, "retailer": retailer}
    
    print(f"DEBUG: Supplier Valuation: ${env.val_s:.2f}")
    print(f"DEBUG: Retailer Valuation: ${env.val_r:.2f}")
    print(f"Negotiation Zone: ${env.val_s:.2f} - ${env.val_r:.2f}\n")
    print("-" * 60)

    done = False
    while not done:
        proposer_id = env.current_proposer
        agent = agents[proposer_id]
        
        print(f"\n[ROUND {env.current_round + 1}] Turn: {proposer_id.upper()}")
        
        # 1. Strategic Decision (RL)
        action_data = agent.get_strategic_action(obs[proposer_id])
        action_type = action_data["type"]
        price = action_data["price"][0]
        
        action_name = ["ACCEPT", "COUNTER", "QUIT"][action_type]
        
        # 2. Natural Language Justification (LLM)
        if action_type == 1: # COUNTER
            msg = await agent.speak(price)
            print(f"🤖 {proposer_id.capitalize()} proposes: ${price:.2f}")
            print(f"💬 \"{msg}\"")
        elif action_type == 0:
            print(f"🤝 {proposer_id.capitalize()} decided to ACCEPT the offer!")
        else:
            print(f"🚪 {proposer_id.capitalize()} has QUIT the negotiation.")

        # 3. Environment Step
        actions = {proposer_id: action_data}
        obs, rewards, terms, truncs, infos = env.step(actions)
        
        # Update history for the other agent
        other_agent_id = "retailer" if proposer_id == "supplier" else "supplier"
        agents[other_agent_id].update_history(price)
        
        done = any(terms.values()) or any(truncs.values())
        time.sleep(1) # Slow down for visibility

    print("\n" + "-" * 60)
    print("NEGOTIATION OVER")
    if env.deal_price:
        print(f"✅ Result: SUCCESSFUL DEAL at ${env.deal_price:.2f}")
    else:
        print("❌ Result: NO DEAL / FAILED")
    
    print(f"Final Rewards: {rewards}")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(live_battle())

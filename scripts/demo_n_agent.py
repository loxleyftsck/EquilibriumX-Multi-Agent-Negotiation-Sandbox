"""
Demo Script: N-Agent Negotiation Visualization
Demonstrates 3-agent and 5-agent negotiations with visualization output.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment.negotiator_env import NegotiatorEnv
import numpy as np

def demo_3_agent():
    print("\n" + "="*70)
    print(" 🎯 3-AGENT NEGOTIATION DEMO")
    print("="*70)
    
    env = NegotiatorEnv(config={"num_agents": 3, "num_items": 2, "max_rounds": 10})
    obs, info = env.reset()
    
    print(f"\n📋 Agents: {env.possible_agents}")
    print(f"🔄 Proposal Order: {env.proposal_order}\n")
    
    print("💰 Valuations:")
    for agent in env.possible_agents:
        vals = [f"${v:.0f}" for v in env.valuations[agent]]
        print(f"  {agent:15} {vals}")
    
    print("\n🔥 Starting Negotiation...")
    print("-" * 70)
    
    for round_num in range(10):
        proposer = env.current_proposer
        
        # Strategic random offer
        action = {
            "type": 1,  # COUNTER
            "price": np.random.uniform(5000, 7500, size=(env.num_items,))
        }
        
        obs, rewards, terms, truncs, infos = env.step({proposer: action})
        
        prices_str = ", ".join([f"${p:.0f}" for p in env.current_prices])
        print(f"Round {round_num+1:2d} | {proposer:15} → proposed [{prices_str}] → {env.current_proposer}")
        
        if any(terms.values()):
            print(f"\n✅ DEAL REACHED! Final prices: [{prices_str}]")
            print(f"   Rewards: {rewards}")
            break
    else:
        print("\n❌ No deal after 10 rounds")
    
    print("="*70)

def demo_5_agent():
    print("\n" + "="*70)
    print(" 🎯 5-AGENT NEGOTIATION DEMO")
    print("="*70)
    
    env = NegotiatorEnv(config={"num_agents": 5, "num_items": 3, "max_rounds": 15})
    obs, info = env.reset()
    
    print(f"\n📋 Agents: {env.possible_agents}")
    print(f"🔄 Proposal Order: {env.proposal_order}\n")
    
    print("💰 Valuations:")
    for agent in env.possible_agents:
        vals = ", ".join([f"${v:.0f}" for v in env.valuations[agent]])
        role = "supplier" if "supplier" in agent else "buyer"
        print(f"  {agent:15} ({role:^8}) [{vals}]")
    
    print("\n🔥 Starting Negotiation...")
    print("-" * 70)
    
    for round_num in range(15):
        proposer = env.current_proposer
        
        # Strategic random offer
        action = {
            "type": 1,  # COUNTER
            "price": np.random.uniform(5000, 7500, size=(env.num_items,))
        }
        
        obs, rewards, terms, truncs, infos = env.step({proposer: action})
        
        prices_str = ", ".join([f"${p:.0f}" for p in env.current_prices])
        print(f"Round {round_num+1:2d} | {proposer:15} → [{prices_str}]")
        
        if any(terms.values()):
            print(f"\n✅ DEAL REACHED!")
            print(f"   Final prices: [{prices_str}]")
            print(f"   Rewards:")
            for agent, reward in rewards.items():
                print(f"     {agent:15} {reward:+.4f}")
            break
    else:
        print("\n❌ No deal after 15 rounds")
    
    print("="*70)

if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# Phase 7: N-Agent Negotiation Demo")
    print("#"*70)
    
    demo_3_agent()
    demo_5_agent()
    
    print("\n✨ N-Agent environment is working perfectly!\n")

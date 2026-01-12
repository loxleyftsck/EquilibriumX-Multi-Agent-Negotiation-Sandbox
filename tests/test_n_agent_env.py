"""
Test script for N-Agent Negotiation Environment
Tests 3-agent and 5-agent scenarios to verify Phase 7 core functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment.negotiator_env import NegotiatorEnv
import numpy as np

def test_2_agent_backward_compatibility():
    print("=" * 60)
    print("TEST 1: 2-Agent Mode (Backward Compatibility)")
    print("=" * 60)
    
    env = NegotiatorEnv(config={"num_items": 2, "max_rounds": 5})
    obs, info = env.reset()
    
    print(f"Agents: {env.possible_agents}")
    print(f"Valuations:")
    for agent in env.possible_agents:
        print(f"  {agent}: {env.valuations[agent]}")
    
    # Run a few rounds
    for round_num in range(3):
        proposer = env.current_proposer
        action = {
            "type": 1,  # COUNTER
            "price": np.random.uniform(5000, 7000, size=(env.num_items,))
        }
        obs, rewards, terms, truncs, infos = env.step({proposer: action})
        print(f"Round {round_num+1}: {proposer} proposed, switched to {env.current_proposer}")
    
    assert len(env.possible_agents) == 2
    print("PASS: 2-Agent mode working!")

def test_3_agent_negotiation():
    print("\\n" + "=" * 60)
    print("TEST 2: 3-Agent Negotiation")
    print("=" * 60)
    
    env = NegotiatorEnv(config={"num_agents": 3, "num_items": 2, "max_rounds": 10})
    obs, info = env.reset()
    
    print(f"Agents: {env.possible_agents}")
    print(f"Valuations:")
    for agent in env.possible_agents:
        print(f"  {agent}: {env.valuations[agent]}")
    
    # Run negotiation
    for round_num in range(6):
        proposer = env.current_proposer
        action = {
            "type": 1,  # COUNTER
            "price": np.random.uniform(5000, 7500, size=(env.num_items,))
        }
        obs, rewards, terms, truncs, infos = env.step({proposer: action})
        print(f"Round {round_num+1}: {proposer} -> {env.current_proposer}")
        
        if any(terms.values()):
            break
    
    assert len(env.possible_agents) == 3
    print("PASS: 3-Agent negotiation works!")

def test_5_agent_negotiation():
    print("\\n" + "=" * 60)
    print("TEST 3: 5-Agent Negotiation")
    print("=" * 60)
    
    env = NegotiatorEnv(config={"num_agents": 5, "num_items": 3, "max_rounds": 15})
    obs, info = env.reset()
    
    print(f"Agents: {env.possible_agents}")
    print("Running 5-agent negotiation...")
    agents_seen = set()
    for round_num in range(10):
        proposer = env.current_proposer
        agents_seen.add(proposer)
        
        action = {
            "type": 1,  # COUNTER
            "price": np.random.uniform(5000, 7500, size=(env.num_items,))
        }
        obs, rewards, terms, truncs, infos = env.step({proposer: action})
        print(f"Round {round_num+1}: {proposer} -> {env.current_proposer}")
        
        if any(terms.values()):
            break
    
    print(f"Agents that got turns: {agents_seen}")
    assert len(env.possible_agents) == 5
    print("PASS: 5-Agent negotiation works!")

if __name__ == "__main__":
    print("\\nPhase 7: N-Agent Environment Test Suite")
    print("=" * 60)
    
    try:
        test_2_agent_backward_compatibility()
        test_3_agent_negotiation()
        test_5_agent_negotiation()
        
        print("\\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

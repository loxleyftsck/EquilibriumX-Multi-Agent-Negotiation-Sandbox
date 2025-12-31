import pytest
import numpy as np
from src.environment.negotiator_env import NegotiatorEnv

@pytest.fixture
def env():
    return NegotiatorEnv(config={"max_rounds": 10, "num_items": 1})

def test_initialization(env):
    obs, info = env.reset()
    assert "supplier" in obs
    assert "retailer" in obs
    # Check valuation feasibility (element-wise for arrays)
    assert np.all(env.val_s <= env.val_r)
    # Check observation shape (1 item: 2*1 + 2 + 1*3 = 7)
    assert obs["supplier"].shape == (7,)
    assert obs["retailer"].shape == (7,)
    # Check turn (Supplier starts)
    assert env.current_proposer == "supplier"

def test_step_mechanics(env):
    env.reset()
    # Supplier proposes 5000
    actions = {
        "supplier": {"type": 1, "price": np.array([5000.0])},
        "retailer": {"type": 1, "price": np.array([0.0])} # Should be ignored
    }
    obs, rewards, terms, truncs, infos = env.step(actions)
    
    assert env.current_prices[0] == 5000.0
    assert env.current_round == 1
    assert env.current_proposer == "retailer"
    assert terms["supplier"] == False
    
    # Retailer Counters 5500
    actions = {
        "retailer": {"type": 1, "price": np.array([5500.0])}
    }
    obs, rewards, terms, truncs, infos = env.step(actions)
    assert env.current_prices[0] == 5500.0
    assert env.current_round == 2
    assert env.current_proposer == "supplier"

def test_agreement(env):
    env.reset()
    # Force valuations for deterministic check
    env.val_s = np.array([4000.0])
    env.val_r = np.array([8000.0])
    env.valuations["supplier"] = env.val_s
    env.valuations["retailer"] = env.val_r
    env.max_price = 10000
    
    # Supplier proposes 6000
    env.step({"supplier": {"type": 1, "price": np.array([6000.0])}})
    
    # Retailer Accepts
    actions = {"retailer": {"type": 0, "price": np.array([0.0])}}
    obs, rewards, terms, truncs, infos = env.step(actions)
    
    # Deal at 6000
    assert terms["supplier"] == True
    assert env.deal_prices[0] == 6000.0
    
    # Check Rewards
    # Supplier: (6000 - 4000)/10000 = 0.2 * discount(0.99^1)
    expected_r_sup = 0.2 * (0.99**1)
    assert np.isclose(rewards["supplier"], expected_r_sup)

def test_walkaway(env):
    env.reset()
    actions = {"supplier": {"type": 2, "price": np.array([0.0])}} # Quit
    obs, rewards, terms, truncs, infos = env.step(actions)
    
    assert terms["supplier"] == True
    assert rewards["supplier"] == -0.1
    assert infos["supplier"]["result"] == "quit"

def test_timeout():
    # Use stricter max_rounds for timeout test
    env = NegotiatorEnv(config={"max_rounds": 3, "num_items": 1})
    env.reset()
    
    # Round 1 (current_round goes from 0 to 1)
    obs, rewards, terms, truncs, infos = env.step({"supplier": {"type": 1, "price": np.array([5000.0])}})
    assert env.current_round == 1
    assert not any(truncs.values())
    
    # Round 2 (current_round goes from 1 to 2)
    obs, rewards, terms, truncs, infos = env.step({"retailer": {"type": 1, "price": np.array([6000.0])}})
    assert env.current_round == 2
    assert not any(truncs.values())
    
    # Round 3 (current_round goes from 2 to 3, equals max_rounds, should truncate)
    obs, rewards, terms, truncs, infos = env.step({"supplier": {"type": 1, "price": np.array([5500.0])}})
    assert env.current_round == 3
    assert truncs["supplier"] == True
    assert truncs["retailer"] == True
    assert rewards["supplier"] == -0.05
    assert rewards["retailer"] == -0.05

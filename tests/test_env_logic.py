import pytest
import numpy as np
from src.environment.negotiator_env import NegotiatorEnv

@pytest.fixture
def env():
    return NegotiatorEnv(config={"max_rounds": 10})

def test_initialization(env):
    obs, info = env.reset()
    assert "supplier" in obs
    assert "retailer" in obs
    # Check valuation feasibility
    assert env.val_s <= env.val_r
    # Check observation shape
    assert obs["supplier"].shape == (10,)
    assert obs["retailer"].shape == (10,)
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
    
    assert env.current_price == 5000.0
    assert env.current_round == 1
    assert env.current_proposer == "retailer"
    assert terms["supplier"] == False
    
    # Retailer Counters 5500
    actions = {
        "retailer": {"type": 1, "price": np.array([5500.0])}
    }
    obs, rewards, terms, truncs, infos = env.step(actions)
    assert env.current_price == 5500.0
    assert env.current_round == 2
    assert env.current_proposer == "supplier"

def test_agreement(env):
    env.reset()
    # Force valuations for deterministic check
    env.val_s = 4000
    env.val_r = 8000
    env.max_price = 10000
    
    # Supplier proposes 6000
    env.step({"supplier": {"type": 1, "price": [6000.0]}})
    
    # Retailer Accepts
    actions = {"retailer": {"type": 0, "price": [0.0]}}
    obs, rewards, terms, truncs, infos = env.step(actions)
    
    # Deal at 6000
    assert terms["supplier"] == True
    assert infos["deal_price"] == 6000.0
    
    # Check Rewards
    # Supplier: (6000 - 4000)/10000 = 0.2 * discount(0.99^1)
    expected_r_sup = 0.2 * (0.99**1)
    assert np.isclose(rewards["supplier"], expected_r_sup)

def test_walkaway(env):
    env.reset()
    actions = {"supplier": {"type": 2, "price": [0.0]}} # Quit
    obs, rewards, terms, truncs, infos = env.step(actions)
    
    assert terms["supplier"] == True
    assert rewards["supplier"] == -0.1
    assert infos["supplier"]["result"] == "quit"

def test_timeout(env):
    env = NegotiatorEnv(config={"max_rounds": 2})
    env.reset()
    
    # Round 1
    env.step({"supplier": {"type": 1, "price": [5000]}})
    # Round 2
    env.step({"retailer": {"type": 1, "price": [6000]}})
    
    # Round 3 (Should trigger timeout)
    obs, rewards, terms, truncs, infos = env.step({"supplier": {"type": 1, "price": [5500]}})
    
    assert truncs["supplier"] == True
    assert rewards["supplier"] == -0.05

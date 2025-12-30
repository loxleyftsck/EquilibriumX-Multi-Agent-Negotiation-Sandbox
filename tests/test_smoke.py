import pytest
from src.environment.negotiator_env import NegotiatorEnv

@pytest.fixture
def env():
    return NegotiatorEnv()

def test_env_initialization(env):
    """Smoke test to ensure environment can be instantiated."""
    assert env is not None
    assert env.possible_agents == ["supplier", "retailer"]

def test_api_import():
    """Smoke test to ensure API module is importable."""
    from src.api.app import app
    assert app.title == "EquilibriumX API"

import traceback
import sys

try:
    from src.environment.negotiator_env import NegotiatorEnv
    env = NegotiatorEnv(config={'num_agents': 3})
    print("SUCCESS!")
except Exception as e:
    traceback.print_exc()
    sys.exit(1)

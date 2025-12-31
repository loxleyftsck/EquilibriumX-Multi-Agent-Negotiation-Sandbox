import os
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.environment.negotiator_env import NegotiatorEnv
from src.utils.mlflow_logger import MLflowLogger

# A simple Policy Network
class SimplePolicy(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(SimplePolicy, self).__init__()
        self.common = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU()
        )
        self.type_head = nn.Linear(64, output_dim)
        self.price_head = nn.Linear(64, 1)

    def forward(self, x):
        features = self.common(x)
        type_logits = self.type_head(features)
        price_pred = torch.sigmoid(self.price_head(features))
        return type_logits, price_pred

def train_simple():
    print("=== EquilibriumX Simple RL Training (Non-Ray) ===")
    env = NegotiatorEnv(config={"max_rounds": 10})
    logger = MLflowLogger()
    
    # 10 is the size of observation space defined in negotiator_env.py
    # 3 is the number of action types (Accept, Counter, Quit)
    supplier_policy = SimplePolicy(10, 3)
    retailer_policy = SimplePolicy(10, 3)
    
    optimizer = optim.Adam(list(supplier_policy.parameters()) + list(retailer_policy.parameters()), lr=1e-3)
    
    with logger.start_run(run_name="Simple_RL_Windows_Run"):
        logger.log_params({"algo": "SimplePolicyGradient", "backend": "torch_local"})
        
        for ep in range(20): # Small number for demonstration
            obs, info = env.reset()
            done = False
            total_rewards = {"supplier": 0, "retailer": 0}
            
            while not done:
                # Get current proposer
                proposer = env.current_proposer
                policy = supplier_policy if proposer == "supplier" else retailer_policy
                
                # Inference
                state_tensor = torch.from_numpy(obs[proposer]).float().unsqueeze(0)
                type_logits, price_pred = policy(state_tensor)
                
                # Select action (Simple Greedy for demo)
                action_type = torch.argmax(type_logits, dim=1).item()
                # If round 0, don't allow Accept (0) or Quit (2) for a more interesting run
                if env.current_round == 0:
                    action_type = 1 # COUNTER
                
                raw_price = price_pred.item() * 10000.0
                
                actions = {
                    proposer: {
                        "type": action_type,
                        "price": np.array([raw_price], dtype=np.float32)
                    }
                }
                
                obs, rewards, terms, truncs, infos = env.step(actions)
                
                for k, v in rewards.items():
                    total_rewards[k] += v
                
                done = any(terms.values()) or any(truncs.values())
            
            # Simple logging
            print(f"Episode {ep}: Rewards = {total_rewards}")
            logger.log_metrics({
                "supplier_reward": total_rewards["supplier"],
                "retailer_reward": total_rewards["retailer"]
            }, step=ep)

    print("\nSimple run complete. Metrics logged to MLflow.")

if __name__ == "__main__":
    train_simple()

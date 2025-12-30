import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ray
from ray import air, tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.tune.registry import register_env
from src.environment.negotiator_env import NegotiatorEnv
from src.utils.mlflow_logger import MLflowLogger

def env_creator(env_config):
    return NegotiatorEnv(config=env_config)

def train():
    # 1. Initialize Ray
    # On some Windows systems, Ray child process management can fail.
    # Using local_mode=True as a fallback or limiting workers.
    try:
        ray.init(ignore_reinit_error=True, num_cpus=4)
    except Exception as e:
        print(f"Standard Ray init failed: {e}. Falling back to local_mode.")
        ray.init(local_mode=True)
    
    # 2. Register Environment
    register_env("negotiator_env", env_creator)
    
    # 3. Initialize Logger
    logger = MLflowLogger()
    
    # 4. Define Config
    config = (
        PPOConfig()
        .environment("negotiator_env", env_config={"max_rounds": 10})
        .framework("torch")
        .rollouts(num_rollout_workers=2)
        .training(
            lr=3e-4,
            gamma=0.99,
            lambda_=0.95,
            clip_param=0.2,
            train_batch_size=4000
        )
        .multi_agent(
            policies={"supplier", "retailer"},
            policy_mapping_fn=lambda agent_id, *args, **kwargs: agent_id,
        )
        .debugging(log_level="ERROR")
    )
    
    # 5. Start Training Run with MLflow
    with logger.start_run(run_name="MAPPO_Negotiation_Baseline"):
        logger.log_params({
            "algo": "PPO",
            "framework": "torch",
            "lr": 3e-4,
            "gamma": 0.99
        })
        
        algo = config.build()
        
        for i in range(10): # Initial small run for verification
            result = algo.train()
            
            # Log metrics to MLflow
            metrics = {
                "episode_reward_mean": result.get("episode_reward_mean", 0),
                "episodes_total": result.get("episodes_total", 0),
                "training_iteration": i
            }
            logger.log_metrics(metrics, step=i)
            
            if i % 1 == 0:
                print(f"Iteration {i}: Reward Mean = {metrics['episode_reward_mean']:.2f}")
        
        # 6. Save Model
        checkpoint_dir = algo.save("models/ppo_baseline")
        print(f"Checkpoint saved at: {checkpoint_dir}")
        logger.log_artifact(checkpoint_dir)

if __name__ == "__main__":
    train()

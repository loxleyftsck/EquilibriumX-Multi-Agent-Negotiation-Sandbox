"""
Test Script: Verify MLflow Integration
Tests MLflow logging capabilities for EquilibriumX experiments.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.mlflow_logger import MLflowLogger
import mlflow

def test_mlflow_basic():
    print("\n" + "="*70)
    print(" 🧪 TEST 1: Basic MLflow Logging")
    print("="*70)
    
    logger = MLflowLogger(experiment_name="Test_N_Agent_Environment")
    
    with logger.start_run(run_name="test_3_agent"):
        # Log parameters
        params = {
            "num_agents": 3,
            "num_items": 2,
            "max_rounds": 10,
            "algorithm": "PPO"
        }
        logger.log_params(params)
        print(f"✓ Logged parameters: {params}")
        
        # Log metrics
        for step in range(5):
            metrics = {
                "avg_reward": 0.5 + (step * 0.1),
                "deal_rate": 0.6 + (step * 0.05),
                "avg_rounds": 5 - (step * 0.2)
            }
            logger.log_metrics(metrics, step=step)
            print(f"  Step {step}: reward={metrics['avg_reward']:.2f}, deal_rate={metrics['deal_rate']:.2f}")
        
        print("✓ Logged 5 steps of metrics")
    
    print("\n✅ Basic MLflow logging works!")

def test_mlflow_n_agent_simulation():
    print("\n" + "="*70)
    print(" 🧪 TEST 2: N-Agent Simulation Logging")
    print("="*70)
    
    from src.environment.negotiator_env import NegotiatorEnv
    import numpy as np
    
    logger = MLflowLogger(experiment_name="EquilibriumX_Negotiation")
    
    for n_agents in [3, 5]:
        with logger.start_run(run_name=f"demo_{n_agents}_agents"):
            # Log config
            config = {
                "num_agents": n_agents,
                "num_items": 2,
                "max_rounds": 10,
                "environment": "NegotiatorEnv"
            }
            logger.log_params(config)
            
            # Run simulation
            env = NegotiatorEnv(config=config)
            obs, info = env.reset()
            
            deals = 0
            total_rounds = 0
            
            for episode in range(3):
                obs, info = env.reset()
                for round_num in range(10):
                    proposer = env.current_proposer
                    action = {
                        "type": 1,
                        "price": np.random.uniform(5000, 7500, size=(config["num_items"],))
                    }
                    obs, rewards, terms, truncs, infos = env.step({proposer: action})
                    
                    if any(terms.values()):
                        deals += 1
                        total_rounds += round_num + 1
                        break
            
            # Log results
            metrics = {
                "deal_rate": deals / 3,
                "avg_rounds": total_rounds / max(deals, 1)
            }
            logger.log_metrics(metrics)
            
            print(f"  {n_agents}-agent: deal_rate={metrics['deal_rate']:.2f}, avg_rounds={metrics['avg_rounds']:.1f}")
    
    print("\n✅ N-agent simulation logging works!")

def check_mlflow_ui():
    print("\n" + "="*70)
    print(" 📊 MLflow UI Information")
    print("="*70)
    print("\nTo view your experiments in the MLflow UI, run:")
    print("  cd c:\\Users\\LENOVO\\Documents\\EquilibriumX Multi-Agent Negotiation Sandbox")
    print("  mlflow ui")
    print("\nThen open: http://localhost:5000")
    print("="*70)

if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# MLflow/MLOps Integration Test")
    print("#"*70)
    
    try:
        test_mlflow_basic()
        test_mlflow_n_agent_simulation()
        check_mlflow_ui()
        
        print("\n" + "="*70)
        print("✅✅✅ ALL MLFLOW TESTS PASSED! ✅✅✅")
        print("="*70)
        print("\n✨ MLflow integration is fully functional!\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

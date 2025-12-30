import mlflow
import os
from datetime import datetime

class MLflowLogger:
    def __init__(self, experiment_name="EquilibriumX_Negotiation"):
        self.experiment_name = experiment_name
        mlflow.set_experiment(self.experiment_name)
        
    def start_run(self, run_name=None):
        if run_name is None:
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return mlflow.start_run(run_name=run_name)
        
    def log_params(self, params: dict):
        mlflow.log_params(params)
        
    def log_metrics(self, metrics: dict, step: int = None):
        mlflow.log_metrics(metrics, step=step)
        
    def log_model(self, model, artifact_path="model"):
        mlflow.pytorch.log_model(model, artifact_path)
        
    def log_artifact(self, local_path, artifact_path=None):
        mlflow.log_artifact(local_path, artifact_path)

# Example Usage Template
if __name__ == "__main__":
    logger = MLflowLogger()
    with logger.start_run(run_name="Initial_Restructure_Test"):
        logger.log_params({"learning_rate": 0.001, "batch_size": 32})
        logger.log_metrics({"accuracy": 0.85}, step=1)
        print("MLflow tracking initialized for EquilibriumX.")

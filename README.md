# EquilibriumX: Multi-Agent Negotiation Sandbox

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MLflow](https://img.shields.io/badge/Tracking-MLflow-blueviolet)](https://mlflow.org/)
[![IEEE Paper](https://img.shields.io/badge/IEEE-Paper-blue)](./paper/equilibriumx_paper.pdf)

**EquilibriumX** is a hybrid multi-agent negotiation platform that bridges the gap between game-theoretic strategic optimality and human-like natural language communication.

## 🌟 Key Features

- 🤖 **Hybrid Neuro-Symbolic AI**: Combines Reinforcement Learning (RL) for strategy with Large Language Models (LLMs) for communication.
- 📉 **Nash Convergence**: Agents learn to converge toward theoretical Nash Equilibrium prices in bilateral bargaining.
- 📈 **Experiment Tracking**: Integrated with **MLflow** for robust monitoring of hyperparameters, training metrics, and model artifacts.
- 💬 **Natural Communication**: LLM-driven generation of context-aware negotiation messages with configurable personality styles.
- 📊 **Real-time Visualization**: Interactive dashboard with price convergence charts, utility tracking, and Nash distance monitoring.
- 🚀 **Distributed Scaling**: Built on Ray RLlib for high-performance multi-agent training.

## 🏗️ Architecture

The system is composed of four primary layers:

![EquilibriumX Architecture](./assets/equilibriumx_architecture.png)

1. **RL Engine (Ray RLlib)**: Handles strategic decision-making using PPO/SAC.
2. **LLM Service (Ollama)**: Translates strategic actions into human-interpretable messages.
3. **Tracking Layer (MLflow)**: Logs every negotiation run, hyperparameter sweep, and model checkpoint.
4. **API Gateway (FastAPI)**: Manages real-time WebSocket streams and session states.
5. **Frontend (Next.js)**: Provides an interactive user interface for monitoring and control.

## 📁 Repository Structure

- `src/`: Core logic for agents, environments, and LLM integration.
- `docs/`: In-depth documentation and project roadmap.
- `paper/`: Research paper (IEEE format), theoretical derivations, and UML diagrams.
- `notebooks/`: R&D experiments and analysis.
- `scripts/`: Entry points for training and evaluation.

## 🚀 Getting Started

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up MLflow:

   ```bash
   mlflow ui
   ```

3. Refer to the [Technical Documentation](./docs/README.txt) for detailed setup and usage.

## 🎓 Research

Read our full paper: [EquilibriumX: A Hybrid RL-LLM Framework for Multi-Agent Negotiation](./paper/equilibriumx_paper.pdf)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

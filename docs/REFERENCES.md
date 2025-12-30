# 📚 Recommended Reading & References

This list curates the most essential books and research papers for understanding the theoretical foundations of **EquilibriumX**.

## 📖 Textbooks (Foundational Theory)

### 1. Game Theory & Mechanism Design

* **"Multiagent Systems: Algorithmic, Game-Theoretic, and Logical Foundations"** by Yoav Shoham & Kevin Leyton-Brown (2009).
  * *Why*: The "bible" of multi-agent systems. Covers Nash equilibrium, mechanism design, and bargaining theory extensively.
  * *Key Chapters*: 3 (Game Theory), 11 (Bargaining).

* **"Game Theory"** by Drew Fudenberg & Jean Tirole (1991).
  * *Why*: Rigorous mathematical treatment of sequential games and Perfect Bayesian Equilibrium.
  * *Relevance*: Essential for understanding the "Subgame Perfect Equilibrium" concept used in our paper.

### 2. Reinforcement Learning

* **"Reinforcement Learning: An Introduction"** (2nd Ed.) by Richard S. Sutton & Andrew G. Barto (2018).
  * *Why*: The standard introduction to RL.
  * *Key Chapters*: 13 (Policy Gradient Methods - basis for PPO).

## 📄 Key Research Papers (Implementation)

### Multi-Agent Negotiation (MARL)

1. **"Deal or No Deal? End-to-End Learning for Negotiation Dialogues"** (Lewis et al., Facebook AI Research, 2017).
    * *Significance*: First major work to combine RL with language models (LSTMs at the time) for negotiation.
    * *Link*: [arXiv:1706.05125](https://arxiv.org/abs/1706.05125)

2. **"Emergent Competing Strategic Behaviors in Multi-Agent Negotiation"** (Cao et al., DeepMind, 2018).
    * *Significance*: Demonstrates how agents learn to communicate and devise strategies in bargaining channels.

### LLMs & Strategic Reasoning

3. **"Improving Language Model Negotiation with Self-Play and In-Context Learning"** (Fu et al., 2023).
    * *Significance*: Modern approach using LLMs (like GPT-4) to simulate negotiation, directly relevant to our hybrid architecture.
    * *Link*: [arXiv:2305.10142](https://arxiv.org/abs/2305.10142)

2. **"Human-level play in the game of Diplomacy by combining language models with strategic reasoning"** (Bakhtin et al., Meta AI, 2022).
    * *Significance*: The "Cicero" paper. Shows how to combine strategic planning (RL/Search) with natural language generation.
    * *Link*: [Science Magazine](https://www.science.org/doi/10.1126/science.ade9097)

## 🛠️ Technical References (Architecture)

* **"Proximal Policy Optimization Algorithms"** (Schulman et al., OpenAI, 2017).
  * *Relevance*: The PPO algorithm used in `src/agents/ppo_agent.py`.
* **"PettingZoo: Gym for Multi-Agent Reinforcement Learning"** (Terry et al., 2021).
  * *Relevance*: The standard interface used for our `BargainingEnv`.

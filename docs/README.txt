# EquilibriumX: Multi-Agent Negotiation Sandbox
## Complete Technical Documentation

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Theoretical Foundation](#theoretical-foundation)
3. [System Architecture](#system-architecture)
4. [Implementation Details](#implementation-details)
5. [Development Roadmap](#development-roadmap)
6. [API Specification](#api-specification)
7. [Evaluation Metrics](#evaluation-metrics)
8. [Deployment Guide](#deployment-guide)

---

## 🎯 Executive Summary

**EquilibriumX** is a cutting-edge multi-agent negotiation platform that combines reinforcement learning (RL) with large language models (LLMs) to simulate realistic bargaining scenarios between autonomous agents. The system demonstrates convergence toward Nash Equilibrium while maintaining human-like communication patterns.

### Key Innovation
**Hybrid Neuro-Symbolic Architecture**: RL agents handle strategic decision-making (pricing, timing), while LLMs generate contextually appropriate natural language responses with configurable personality traits.

### Core Features
- **Game-theoretic foundation**: Incomplete information bargaining games
- **RL-driven strategy**: PPO/SAC algorithms for optimal policy learning
- **LLM-powered communication**: Natural language generation via Ollama
- **Real-time visualization**: Interactive dashboard showing convergence to equilibrium
- **Scalable architecture**: Ray RLlib for distributed training

---

## 📐 Theoretical Foundation

### 1. Game Theory Framework

#### Problem Definition: Bilateral Bargaining
Two agents negotiate over the price and quantity of goods:
- **Agent S (Supplier)**: Wants to maximize selling price
- **Agent R (Retailer)**: Wants to minimize buying price

#### Game Characteristics
- **Type**: Sequential bargaining game with incomplete information
- **Information Structure**: Each agent has private reservation prices
- **Time Horizon**: Finite (T rounds with deadline)
- **Discount Factor**: δ ∈ (0,1) representing time preference

#### Nash Equilibrium Conditions

For a price agreement p* to be Nash Equilibrium:

1. **Individual Rationality**:
   - p* ≥ Vₛ (Supplier's valuation)
   - p* ≤ Vᵣ (Retailer's valuation)

2. **No Profitable Deviation**:
   - If Agent S raises price → Agent R rejects → U(S) = 0
   - If Agent S lowers price → Lower profit than p*
   - Similar logic for Agent R

3. **Mathematical Formulation**:
   ```
   p* = arg max[Uₛ(p) + Uᵣ(p)]
   subject to: Vₛ ≤ p ≤ Vᵣ
   ```

#### Pareto Optimality
A deal is Pareto Optimal when no agent can improve their utility without harming the other. In bargaining:
```
p* ∈ [Vₛ, Vᵣ] where surplus = Vᵣ - Vₛ is maximized
```

### 2. Reinforcement Learning Formulation

#### State Space (S)
```python
state = {
    'current_price': float,           # Latest offered price
    'offer_history': List[float],     # Last k offers
    'round_number': int,              # Current negotiation round
    'time_remaining': float,          # Normalized (0-1)
    'agent_role': str,                # 'supplier' or 'retailer'
    'estimated_opponent_reservation': float,  # Learned belief
    'deal_zone': float,               # |current_price - estimated_BATNA|
    'negotiation_momentum': float     # Rate of price change
}
```

#### Action Space (A)
```python
action_space = Discrete(3) + Box(low=0, high=max_price)

Actions:
1. ACCEPT: Accept current offer
2. COUNTER: Make counter-offer with new price
3. WALK_AWAY: Terminate negotiation (Nash threat point)
```

#### Reward Function (Critical Component)

**Supplier Reward**:
```python
def reward_supplier(deal_price, valuation, round, max_rounds):
    if deal_price is None:  # No deal
        return -10  # Opportunity cost
    
    base_profit = deal_price - valuation
    discount = (1 - round/max_rounds) ** 2  # Time penalty
    
    # Bonus for quick deals
    speed_bonus = 5 if round < max_rounds * 0.3 else 0
    
    return base_profit * discount + speed_bonus
```

**Retailer Reward**:
```python
def reward_retailer(deal_price, valuation, round, max_rounds):
    if deal_price is None:
        return -10
    
    base_profit = valuation - deal_price  # Savings
    discount = (1 - round/max_rounds) ** 2
    
    speed_bonus = 5 if round < max_rounds * 0.3 else 0
    
    return base_profit * discount + speed_bonus
```

**Design Rationale**:
- **Exponential discount**: Mimics real-world time value of money
- **Negative reward for no-deal**: Prevents excessive risk-taking
- **Speed bonus**: Encourages efficient negotiation

#### Bellman Equation
```
Q(s,a) = E[r + γ · max Q(s',a') | s,a]
       = E[Immediate Profit + Discounted Future Value]
```

### 3. Learning Dynamics

#### Opponent Modeling
Agents maintain belief distribution over opponent's reservation price:
```python
belief_opponent_valuation ~ N(μ, σ²)

# Update rule (Bayesian):
μₜ₊₁ = μₜ + α(observed_offer - μₜ)
σₜ₊₁² = (1 - β)σₜ²
```

#### Exploration-Exploitation Trade-off
```python
epsilon = max(0.01, 0.5 * (0.995 ** episode))  # Decay schedule

action = {
    random_action()      if random() < epsilon  # Explore
    policy(state)        otherwise              # Exploit
}
```

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Negotiation  │  │  Analytics   │  │   Control    │     │
│  │   Chat UI    │  │  Dashboard   │  │   Panel      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │ WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              API Gateway (FastAPI + Redis)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Session    │  │   Message    │  │    State     │     │
│  │  Management  │  │   Queue      │  │   Storage    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
           │                                      │
           ▼                                      ▼
┌──────────────────────┐              ┌──────────────────────┐
│   RL Engine          │              │   LLM Service        │
│   (Ray RLlib)        │              │   (Ollama)           │
│                      │              │                      │
│  ┌────────────────┐ │              │  ┌────────────────┐ │
│  │ Supplier Agent │ │◄────────────►│  │ Prompt Engine  │ │
│  │    (PPO)       │ │  Strategy    │  │                │ │
│  └────────────────┘ │              │  └────────────────┘ │
│                      │              │          │          │
│  ┌────────────────┐ │              │  ┌────────────────┐ │
│  │ Retailer Agent │ │◄────────────►│  │  Style Models  │ │
│  │    (PPO)       │ │  Translation │  │  (Aggressive/  │ │
│  └────────────────┘ │              │  │  Cooperative)  │ │
│                      │              │  └────────────────┘ │
└──────────────────────┘              └──────────────────────┘
           │                                      │
           ▼                                      ▼
┌─────────────────────────────────────────────────────────────┐
│            Database (PostgreSQL + TimescaleDB)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Agent       │  │  Negotiation │  │  Performance │     │
│  │  Policies    │  │  Logs        │  │  Metrics     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Frontend Layer (Next.js + TypeScript)

**Key Components**:
- **NegotiationChat**: Real-time message display with typing indicators
- **AnalyticsDashboard**: Live metrics visualization
- **ControlPanel**: Simulation parameters configuration

**Tech Stack**:
```json
{
  "framework": "Next.js 14",
  "language": "TypeScript",
  "state": "Zustand",
  "ui": "shadcn/ui + Tailwind",
  "charts": "Recharts + D3.js",
  "websocket": "Socket.io-client"
}
```

#### 2. API Gateway (FastAPI)

**Core Responsibilities**:
- WebSocket management for real-time updates
- Request routing to RL/LLM services
- Session state management
- Rate limiting and authentication

**Key Endpoints**:
```python
POST   /api/v1/simulation/start
GET    /api/v1/simulation/{session_id}/status
WS     /api/v1/simulation/{session_id}/stream
POST   /api/v1/agent/train
GET    /api/v1/agent/{agent_id}/policy
POST   /api/v1/metrics/export
```

#### 3. RL Engine (Ray RLlib)

**Training Infrastructure**:
```python
# Ray cluster configuration
ray.init(
    num_cpus=8,
    num_gpus=1,
    include_dashboard=True
)

# Multi-agent PPO trainer
trainer = PPOTrainer(
    env=BargainingEnv,
    config={
        "multiagent": {
            "policies": {
                "supplier": (PPOTFPolicy, obs_space, act_space, {}),
                "retailer": (PPOTFPolicy, obs_space, act_space, {})
            },
            "policy_mapping_fn": lambda agent_id: agent_id,
            "policies_to_train": ["supplier", "retailer"]
        },
        "framework": "torch",
        "num_workers": 4,
        "num_envs_per_worker": 2
    }
)
```

#### 4. LLM Service (Ollama)

**Prompt Template**:
```python
NEGOTIATION_PROMPT = """
You are a {role} in a negotiation. Your personality is {style}.

Current Context:
- Your internal strategy suggests: {action}
- Price point: ${price}
- Round: {round}/{max_rounds}
- History: {offer_history}

Generate a natural negotiation message that:
1. Reflects the {style} personality
2. Communicates the strategic intent: {action}
3. Stays within 2-3 sentences
4. Maintains professional business tone

Response:"""
```

---

## 💻 Implementation Details

### Phase 1: Environment Implementation

#### Custom PettingZoo Environment

```python
from pettingzoo import ParallelEnv
from gymnasium import spaces
import numpy as np

class BargainingEnv(ParallelEnv):
    metadata = {'name': 'bargaining_v1'}
    
    def __init__(self, config):
        super().__init__()
        self.max_rounds = config.get('max_rounds', 10)
        self.supplier_valuation = config.get('supplier_val', 5000)
        self.retailer_valuation = config.get('retailer_val', 8000)
        
        self.possible_agents = ['supplier', 'retailer']
        self.agents = self.possible_agents[:]
        
        # Observation space: [current_price, round, time_left, offer_history]
        self.observation_spaces = {
            agent: spaces.Box(
                low=0, 
                high=10000, 
                shape=(5,), 
                dtype=np.float32
            ) for agent in self.possible_agents
        }
        
        # Action space: [action_type, price_value]
        # action_type: 0=Accept, 1=Counter, 2=WalkAway
        self.action_spaces = {
            agent: spaces.Dict({
                'action_type': spaces.Discrete(3),
                'price': spaces.Box(low=0, high=10000, shape=(1,))
            }) for agent in self.possible_agents
        }
        
        self.reset()
    
    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.round = 0
        self.current_offer = None
        self.offer_history = []
        self.active_negotiator = 'supplier'  # First mover
        
        observations = {
            agent: self._get_observation(agent) 
            for agent in self.agents
        }
        infos = {agent: {} for agent in self.agents}
        
        return observations, infos
    
    def _get_observation(self, agent):
        """Construct observation vector for an agent"""
        return np.array([
            self.current_offer or 0,
            self.round,
            (self.max_rounds - self.round) / self.max_rounds,  # Normalized time
            np.mean(self.offer_history[-3:]) if self.offer_history else 0,
            len(self.offer_history)
        ], dtype=np.float32)
    
    def step(self, actions):
        """Execute one step of negotiation"""
        self.round += 1
        rewards = {agent: 0 for agent in self.agents}
        terminations = {agent: False for agent in self.agents}
        truncations = {agent: False for agent in self.agents}
        
        # Only process action from active negotiator
        active_action = actions[self.active_negotiator]
        action_type = active_action['action_type']
        offered_price = active_action['price'][0]
        
        if action_type == 0:  # ACCEPT
            deal_price = self.current_offer
            rewards = self._calculate_rewards(deal_price)
            terminations = {agent: True for agent in self.agents}
            
        elif action_type == 2:  # WALK AWAY
            rewards = {agent: -10 for agent in self.agents}  # Penalty
            terminations = {agent: True for agent in self.agents}
            
        else:  # COUNTER OFFER
            self.current_offer = offered_price
            self.offer_history.append(offered_price)
            
            # Switch active negotiator
            self.active_negotiator = (
                'retailer' if self.active_negotiator == 'supplier' 
                else 'supplier'
            )
        
        # Check timeout
        if self.round >= self.max_rounds:
            rewards = {agent: -5 for agent in self.agents}
            truncations = {agent: True for agent in self.agents}
        
        observations = {
            agent: self._get_observation(agent) 
            for agent in self.agents
        }
        infos = {
            agent: {'round': self.round, 'active': self.active_negotiator} 
            for agent in self.agents
        }
        
        return observations, rewards, terminations, truncations, infos
    
    def _calculate_rewards(self, deal_price):
        """Calculate rewards for both agents when deal is reached"""
        if deal_price is None:
            return {'supplier': -10, 'retailer': -10}
        
        # Time discount factor
        time_discount = (1 - self.round / self.max_rounds) ** 2
        
        # Supplier profit
        supplier_profit = (deal_price - self.supplier_valuation) * time_discount
        
        # Retailer profit (savings)
        retailer_profit = (self.retailer_valuation - deal_price) * time_discount
        
        # Bonus for quick deals
        speed_bonus = 5 if self.round < self.max_rounds * 0.3 else 0
        
        return {
            'supplier': supplier_profit + speed_bonus,
            'retailer': retailer_profit + speed_bonus
        }
```

### Phase 2: RL Training Pipeline

#### PPO Agent Configuration

```python
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.policy.policy import PolicySpec

def create_training_config():
    config = (
        PPOConfig()
        .environment(
            env=BargainingEnv,
            env_config={
                'max_rounds': 10,
                'supplier_val': np.random.randint(4000, 6000),
                'retailer_val': np.random.randint(7000, 9000)
            }
        )
        .framework('torch')
        .training(
            lr=3e-4,
            gamma=0.99,
            lambda_=0.95,
            clip_param=0.2,
            vf_clip_param=10.0,
            entropy_coeff=0.01,
            train_batch_size=4000,
            sgd_minibatch_size=128,
            num_sgd_iter=10
        )
        .multi_agent(
            policies={
                'supplier': PolicySpec(
                    observation_space=spaces.Box(0, 10000, (5,)),
                    action_space=spaces.Dict({
                        'action_type': spaces.Discrete(3),
                        'price': spaces.Box(0, 10000, (1,))
                    })
                ),
                'retailer': PolicySpec(
                    observation_space=spaces.Box(0, 10000, (5,)),
                    action_space=spaces.Dict({
                        'action_type': spaces.Discrete(3),
                        'price': spaces.Box(0, 10000, (1,))
                    })
                )
            },
            policy_mapping_fn=lambda agent_id, *args, **kwargs: agent_id,
            policies_to_train=['supplier', 'retailer']
        )
        .resources(
            num_gpus=1,
            num_cpus_per_worker=1
        )
        .rollouts(
            num_rollout_workers=4,
            num_envs_per_worker=2
        )
    )
    
    return config

# Training loop
def train_agents(num_iterations=1000):
    config = create_training_config()
    algo = config.build()
    
    best_reward = -float('inf')
    
    for i in range(num_iterations):
        result = algo.train()
        
        # Log metrics
        episode_reward_mean = result['episode_reward_mean']
        print(f"Iteration {i}: Reward = {episode_reward_mean:.2f}")
        
        # Save checkpoint
        if episode_reward_mean > best_reward:
            best_reward = episode_reward_mean
            checkpoint_path = algo.save()
            print(f"Saved checkpoint: {checkpoint_path}")
        
        # Check convergence to Nash Equilibrium
        if i % 50 == 0:
            eval_results = evaluate_nash_convergence(algo)
            print(f"Nash Distance: {eval_results['nash_distance']:.4f}")
    
    return algo
```

### Phase 3: LLM Integration

#### Ollama Communication Layer

```python
import requests
import json

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama3"
    
    def generate_negotiation_message(
        self, 
        role: str,
        style: str,
        action: str,
        price: float,
        context: dict
    ) -> str:
        """Generate natural language negotiation message"""
        
        prompt = f"""You are a {role} in a negotiation. Your personality is {style}.

Current Context:
- Your internal strategy suggests: {action}
- Price point: ${price:,.2f}
- Round: {context['round']}/{context['max_rounds']}
- Previous offers: {context['offer_history']}

Generate a natural negotiation message that:
1. Reflects the {style} personality
2. Communicates the strategic intent: {action}
3. Stays within 2-3 sentences
4. Maintains professional business tone

Response:"""
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 150
                }
            }
        )
        
        if response.status_code == 200:
            return response.json()['response'].strip()
        else:
            return f"[{role}] ${price:,.2f}"  # Fallback
    
    def generate_with_style_examples(self, **kwargs):
        """Generate with few-shot examples for consistency"""
        
        style_examples = {
            "aggressive": [
                "That price is unacceptable. I need at least $7,500 or I walk.",
                "You're wasting my time. Final offer: $6,800."
            ],
            "cooperative": [
                "I appreciate your offer. Could we meet at $6,500 for mutual benefit?",
                "Let's find a win-win. How about $6,200 to build long-term partnership?"
            ],
            "analytical": [
                "Based on market data, $6,300 represents fair value. Here's my analysis...",
                "The cost structure supports $6,400. Let me explain the breakdown."
            ]
        }
        
        style = kwargs.get('style', 'cooperative')
        examples = style_examples.get(style, style_examples['cooperative'])
        
        enhanced_prompt = f"{kwargs['prompt']}\n\nStyle Examples:\n"
        enhanced_prompt += "\n".join(f"- {ex}" for ex in examples[:2])
        
        # Call generation with enhanced prompt
        return self.generate_negotiation_message(**kwargs)
```

### Phase 4: API Server

#### FastAPI Backend

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uuid

app = FastAPI(title="EquilibriumX API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SimulationConfig(BaseModel):
    supplier_valuation: float
    retailer_valuation: float
    max_rounds: int = 10
    supplier_style: str = "cooperative"
    retailer_style: str = "cooperative"

class SimulationManager:
    def __init__(self):
        self.sessions = {}
        self.rl_algo = None  # Load trained model
        self.llm_client = OllamaClient()
    
    async def run_simulation(self, session_id: str, config: SimulationConfig, websocket: WebSocket):
        """Run negotiation simulation and stream updates"""
        
        env = BargainingEnv({
            'max_rounds': config.max_rounds,
            'supplier_val': config.supplier_valuation,
            'retailer_val': config.retailer_valuation
        })
        
        obs, _ = env.reset()
        done = False
        
        messages = []
        
        while not done:
            # Get RL actions
            actions = {}
            for agent in env.agents:
                policy_id = agent
                action = self.rl_algo.compute_single_action(
                    obs[agent], 
                    policy_id=policy_id
                )
                actions[agent] = action
            
            # Generate natural language
            for agent, action in actions.items():
                if agent == env.active_negotiator:
                    action_type = ['ACCEPT', 'COUNTER', 'WALK_AWAY'][action['action_type']]
                    price = action['price'][0]
                    
                    style = (config.supplier_style if agent == 'supplier' 
                            else config.retailer_style)
                    
                    message_text = self.llm_client.generate_negotiation_message(
                        role=agent,
                        style=style,
                        action=action_type,
                        price=price,
                        context={
                            'round': env.round,
                            'max_rounds': env.max_rounds,
                            'offer_history': env.offer_history[-3:]
                        }
                    )
                    
                    message = {
                        'agent': agent,
                        'round': env.round,
                        'action': action_type,
                        'price': price,
                        'message': message_text,
                        'timestamp': time.time()
                    }
                    
                    messages.append(message)
                    
                    # Stream to frontend
                    await websocket.send_json(message)
                    await asyncio.sleep(1)  # Simulate thinking time
            
            # Environment step
            obs, rewards, terminations, truncations, infos = env.step(actions)
            
            done = any(terminations.values()) or any(truncations.values())
        
        # Send final results
        final_result = {
            'type': 'SIMULATION_COMPLETE',
            'deal_reached': any(r > 0 for r in rewards.values()),
            'final_price': env.current_offer,
            'total_rounds': env.round,
            'rewards': rewards,
            'messages': messages
        }
        
        await websocket.send_json(final_result)

manager = SimulationManager()

@app.websocket("/api/v1/simulation/{session_id}/stream")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    try:
        # Receive configuration
        config_data = await websocket.receive_json()
        config = SimulationConfig(**config_data)
        
        # Run simulation
        await manager.run_simulation(session_id, config, websocket)
        
    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
    except Exception as e:
        await websocket.send_json({'error': str(e)})
        await websocket.close()

@app.post("/api/v1/simulation/start")
async def start_simulation(config: SimulationConfig):
    session_id = str(uuid.uuid4())
    return {
        'session_id': session_id,
        'websocket_url': f'/api/v1/simulation/{session_id}/stream'
    }
```

---

## 📊 Evaluation Metrics

### 1. Convergence to Nash Equilibrium

**Nash Distance Metric**:
```python
def calculate_nash_distance(deal_price, supplier_val, retailer_val):
    """
    Measures how far the deal is from theoretical Nash price
    Nash price = (supplier_val + retailer_val) / 2 (in symmetric case)
    """
    nash_price = (supplier_val + retailer_val) / 2
    return abs(deal_price - nash_price) / nash_price

# Target: Distance < 0.05 (within 5% of Nash equilibrium)
```

### 2. Pareto Efficiency

```python
def is_pareto_optimal(deal_price, supplier_val, retailer_val):
    """
    Check if deal is in the Pareto optimal range
    """
    return supplier_val <= deal_price <= retailer_val

def pareto_efficiency_score(deal_price, supplier_val, retailer_val):
    """
    Measure how much of potential surplus is captured
    """
    if not is_pareto_optimal(deal_price, supplier_val, retailer_val):
        return 0.0
    
    max_surplus = retailer_val - supplier_val
    actual_surplus = deal_price - supplier_val  # Supplier's share
    
    # Ideal is 50-50 split
    ideal_split = max_surplus / 2
    deviation = abs(actual_surplus - ideal_split)
    
    return 1 - (deviation / ideal_split)
```

### 3. Negotiation Efficiency

```python
def negotiation_efficiency(rounds_taken, max_rounds, deal_reached):
    """
    Measure how efficiently agents reached agreement
    """
    if not deal_reached:
        return 0.0
    
    time_efficiency = 1 - (rounds_taken / max_rounds)
    
    # Bonus for very quick deals
    if rounds_taken <= 3:
        time_efficiency += 0.2
    
    return min(1.0, time_efficiency)
```

### 4. LLM Quality Metrics

```python
def evaluate_message_quality(message, action, price):
    """
    Evaluate naturalness and coherence of LLM-generated messages
    """
    metrics = {
        'contains_price': str(price) in message,
        'appropriate_length': 10 < len(message.split()) < 50,
        'action_alignment': action.lower() in message.lower(),
        'professional_tone': not any(word in message.lower() 
                                     for word in ['stupid', 'idiot', 'dumb'])
    }
    
    return sum(metrics.values()) / len(metrics)
```

---

## 🚀 Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Working RL environment with basic agents

**Deliverables**:
- [ ] Custom PettingZoo environment
- [ ] State/action space validation
- [ ] Reward function implementation
- [ ] Unit tests for environment logic
- [ ] Simple random agents for testing

**Success Criteria**:
- Agents can complete 100 episodes without crashes
- Reward signals are correctly calculated
- Environment respects game rules (e.g., no negative prices)

### Phase 2: RL Training (Weeks 3-4)
**Goal**: Agents learn to converge to Nash Equilibrium

**Deliverables**:
- [ ] Ray RLlib integration
- [ ] PPO/SAC algorithm configuration
- [ ] Multi-agent training pipeline
- [ ] Opponent modeling implementation
- [ ] Convergence metrics tracking
- [ ] Training visualization dashboard

**Success Criteria**:
- Nash distance < 0.05 (within 5% of equilibrium)
- Deal success rate > 90%
- Average rounds to deal < 5
- Pareto efficiency score > 0.85

### Phase 3: LLM Integration (Weeks 5-6)
**Goal**: Natural language communication layer

**Deliverables**:
- [ ] Ollama local deployment
- [ ] Prompt engineering templates
- [ ] Style personality system (aggressive/cooperative/analytical)
- [ ] Message quality evaluation
- [ ] Context-aware response generation
- [ ] Fallback mechanisms for LLM failures

**Success Criteria**:
- Message quality score > 0.8
- Response time < 2 seconds
- Proper alignment between RL strategy and LLM message
- No inappropriate or unprofessional language

### Phase 4: Frontend Development (Weeks 7-8)
**Goal**: Interactive real-time dashboard

**Deliverables**:
- [ ] Next.js 14 app setup
- [ ] WebSocket real-time updates
- [ ] Negotiation chat interface
- [ ] Analytics dashboard (charts, metrics)
- [ ] Control panel (parameter configuration)
- [ ] Responsive design
- [ ] Dark mode support

**Success Criteria**:
- < 100ms UI update latency
- Mobile responsive
- Accessible (WCAG 2.1 AA)
- Clean, professional design

### Phase 5: Production Hardening (Weeks 9-10)
**Goal**: Production-ready deployment

**Deliverables**:
- [ ] Docker containerization
- [ ] PostgreSQL database setup
- [ ] Redis caching layer
- [ ] API authentication & rate limiting
- [ ] Logging and monitoring
- [ ] Error handling and recovery
- [ ] Load testing and optimization

**Success Criteria**:
- Handle 100+ concurrent sessions
- 99.9% uptime
- < 500ms API response time (p95)
- Comprehensive error handling

### Phase 6: Advanced Features (Weeks 11-12)
**Goal**: Enhanced capabilities

**Deliverables**:
- [ ] Multi-item negotiation (bundles)
- [ ] Group negotiations (3+ agents)
- [ ] Historical analysis and replay
- [ ] Custom agent training interface
- [ ] Export/import trained policies
- [ ] A/B testing framework

**Success Criteria**:
- All features fully tested
- Documentation complete
- User adoption > 50 sessions/week

---

## 🔌 API Specification

### Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.equilibriumx.com/api/v1
```

### Authentication
```http
POST /auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}

Response:
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Simulation Endpoints

#### Start Simulation
```http
POST /simulation/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "supplier_valuation": 5000,
  "retailer_valuation": 8000,
  "max_rounds": 10,
  "supplier_style": "aggressive",
  "retailer_style": "cooperative"
}

Response:
{
  "session_id": "uuid",
  "websocket_url": "/simulation/{session_id}/stream",
  "status": "created",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### WebSocket Stream
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/simulation/{session_id}/stream');

// Send configuration
ws.send(JSON.stringify({
  supplier_valuation: 5000,
  retailer_valuation: 8000,
  max_rounds: 10
}));

// Receive messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Message format:
  {
    "agent": "supplier",
    "round": 1,
    "action": "COUNTER",
    "price": 6500,
    "message": "I propose $6,500 as a fair starting point.",
    "timestamp": 1704067200
  }
  
  // Final result:
  {
    "type": "SIMULATION_COMPLETE",
    "deal_reached": true,
    "final_price": 6400,
    "total_rounds": 5,
    "rewards": {
      "supplier": 12.5,
      "retailer": 14.2
    },
    "nash_distance": 0.03,
    "pareto_efficiency": 0.92
  }
};
```

#### Get Simulation Status
```http
GET /simulation/{session_id}/status
Authorization: Bearer {token}

Response:
{
  "session_id": "uuid",
  "status": "running" | "completed" | "failed",
  "current_round": 3,
  "max_rounds": 10,
  "deal_reached": false,
  "started_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:30Z"
}
```

### Agent Management

#### Train New Agent
```http
POST /agent/train
Authorization: Bearer {token}
Content-Type: application/json

{
  "agent_type": "supplier" | "retailer",
  "algorithm": "PPO" | "SAC",
  "training_config": {
    "num_iterations": 1000,
    "learning_rate": 0.0003,
    "gamma": 0.99
  }
}

Response:
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_duration_minutes": 30
}
```

#### Get Agent Policy
```http
GET /agent/{agent_id}/policy
Authorization: Bearer {token}

Response:
{
  "agent_id": "uuid",
  "agent_type": "supplier",
  "algorithm": "PPO",
  "trained_at": "2024-01-01T00:00:00Z",
  "performance_metrics": {
    "nash_distance": 0.04,
    "deal_rate": 0.93,
    "average_rounds": 4.2
  },
  "download_url": "/agent/{agent_id}/download"
}
```

### Metrics & Analytics

#### Export Session Metrics
```http
POST /metrics/export
Authorization: Bearer {token}
Content-Type: application/json

{
  "session_ids": ["uuid1", "uuid2"],
  "format": "csv" | "json"
}

Response:
{
  "download_url": "/metrics/export/{export_id}",
  "expires_at": "2024-01-02T00:00:00Z"
}
```

---

## 🚢 Deployment Guide

### Prerequisites
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Node.js** 18+ (for frontend development)
- **Python** 3.10+
- **RAM**: Minimum 8GB (16GB recommended)
- **GPU**: Optional but recommended for training (NVIDIA with CUDA 11.8+)

### Quick Start (Development)

#### 1. Clone Repository
```bash
git clone https://github.com/yourusername/equilibriumx.git
cd equilibriumx
```

#### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**.env Configuration**:
```bash
# Database
POSTGRES_USER=equilibrium_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=equilibriumx
DATABASE_URL=postgresql://equilibrium_user:your_secure_password@db:5432/equilibriumx

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_SECRET_KEY=your_super_secret_key_here_change_in_production
API_HOST=0.0.0.0
API_PORT=8000

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3

# Ray
RAY_NUM_CPUS=8
RAY_NUM_GPUS=1
```

#### 3. Start Services
```bash
# Start all services with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Services will be available at:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Ray Dashboard: http://localhost:8265
```

#### 4. Initialize Database
```bash
# Run migrations
docker-compose exec api python -m alembic upgrade head

# Seed initial data (optional)
docker-compose exec api python scripts/seed_data.py
```

#### 5. Download LLM Model
```bash
# Pull Llama3 model in Ollama container
docker-compose exec ollama ollama pull llama3

# Verify model is ready
docker-compose exec ollama ollama list
```

### Production Deployment

#### Using Docker Compose
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

#### Manual Deployment

**Backend (FastAPI)**:
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set production environment variables
export DATABASE_URL=postgresql://user:pass@host:5432/db
export REDIS_URL=redis://host:6379/0
export API_SECRET_KEY=production_secret

# Run with Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

**Frontend (Next.js)**:
```bash
cd frontend

# Install dependencies
npm install

# Build production bundle
npm run build

# Start production server
npm start

# Or use PM2 for process management
pm2 start npm --name "equilibriumx-frontend" -- start
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "ollama": "ready",
  "ray": "running"
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Ollama Model Not Found
```bash
# Symptom: "Model llama3 not found" error

# Solution: Pull the model
docker-compose exec ollama ollama pull llama3

# Alternative: Use different model
# Update .env: OLLAMA_MODEL=mistral
docker-compose exec ollama ollama pull mistral
```

#### 2. Ray Initialization Fails
```bash
# Symptom: "Cannot initialize Ray cluster"

# Solution: Increase resources
# In docker-compose.yml, add:
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
```

#### 3. WebSocket Connection Issues
```bash
# Symptom: WebSocket connection refused

# Solution: Check CORS settings in backend/app/main.py
# Ensure frontend URL is in allowed origins
allow_origins=["http://localhost:3000", "https://yourproduction.com"]
```

#### 4. Database Connection Timeout
```bash
# Symptom: "Could not connect to database"

# Solution: Verify database is running
docker-compose ps

# Check database logs
docker-compose logs db

# Test connection manually
docker-compose exec db psql -U equilibrium_user -d equilibriumx
```

#### 5. Training Jobs Crash
```bash
# Symptom: Out of memory during training

# Solution: Reduce batch size
# In backend/app/rl/config.py:
train_batch_size=2000  # Reduced from 4000
num_workers=2  # Reduced from 4
```

### Performance Optimization

#### Enable GPU Acceleration
```bash
# Verify NVIDIA drivers
nvidia-smi

# Update docker-compose.yml:
services:
  api:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

#### Redis Caching
```python
# Cache frequently accessed agents
from app.cache import redis_client

# Cache policy for 1 hour
redis_client.setex(
    f"agent_policy:{agent_id}",
    3600,
    policy_data
)
```

---

## 📚 Usage Examples

### Quick Start Example

```python
import requests
import websocket
import json

# 1. Start a simulation
response = requests.post(
    "http://localhost:8000/api/v1/simulation/start",
    json={
        "supplier_valuation": 5000,
        "retailer_valuation": 8000,
        "max_rounds": 10,
        "supplier_style": "aggressive",
        "retailer_style": "cooperative"
    }
)

session_id = response.json()["session_id"]

# 2. Connect to WebSocket
ws = websocket.WebSocket()
ws.connect(f"ws://localhost:8000/api/v1/simulation/{session_id}/stream")

# 3. Send configuration
ws.send(json.dumps({
    "supplier_valuation": 5000,
    "retailer_valuation": 8000,
    "max_rounds": 10
}))

# 4. Receive negotiation messages
while True:
    message = json.loads(ws.recv())
    
    if message.get("type") == "SIMULATION_COMPLETE":
        print(f"Deal reached: ${message['final_price']}")
        print(f"Rounds: {message['total_rounds']}")
        print(f"Nash distance: {message['nash_distance']}")
        break
    else:
        print(f"[{message['agent']}] Round {message['round']}: {message['message']}")
```

### Custom Agent Training

```python
from app.rl.trainer import create_training_config, train_agents

# Configure custom training
config = create_training_config()

# Modify hyperparameters
config.training(
    lr=5e-4,  # Higher learning rate
    gamma=0.95,  # Lower discount factor
    train_batch_size=8000  # Larger batch
)

# Train for 2000 iterations
trained_algo = train_agents(num_iterations=2000)

# Save policy
checkpoint_path = trained_algo.save("./checkpoints/custom_agent")
print(f"Saved to: {checkpoint_path}")
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Setup Development Environment
```bash
# Fork and clone repository
git clone https://github.com/yourusername/equilibriumx.git
cd equilibriumx

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Code Standards
- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow ESLint configuration
- **Tests**: Minimum 80% coverage for new code
- **Documentation**: Update README for new features

### Pull Request Process
1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests for new functionality
3. Ensure all tests pass: `pytest`
4. Update documentation
5. Submit PR with clear description

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 📞 Contact & Support

- **GitHub Issues**: [github.com/yourusername/equilibriumx/issues](https://github.com/yourusername/equilibriumx/issues)
- **Email**: support@equilibriumx.com
- **Documentation**: [docs.equilibriumx.com](https://docs.equilibriumx.com)

---

## 🎓 Citation

If you use EquilibriumX in your research, please cite:

```bibtex
@software{equilibriumx2024,
  title={EquilibriumX: Multi-Agent Negotiation Sandbox},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/equilibriumx},
  note={A hybrid RL-LLM platform for game-theoretic bargaining}
}
```

---

## 🌟 Acknowledgments

- **Ray RLlib**: Distributed RL framework
- **Ollama**: Local LLM inference
- **PettingZoo**: Multi-agent environment standard
- **FastAPI**: Modern Python web framework
- **Next.js**: React framework for production

---

**Built with ❤️ for the AI and Game Theory community**
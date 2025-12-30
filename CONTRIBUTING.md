# Contributing to EquilibriumX

Thank you for your interest in contributing to EquilibriumX! To maintain a high-quality codebase for research and production, we follow a strict branching strategy.

## 🌿 Branching Strategy

We use a modified Gitflow workflow tailored for research & development.

### 1. `master` (Production / Stable)

* **Purpose**: The official, stable release history.
* **Rule**: Never push directly to master. Only merge from `develop` via Pull Request (PR) after passing tests.
* **Artifacts**: Should align with published research papers or stable releases.

### 2. `develop` (Integration / Active Dev)

* **Purpose**: The main integration branch for ongoing development.
* **Rule**: All feature branches are merged here. This branch contains the latest "bleeding edge" code.
* **CI/CD**: Automatic testing runs on every push.

### 3. `prototype` (Experimental / MVP)

* **Purpose**: A sandbox for rapid experimentation, wild ideas, and "hacky" MVPs.
* **Rule**: Code quality standards are lower here. Useful for trying out new RL algorithms or LLM prompts quickly.
* **Warning**: This branch may be force-pushed or reset. Do not rely on it for long-term stability.

### 4. `feature/*` (Feature Branches)

* **Purpose**: Specific features or bug fixes.
* **Naming Convention**: `feature/feature-name` or `fix/bug-description`.
* **Flow**: Branch off `develop`, merge back to `develop` via PR.

## 🚀 Workflow Example

1. **Clone the repo**:

    ```bash
    git clone https://github.com/loxleyftsck/EquilibriumX-Multi-Agent-Negotiation-Sandbox.git
    ```

2. **Checkout the development branch**:

    ```bash
    git checkout develop
    ```

3. **Create a feature branch**:

    ```bash
    git checkout -b feature/new-reward-function
    ```

4. **Commit your changes**:

    ```bash
    git commit -m "feat: implement localized reward function"
    ```

5. **Push and create a PR**:

    ```bash
    git push origin feature/new-reward-function
    ```

## 📝 Coding Standards

* **Python**: Follow PEP 8. Use type hints (`mypy` compliant).
* **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `docs:`).

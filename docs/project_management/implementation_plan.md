# Professional AI Project Restructuring Plan

This plan aims to reorganize the **EquilibriumX** repository into a standard, production-ready structure suitable for an AI Researcher or Engineer. This will improve maintainability, professional presentation on GitHub, and ease of collaboration.

## 📁 Proposed Directory Structure

```text
EquilibriumX/
├── .github/              # GitHub Actions and templates
├── assets/               # Visuals for README (logos, diagrams)
├── docs/                 # Extended documentation
│   ├── README.txt        # Detailed technical documentation
│   └── ROADMAP.md        # Project vision and timeline
├── paper/                # Academic research materials
│   ├── equilibriumx_paper.tex
│   ├── equilibriumx_paper.pdf
│   └── references.bib
├── src/                  # Core source code
│   ├── environment/      # PettingZoo bargaining environment
│   ├── agents/           # RL agent implementations
│   ├── llm/              # LLM integration logic
│   └── utils/            # Helper functions
├── scripts/              # Training and evaluation entry points
├── notebooks/            # Jupyter notebooks for R&D
├── models/               # Saved model checkpoints (gitignored)
├── tests/                # Unit and integration tests
├── .gitignore            # Standard Python/AI ignore rules
└── requirements.txt      # Project dependencies
```

## 🛠️ Proposed Changes

### 1. Repository Organization

- Move `Readme.txt` and `ROADMAP.md` to `docs/`.
- Maintain `paper/` directory for the LaTeX source.
- Create placeholder directories for `src/`, `notebooks/`, `models/`, and `tests/` with `.gitkeep` files to preserve structure.
- Create a root level `README.md` (Markdown version) that points to the detailed documentation and provides a professional high-level overview.

### 2. Git Configuration

- Initialize Git repository.
- Create a robust `.gitignore` to exclude:
  - `__pycache__`
  - Virtual environments (`venv/`)
  - Model checkpoints (`models/*.pt`, `models/*.pth`, `models/*.zip`)
  - LaTeX auxiliary files (`*.aux`, `*.log`, `*.out`)
  - Data logs and temporary files.

### 3. GitHub Preparation

- Set up a professional `README.md` for the GitHub landing page.
- Note: I will need the user to provide a GitHub remote URL if they want me to actually `git push`. Otherwise, I will prepare everything for a manual push.

### 4. MLflow Integration

- Create `requirements.txt` with `mlflow` and other dependencies.
- Create `src/utils/mlflow_logger.py` to handle experiment tracking.
- Integrate MLflow into the training logic (placeholders in `src/agents/`).

### 5. Research Paper Theory Refinement

- Review and refine the "Theoretical Foundation" section in `paper/equilibriumx_paper.tex`.
- Ensure mathematical formulations for Nash Equilibrium and RL (MDP) are rigorous.
- Verify IEEE citation style and completeness of references.
- Fix any LaTeX compilation errors (e.g., missing packages or malformed equations).

### 6. GitHub Deployment

- Set remote origin: `git@github.com:loxleyftsck/EquilibriumX-Multi-Agent-Negotiation-Sandbox.git`.
- Final commit and push.

## 🧪 Verification Plan

### Automated Checks

- Run `ls -R` to verify the directory structure.
- Run `git status` to verify staging.
- Check `requirements.txt` for `mlflow`.
- Attempt a final local LaTeX compilation (or verify on Overleaf if local still lags).

### Manual Verification

- Review the refined theory in `paper/equilibriumx_paper.tex`.
- Confirm MLflow tracking logic in `src/utils/mlflow_logger.py`.
- Verify GitHub remote is set correctly.

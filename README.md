# fair-data-learning

Learning project for **FAIR semantic data infrastructure**, **data science**, and **MLOps** using materials science data.

> **Skill roadmap:** see [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md) for the full learning plan covering data science, FAIR/semantic infrastructure, MLOps, and job preparation.

## Goals

- Practice FAIR principles with real research data
- Learn data pipelines and exploratory analysis
- Build and deploy ML models with MLOps best practices

## Project Structure

```
fair-data-learning/
├── data/
│   ├── raw/          # Original data from Materials Project
│   └── processed/    # Cleaned, feature-engineered data (DVC-managed)
├── notebooks/        # Jupyter notebooks for exploration and modeling
├── src/              # Reusable Python modules (pipeline stages)
├── tests/            # pytest unit tests for data & training code
├── metadata/         # FAIR metadata (Schema.org, DCAT)
├── models/           # Trained model artifacts (DVC-managed)
├── params.yaml       # ML configuration (features, models, mlflow)
├── dvc.yaml          # DVC pipeline: features -> train -> evaluate
├── Makefile          # Shortcuts: make setup/test/pipeline/ui
└── requirements.txt  # Python dependencies
```

## Getting Started

```bash
# 1. Environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. API key for fetching data (optional for re-running)
echo "MP_API_KEY=your_key_here" > .env

# 3. Run the full ML pipeline (DVC)
dvc repro

# 4. Inspect metrics
dvc metrics show

# 5. View experiment tracking
mlflow ui --backend-store-uri sqlite:///mlflow.db   # http://localhost:5000
```

## MLOps Workflow

| Tool | Purpose in this repo |
|------|----------------------|
| DVC | Version data + pipeline stages, caching, reproducibility |
| MLflow | Track experiments (params, metrics), model registry |
| pytest | Unit tests for feature engineering and pipeline code |
| GitHub Actions | CI: run tests + pipeline on every push (`dvc repro`) |
| Makefile | Convenience wrappers (`make test`, `make metrics`, `make ui`) |

### Pipeline stages

```
data/mp_oxides_clean.csv --features--> features.parquet
features.parquet --train--> model.pkl + metrics.json
model.pkl --evaluate--> feature_importances.csv/png
```

Change a value in `params.yaml` (e.g. `RandomForest.n_estimators`)
and rerun `dvc repro` — only affected stages re-run.

## Data Source

Materials Project API: https://next-gen.materialsproject.org/api

## License

Apache 2.0
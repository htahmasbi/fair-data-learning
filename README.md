# fair-data-learning

Learning project for **FAIR semantic data infrastructure**, **data science**, and **MLOps** using materials science data.

## Goals

- Practice FAIR principles with real research data
- Learn data pipelines and exploratory analysis
- Build and deploy ML models with MLOps best practices

## Project Structure

```
fair-data-learning/
├── data/
│   ├── raw/          # Original data from Materials Project
│   └── processed/    # Cleaned, feature-engineered data
├── notebooks/        # Jupyter notebooks for exploration and modeling
├── src/              # Reusable Python code
├── metadata/         # FAIR metadata (Schema.org, DCAT)
├── .env              # API keys (not committed)
└── requirements.txt  # Python dependencies
```

## Getting Started

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your Materials Project API key
echo "MP_API_KEY=your_key_here" > .env
```

## Data Source

Materials Project API: https://next-gen.materialsproject.org/api

## License

Apache 2.0

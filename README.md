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
mp_oxides_clean.csv + model.pkl + metrics.json --semantic--> knowledge_graph.ttl (RDF)
```

Change a value in `params.yaml` (e.g. `RandomForest.n_estimators`)
and rerun `dvc repro` — only affected stages re-run.

## FAIR / Semantic Layer

- `metadata/dataset_metadata.jsonld` — machine-readable metadata using Schema.org + DCAT + PROV-O
- `metadata/materials_ontology.owl` — OWL ontology (classes/properties), editable in Protégé
- `metadata/ro-crate-metadata.json` — RO-Crate research object bundle
- `src/vocab.py` — URIs/namespaces for the materials ontology
- `src/rdf.py` — builds `knowledge_graph.ttl` (13k triples: materials → structures → properties → provenance)
- `src/model_rdf.py` — model provenance as RDF, merged into the same graph (see below)
- `src/sparql.py` — example SPARQL queries (run via `python src/sparql.py`)
- `notebooks/03_fair_semantic_layer.ipynb` — interactive walkthrough
- `CITATION.cff` — cite this repository (shown automatically on GitHub)
- `.zenodo.json` — Zenodo archive config (publish a GitHub Release → DOI)
- `FAIRNESS_CHECKLIST.md` — 15 FAIR sub-principles mapped to evidence (9/15 fully met)

Regenerate bundled artifacts:

```bash
python src/ontology.py   # -> metadata/materials_ontology.owl
python src/ro_crate.py   # -> metadata/ro-crate-metadata.json
```

## Semantic MLOps (model provenance in the knowledge graph)

`src/model_rdf.py` asserts the training history of `model.pkl` as RDF, using
the **PROV-O** and **ML-Schema** W3C vocabularies, and merges it into the same
graph as the materials:

```
model  --prov:wasGeneratedBy-->  run  --mls:hasInput-->  dataset (mp-oxides-v1)
                                    --mls:hasOutput-->   evaluation (CV R² = 0.72)
                                    --mls:hasOutput-->   model
model  --prov:wasAttributedTo--> orcid:0000-0002-3072-8217   (FAIR F3)
model  --owl:versionInfo-->      <git sha>
```

The model URI is **content-addressed** (md5 of `model.pkl`), so the identity of
an artifact is a fingerprint of its exact bytes. Because materials, dataset and
model share one graph, a single SPARQL query traverses the whole chain, e.g.
`materials_behind_the_model` returns the material count, dataset, model and CV
R² together:

```sparql
?dataset prov:hadMember ?material .
?model   a mls:Model ; prov:wasGeneratedBy ?run .
?run     mls:hasInput ?dataset ; mls:hasOutput ?evaluation .
?evaluation mls:specifiedBy meas:cv_r2_mean ; mls:hasValue ?cvR2 .
```

This is what MLflow cannot do on its own: its facts stay inside MLflow, whereas
here they are queryable *alongside the data and the materials they describe*.

## Deployment (FastAPI + Docker)

The trained model is served as a REST API with input validation and
auto-generated OpenAPI docs.

```bash
# Local
make serve      # http://localhost:8000/docs

# Container
make docker-build && make docker-run
```

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Liveness probe (`model_loaded` flag) |
| `/model-info` | GET | Provenance: best model, CV metrics, features (FAIR/R) |
| `/predict` | POST | `formula` + properties → predicted band gap (eV) |
| `/docs` | GET | Interactive Swagger UI |

Example:

```bash
curl -X POST http://localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"formula":"MgO","formation_energy_per_atom":-3.0,"density":3.58,
       "nsites":4,"energy_above_hull":0.0,"crystal_system":"Cubic",
       "space_group":"Fm-3m"}'
# {"formula":"MgO","predicted_band_gap_eV":4.1048}
```

**Production patterns implemented:**
- Model loaded **once** at startup (lifespan), not per request (~35 ms/prediction)
- Feature engineering **shared** with training via `src.data` — avoids train/serve skew
- Schema-driven input validation (Pydantic) → free OpenAPI docs
- Non-root container user, `HEALTHCHECK` using the `/health` endpoint
- `.dockerignore` excludes `.env`, venv, and DVC cache so secrets never enter the image

> Note: `models/model.pkl` is DVC-tracked (gitignored), so run `dvc pull`
> before `docker build` on a fresh clone.

## Data Source

Materials Project API: https://next-gen.materialsproject.org/api

## License

Apache 2.0
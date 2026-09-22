# Learning Roadmap: FAIR Semantic Data Infrastructure + Data Science + MLOps

> Personal skill development plan for a job in modern research data / AI infrastructure.
> Everything linked to a working project: this repository.

---

## Roadmap Overview

| Phase | Focus | Deliverable in this repo |
|-------|-------|--------------------------|
| 1 | Data Science Fundamentals | `01_fetch_explore_mp_data.ipynb` (done) |
| 2 | Reproducible ML / Model Building | `02_bandgap_prediction.ipynb` |
| 3 | FAIR + Semantic Data | `metadata/`, SPARQL layer |
| 4 | MLOps Tooling | DVC, MLflow, CI/CD |
| 5 | Deployment & Production | FastAPI + Docker |
| 6 | Interview / Portfolio polish | README, docs, portfolio |

---

## Stage 1: Data Science Fundamentals ✅ (in progress)

Core proficiency with pandas, numpy, matplotlib, and standard ML libraries.

### Skills
- [x] Environment setup (venv, requirements.txt, reproducibility basics)
- [x] API-based data acquisition (Materials Project via MPRester)
- [x] Basic EDA: distributions, correlations, missing data (notebook 01)
- [x] Data cleaning & imputation strategies (SimpleImputer pipeline)
- [x] Feature engineering (composition-derived features via pymatgen)
- [x] Train a baseline model (Ridge, RandomForest, GradientBoost)
- [x] Model evaluation: cross-validation, metrics (R², MAE, RMSE)
- [x] Permutation importance analysis

### Tools
- pandas, numpy, matplotlib, seaborn
- scikit-learn

### Project milestone
- [x] Notebook 02: predict band gap from composition/structural features (GradientBoost R²=0.96 train, MAE=0.18 eV)

---

## Stage 2: FAIR & Semantic Data Infrastructure

FAIR = **F**indable, **A**ccessible, **I**nteroperable, **R**eusable.
These skills are the differentiator for research-data jobs (RDM, FAIR data steward, data engineer).

### Skills
- [ ] FAIR principles deep-dive (metadata, PIDs/DOIs, licensing, provenance)
- [ ] Metadata standards: Schema.org, DCAT, Dublin Core, CFF
- [ ] Semantic web basics: RDF, ontologies, namespaces, URIs
- [ ] SPARQL query language + RDFLib for querying knowledge graphs
- [ ] Data containers: RO-Crate, CFF (citation file format), DataCite
- [ ] Ontology development in a domain (e.g., materials) with Protégé
- [ ] Provenance modelling (W3C PROV-O)
- [ ] Working with PIDs/DOIs and repositories (Zenodo, Figshare)
- [ ] Zotero for reference management integration

### Tools
- RDFLib, SPARQL endpoints
- Protégé (ontology editor)
- Frictionless Data / Data Package
- Json-schema / data validation (pydantic)

### Project milestone
- [ ] Publish `mp_oxides_clean.csv` as a FAIR data package (metadata JSON-LD, schema, pid)
- [ ] Build a small knowledge graph: materials → structures → properties → publications, queryable via SPARQL

---

## Stage 3: MLOps & Reproducible ML

MLOps = CI/CD for ML + data/model versioning + experiment tracking + monitoring. This is what employers explicitly search for.

### Skills
- [ ] Data versioning: **DVC** (data + model as code)
- [ ] Experiment tracking: **MLflow** (params, metrics, artifacts, model registry)
- [ ] Project structure: `src/` packages, tests, `pyproject.toml`, Makefile
- [ ] Unit tests for data pipelines and models (pytest)
- [ ] CI/CD: GitHub Actions (lint, test, train, validate)
- [ ] Model registry + model serving (MLflow serve, ONNX)
- [ ] Containerization: Docker (image for model, deterministic deps)
- [ ] Configuration & feature store concepts (options: Feast, or simple versioned features)
- [ ] Model monitoring basics: drift, retraining triggers (Evidently/AI)
- [ ] Reproducibility: pinned dependencies, seeds, hashes, environments

### Tools
- DVC, MLflow, pytest, GitHub Actions
- Docker, ONNX
- Evidently (drift), optionally Kubeflow/Airflow (later)

### Project milestone
- [ ] Reproduce notebook 02 end-to-end via `dvc repro`
- [ ] Track all experiments in MLflow with model registry
- [ ] GitHub Actions: `test` → `train` → `register model`
- [ ] Serve band-gap model via Dockerized FastAPI + CI pipeline

---

## Stage 4: Deployment & Production Engineering

For jobs involving production ML/AI systems.

### Skills
- [ ] REST API design with **FastAPI** (endpoints, validation, docs)
- [ ] Async/concurrency basics (where relevant)
- [ ] Deployment: Docker, compose; cloud options (Fly.io, GCP/AWS free tiers)
- [ ] Logging, error handling, timeouts
- [ ] Model artifacts & feature computation service separation
- [ ] Light-weight monitoring (Evidently + FastAPI health checks)

### Tools
- FastAPI, uvicorn, Docker, compose
- Optional: cloud GPU (later)

---

## Stage 5: Semantic Enrichment of the Pipeline (advanced)

Once Stage 2 & 3 basics are done, combine them — this is the "semantic MLOps" niche that is rare and valuable.

- [ ] Automated metadata generation for models/datasets (MLflow + DataCite crosswalk)
- [ ] Publishing models with CFF (citation file format) to make them citable
- [ ] Linking dataset ↔ model ↔ paper in a knowledge graph
- [ ] Dataset quality reporting with Frictionless
- [ ] Contributing to a community ontology (e.g., Materials Ontology)

---

## Portfolio / Job Polish

For job applications as Data Scientist / ML Engineer / FAIR data / data engineer:

### Skills
- [ ] One strong portfolio repo with clean README badges (CI passing, coverage)
- [ ] Document reproducible single-command setup (`make setup` / `make reproduce`)
- [ ] Blog posts or short notes per milestone (LinkedIn / dev.to)
- [ ] Translate project into resume bullet points:
  - Built ETL+EDA pipeline pulling 1,000+ material records from public API
  - Achieved band-gap prediction R²=0.8 via baseline→boosted pipeline
  - Reproducible DVC pipeline with MLflow experiments registry
  - Containerized FastAPI service with CI-tested health checks

### Practice areas for interviews
- [ ] SQL practice (basic window functions, joins, CTEs) — free: SQLite exercises
- [ ] Python coding problems (arrays, dicts, OOP, pandas)
- [ ] Explain ML basics: bias/variance, regularization, cross-val, class imbalance
- [ ] FAIR quiz practice: GO FAIR metrics, DMP (data management plans)

---

## Weekly suggested cadence (≈ 5–10 h/week)

| Week | Main milestone |
|------|----------------|
| 1 | Finish notebook 02 (band gap model) |
| 2 | DVC + MLflow on notebook 02 |
| 3 | Tests + GitHub Actions pipeline |
| 4 | FAIR data package + metadata JSON-LD |
| 5 | SPARQL + small knowledge graph |
| 6 | FastAPI + Docker deploy |
| 7 | CI/CD end-to-end + portfolio README |
| 8 | Polish, resume bullets, mock interviews |

---

## Recommended learning resources

### FAIR / semantic
- GO FAIR: https://www.go-fair.org/how-to-go-fair/
- FAIR Principles (Wilkinson et al. 2016)
- DCAT 2/3 spec: https://www.w3.org/TR/vocab-dcat-3/
- RO-Crate spec: https://www.researchobject.org/ro-crate/
- RDF 1.1 primer: https://www.w3.org/TR/rdf11-primer/

### Data science / ML
- Introduction to Statistical Learning (ISLR) — free PDF
- sklearn docs examples
- Kaggle beginner competitions (Titanic, House Prices)

### MLOps
- DVC docs: https://dvc.org/doc
- MLflow docs: https://mlflow.org/docs/latest
- Practical MLOps (O'Reilly), or Made With ML tutorials
- Zero to Mastery MLOps course (optional)

### Interviews / careers
- StrataScratch or LeetCode for SQL/Python
- The Pragmatic Engineer newsletter / blog
- Research data management job boards, e.g. CODATA, RDA

---

## Skill matrix for resume (self-assessment)

| Skill group | Level now | Target | Status |
|-------------|-----------|--------|--------|
| Python/pandas EDA | Beginner | Proficient | ✅ done |
| Materials science domain | Proficient | — | existing |
| scikit-learn ML | Beginner | Proficient | in progress |
| SQL | — | Basic | to do |
| FAIR metadata/RDF | Beginner | Proficient | to do |
| DVC | — | Proficient | to do |
| MLflow | — | Proficient | to do |
| Docker/CI | — | Basic | to do |
| FastAPI | — | Basic | to do |

---

*Last updated: 2026-09-14*
*Owner: htahmasbi*
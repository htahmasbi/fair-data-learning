PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup dev test train reproduce pipeline evaluate ui lint clean serve docker-build docker-run docker-test

## Create venv and install dependencies
setup:
	python3 -m venv .venv
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

## Run unit tests
test:
	$(PYTHON) -m pytest tests/ -v

## Run the full DVC pipeline (features -> train -> evaluate)
pipeline:
	$(PYTHON) -m dvc repro

## Show experiment metrics
metrics:
	$(PYTHON) -m dvc metrics show

## Launch MLflow UI (http://localhost:5000)
ui:
	$(PYTHON) -m mlflow ui --backend-store-uri sqlite:///mlflow.db

## Train models directly (no DVC) with experiment tracking
train:
	$(PYTHON) src/features.py
	$(PYTHON) src/train.py
	$(PYTHON) src/evaluate.py

## Show DVC pipeline graph
graph:
	$(PYTHON) -m dvc dag

## Git init + DVC tracked data not needed for small repo; run after setup
dev: setup test

## Serve the model locally (http://localhost:8000/docs)
serve:
	$(PYTHON) -m uvicorn src.api:app --reload --port 8000

## Build the Docker image (run `dvc pull` first to fetch models/)
docker-build:
	docker build -t fair-data-learning:latest .

## Run the containerized API (http://localhost:8000/docs)
docker-run:
	docker run --rm -p 8000:8000 fair-data-learning:latest

## Build + smoke-test the container in one step
docker-test: docker-build
	docker run -d --rm -p 8000:8000 --name fdl-api fair-data-learning:latest
	sleep 8
	curl -s http://localhost:8000/health
	curl -s -X POST http://localhost:8000/predict -H 'Content-Type: application/json' \
	  -d '{"formula":"MgO","formation_energy_per_atom":-3.0,"density":3.58,"nsites":4,"energy_above_hull":0.0,"crystal_system":"Cubic","space_group":"Fm-3m"}'
	docker stop fdl-api
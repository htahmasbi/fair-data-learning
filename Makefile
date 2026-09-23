PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup dev test train reproduce pipeline evaluate ui lint clean dvc-remote

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
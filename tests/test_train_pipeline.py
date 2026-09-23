"""Tests for the train pipeline (src/train.py)."""

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.config import load_params
from src.train import MODEL_REGISTRY, build_pipeline


def test_params_yaml_loads():
    params = load_params()
    assert "train" in params
    assert "features" in params
    assert params["train"]["cv_folds"] == 5
    assert "band_gap" in params["train"]["target"]


def test_all_models_registered():
    assert set(MODEL_REGISTRY) == {"Ridge", "RandomForest", "GradientBoost"}


def test_build_pipeline_returns_sklearn_pipeline():
    params = load_params()
    pipe = build_pipeline(MODEL_REGISTRY["GradientBoost"], params["features"], 42)
    assert isinstance(pipe, Pipeline)
    # Pipeline must have preprocess + model steps
    assert "preprocess" in pipe.named_steps and "model" in pipe.named_steps


def test_pipeline_fits_predicts_on_small_data():
    params = load_params()
    rng = np.random.default_rng(0)
    X = pd.DataFrame(
        {
            "formation_energy_per_atom": rng.normal(size=50),
            "density": rng.normal(size=50),
            "nsites": rng.integers(1, 50, 50),
            "energy_above_hull": rng.normal(size=50),
            "n_elements": rng.integers(1, 4, 50),
            "avg_electroneg": rng.uniform(1, 3.5, 50),
            "std_electroneg": rng.uniform(0, 1, 50),
            "range_electroneg": rng.uniform(0, 2, 50),
            "avg_atomic_number": rng.uniform(5, 60, 50),
            "total_electrons": rng.uniform(10, 200, 50),
            "spacegroup_num": rng.integers(1, 230, 50),
            "crystal_system": ["Cubic"] * 50,
        }
    )
    y = rng.normal(size=50)
    pipe = build_pipeline(MODEL_REGISTRY["Ridge"], params["features"], 42)
    pipe.fit(X, y)
    preds = pipe.predict(X)
    assert preds.shape == (50,)
    assert np.isfinite(preds).all()
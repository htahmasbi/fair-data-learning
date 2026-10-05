"""Tests for the FastAPI service (src/api.py)."""

import pytest
from fastapi.testclient import TestClient

from src.api import app, _build_feature_row, PredictRequest


@pytest.fixture
def client():
    # `with` triggers lifespan -> model loads once
    with TestClient(app) as c:
        yield c


VALID_PAYLOAD = {
    "formula": "Fe2O3",
    "formation_energy_per_atom": -1.69,
    "density": 5.27,
    "nsites": 30,
    "energy_above_hull": 0.0,
    "crystal_system": "Trigonal",
    "space_group": "R-3c",
}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "model_loaded": True}


def test_model_info_exposes_provenance(client):
    data = client.get("/model-info").json()
    assert data["model_name"] == "band_gap_predictor"
    assert data["best_model"] in {"Ridge", "RandomForest", "GradientBoost"}
    assert "features" in data and data["features"]


def test_predict_returns_sensible_value(client):
    r = client.post("/predict", json=VALID_PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert body["formula"] == "Fe2O3"
    gap = body["predicted_band_gap_eV"]
    # Physical sanity: band gaps span ~0-8 eV for oxides
    assert 0.0 <= gap <= 10.0


def test_predict_is_deterministic(client):
    a = client.post("/predict", json=VALID_PAYLOAD).json()["predicted_band_gap_eV"]
    b = client.post("/predict", json=VALID_PAYLOAD).json()["predicted_band_gap_eV"]
    assert a == b


def test_predict_validates_missing_fields(client):
    r = client.post("/predict", json={"formula": "Fe2O3"})
    assert r.status_code == 422  # FastAPI/Pydantic validation


def test_predict_rejects_invalid_formula(client):
    bad = {**VALID_PAYLOAD, "formula": "NotAnElement123"}
    r = client.post("/predict", json=bad)
    # Either validation (400 from feature build) or 400 prediction failure
    assert r.status_code in (400, 422)


def test_predict_without_space_group_still_works(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "space_group"}
    r = client.post("/predict", json=payload)
    assert r.status_code == 200  # imputer handles missing spacegroup_num


def test_build_feature_row_uses_shared_features():
    """Training-serving consistency: same feature names as training."""
    req = PredictRequest(**VALID_PAYLOAD)
    row = _build_feature_row(req)
    for col in ["n_elements", "avg_electroneg", "spacegroup_num", "crystal_system"]:
        assert col in row.columns
    assert row["n_elements"].iloc[0] == 2
    assert row["spacegroup_num"].iloc[0] == 167  # R-3c


def test_openapi_schema_generated(client):
    schema = client.get("/openapi.json").json()
    assert "paths" in schema
    assert "/predict" in schema["paths"]
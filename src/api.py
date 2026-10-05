"""FastAPI service: serve the trained band-gap model.

Key production patterns demonstrated:
  1. Model is loaded ONCE at startup, not per request
  2. Feature engineering is SHARED with training via src.data (avoids skew)
  3. Input validation is derived from type hints (Pydantic) -> free OpenAPI docs
  4. /health for load balancers; /model-info exposes provenance (FAIR/R)

Run locally:
    uvicorn src.api:app --reload
Docs:
    http://localhost:8000/docs
"""

import json
from contextlib import asynccontextmanager

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import PROJECT_ROOT, load_params
from src.data import formula_to_features, space_group_number

# Module-level cache so the model is loaded once per worker process.
MODEL_PATH = PROJECT_ROOT / "models" / "model.pkl"
MODEL = None
PARAMS = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model once on startup; runs again on worker restart."""
    global MODEL, PARAMS
    PARAMS = load_params()
    MODEL = joblib.load(MODEL_PATH)
    yield
    MODEL = None


app = FastAPI(
    title="Band Gap Prediction API",
    description="Predicts DFT band gap of oxide materials (trained on Materials Project data).",
    version="1.0.0",
    lifespan=lifespan,
)


class PredictRequest(BaseModel):
    """Input schema. Composition-derived features are computed server-side
    from `formula`, so the client only sends formula + independent properties."""

    formula: str = Field(..., examples=["Fe2O3"], description="Chemical formula, e.g. 'Fe2O3'")
    formation_energy_per_atom: float = Field(..., description="eV/atom")
    density: float = Field(..., gt=0, description="g/cm^3")
    nsites: int = Field(..., gt=0, description="Number of sites in unit cell")
    energy_above_hull: float = Field(..., description="eV/atom; 0 if on hull")
    crystal_system: str = Field(..., examples=["Trigonal"], description="e.g. Cubic, Hexagonal, Trigonal, ...")
    space_group: str | None = Field(
        None,
        examples=["R-3c"],
        description="Optional Hermann-Mauguin symbol (e.g. 'R-3c'). Omitted -> imputed with training median.",
    )


def _build_feature_row(req: PredictRequest) -> pd.DataFrame:
    """Build a one-row feature DataFrame using the SAME functions as training."""
    row = {
        "formation_energy_per_atom": req.formation_energy_per_atom,
        "density": req.density,
        "nsites": req.nsites,
        "energy_above_hull": req.energy_above_hull,
        "crystal_system": req.crystal_system,
        "spacegroup_num": space_group_number(req.space_group),
        **formula_to_features(req.formula),
    }
    return pd.DataFrame([row])


@app.get("/health", summary="Liveness probe")
def health() -> dict:
    return {"status": "ok", "model_loaded": MODEL is not None}


@app.get("/model-info", summary="Model provenance (FAIR/R)")
def model_info() -> dict:
    metrics_path = PROJECT_ROOT / "metrics.json"
    metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
    return {
        "model_name": "band_gap_predictor",
        "best_model": metrics.get("best_model"),
        "cv_metrics": metrics.get("cv_metrics"),
        "features": PARAMS["features"] if PARAMS else {},
        "training_data": "Materials Project (oxides, 1000 materials)",
        "framework": "scikit-learn + FastAPI",
    }


@app.post("/predict", summary="Predict band gap (eV) for a material")
def predict(req: PredictRequest) -> dict:
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        features = _build_feature_row(req)
        pred = float(MODEL.predict(features)[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")
    return {"formula": req.formula, "predicted_band_gap_eV": round(pred, 4)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=False)
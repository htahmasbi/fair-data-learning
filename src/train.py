"""CLI stage: feature matrix -> trained model + CV metrics.

(1) Cross-validates each model defined in params.yaml
(2) Fits the best model on the full training set
(3) Logs everything to MLflow (params, metrics, artifacts)
(4) Saves best model as model.pkl + metrics to metrics.json

Run:
    python src/train.py
"""

import json
import sys
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Make `from src import ...` work when run as `python src/train.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_params

MODEL_REGISTRY = {
    "Ridge": Ridge,
    "RandomForest": RandomForestRegressor,
    "GradientBoost": HistGradientBoostingRegressor,
}


def build_pipeline(model, feature_config, random_state) -> Pipeline:
    """Assemble preprocessor + model into a single scikit-learn Pipeline.
    A Pipeline guarantees training and inference apply the same transforms.
    """
    numeric, categorical = feature_config["numeric"], feature_config["categorical"]
    preprocessor = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric,
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )
    return Pipeline([("preprocess", preprocessor), ("model", model(random_state=random_state))])


def make_pipeline_kwargs(model_name: str, params: dict) -> dict:
    """Slice the per-model params from params.yaml."""
    model_params = params["train"]["models"][model_name]
    return {f"model__{k}": v for k, v in model_params.items()}


def main() -> None:
    params = load_params()
    train_cfg = params["train"]
    feat_cfg = params["features"]
    mlflow_cfg = params["mlflow"]

    X = pd.read_parquet(
        Path(params["data"]["output_dir"]) / "features.parquet"
    )
    y = pd.read_parquet(
        Path(params["data"]["output_dir"]) / "target.parquet"
    )[train_cfg["target"]]

    cv = KFold(
        n_splits=train_cfg["cv_folds"], shuffle=True, random_state=train_cfg["random_state"]
    )

    mlflow.set_tracking_uri(mlflow_cfg["tracking_uri"])
    mlflow.set_experiment(mlflow_cfg["experiment_name"])

    seed = train_cfg["random_state"]
    results = {}

    for name in train_cfg["models"]:
        model_cls = MODEL_REGISTRY[name]
        # Pass random_state only if the estimator supports it
        pipeline = build_pipeline(model_cls, feat_cfg, seed)
        pipeline.set_params(**make_pipeline_kwargs(name, params))

        with mlflow.start_run(run_name=name):
            scores_r2 = cross_val_score(pipeline, X, y, cv=cv, scoring="r2")
            scores_mae = -cross_val_score(pipeline, X, y, cv=cv, scoring="neg_mean_absolute_error")
            scores_rmse = -cross_val_score(pipeline, X, y, cv=cv, scoring="neg_root_mean_squared_error")

            metrics = {
                "cv_r2_mean": float(scores_r2.mean()),
                "cv_r2_std": float(scores_r2.std()),
                "cv_mae": float(scores_mae.mean()),
                "cv_rmse": float(scores_rmse.mean()),
            }
            results[name] = metrics

            mlflow.log_params(make_pipeline_kwargs(name, params))
            mlflow.log_metrics(metrics)
            mlflow.set_tags({"model": name})
            print(f"[{name}] CV R2={metrics['cv_r2_mean']:.3f} MAE={metrics['cv_mae']:.3f}")

    # Fit best model on full data, log artifact + signature
    best_name = max(results, key=lambda k: results[k]["cv_r2_mean"])
    best_pipeline = build_pipeline(MODEL_REGISTRY[best_name], feat_cfg, seed)
    best_pipeline.set_params(**make_pipeline_kwargs(best_name, params))
    best_pipeline.fit(X, y)

    preds = best_pipeline.predict(X)
    signature = infer_signature(X, preds)
    model_path = PROJECT_ROOT / "models" / "model.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, model_path)

    with mlflow.start_run(run_name=f"{best_name}-fullfit"):
        mlflow.log_params(make_pipeline_kwargs(best_name, params))
        mlflow.log_metrics(
            {
                "train_r2": r2_score(y, preds),
                "train_mae": mean_absolute_error(y, preds),
                "train_rmse": np.sqrt(mean_squared_error(y, preds)),
            }
        )
        mlflow.sklearn.log_model(
            best_pipeline, artifact_path="model", signature=signature,
            serialization_format="cloudpickle",
            registered_model_name="band_gap_predictor",
        )
        mlflow.log_artifact(str(model_path))

    summary = {"best_model": best_name, "cv_metrics": results}
    metrics_path = PROJECT_ROOT / "metrics.json"
    metrics_path.write_text(json.dumps(summary, indent=2))
    print(f"\nBest model: {best_name} (CV R2={results[best_name]['cv_r2_mean']:.3f})")
    print(f"Saved model: {model_path}")
    print(f"Saved metrics: {metrics_path}")


if __name__ == "__main__":
    main()
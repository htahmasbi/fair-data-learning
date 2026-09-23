"""CLI stage: raw CSV -> engineered feature matrix (features.parquet).

Run via DVC or directly:
    python src/features.py
"""

import sys
from pathlib import Path

import pandas as pd

# Make `from src import ...` work when run as `python src/features.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_params
from src.data import load_raw_data, make_features


def main() -> None:
    params = load_params()
    feat_cfg = params["features"]

    df = load_raw_data(Path(params["data"]["input"]))
    df = make_features(df)

    feature_cols = feat_cfg["numeric"] + feat_cfg["categorical"]
    X = df[feature_cols]
    y = df[params["train"]["target"]]

    output_dir = Path(params["data"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    X.to_parquet(output_dir / "features.parquet")
    y.to_frame().to_parquet(output_dir / "target.parquet")

    print(f"Features matrix: {X.shape} rows x {X.shape[1]} cols")
    print(f"Saved to {output_dir / 'features.parquet'}")


if __name__ == "__main__":
    main()
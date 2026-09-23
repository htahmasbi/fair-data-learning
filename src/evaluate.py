"""CLI stage: trained model -> feature importance report (CSV + figure).

Permutation importance = how much each feature degrades R2 when shuffled.
Model-agnostic (works even for models without fitted importances).
"""

import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.inspection import permutation_importance

# Make `from src import ...` work when run as `python src/evaluate.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_params


def main() -> None:
    params = load_params()
    feat_cfg = params["features"]
    out_dir = Path(params["data"]["output_dir"])

    X = pd.read_parquet(out_dir / "features.parquet")
    y = pd.read_parquet(out_dir / "target.parquet")[params["train"]["target"]]

    pipeline = joblib.load(PROJECT_ROOT / "models" / "model.pkl")
    model = pipeline.named_steps["model"]

    preprocess = pipeline.named_steps["preprocess"]
    X_processed = preprocess.transform(X)

    cat_names = list(preprocess.named_transformers_["cat"].get_feature_names_out())
    all_names = feat_cfg["numeric"] + cat_names

    imp = permutation_importance(
        model, X_processed, y, n_repeats=10, random_state=42, scoring="r2"
    )
    imp_df = (
        pd.DataFrame({"feature": all_names, "importance": imp.importances_mean})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    imp_df.to_csv(out_dir / "feature_importances.csv", index=False)

    top = imp_df.head(12)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top["feature"][::-1], top["importance"][::-1], color="tab:blue", alpha=0.8)
    ax.set_xlabel("Permutation importance (drop in R2)")
    ax.set_title("Top Feature Importances")
    plt.tight_layout()
    fig.savefig(out_dir / "feature_importances.png", dpi=150, bbox_inches="tight")
    print(imp_df.head(12).to_string(index=False))
    print(f"Saved {out_dir / 'feature_importances.csv'}")


if __name__ == "__main__":
    main()
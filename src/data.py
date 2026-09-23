"""Data loading and feature engineering.

The functions here are deliberately pure & simple:
input -> output, no side effects, so they are trivial to unit test.
"""

import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element
from pymatgen.symmetry.groups import SpaceGroup


def formula_to_features(formula: str) -> dict:
    """Derive chemical descriptors from a composition formula string."""
    comp = Composition(formula)
    ens = [Element(el).X for el in comp]
    zs = [Element(el).Z for el in comp]
    return {
        "n_elements": len(comp),
        "avg_electroneg": float(comp.average_electroneg),
        "std_electroneg": float(np.std(ens)),
        "range_electroneg": float(max(ens) - min(ens)),
        "avg_atomic_number": float(np.mean(zs)),
        "total_electrons": float(comp.total_electrons),
    }


def space_group_number(symbol) -> float:
    """Map a Hermann-Mauguin symbol (e.g. 'Pm') to its crystallographic number."""
    if pd.isna(symbol):
        return np.nan
    try:
        return float(SpaceGroup(symbol).int_number)
    except Exception:
        return np.nan


def load_raw_data(path) -> pd.DataFrame:
    """Load the raw cleaned CSV."""
    return pd.read_csv(path)


def make_features(df: pd.DataFrame) -> tuple:
    """Feature engineering: composition descriptors + structural encodings.

    Returns (X, y) where X is a DataFrame of engineered features and
    y is the target Series (band gap).
    """
    df = df.copy()
    comp_feats = pd.DataFrame(df["formula"].apply(formula_to_features).tolist())
    df = pd.concat([df, comp_feats], axis=1)
    df["spacegroup_num"] = df["space_group"].apply(space_group_number)
    return df
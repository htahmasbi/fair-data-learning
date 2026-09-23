"""Tests for feature engineering (src/data.py)."""

import numpy as np
import pandas as pd
import pytest

from src.data import formula_to_features, make_features, space_group_number


def test_formula_to_features_basic():
    feats = formula_to_features("Fe2O3")
    assert feats["n_elements"] == 2
    # O (3.44) > Fe (1.83) -> range and std > 0
    assert feats["range_electroneg"] == pytest.approx(1.61)
    assert feats["std_electroneg"] > 0
    assert feats["total_electrons"] == pytest.approx(76)
    # Electronegativity between aliovalent elements
    assert 1 < feats["avg_electroneg"] < 4


def test_formula_to_features_single_element():
    feats = formula_to_features("Mg")
    assert feats["n_elements"] == 1
    assert feats["std_electroneg"] == pytest.approx(0.0)
    assert feats["range_electroneg"] == pytest.approx(0.0)


def test_space_group_number_known_and_unknown():
    assert space_group_number("Pm") == 6  # even without explicit digit
    assert space_group_number("P 43 21 2") != space_group_number("Pm")
    assert np.isnan(space_group_number("NotAGroup"))


def test_make_features_adds_columns():
    df = pd.DataFrame(
        {
            "formula": ["Fe2O3", "MgO"],
            "space_group": ["P1", "Fm-3m"],
        }
    )
    out = make_features(df)
    for col in [
        "n_elements",
        "avg_electroneg",
        "std_electroneg",
        "range_electroneg",
        "avg_atomic_number",
        "total_electrons",
        "spacegroup_num",
    ]:
        assert col in out.columns
    assert out["spacegroup_num"].iloc[0] > 0
"""
Equivalence tests for the vectorized `build_intersectional_labels` fast path.

`build_intersectional_labels` was changed from a row-wise `.agg(sep.join, axis=1)`
call (O(n) Python-level string joins) to a vectorized `Series.str.cat` chain for
the common case (non-empty frame, no NaN under include_na=False). The two edge
cases below still fall back to the original row-wise call, so this test pins the
*new* code against the *original* implementation (kept here as an oracle) across
all the known-tricky inputs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fairness_pipeline_dev_toolkit.utils.intersectional import build_intersectional_labels


def _oracle(attrs_df, columns=None, sep="||", include_na=True):
    """Original row-wise implementation, kept as a equivalence oracle."""
    if columns is None:
        columns = list(attrs_df.columns)

    df = attrs_df[columns].copy()

    if include_na:
        df = df.fillna("NaN")
        labels = df.astype(str).agg(sep.join, axis=1)
    else:
        labels = df.astype("string").agg(sep.join, axis=1)

    return labels.astype("category")


def _assert_equivalent(df, **kwargs):
    new = build_intersectional_labels(df, **kwargs)
    old = _oracle(df, **kwargs)

    if isinstance(old, pd.DataFrame):
        # 0-row `.agg` DataFrame-return quirk: both paths must share it.
        assert isinstance(new, pd.DataFrame)
        assert old.shape == new.shape
        return

    assert isinstance(new, pd.Series)
    pd.testing.assert_series_equal(new.astype(object), old.astype(object), check_names=False)


class TestBuildIntersectionalLabelsVectorizedEquivalence:
    def test_many_rows(self):
        rng = np.random.default_rng(0)
        n = 5000
        df = pd.DataFrame(
            {
                "race": rng.choice(["A", "B", "C"], size=n),
                "gender": rng.choice(["M", "F"], size=n),
                "age_band": rng.choice(["young", "old"], size=n),
            }
        )
        _assert_equivalent(df)

    def test_wide_mixed_dtypes(self):
        df = pd.DataFrame(
            {
                "a": [1, 2, 3, 4],
                "b": ["x", "y", "z", "w"],
                "c": [1.5, 2.5, np.nan, 4.5],
                "d": [True, False, True, False],
            }
        )
        _assert_equivalent(df, include_na=True)

    def test_single_column(self):
        df = pd.DataFrame({"group": ["A", "B", "A", "B", "C"]})
        _assert_equivalent(df)

    def test_custom_separator_and_column_subset(self):
        df = pd.DataFrame(
            {
                "race": ["A", "B", "C"],
                "gender": ["M", "F", "M"],
                "age": [25, 30, 40],
            }
        )
        _assert_equivalent(df, columns=["race", "gender"], sep="_")

    def test_single_row(self):
        df = pd.DataFrame({"race": ["A"], "gender": ["M"]})
        _assert_equivalent(df)

    def test_include_na_true_with_nan(self):
        df = pd.DataFrame(
            {
                "race": ["A", "B", None, "A"],
                "gender": ["M", "F", "M", None],
            }
        )
        _assert_equivalent(df, include_na=True)

    def test_include_na_false_without_nan(self):
        df = pd.DataFrame(
            {
                "race": ["A", "B", "C"],
                "gender": ["M", "F", "M"],
            }
        )
        _assert_equivalent(df, include_na=False)

    def test_include_na_false_with_nan_raises_type_error(self):
        df = pd.DataFrame(
            {
                "race": ["A", "B", None],
                "gender": ["M", "F", "M"],
            }
        )
        with pytest.raises(TypeError):
            build_intersectional_labels(df, include_na=False)
        with pytest.raises(TypeError):
            _oracle(df, include_na=False)

    def test_all_nan(self):
        df = pd.DataFrame(
            {
                "race": [None, None, None],
                "gender": [None, None, None],
            }
        )
        _assert_equivalent(df, include_na=True)

    def test_empty_dataframe(self):
        df = pd.DataFrame(
            {"race": pd.Series([], dtype=object), "gender": pd.Series([], dtype=object)}
        )
        _assert_equivalent(df, include_na=True)
        _assert_equivalent(df, include_na=False)

    @pytest.mark.parametrize("seed", range(5))
    def test_fuzz_sweep(self, seed):
        rng = np.random.default_rng(seed)
        n = rng.integers(1, 200)
        n_cols = rng.integers(1, 5)
        data = {}
        for i in range(n_cols):
            choices = rng.choice(["A", "B", "C", "D", None], size=n)
            data[f"col_{i}"] = choices
        df = pd.DataFrame(data)
        _assert_equivalent(df, include_na=True)

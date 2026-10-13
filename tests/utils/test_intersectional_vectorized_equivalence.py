"""Equivalence tests for the vectorised `build_intersectional_labels` fast path.

`build_intersectional_labels` used to join every row with Python-level
`.agg(sep.join, axis=1)`, which dominates wall time for wide/long `attrs_df`
(see benchmarks/benchmark_metrics_100k.py intersectional cases). The fast path
below reproduces the same row-wise, ordered, separator-joined concatenation
with vectorised `Series.str.cat`, falling back to the original row-wise code
for the empty-frame and any-NaN-with-``include_na=False`` edge cases where
``str.cat``'s default NaN handling would silently diverge from ``sep.join``
raising.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fairness_pipeline_dev_toolkit.utils.intersectional import build_intersectional_labels


def _oracle(attrs_df, columns=None, sep="||", include_na=True):
    """Unvectorised reference: the original row-wise implementation."""
    if columns is None:
        columns = list(attrs_df.columns)
    df = attrs_df[columns].copy()
    if include_na:
        df = df.fillna("NaN")
        labels = df.astype(str).agg(sep.join, axis=1)
    else:
        labels = df.astype("string").agg(sep.join, axis=1)
    return labels.astype("category")


def _assert_same_labels(new: pd.Series, old: pd.Series) -> None:
    assert isinstance(new, pd.Series)
    assert new.dtype.name == "category"
    pd.testing.assert_series_equal(new.astype(object), old.astype(object), check_names=False)


class TestVectorizedEquivalence:
    def test_two_columns_many_rows_no_nan(self):
        rng = np.random.default_rng(0)
        n = 5_000
        df = pd.DataFrame(
            {
                "race": rng.choice(["A", "B", "C", "D", "E"], size=n),
                "gender": rng.choice(["M", "F"], size=n),
            }
        )
        for include_na in (True, False):
            new = build_intersectional_labels(df, include_na=include_na)
            old = _oracle(df, include_na=include_na)
            _assert_same_labels(new, old)

    def test_three_wide_columns_mixed_dtypes(self):
        rng = np.random.default_rng(1)
        n = 2_000
        df = pd.DataFrame(
            {
                "race": rng.choice(["A", "B", "C"], size=n),
                "age_group": rng.integers(0, 5, size=n),
                "score": rng.normal(size=n).round(3),
            }
        )
        for include_na in (True, False):
            new = build_intersectional_labels(df, include_na=include_na)
            old = _oracle(df, include_na=include_na)
            _assert_same_labels(new, old)

    def test_single_column(self):
        df = pd.DataFrame({"group": ["A", "B", "A", "B", "C"]})
        for include_na in (True, False):
            new = build_intersectional_labels(df, include_na=include_na)
            old = _oracle(df, include_na=include_na)
            _assert_same_labels(new, old)

    def test_custom_separator_and_column_subset(self):
        df = pd.DataFrame(
            {
                "race": ["A", "B", "A"],
                "gender": ["M", "F", "F"],
                "age": [20, 30, 40],
            }
        )
        new = build_intersectional_labels(df, columns=["race", "gender"], sep="_")
        old = _oracle(df, columns=["race", "gender"], sep="_")
        _assert_same_labels(new, old)

    def test_single_row(self):
        df = pd.DataFrame({"race": ["A"], "gender": ["M"]})
        for include_na in (True, False):
            new = build_intersectional_labels(df, include_na=include_na)
            old = _oracle(df, include_na=include_na)
            _assert_same_labels(new, old)

    def test_include_na_true_with_missing_values(self):
        df = pd.DataFrame(
            {
                "race": ["A", None, "B", np.nan],
                "gender": ["M", "F", None, "F"],
            }
        )
        new = build_intersectional_labels(df, include_na=True)
        old = _oracle(df, include_na=True)
        _assert_same_labels(new, old)
        assert "NaN" in str(new.iloc[1])

    def test_include_na_false_no_missing_values_uses_fast_path(self):
        df = pd.DataFrame({"race": ["A", "B", "A"], "gender": ["M", "F", "F"]})
        new = build_intersectional_labels(df, include_na=False)
        old = _oracle(df, include_na=False)
        _assert_same_labels(new, old)

    def test_include_na_false_with_missing_values_raises_like_original(self):
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

    def test_all_nan_values(self):
        df = pd.DataFrame({"race": [None, None], "gender": [None, None]})
        new = build_intersectional_labels(df, include_na=True)
        old = _oracle(df, include_na=True)
        _assert_same_labels(new, old)

    def test_empty_dataframe_matches_original_quirk(self):
        df = pd.DataFrame({"race": [], "gender": []})
        new = build_intersectional_labels(df, include_na=True)
        old = _oracle(df, include_na=True)
        # The original row-wise `.agg` returns a DataFrame (not a Series) for a
        # zero-row input; the fast path falls back to the same code for this case,
        # so both outputs must have the same (unusual) type.
        assert type(new) is type(old)
        if isinstance(old, pd.DataFrame):
            pd.testing.assert_frame_equal(new, old)
        else:
            _assert_same_labels(new, old)

    def test_intersectional_combinations_match_across_many_seeds(self):
        for seed in range(5):
            rng = np.random.default_rng(seed)
            n = 1_000
            df = pd.DataFrame(
                {
                    "race": rng.choice(
                        ["A", "B", "C", "D", "E"], size=n, p=[0.5, 0.2, 0.15, 0.1, 0.05]
                    ),
                    "gender": rng.choice(["M", "F"], size=n),
                    "age_group": rng.choice(["<30", "30-50", "50+"], size=n),
                }
            )
            for include_na in (True, False):
                new = build_intersectional_labels(df, include_na=include_na)
                old = _oracle(df, include_na=include_na)
                _assert_same_labels(new, old)

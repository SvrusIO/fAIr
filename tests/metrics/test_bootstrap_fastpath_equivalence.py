"""Equivalence tests for the vectorised bootstrap statistic fast path.

``core.py`` computes bootstrap CIs by calling a per-replicate statistic
function ``B`` times (default 1000). The original implementation
(``dpd_stat_from_indices`` / ``eod_stat_from_indices`` / ``mae_gap_stat_from_indices``)
loops over every analysis group inside each replicate, doing an
``O(n_groups * n)`` boolean comparison per draw. The fast path
(``_dpd_stat_from_codes`` / ``_eod_stat_from_codes`` / ``_mae_stat_from_codes``)
precomputes an integer group code once per bootstrap *call* and does a single
vectorised ``np.bincount`` pass per replicate. These tests prove the two
produce identical values (bit-exact for the 0/1-valued DPD and EOD statistics,
and within floating-point summation-order noise for MAE) across group-size
edge cases, and that the analyzer's end-to-end CI matches an independent
oracle built from the original, unoptimised statistic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from fairness_pipeline_dev_toolkit.metrics.core import (
    FairnessAnalyzer,
    _dpd_stat_from_codes,
    _eod_stat_from_codes,
    _group_codes,
    _mae_stat_from_codes,
    _sens_keys,
    dpd_stat_from_indices,
    eod_stat_from_indices,
    mae_gap_stat_from_indices,
)
from fairness_pipeline_dev_toolkit.stats.bootstrap import bootstrap_ci


def _codes_for(group_of, group_keys):
    return _group_codes(group_of, group_keys), len(group_keys)


class TestDPDFastPathEquivalence:
    @pytest.mark.parametrize("seed", range(10))
    def test_matches_reference_many_resamples(self, seed):
        rng = np.random.default_rng(seed)
        n = 500
        n_groups = 6
        y_pred = rng.integers(0, 2, size=n).astype(float)
        raw_groups = rng.integers(0, n_groups, size=n)
        group_of = _sens_keys(raw_groups)
        group_keys = [str(g) for g in range(n_groups)]
        codes, n_g = _codes_for(group_of, group_keys)

        for _ in range(20):
            sample = rng.integers(0, n, size=n)
            old = dpd_stat_from_indices(sample, y_pred, group_of, group_keys)
            new = _dpd_stat_from_codes(sample, y_pred, codes, n_g)
            if np.isnan(old):
                assert np.isnan(new)
            else:
                assert new == pytest.approx(old, abs=1e-12)

    def test_empty_group_in_resample_returns_nan(self):
        y_pred = np.array([0.0, 1.0, 0.0, 1.0, 1.0, 0.0])
        group_of = _sens_keys(np.array([0, 0, 0, 1, 1, 1]))
        group_keys = ["0", "1"]
        codes, n_g = _codes_for(group_of, group_keys)
        # Resample only touches group "0" — group "1" is absent.
        sample = np.array([0, 1, 2, 0, 1, 2])
        old = dpd_stat_from_indices(sample, y_pred, group_of, group_keys)
        new = _dpd_stat_from_codes(sample, y_pred, codes, n_g)
        assert np.isnan(old) and np.isnan(new)

    def test_single_row_group(self):
        y_pred = np.array([1.0, 0.0, 0.0, 1.0])
        group_of = _sens_keys(np.array(["a", "b", "b", "b"]))
        group_keys = ["a", "b"]
        codes, n_g = _codes_for(group_of, group_keys)
        sample = np.array([0, 1, 2, 3])
        old = dpd_stat_from_indices(sample, y_pred, group_of, group_keys)
        new = _dpd_stat_from_codes(sample, y_pred, codes, n_g)
        assert new == pytest.approx(old, abs=1e-12)

    def test_excluded_small_group_is_ignored(self):
        """A group present in group_of but absent from group_keys (e.g. below
        min_group_size, or an original NaN label) must not affect the result."""
        y_pred = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 1.0])
        group_of = _sens_keys(np.array(["a", "a", "b", "b", "tiny", "tiny"]))
        group_keys = ["a", "b"]  # "tiny" excluded
        codes, n_g = _codes_for(group_of, group_keys)
        sample = np.arange(6)
        old = dpd_stat_from_indices(sample, y_pred, group_of, group_keys)
        new = _dpd_stat_from_codes(sample, y_pred, codes, n_g)
        assert new == pytest.approx(old, abs=1e-12)
        # codes for the excluded group must be -1
        assert (codes[np.asarray(group_of) == "tiny"] == -1).all()

    def test_intersectional_many_groups(self):
        rng = np.random.default_rng(3)
        n = 2000
        race = rng.choice(["A", "B", "C", "D", "E"], size=n)
        gender = rng.choice(["M", "F"], size=n)
        age = rng.choice(["<30", "30-50", "50+"], size=n)
        labels = pd.Series([f"{r}||{g}||{a}" for r, g, a in zip(race, gender, age)]).to_numpy()
        group_keys = sorted(set(labels.tolist()))
        y_pred = rng.integers(0, 2, size=n).astype(float)
        group_of = _sens_keys(labels)
        codes, n_g = _codes_for(group_of, group_keys)

        for seed in range(5):
            r2 = np.random.default_rng(seed)
            sample = r2.integers(0, n, size=n)
            old = dpd_stat_from_indices(sample, y_pred, group_of, group_keys)
            new = _dpd_stat_from_codes(sample, y_pred, codes, n_g)
            if np.isnan(old):
                assert np.isnan(new)
            else:
                assert new == pytest.approx(old, abs=1e-12)


class TestEODFastPathEquivalence:
    @pytest.mark.parametrize("seed", range(10))
    def test_matches_reference_many_resamples(self, seed):
        rng = np.random.default_rng(seed + 100)
        n = 500
        n_groups = 5
        y_true = rng.integers(0, 2, size=n).astype(float)
        y_pred = rng.integers(0, 2, size=n).astype(float)
        raw_groups = rng.integers(0, n_groups, size=n)
        group_of = _sens_keys(raw_groups)
        group_keys = [str(g) for g in range(n_groups)]
        codes, n_g = _codes_for(group_of, group_keys)

        for _ in range(20):
            sample = rng.integers(0, n, size=n)
            old = eod_stat_from_indices(sample, y_true, y_pred, group_of, group_keys)
            new = _eod_stat_from_codes(sample, y_true, y_pred, codes, n_g)
            if np.isnan(old):
                assert np.isnan(new)
            else:
                assert new == pytest.approx(old, abs=1e-12)

    def test_group_with_no_positives_or_negatives(self):
        # group "b" has only y_true == 1 rows -> fpr undefined for that group.
        y_true = np.array([1.0, 1.0, 1.0, 0.0, 1.0, 0.0])
        y_pred = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 1.0])
        group_of = _sens_keys(np.array(["a", "a", "a", "a", "b", "b"]))
        group_keys = ["a", "b"]
        codes, n_g = _codes_for(group_of, group_keys)
        sample = np.arange(6)
        old = eod_stat_from_indices(sample, y_true, y_pred, group_of, group_keys)
        new = _eod_stat_from_codes(sample, y_true, y_pred, codes, n_g)
        if np.isnan(old):
            assert np.isnan(new)
        else:
            assert new == pytest.approx(old, abs=1e-12)

    def test_empty_group_returns_nan(self):
        y_true = np.array([1.0, 0.0, 1.0, 0.0])
        y_pred = np.array([1.0, 0.0, 0.0, 1.0])
        group_of = _sens_keys(np.array(["a", "a", "b", "b"]))
        group_keys = ["a", "b"]
        codes, n_g = _codes_for(group_of, group_keys)
        sample = np.array([0, 1, 0, 1])  # group "b" absent
        old = eod_stat_from_indices(sample, y_true, y_pred, group_of, group_keys)
        new = _eod_stat_from_codes(sample, y_true, y_pred, codes, n_g)
        assert np.isnan(old) and np.isnan(new)


class TestMAEFastPathEquivalence:
    @pytest.mark.parametrize("seed", range(10))
    def test_matches_reference_many_resamples(self, seed):
        rng = np.random.default_rng(seed + 200)
        n = 2000
        n_groups = 7
        abs_err = np.abs(rng.normal(0, 1, size=n))
        raw_groups = rng.integers(0, n_groups, size=n)
        group_of = _sens_keys(raw_groups)
        group_keys = [str(g) for g in range(n_groups)]
        codes, n_g = _codes_for(group_of, group_keys)

        for _ in range(20):
            sample = rng.integers(0, n, size=n)
            old = mae_gap_stat_from_indices(sample, abs_err, group_of, group_keys)
            new = _mae_stat_from_codes(sample, abs_err, codes, n_g)
            if np.isnan(old):
                assert np.isnan(new)
            else:
                # Float summation order differs between the two paths; still
                # must agree far tighter than the stated 1e-12 contract since
                # group sums here are O(1) in magnitude.
                assert new == pytest.approx(old, rel=0, abs=1e-12)

    def test_single_row_group(self):
        abs_err = np.array([0.3, 1.2, 0.7, 0.1])
        group_of = _sens_keys(np.array(["x", "y", "y", "y"]))
        group_keys = ["x", "y"]
        codes, n_g = _codes_for(group_of, group_keys)
        sample = np.arange(4)
        old = mae_gap_stat_from_indices(sample, abs_err, group_of, group_keys)
        new = _mae_stat_from_codes(sample, abs_err, codes, n_g)
        assert new == pytest.approx(old, abs=1e-12)


class TestAnalyzerEndToEndOracle:
    """The analyzer's internal CI must match an independent oracle built from
    the original (slow) per-group-loop statistic, for all three metrics and
    for the intersectional code path."""

    def test_dpd_ci_oracle(self):
        rng = np.random.default_rng(1)
        n_per = 40
        y_pred = rng.integers(0, 2, size=n_per * 2).astype(float)
        sensitive = np.repeat([0, 1], n_per)

        fa = FairnessAnalyzer(min_group_size=10, backend="native")
        res = fa.demographic_parity_difference(
            y_pred, sensitive, with_ci=True, ci_samples=300, with_effect_size=False
        )
        group_of = _sens_keys(sensitive)
        groups = ["0", "1"]
        obs_idx = np.arange(len(y_pred), dtype=int)

        def stat_fn(sample_idx):
            return dpd_stat_from_indices(sample_idx, y_pred, group_of, groups)

        expected = bootstrap_ci(obs_idx, stat_fn, B=300, random_state=42)
        assert res.ci[0] == pytest.approx(expected[0], abs=1e-12)
        assert res.ci[1] == pytest.approx(expected[1], abs=1e-12)

    def test_eod_ci_oracle_intersectional(self):
        rng = np.random.default_rng(2)
        n = 1500
        attrs = pd.DataFrame(
            {
                "race": rng.choice(["A", "B", "C"], size=n),
                "gender": rng.choice(["M", "F"], size=n),
            }
        )
        y_true = rng.integers(0, 2, size=n).astype(float)
        y_pred = rng.integers(0, 2, size=n).astype(float)

        fa = FairnessAnalyzer(min_group_size=30, backend="native")
        res = fa.equalized_odds_difference(
            y_true,
            y_pred,
            sensitive=None,
            intersectional=True,
            attrs_df=attrs,
            with_ci=True,
            ci_samples=200,
            with_effect_size=False,
        )

        from fairness_pipeline_dev_toolkit.utils.intersectional import min_group_mask

        labels = fa._intersectional_prep(attrs, None)
        mask = np.asarray(min_group_mask(labels, 30), dtype=bool)
        sens = np.asarray(labels)[mask]
        yt = y_true[mask]
        yp = y_pred[mask]

        groups = [g for g, n_ in (res.n_per_group or {}).items() if n_ >= 30]
        group_of = _sens_keys(sens)
        group_keys = [str(g) for g in groups]
        obs_idx = np.arange(len(yp), dtype=int)

        def stat_fn(sample_idx):
            return eod_stat_from_indices(sample_idx, yt, yp, group_of, group_keys)

        expected = bootstrap_ci(obs_idx, stat_fn, B=200, random_state=42)
        assert res.ci[0] == pytest.approx(expected[0], abs=1e-12)
        assert res.ci[1] == pytest.approx(expected[1], abs=1e-12)

    def test_mae_ci_oracle_intersectional(self):
        rng = np.random.default_rng(4)
        n = 1500
        attrs = pd.DataFrame(
            {
                "race": rng.choice(["A", "B", "C"], size=n),
                "gender": rng.choice(["M", "F"], size=n),
            }
        )
        y_true = rng.normal(0, 1, size=n)
        y_pred = y_true + rng.normal(0, 0.5, size=n)

        fa = FairnessAnalyzer(min_group_size=30, backend="native")
        res = fa.mae_parity_difference(
            y_true,
            y_pred,
            sensitive=None,
            intersectional=True,
            attrs_df=attrs,
            with_ci=True,
            ci_samples=200,
            with_effect_size=False,
        )

        from fairness_pipeline_dev_toolkit.utils.intersectional import min_group_mask

        labels = fa._intersectional_prep(attrs, None)
        mask = np.asarray(min_group_mask(labels, 30), dtype=bool)
        sens = np.asarray(labels)[mask]
        yt = y_true[mask]
        yp = y_pred[mask]
        abs_err = np.abs(yt - yp)

        groups = [g for g, n_ in (res.n_per_group or {}).items() if n_ >= 30]
        group_of = _sens_keys(sens)
        group_keys = [str(g) for g in groups]
        obs_idx = np.arange(len(yp), dtype=int)

        def stat_fn(sample_idx):
            return mae_gap_stat_from_indices(sample_idx, abs_err, group_of, group_keys)

        expected = bootstrap_ci(obs_idx, stat_fn, B=200, random_state=42)
        assert res.ci[0] == pytest.approx(expected[0], abs=1e-12)
        assert res.ci[1] == pytest.approx(expected[1], abs=1e-12)

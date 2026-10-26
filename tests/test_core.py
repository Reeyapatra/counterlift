import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from counterlift.data import FEATURES, load_sample, synthetic, validate
from counterlift.pipeline import run, score_file
from counterlift.statistics import (bootstrap_mean, choose_policy, dr_signal,
                                       experiment_report, gain_curve)


class CausalChecks(unittest.TestCase):
    def test_policy_budget_and_negative_value(self):
        scores = np.array([-.2, .01, .3, .4])
        np.testing.assert_array_equal(choose_policy(scores, .5, .05), [0, 0, 1, 1])
        self.assertEqual(choose_policy(scores, 0).sum(), 0)
        self.assertEqual(choose_policy(scores, 1, 1).sum(), 0)
        with self.assertRaises(ValueError):
            choose_policy(scores, 1.1)

    def test_dr_matches_known_effect_in_randomized_simulation(self):
        rng = np.random.default_rng(7)
        n = 150_000
        t = rng.binomial(1, .8, n)
        y = rng.binomial(1, .1 + .1 * t)
        phi = dr_signal(t, y, np.full(n, .1), np.full(n, .2), .8)
        self.assertAlmostEqual(phi.mean(), .1, delta=.01)
        ci = bootstrap_mean(phi, 50)
        # A particular 95% interval is allowed to miss the truth.
        self.assertLess(ci["lower"], ci["estimate"])
        self.assertGreater(ci["upper"], ci["estimate"])

    def test_known_propensity_interval_coverage_over_repeated_experiments(self):
        rng = np.random.default_rng(22)
        covered = 0
        for trial in range(100):
            t = rng.binomial(1, .8, 3000)
            y = rng.binomial(1, .1 + .1 * t)
            phi = dr_signal(t, y, np.full(len(t), .1), np.full(len(t), .2), .8)
            ci = bootstrap_mean(phi, 100, trial)
            covered += ci["lower"] <= .1 <= ci["upper"]
        self.assertGreaterEqual(covered, 85)

    def test_zero_treatment_effect_synthetic_null(self):
        rng = np.random.default_rng(10)
        t = rng.binomial(1, .85, 100_000)
        y = rng.binomial(1, .1, len(t))
        phi = dr_signal(t, y, np.full(len(t), .1), np.full(len(t), .1), .85)
        self.assertAlmostEqual(phi.mean(), 0, delta=.01)

    def test_post_treatment_columns_never_features(self):
        self.assertNotIn("visit", FEATURES)
        self.assertNotIn("exposure", FEATURES)
        self.assertNotIn("treatment", FEATURES)
        df = synthetic(1000)
        df.loc[0, "f0"] = np.nan
        with self.assertRaises(ValueError):
            validate(df)

    def test_srm_is_not_invented(self):
        report = experiment_report(synthetic(10_000))
        self.assertIsNone(report["srm_pvalue"])
        self.assertIsNotNone(experiment_report(synthetic(10_000), .85)["srm_pvalue"])

    def test_gain_curve_endpoint_is_ipw_ate(self):
        df = synthetic(10_000)
        t, y = df.treatment.to_numpy(), df.conversion.to_numpy()
        _, curve = gain_curve(df.f0.to_numpy(), t, y, .85)
        expected = np.mean(t * y / .85 - (1-t) * y / .15)
        self.assertAlmostEqual(curve.iloc[-1, 1], expected)

    def test_sampling_is_reproducible_and_spans_source(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "source.csv"
            synthetic(5000).drop(columns="_source_row").to_csv(path, index=False)
            a, provenance = load_sample(path, 1000)
            b, _ = load_sample(path, 1000)
            pd.testing.assert_frame_equal(a, b)
            self.assertGreater(a._source_row.max(), 4000)
            self.assertEqual(provenance["source_rows"], 5000)

    def test_pipeline_and_batch_scoring(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "run"
            manifest = run(synthetic(6000), out, {"dataset": "SYNTHETIC TEST"}, repeats=50)
            self.assertIn(manifest["winner"], ["constant_ate", "t_learner", "dr_learner", "treat_none"])
            evaluation = pd.read_csv(out / "policy_evaluation.csv")
            self.assertTrue((evaluation.selected_fraction <= evaluation.budget_fraction + 1e-9).all())
            self.assertEqual(evaluation.loc[evaluation.model == "treat_none", "incremental_per_user"].abs().sum(), 0)
            with sqlite3.connect(out / "audit.sqlite") as db:
                rows = db.execute("SELECT COUNT(*), COUNT(DISTINCT _source_row) FROM assignments").fetchone()
                self.assertEqual(rows, (6000, 6000))
            source = root / "new.csv"
            synthetic(100, seed=5)[FEATURES].to_csv(source, index=False)
            report = score_file(out / "model.joblib", source, root / "scores.csv")
            self.assertEqual(report["rows"], 100)
            self.assertTrue(np.isfinite(pd.read_csv(root / "scores.csv").estimated_uplift).all())
            self.assertEqual(json.loads((out / "manifest.json").read_text())["seed"], 42)
            with self.assertRaises(ValueError):
                run(synthetic(6000), out, {}, repeats=50)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from counterlift.artifacts import export_public, verify_run
from counterlift.data import FEATURES, synthetic
from counterlift.models import fit_models, predict
from counterlift.pipeline import run, score_file
from counterlift.statistics import (capacity_policy, choose_policy, dr_signal,
                                     experiment_report, interval)


class ScientificHardening(unittest.TestCase):
    def test_comparator_fills_zero_probability_capacity(self):
        np.testing.assert_array_equal(capacity_policy(np.zeros(5), .4), [1, 1, 0, 0, 0])
        self.assertEqual(choose_policy(np.zeros(5), .4).sum(), 0)

    def test_invalid_financial_and_aipw_inputs(self):
        for cost, value in [(np.nan, 1), (0, np.inf), (np.inf, 1)]:
            with self.assertRaises(ValueError):
                choose_policy([.1], 1, cost, value)
        for args in [([1, 0], [1], [.1, .1], [.2, .2], .8),
                     ([2], [1], [.1], [.2], .8),
                     ([1], [1], [-.1], [.2], .8)]:
            with self.assertRaises(ValueError):
                dr_signal(*args)

    def test_negative_heterogeneous_effect_and_known_policy_ordering(self):
        rng = np.random.default_rng(23)
        n = 200_000
        x = rng.normal(size=n)
        tau = np.where(x > 0, .12, -.06)
        t = rng.binomial(1, .7, n)
        m0 = np.full(n, .15)
        y = rng.binomial(1, m0 + t * tau)
        phi = dr_signal(t, y, m0, m0 + tau, .7)
        ipw = t * y / .7 - (1-t) * y / .3
        for signal in (phi, ipw):
            self.assertAlmostEqual(np.mean(signal[x > 0]), .12, delta=.01)
            self.assertAlmostEqual(np.mean(signal[x <= 0]), -.06, delta=.01)
            self.assertGreater(np.mean((x > 0) * signal), np.mean((x <= 0) * signal))
        # Swapping assignment and nuisance arms reverses the estimand.
        np.testing.assert_allclose(dr_signal(1-t, y, m0+tau, m0, .3), -phi)

    def test_constant_features_and_rare_outcome_rejection(self):
        df = synthetic(6000)
        df[FEATURES] = 0.
        report = experiment_report(df)
        self.assertTrue(all(v == 0 for v in report['standardized_mean_differences'].values()))
        models = fit_models(df[FEATURES].to_numpy(), df.treatment.to_numpy(), df.conversion.to_numpy(), .85)
        scores, _, _ = predict(models, np.zeros((3, 12)))
        self.assertTrue(all(np.isfinite(a).all() for a in scores.values()))
        df['conversion'] = 0
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, '10 conversions'):
                run(df, Path(d)/'rare', {}, repeats=50)
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_fitted_propensity_coverage_includes_independent_training_uncertainty(self):
        rng = np.random.default_rng(2026)
        covered = 0
        for _ in range(200):
            e = rng.binomial(1, .7, 4000).mean()
            t = rng.binomial(1, .7, 4000)
            x = rng.binomial(1, .5, 4000)
            m0 = .1 + .05*x
            tau = .04 + .04*x
            y = rng.binomial(1, m0+t*tau)
            ci = interval(dr_signal(t, y, m0, m0+tau, e))
            covered += ci['lower'] <= .06 <= ci['upper']
        self.assertGreaterEqual(covered, 175)
        self.assertLessEqual(covered, 200)

    def test_full_pipeline_isolation_integrity_export_and_idempotent_scoring(self):
        import counterlift.pipeline as pipeline
        df = synthetic(6000)
        seen = []
        original = pipeline.predict
        def observe(models, x):
            seen.append(x.copy())
            return original(models, x)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with patch.object(pipeline, 'predict', side_effect=observe):
                manifest = run(df, root/'run', {'dataset': 'SYNTHETIC TEST'}, repeats=50)
            self.assertEqual([len(a) for a in seen], [1200, 1200])
            self.assertFalse(set(map(tuple, seen[0])) & set(map(tuple, seen[1])))
            verify_run(root/'run')
            export_public(root/'run', root/'public')
            verify_run(root/'public', public=True)
            self.assertEqual((root/'public').stat().st_mode & 0o777, 0o755)
            self.assertFalse((root/'public'/'model.joblib').exists())
            self.assertFalse((root/'public'/'audit.sqlite').exists())
            data = root/'input.csv'
            df[FEATURES].iloc[:20].to_csv(data, index=False)
            score_file(root/'run/model.joblib', data, root/'scores.csv')
            before = (root/'scores.csv').read_bytes()
            score_file(root/'run/model.joblib', data, root/'scores.csv')
            self.assertEqual(before, (root/'scores.csv').read_bytes())
            with self.assertRaises(ValueError):
                score_file(root/'run/model.joblib', data, data)
            (root/'run/experiment.json').write_text('{}')
            with self.assertRaises(ValueError):
                verify_run(root/'run')
            self.assertIn('run_id', manifest)

    def test_test_outcomes_cannot_change_model_selection(self):
        from sklearn.model_selection import train_test_split
        df = synthetic(6000)
        _, rest = train_test_split(np.arange(len(df)), test_size=.4, stratify=df.treatment, random_state=42)
        _, test = train_test_split(rest, test_size=.5, stratify=df.iloc[rest].treatment, random_state=42)
        altered = df.copy()
        altered.loc[test, 'conversion'] = 1-altered.loc[test, 'conversion']
        with tempfile.TemporaryDirectory() as d:
            a = run(df, Path(d)/'a', {}, repeats=50)
            b = run(altered, Path(d)/'b', {}, repeats=50)
            self.assertEqual(a['winner'], b['winner'])
            self.assertEqual(a['validation_selection'], b['validation_selection'])

    def test_permuted_assignment_null(self):
        rng = np.random.default_rng(51)
        n = 150000
        x = rng.normal(size=n)
        t = rng.binomial(1, .7, n)
        y = rng.binomial(1, .1 + .08*t*(x > 0))
        shuffled = rng.permutation(t)
        # A randomized permutation breaks the original causal assignment link.
        phi = dr_signal(shuffled, y, np.full(n,.12), np.full(n,.12), .7)
        self.assertAlmostEqual(phi.mean(), 0., delta=.008)

    def test_duplicate_source_ids_rejected(self):
        df = synthetic(6000)
        df['_source_row'] = 1
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'source-row'):
                run(df, Path(d)/'run', {}, repeats=50)


if __name__ == '__main__':
    unittest.main()

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from .data import FEATURES


def interval(values):
    values = np.asarray(values, float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("Need at least two finite observations")
    estimate = values.mean()
    se = values.std(ddof=1) / np.sqrt(len(values))
    return {"estimate": float(estimate), "lower": float(estimate - 1.96 * se),
            "upper": float(estimate + 1.96 * se), "n": len(values)}


def experiment_report(df, expected_assignment=None):
    a, b = df[df.treatment == 1], df[df.treatment == 0]
    if min(len(a), len(b)) < 2:
        raise ValueError("Insufficient observations in an experiment arm")
    ate = float(a.conversion.mean() - b.conversion.mean())
    se = np.sqrt(a.conversion.var(ddof=1) / len(a) + b.conversion.var(ddof=1) / len(b))
    if expected_assignment is not None and not 0 < expected_assignment < 1:
        raise ValueError("Expected assignment must be strictly between zero and one")
    pooled = np.sqrt((a[FEATURES].var() + b[FEATURES].var()) / 2)
    difference = a[FEATURES].mean() - b[FEATURES].mean()
    smd = difference / pooled.replace(0, np.nan)
    # Constant features in both arms are balanced only when their means match.
    smd = smd.mask((pooled == 0) & (difference == 0), 0)
    return {"estimand": "assignment conversion risk difference; causal ITT interpretation requires released-sample randomization",
            "n": len(df), "treated": len(a), "control": len(b),
            "treated_conversions": int(a.conversion.sum()),
            "control_conversions": int(b.conversion.sum()),
            "treatment_rate": len(a) / len(df),
            "treatment_conversion_rate": float(a.conversion.mean()),
            "control_conversion_rate": float(b.conversion.mean()),
            "ate": ate, "lower": float(ate - 1.96 * se), "upper": float(ate + 1.96 * se),
            "interval_method": "unadjusted independent-arm Wald; rare events warrant caution",
            "standardized_mean_differences": {k: None if not np.isfinite(v) else float(v) for k, v in smd.items()},
            "srm_pvalue": None if expected_assignment is None else float(
                binomtest(len(a), len(df), expected_assignment).pvalue),
            "srm_note": "Only test SRM against an externally documented allocation, not fitted allocation"}


def dr_signal(t, y, m0, m1, propensity):
    """AIPW pseudo-outcome for incremental policy value versus treating nobody."""
    t, y, m0, m1 = [np.asarray(a, dtype=float) for a in (t, y, m0, m1)]
    if any(a.shape != t.shape for a in (y, m0, m1)) or t.ndim != 1:
        raise ValueError("AIPW inputs must be matching one-dimensional arrays")
    if not all(np.isfinite(a).all() for a in (t, y, m0, m1)):
        raise ValueError("AIPW inputs must be finite")
    if not np.isin(t, [0, 1]).all() or not np.isin(y, [0, 1]).all():
        raise ValueError("Assignment and outcome must be binary")
    if not all(((a >= 0) & (a <= 1)).all() for a in (m0, m1)):
        raise ValueError("Nuisance predictions must be probabilities")
    if not 0 < propensity < 1:
        raise ValueError("Propensity must be strictly between zero and one")
    return m1 - m0 + t * (y - m1) / propensity - (1 - t) * (y - m0) / (1 - propensity)


def choose_policy(scores, fraction, cost=0.0, value=1.0):
    """Equal per-assignment cost: capacity is an upper bound, never force negative value."""
    scores = np.asarray(scores, float)
    if not 0 <= fraction <= 1 or not np.isfinite([cost, value]).all() or cost < 0 or value <= 0 or scores.ndim != 1 or not np.isfinite(scores).all():
        raise ValueError("Invalid policy inputs")
    k = int(np.floor(fraction * len(scores)))
    positive = np.flatnonzero(value * scores - cost > 0)
    ranked = positive[np.argsort(-scores[positive], kind="stable")]
    policy = np.zeros(len(scores), dtype=int)
    policy[ranked[:k]] = 1
    return policy


def bootstrap_mean(values, repeats=200, seed=42):
    if repeats < 50:
        raise ValueError("Use at least 50 bootstrap replicates")
    values = np.asarray(values, float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("Need at least two finite observations")
    rng = np.random.default_rng(seed)
    draws = [values[rng.integers(0, len(values), len(values))].mean() for _ in range(repeats)]
    low, high = np.quantile(draws, [0.025, 0.975])
    return {"estimate": float(values.mean()), "lower": float(low), "upper": float(high),
            "method": "percentile evaluation-row bootstrap, fixed trained policy"}


def gain_curve(scores, t, y, propensity):
    """IPW cumulative incremental conversions per eligible user; Qini removes random line."""
    scores, t, y = [np.asarray(a, dtype=float) for a in (scores, t, y)]
    if scores.ndim != 1 or scores.shape != y.shape or len(y) < 2 or not np.isfinite(scores).all():
        raise ValueError("Invalid ranking inputs")
    order = np.argsort(-scores, kind="stable")
    observed = dr_signal(t, y, np.zeros(len(y)), np.zeros(len(y)), propensity)
    gain = np.r_[0, np.cumsum(observed[order]) / len(y)]
    x = np.linspace(0, 1, len(gain))
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    auuc = float(trap(gain, x))
    qini = float(trap(gain - x * gain[-1], x))
    idx = np.unique(np.linspace(0, len(y), min(101, len(y) + 1)).astype(int))
    return {"auuc_ipw": auuc, "qini_ipw": qini}, pd.DataFrame(
        {"fraction": x[idx], "incremental_conversions_per_eligible_user": gain[idx]})


def capacity_policy(scores, fraction):
    """Fill a comparator budget even if every response score is zero."""
    scores = np.asarray(scores, float)
    if scores.ndim != 1 or not np.isfinite(scores).all() or not 0 <= fraction <= 1:
        raise ValueError("Invalid capacity policy inputs")
    pi = np.zeros(len(scores), dtype=int)
    pi[np.argsort(-scores, kind="stable")[:int(np.floor(fraction * len(scores)))]] = 1
    return pi

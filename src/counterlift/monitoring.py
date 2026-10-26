"""Feature-mean shift screening, never delayed conversion-effect monitoring."""
import numpy as np


def fit_reference(x):
    x = np.asarray(x, float)
    mean, std = x.mean(axis=0), x.std(axis=0, ddof=1)
    scale = np.where(std > 0, std, 1.)
    return {'reference_mean': mean, 'reference_std': std,
            'reference_covariance': np.cov(x / scale, rowvar=False), 'reference_n': len(x)}


def feature_shift(x, reference, alpha=.05, draws=5000, seed=42):
    """Gaussian-reference max-statistic threshold with baseline/target sample sizes.

    Conditional covariance is estimated from training features only. Simulation
    preserves estimated correlations and targets familywise alpha for mean shifts.
    Heavy tails, selection, dependence and covariance estimation can invalidate it.
    """
    x = np.asarray(x, float)
    mean, std = reference['reference_mean'], reference['reference_std']
    if x.ndim != 2 or len(x) < 1 or not np.isfinite(x).all():
        raise ValueError('Shift screening requires at least one finite row')
    if not 0 < alpha < 1 or draws < 100:
        raise ValueError('Invalid screening calibration inputs')
    scale = np.where(std > 0, std, 1.)
    shift = (x.mean(axis=0)-mean)/scale
    covariance = reference['reference_covariance'] * (1/len(x) + 1/reference['reference_n'])
    rng = np.random.default_rng(seed)
    null = rng.multivariate_normal(np.zeros(x.shape[1]), covariance, size=draws)
    maxima = np.abs(null).max(axis=1)
    threshold = float(np.quantile(maxima, 1-alpha))
    changed_constant = bool(np.any((std == 0) & np.any(x != mean, axis=0)))
    statistic = float(np.abs(shift).max())
    return {'shift_alert': bool(statistic > threshold or changed_constant),
            'shift_threshold': threshold, 'max_absolute_standardized_mean_shift': statistic,
            'constant_feature_changed': changed_constant,
            'simulated_max_statistic_pvalue': float((1+np.sum(maxima >= statistic))/(draws+1)),
            'standardized_mean_shift': shift,
            'threshold_basis': f'Gaussian-reference simulation of maximum feature mean shift, estimated training covariance; alpha={alpha}, {draws} draws',
            'note': 'Approximate iid feature-mean screening only; not calibrated on Criteo, not a causal-effect drift monitor. Heavy tails, dependence and covariance uncertainty may invalidate the threshold.'}

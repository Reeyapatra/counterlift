import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.model_selection import StratifiedKFold


def classifier(seed):
    # No class reweighting: the outcome probabilities enter causal estimators.
    return HistGradientBoostingClassifier(max_iter=80, max_leaf_nodes=15,
                                          min_samples_leaf=40, l2_regularization=2,
                                          random_state=seed)


def pair_fit(x, t, y, seed):
    models = []
    for arm in [0, 1]:
        mask = t == arm
        if len(np.unique(y[mask])) < 2:
            raise ValueError("Every training arm needs conversions and nonconversions; increase sample")
        model = classifier(seed + arm)
        model.fit(x[mask], y[mask])
        models.append(model)
    return models


def fit_models(x, t, y, propensity, seed=42, folds=3):
    from .statistics import dr_signal
    strata = 2 * t + y
    if np.bincount(strata, minlength=4).min() < folds:
        raise ValueError("Not enough events in every treatment/outcome cell for cross-fitting")
    pseudo = np.empty(len(y))
    for train, valid in StratifiedKFold(folds, shuffle=True, random_state=seed).split(x, strata):
        m0, m1 = pair_fit(x[train], t[train], y[train], seed)
        pseudo[valid] = dr_signal(t[valid], y[valid], m0.predict_proba(x[valid])[:, 1],
                                 m1.predict_proba(x[valid])[:, 1], propensity)
    dr = HistGradientBoostingRegressor(max_iter=80, max_leaf_nodes=10,
                                       min_samples_leaf=100, l2_regularization=5,
                                       random_state=seed).fit(x, pseudo)
    m0, m1 = pair_fit(x, t, y, seed)
    response = classifier(seed).fit(x[t == 1], y[t == 1])
    return {"m0": m0, "m1": m1, "dr": dr, "response": response,
            "constant_ate": float(y[t == 1].mean() - y[t == 0].mean())}


def predict(models, x):
    p0 = models["m0"].predict_proba(x)[:, 1]
    p1 = models["m1"].predict_proba(x)[:, 1]
    return {"constant_ate": np.full(len(x), models["constant_ate"]),
            "response": models["response"].predict_proba(x)[:, 1],
            "t_learner": p1 - p0,
            "dr_learner": np.clip(models["dr"].predict(x), -1, 1)}, p0, p1

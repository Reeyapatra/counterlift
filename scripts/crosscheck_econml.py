"""Optional independent synthetic learner check; use the separate causal lock."""
import json
import sys
from importlib.metadata import version
from pathlib import Path

import numpy as np
from econml.dr import DRLearner
from sklearn.linear_model import LogisticRegression, Ridge

# The core package is imported as source so the optional environment can use
# EconML's supported scikit-learn version without changing the application lock.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from counterlift.data import synthetic, FEATURES
from counterlift.models import fit_models, predict

train, test = synthetic(30000, 31), synthetic(20000, 32)
x, t, y = train[FEATURES].to_numpy(), train.treatment.to_numpy(), train.conversion.to_numpy()
xt = test[FEATURES].to_numpy()
truth = np.where(xt[:,0] > 0, .10, -.025)
custom, _, _ = predict(fit_models(x,t,y,.85,31), xt)
reference = DRLearner(model_propensity=LogisticRegression(max_iter=500, solver="liblinear"),
                      model_regression=LogisticRegression(max_iter=500, solver="liblinear"),
                      model_final=Ridge(alpha=10), cv=3, random_state=31, discrete_outcome=True)
reference.fit(y,t,X=x)
effect = reference.effect(xt)
report = {'dataset':'SYNTHETIC INDEPENDENT TRAIN/TEST', 'seed_train':31, 'seed_test':32,
          'truth_mean':float(truth.mean()), 'custom_dr_mean':float(custom['dr_learner'].mean()),
          'econml_dr_mean':float(effect.mean()),
          'custom_dr_rmse':float(np.sqrt(np.mean((custom['dr_learner']-truth)**2))),
          'econml_dr_rmse':float(np.sqrt(np.mean((effect-truth)**2))),
          'econml_version':version('econml'), 'scikit_learn_version':version('scikit-learn'),
          'scope':'Separate nuisance/final learners: agreement is checked against synthetic truth, not numerical estimator equivalence or Criteo superiority.'}
print(json.dumps(report,indent=2))
if abs(report['custom_dr_mean']-report['truth_mean']) > .03 or abs(report['econml_dr_mean']-report['truth_mean']) > .03:
    raise SystemExit('Learner cross-check failed mean-effect tolerance')

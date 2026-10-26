"""Empirical synthetic null/shift checks for the approximate feature screening rule."""
import json
from pathlib import Path
import numpy as np
from counterlift.monitoring import fit_reference, feature_shift

rng=np.random.default_rng(2026)
null_alerts, shifted_alerts = 0,0
trials=300
for trial in range(trials):
    # Correlated baseline features, estimated reference rather than known covariance.
    shared=rng.normal(size=(1200,1))
    reference=fit_reference(.5*shared+rng.normal(size=(1200,12)))
    shared=rng.normal(size=(300,1))
    target=.5*shared+rng.normal(size=(300,12))
    null_alerts+=feature_shift(target, reference, draws=5000,seed=trial)['shift_alert']
    target[:,0]+=.5
    shifted_alerts+=feature_shift(target, reference, draws=5000,seed=trial)['shift_alert']
report={'dataset':'SYNTHETIC CORRELATED GAUSSIAN FEATURES','seed':2026,'trials':trials,
        'reference_n':1200,'target_n':300,'target_familywise_alpha':.05,
        'null_alert_fraction':null_alerts/trials,'shifted_alert_fraction':shifted_alerts/trials,
        'shift':'.5 units on feature 0',
        'scope':'Gaussian iid sample calibration only; no real-data, heavy-tail, group-dependence or causal-effect-drift calibration'}
Path('docs/shift_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if not .01 <= report['null_alert_fraction'] <= .10 or report['shifted_alert_fraction'] < .9:
    raise SystemExit('Synthetic screening validation outside declared tolerances')

"""Repeated synthetic experiments; no Criteo or learned-policy coverage claim."""
import argparse
import json
from pathlib import Path
import numpy as np
from counterlift.statistics import dr_signal, interval


def evaluate(trials=200, n=4000, seed=2026):
    rng = np.random.default_rng(seed)
    rows = []
    for effect in ('null', 'negative', 'heterogeneous'):
        for propensity in ('known', 'independent_training_estimate'):
            for nuisance in ('oracle', 'misspecified'):
                aipw, ipw, covered, ipw_covered = [], [], 0, 0
                for _ in range(trials):
                    x = rng.binomial(1, .5, n)
                    m0 = .1 + .05*x
                    tau = np.zeros(n) if effect == 'null' else np.full(n, -.05) if effect == 'negative' else np.where(x, .12, -.06)
                    truth = 0. if effect == 'null' else -.05 if effect == 'negative' else .03
                    t = rng.binomial(1, .7, n)
                    y = rng.binomial(1, m0+t*tau)
                    e = .7 if propensity == 'known' else rng.binomial(1, .7, n).mean()
                    a, b = (m0, m0+tau) if nuisance == 'oracle' else (np.full(n,.2), np.full(n,.25))
                    ci = interval(dr_signal(t,y,a,b,e))
                    ipw_ci = interval(t*y/e-(1-t)*y/(1-e))
                    aipw.append(ci['estimate']); ipw.append(ipw_ci['estimate'])
                    covered += ci['lower'] <= truth <= ci['upper']
                    ipw_covered += ipw_ci['lower'] <= truth <= ipw_ci['upper']
                rows.append(dict(effect=effect, propensity=propensity, nuisance=nuisance,
                                 truth=truth, trials=trials, n=n, aipw_bias=float(np.mean(aipw)-truth),
                                 ipw_bias=float(np.mean(ipw)-truth), aipw_coverage=covered/trials,
                                 ipw_coverage=ipw_covered/trials))
    return {'dataset':'SYNTHETIC REPEATED EXPERIMENTS', 'seed':seed, 'results':rows,
            'scope':'Fixed nuisance functions; independent training propensity redrawn per trial. Wald intervals exclude propensity uncertainty. No learned-policy, model-selection, rare-Criteo-outcome or transport coverage claim.'}


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out', required=True); args=p.parse_args()
    report=evaluate()
    Path(args.out).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

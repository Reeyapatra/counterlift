# CounterLift decision memo

## Current decision: no live launch

This is **synthetic software evidence**, not a Criteo result or real campaign impact.
The synthetic seed-42 demonstration uses 20,000 simulated eligible records, with
12,000 training, 4,000 validation and 4,000 untouched test records. Selection is
predeclared at 20% capacity, zero hypothetical assignment cost and unit hypothetical
conversion value. No hyperparameter search or test-driven budget optimization was done.

Validation selected the T-learner. Its test net-value difference versus response
targeting was 0.002779 per eligible user, with a paired 95% evaluation-row bootstrap
interval of [-0.005968, 0.010166]. This comparison is inconclusive. Do not turn the
positive point estimate into a claim of superior targeting.

The software audit found and repaired comparator capacity, nonfinite financial
input, source-row identity, artifact-completion and scoring-output safeguards. Only
f0–f11 enter models. A regression test changes test outcomes while preserving the
training and validation data and verifies unchanged model selection. Exact
feature/assignment/outcome duplicates are counted, but no anonymous-row check can
establish independent people or detect all cross-user dependence.

## Independent scientific checks

`simulation_results.json` records 2,400 synthetic experiments: 200 in each of 12
settings covering null/negative/heterogeneous effects, oracle/misspecified outcome
functions and known/independently fitted marginal assignment probabilities. Fixed
AIPW Wald interval coverage ranges from 92.5% to 97%; IPW coverage ranges from 92%
to 97%. There is Monte Carlo error (roughly 1.5 percentage points at 95% coverage
and 200 trials). This is a diagnostic, not universal calibration. The lowest AIPW
coverage occurs with heterogeneous effects, misspecified nuisances and fitted
propensity, whose estimation uncertainty the interval excludes.

`econml_crosscheck.json` compares the custom learner with EconML DRLearner on an
independent synthetic train/test sample. Different nuisance/final learners are
used; this checks mean-effect recovery, not equality of implementations. See the
JSON for the executed versions, errors and tolerances. Neither RMSE is available
for real individual Criteo effects: the true individual effects are unobserved.

## Budget and financial interpretation

The cost break-even for a fixed policy is
`value_per_conversion * incremental_per_eligible_user / selected_fraction`
when selected fraction is nonzero. A negative lower effect bound remains negative.
The UI revalues fixed allocations when costs change; it does not silently optimize
a new profitability threshold. Choosing a different budget after viewing test
curves is exploratory. The valid alternative is no treatment, retained explicitly
in validation selection. Preserve a new confirmation experiment before acting on
any redesign informed by these results.

All intervals condition on trained models and the evaluated policy and exclude
learning, selection, propensity-estimation and population-transport uncertainty.
Scenario money is hypothetical and not Criteo revenue or realized ROI.

## Real-data work remains blocked

The pinned publisher LFS pointer was retrieved and matched the starter SHA-256
`2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc`
at revision `2424920019e49d52d72c13ac1143ec5d53af276b`.
The 311,422,618-byte data download redirects to `us.aws.cdn.hf.co`, which returned
proxy CONNECT 403 in this environment. Required domains have been saved in the
environment draft. No data file, real-data fit, real-data event counts, real-data
model comparison or real-data recommendation is claimed. Once access is applied,
run increasing uniform samples, inspect arm/split conversion counts and memory,
and freeze all selections before inspecting fresh confirmation outcomes.

The pinned publisher card was also inspected: it confirms CC BY-NC-SA 4.0 terms
and nonuniform privacy subsampling. This is a substantive identification caveat.
Original randomization does not prove released-sample ignorability. Unknown
assignment/outcome-dependent release selection cannot be repaired by plugging the
released marginal assignment fraction into IPW or AIPW. Any future real-data memo
must retain that caveat instead of presenting benchmark performance as identified
original-population campaign impact.

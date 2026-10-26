# Scientific specification

## Estimand and validity

T is randomized advertising assignment; Y is binary conversion; X contains f0–f11.
The estimand is the assignment effect in the released population (intention to treat),
not the effect of actually seeing an ad. Do not condition on exposure, visits or
post-assignment selection. Public features are anonymized: no business/demographic
interpretation, treatment history, repeated-user identity, timestamps or pre-period
outcomes are invented. Group dependence cannot be checked without identifiers.

Identification assumes random assignment in the released sample, consistency,
no interference, overlap and comparable eligibility at application time. The rounded
85% treated figure is not an exact original design allocation. Default e is the
training released-sample treatment fraction. A supplied e must describe assignment
in this released sample. Default intervals condition on this plug-in estimate;
they do not propagate its uncertainty. No observational-confounding sensitivity
analysis is presented as necessary proof of validity for this randomized dataset.

## Publisher selection caveat

The pinned publisher card states that privacy subsampling is nonuniform. Original
random assignment does not by itself establish random assignment after that
selection. Released-sample ignorability and overlap are assumptions, not verified
facts; treatment/outcome-dependent selection could invalidate marginal-propensity
IPW/AIPW estimates. These estimators cannot repair an unknown sampling mechanism.
Do not infer original-population commercial effects from this benchmark. Source
row count, checksum and balance checks establish neither randomization nor causal
identification in the release.

## Baselines and nuisance models

1. Constant ATE: simple baseline; tied rankings use deterministic source-order tie breaks.
2. Response: P(Y=1|T=1,X), ranked at the same capacity; not called an effect estimate.
3. T-learner: m1(X)-m0(X).
4. DR learner: fit m0/m1 in three cross-fit training folds, construct orthogonal
   pseudo-outcomes, regress them on X, then refit m0/m1 on the full training split.

No SMOTE or class weights distort probabilities. Conversion rarity requires event
counts per arm/split; ten events is only a crash-prevention minimum, not adequate
statistical power. Larger samples, learner tuning on validation and sparse-outcome
stability checks are required for substantive conclusions.

## Policy and metrics

Let phi_i = m1_i-m0_i + T_i(Y_i-m1_i)/e - (1-T_i)(Y_i-m0_i)/(1-e).
For fixed binary policy pi, its incremental conversion value versus treating none
is mean(pi_i*phi_i). Net value is mean(pi_i*(v*phi_i-c)), with equal cost c charged
per assignment and constant scenario conversion value v. Multiply per-eligible-user
value by a representative target population size for aggregate projections.

Select at most floor(budget_fraction*n) records with positive v*tau_hat-c, ranked
by tau_hat. This is optimal for these predicted scores under equal costs, not under
arbitrary per-person costs. Random/response comparators fill their budget; they do
not apply a fictitious profitability threshold to noncausal scores. A baseline
constant-effect model fills capacity only if its estimated effect is profitable.
No-treatment is eligible during validation model selection.

Model selection maximizes validation net value at the predeclared selection budget.
It does not choose the model from the test budget curve. Test curves evaluate the
frozen policy family; choosing a new budget or costs after examining these curves
is exploratory and requires new confirmation before a deployment claim.

For ranking curve g(q), sort held-out rows by score and accumulate
[T*Y/e-(1-T)*Y/(1-e)] / N up to targeted fraction q. AUUC is the trapezoidal
integral of g(q); Qini is the integral of g(q)-q*g(1). These definitions use raw
incremental conversions per eligible user; numbers cannot be compared with other
libraries without matching normalization. No normalized-Qini near-zero division.

## Uncertainty

ATE uses an independent-arm Wald interval, explicitly labeled. Policy conversion
intervals use percentile resampling of evaluation rows with trained model and
selected budget policy fixed. Net-value intervals use a mean-score normal interval.
Paired policy differences resample per-row differences, preserving covariance.
Intervals are pointwise and exclude refitting, selection, finite-population transport
and estimated-propensity uncertainty. They are unsuitable as guarantees of a
maximized policy across many tried budgets/models. Negative lower bounds remain
visible. All assignment/outcome cells and interval coverage need review for real data.

## Extensions that require new data or separate validation

- CUPED requires genuine pre-treatment outcomes; none are fabricated.
- Chronological validation and drift histories require actual timestamps.
- Multiple channels/offers, carryover and repeated contact require appropriate data.
- Fairness claims require meaningful group definitions and a justified analysis.
- Realized revenue/ROI requires actual monetary outcomes and costs.
- Live launch requires an independently randomized policy-vs-baseline test, power
  planning, guardrails, logging, stop rules and customer/contact permissions.

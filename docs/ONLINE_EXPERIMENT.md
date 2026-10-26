# Proposed online confirmation experiment — not executed

Randomize eligible users between the frozen CounterLift policy and a documented
baseline policy, with the same contact capacity and per-assignment economics.
Randomization unit must be the actual user (or justified cluster), not an anonymous
row. Keep assignment logs, pre-treatment eligibility, contact limits and consistent
outcome windows. Analyze intention to treat; do not condition on actual exposure.

Before launch, specify a primary conversion outcome, horizon, baseline conversion
rate, minimum detectable incremental effect, expected allocation, power, alpha,
multiple-testing policy and cluster/design effects. No Criteo rounded allocation
is a valid substitute for the new experiment's design. For a balanced independent
binary experiment, an approximate per-arm planning size is
`2 * (z_(1-alpha/2) + z_power)^2 * p*(1-p) / delta^2`.
For illustration only, p=0.05, delta=0.005, alpha=0.05 and 80% power implies about
29,800 users per arm before attrition, clustering or multiplicity. Recompute with
a power package and actual design inputs; this is not an approved launch sample.

Define consent/contact permissions, maximum spend, complaint/unsubscribe and
adverse-experience guardrails, sample-ratio monitoring against the actual design,
and data-quality stop conditions. Use a fixed horizon or a justified sequential
procedure; do not repeatedly inspect a fixed-horizon p-value and stop on success.
Freeze the policy/model/version and allocation rules. Track outcome maturity and
missingness. Roll back to baseline on operational guardrail failure. Do not claim
commercial impact until the randomized confirmation and monetary outcomes support it.

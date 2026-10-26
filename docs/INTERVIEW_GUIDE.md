# Explaining CounterLift

- Assignment is the randomized intervention. Actual exposure is downstream and is
  excluded; conditioning on it could break randomized comparability.
- A treated-arm response model predicts purchases. It does not estimate how many
  purchases the assignment causes. It remains a useful budget-matched comparator.
- The T-learner subtracts outcome probabilities from two training-only models.
  DR learning uses out-of-fold nuisance predictions to construct AIPW targets.
- Propensity is assignment probability, not conversion probability. The released
  sample fraction is not proof of the original experiment allocation.
- AUUC and Qini assess rankings using an explicitly documented IPW normalization.
  AIPW policy value estimates a fixed allocation versus treating nobody.
- Validation selects a policy before held-out test outcomes are evaluated. Test
  curves are not permission to select a winning budget after looking at results.
- Synthetic truths enable effect recovery and coverage checks. Real individual
  effects are not observed, so real-data individual-effect accuracy is not claimed.
- Fixed-policy intervals are narrower in scope than uncertainty in the entire
  learned decision process. Negative bounds and inconclusive comparisons stay visible.

Portfolio wording supported by executed checks: built an offline randomized-marketing
analysis pipeline, tested synthetic effect recovery and data isolation, and exercised
a read-only Streamlit decision app. Do not claim Criteo uplift, revenue improvements,
a hosted deployment or production campaign operation without the corresponding evidence.

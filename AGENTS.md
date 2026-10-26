# CounterLift engineering contract

Build decision support for randomized marketing experiments. Never fabricate data,
metrics, successful deployments, experiment results, source verification or business impact.
Read README.md and docs/SCIENTIFIC_SPEC.md before changing estimators.

- Python package owns all statistical logic; app.py only reads evaluated artifacts.
- Use f0–f11 only. Exposure and visits cannot be conversion-model inputs.
- Preserve train/validation/test isolation. Freeze selection before test evaluation.
- Propensity means assignment probability, not purchase probability.
- Do not infer original experiment allocation from rounded dataset documentation.
- Never rebalance outcomes without statistically correct sampling adjustments.
- Scenario costs are per assignment; revenue values are hypothetical.
- Test mathematical invariants, null effects, synthetic known effects and data isolation.
- Run `python -m unittest discover -s tests -v` after statistical changes.
- Keep synthetic demonstrations visibly labeled. Report unsuccessful comparisons.
- Do not add LLMs or agents to the causal decision path. Add infrastructure only for
  a demonstrated operational need.
- Maintain docs/STATUS.md with executed checks, unresolved issues and next actions.
- Use fresh run directories; never silently overwrite evaluated artifacts.
- A portfolio implementation is not evidence of commercial production operation.

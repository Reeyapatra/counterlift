# Build and harden with Codex

Open this extracted project directory in your coding environment. Keep AGENTS.md
in the project root and use the following task. This is a multi-session engineering
task: preserve progress and evidence rather than asking for the entire project
again each session.

## Paste this task

> Continue CounterLift as a product/marketing data science portfolio project.
> Read AGENTS.md, README.md, docs/SCIENTIFIC_SPEC.md and docs/STATUS.md first.
> Inspect the implementation before editing. Complete the next unfinished milestone
> below and run its acceptance checks. Fix failures before proceeding. Maintain an
> honest execution log with exact commands, dataset provenance, resource use and
> results. Do not invent metrics, business feature meanings or production operation.
> Keep the core usable on a laptop. Preserve untouched confirmation data whenever
> model or policy choices change. Explain each major statistical choice in terms I
> can defend in an interview. Proceed with reversible implementation work; identify
> external access or secrets only if a concrete milestone needs them.

## Milestone 1 — environment and scientific correctness

- Install editable package with app dependencies in a clean Python 3.12 environment.
- Generate a resolved dependency lock; run all tests; boot and exercise every UI tab.
- Add CI to install from that lock and run tests on pushes/PRs.
- Strengthen tests with negative effects, heterogeneous effects, constant-feature
  inputs, rare outcomes, treatment permutations and known-policy ordering.
- Independently check AIPW and IPW estimates on randomized simulations with known truth;
  run repeated simulations to assess interval coverage, including propensity fitting.
- Clarify fixed-policy intervals versus learning-procedure uncertainty in the report.

Acceptance: clean installation, passing scientific checks, UI checks recorded, and
no fabricated assertions about Criteo quality or performance.

## Milestone 2 — corrected data and reproducible evidence

- Obtain the corrected source from Criteo/publisher mirror. Record URL, revision,
  SHA-256, source row count, download date, license and citation.
- Run uniform samples at increasing sizes. Record peak memory, runtime and arm/event
  counts. Use at least enough conversion events for stable evaluation; justify size.
- Preserve split membership and audit within-file duplicates/dependence limitations.
- Compare constant, response, T and DR policies at the predeclared budgets. Add an
  EconML estimator only after the baseline pipeline passes, using the same splits.
- Cross-check custom DR results against a maintained-library implementation.
- Select models/hyperparameters on validation; reserve a new confirmation holdout if
  existing test outcomes have been used to redesign the project.
- Write a decision memo with estimates, paired differences, confidence intervals,
  caveats, cost scenarios and an honest go/no-go recommendation.

Acceptance: reproducible real-data run and memo; the uplift model may lose. A
negative result is acceptable; altering splits to manufacture a win is not.

## Milestone 3 — deployment and operational controls

- Add run IDs and source-code commit IDs, artifact checksums, atomic completion
  markers, structured logs, robust resume/failure handling and dependency lock.
- Export only aggregate evaluation artifacts for the public app; train offline.
- Build the Docker image, test startup/health and actual resource use, then deploy
  the read-only Streamlit app to a selected host and verify its public URL.
- Add batch input validation, schema/version compatibility, idempotent jobs and
  scored-file provenance. Define feature-shift alert thresholds using simulations
  or historical reference data; do not call this delayed-effect monitoring.
- Document previous-run selection/rollback and test restoration.
- Build an online experiment proposal, not a fake executed A/B test: policy versus
  baseline, power/MDE assumptions, eligibility, guardrails and stopping rules.

Acceptance: verified hosted demo, successful repeatable batch run, rollback drill,
dependency/security checks and exact operating-cost assumptions.

## Milestone 4 — interview and portfolio presentation

- Produce an architecture image, short demo recording and reproducible-results table.
- Explain assignment vs exposure, prediction vs causation, nuisances/cross-fitting,
  propensity vs response, ranking vs policy value, and uncertainty limitations.
- Present one budget decision with a cost break-even calculation and an alternative.
- Write resume bullets only from executed, documented evidence. Distinguish projected
  incremental conversions from realized commercial impact.

## Explicit scope choices

No LLM is needed for the scientific pipeline. Do not add Kubernetes, Kafka, Redis,
an agent layer, microservices or a feature store solely to expand the stack. A
single reliable batch workflow and auditable decision app are the core deliverables.
This project demonstrates product/marketing DS; it does not cover every DS domain
or establish experience operating a platform at a large technology company.

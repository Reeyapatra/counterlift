# CounterLift execution status

Updated 2026-10-26. Initialized from the supplied starting-code ZIP directly at the
repository root. Branding, package imports, console entrypoint and run environment
variable are CounterLift / `counterlift` / `COUNTERLIFT_RUN`.

## Milestones

1. **Local scientific/environment milestone implemented and exercised.** Clean
   Python 3.12.14 venv, editable package, resolved app lock, scientific tests, all
   four UI tabs and controls, repeated synthetic simulation report and CI workflow.
   This does not establish universal coverage or real-data causal identification.
2. **Real-data milestone blocked.** Publisher revision, LFS pointer checksum, file
   size and license were inspected. Actual data download redirects to
   `us.aws.cdn.hf.co` and gets proxy CONNECT 403. No corrected-data training,
   increasing-size sample runs, real-data model comparison or real-data memo.
   Optional EconML cross-check was completed on independent synthetic data only.
3. **Operational milestone partial.** Atomic completion, schema/checksums, structured
   completion events, run/source IDs, aggregate export, batch idempotency/provenance,
   local container and rollback implemented. Public hosting, real-data shift calibration,
   hosted rollback and operational deployment remain unfinished. Feature-shift screening now uses simulated Gaussian-reference maximum statistics
   with training covariance; it is not causal-effect monitoring.
4. **Portfolio milestone partial.** Decision memo, architecture SVG/Mermaid,
   interview guide, synthetic result files and an actual CLI demo recording exist.
   No real-data results, public app URL, UI screen recording or commercial impact.

## Executed checks

Commands below ran from `/workspace/counterlift` with OpenMP/BLAS set to one thread
for statistical/app checks. Core dependencies: Python 3.12.14, NumPy 2.3.5, pandas
2.2.3, SciPy 1.17.0, scikit-learn 1.8.0, Streamlit 1.66.1, Pillow 13.0.0.

- `python -m venv .venv`; `.venv/bin/python -m pip install -r requirements-lock.txt`;
  `.venv/bin/python -m pip install --no-deps -e .`: passed.
- `.venv/bin/python -m pip check`: passed, no broken requirements.
- `.venv/bin/python -m unittest discover -s tests -v`: **20 tests passed**. Includes
  null/negative/heterogeneous effects, assignment permutation, constant features,
  rare-event rejection, source-row uniqueness, matching AIPW inputs, finite financial
  inputs, zero-probability comparator capacity, test-outcome selection invariance,
  split isolation, corruption rejection, batch idempotency and feature-shift screening.
- `counterlift demo --out runs/demo --bootstrap 200`: 20,000 synthetic rows;
  12,000/4,000/4,000 train/validation/test. Validation selected T-learner. Paired
  test difference vs response 0.002779, 95% interval [-0.005968, 0.010166]:
  **inconclusive**, not superior targeting. Fresh repeat/recording runs were also
  generated; no evaluated run directory was overwritten.
- `.venv/bin/python scripts/scientific_validation.py --out docs/simulation_results.json`:
  2,400 synthetic trials across 12 settings; AIPW coverage 92.5–97%, IPW 92–97%.
  Fixed functions/intervals, not refitted-policy or Criteo coverage.
- Separate causal venv, `python scripts/crosscheck_econml.py`: passed declared
  mean-effect recovery tolerance on independent synthetic samples. EconML 0.16.0,
  scikit-learn 1.6.1; column-vector warnings are recorded as a compatibility caveat.
- `.venv/bin/python scripts/check_app.py`: passed four tabs, synthetic label,
  budget 0/0.5/1, cost/value/population inputs, missing run and corrupt artifact states.
- `counterlift export --run runs/demo --out runs/public-demo`: passed; no model or
  row-level SQLite data in public export. Export permissions support nonroot reads.
- `.venv/bin/python scripts/check_rollback.py`: passed distinct-run A → B → A
  selection and displayed run-ID restoration using two aggregate exports.
- `docker build --build-arg PIP_NO_INDEX=1 -t counterlift:local .`: passed after
  preparing wheels using verified normal pip downloads. Network-based builds failed
  DNS in this environment, so the documented offline-wheel path was used.
- Container ran as UID 65534. Docker healthcheck and HTTP `/_stcore/health` passed;
  inside-container AppTest rendered four tabs and exercised cost/budget controls.
  One idle sample used about 45.4 MiB; this is not a load test or capacity benchmark.
- `pip-audit --disable-pip --no-deps -r requirements-lock.txt --format json`:
  initial audit reported 37 Pillow vulnerabilities. Upgraded 12.3.0 → 13.0.0;
  final audit reported **no known vulnerabilities** in the locked app dependencies.
  See `security_audit.json`. This is not a guarantee of security or a container OS audit.
- `python scripts/validate_shift.py`: 300 correlated-Gaussian synthetic trials;
  6% null alerts at nominal familywise 5%, and 100% detection for the declared
  feature-0 shift. This is not real-data, heavy-tail or dependence calibration.
- CI configuration is present; GitHub-hosted execution is not claimed until observed.

## Corrections and remaining boundaries

Fixed comparator under-allocation for zero response scores; finite-value and shape
validation; undefined constant-feature balance reporting; duplicate source IDs;
partial run publication; scored-file overwrite/idempotency; artifact verification;
public export permissions; AppTest relative-path compatibility; container nonroot
app permissions; unsafe starter dependency pin. Test-budget exploration is explicitly
exploratory; negative and inconclusive policy evidence remains visible.

The publisher says privacy subsampling is nonuniform. Released-sample ignorability
is unverified; checksum and observed marginal allocation do not prove it. Unknown
selection bias is not fixed by AIPW. No exposure/visit features or original allocation
figures are invented. No live launch is recommended from current evidence.

## Next actions

Apply the saved network settings and retry `python scripts/download_data.py` with
checksum verification intact. Then measure increasing uniform samples, audit
conversion cells and dependence limitations, and predeclare choices before a fresh
confirmation evaluation. Choose and authorize a hosting service before public
deployment. Validate feature-shift thresholds on representative data and production-specific
recovery, power/guardrails and operating costs. See `BUILD_WITH_CODEX.md`.

Setup/startup instructions are saved separately in the environment draft; a draft
save is not publication or proof of restoration in a fresh task.

## Commit-linked repeat

After initial commit `06033b5`, `counterlift demo --out runs/committed-demo
--bootstrap 200` recorded that clean commit, completed in 1.309 seconds and used
231,395,328 bytes peak process RSS (about 220.7 MiB). Its aggregate export and UI
checks passed, as did rollback to/from the distinct seed-43 run. See `RESULTS.md`.
Subsequent monitoring hardening replaces the fixed heuristic with an explicitly
approximate Gaussian-reference diagnostic; legacy bundles without covariance expose
only descriptive shifts and do not fabricate a calibrated alert.

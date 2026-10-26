# CounterLift

**Which eligible customers should receive a marketing assignment when spending is limited?**

A runnable offline decision-support project: experiment diagnostics → treatment-effect
models → validation-selected policy → untouched-test evaluation → batch scoring → allocation UI.
This is an offline implementation with a real-data execution path, not a claim of live
campaign impact or completed enterprise deployment. See `docs/STATUS.md` for verification.

## Run locally

Use Python 3.11 or 3.12 in a fresh environment. From this directory:

```bash
python -m venv .venv
```

Activate on Windows PowerShell: `.venv\Scripts\Activate.ps1`.
Activate on macOS/Linux: `source .venv/bin/activate`.

```bash
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
counterlift demo --out runs/demo
streamlit run app.py
```

The demo generates **synthetic** randomized data for software verification. It provides
no evidence about Criteo or real marketing impact. No paid API keys are required.

## Corrected Criteo run

Download `criteo-research-uplift-v2.1.csv.gz` from the publisher's dataset page or
the `criteo/criteo-uplift` publisher mirror. Keep the downloaded file outside Git.
Alternatively run `python scripts/download_data.py` to retrieve a pinned publisher
revision and verify its publisher-reported SHA-256 automatically.
The original release had advertiser-related leakage. The corrected complete source
contains 13,979,592 rows, 12 anonymized baseline features, assignment, visit,
conversion and actual-exposure fields. This project only models assignment → conversion. Publisher privacy subsampling
is nonuniform; causal interpretation in the released sample remains an unverified
identification assumption. See the scientific specification.

```bash
counterlift train --data data/criteo-research-uplift-v2.1.csv.gz --corrected-release --rows 1000000 --bootstrap 500 --selection-budget 0.20 --out runs/criteo-001
```

`--rows` is a uniform sample across the whole source, not a leading slice. The loader
reads the complete source in chunks and records its SHA-256 and row count. Row count
and user declaration do not prove release authenticity: optionally supply
`--expected-sha256` obtained independently from a trusted source. Do not invent it.
Start with a resource-appropriate sample; log event counts, memory and runtime before
attempting all rows. No full-data runtime or scale benchmark is claimed here.

Set `COUNTERLIFT_RUN=runs/criteo-001` in your shell before starting Streamlit
to show that run. In PowerShell use `$env:COUNTERLIFT_RUN="runs/criteo-001"`.
The default UI run is `runs/demo`.

Costs default to zero and conversion value to one. To select under a financial
scenario, pass `--cost 0.01 --value 20`; these are hypothetical inputs, not Criteo economics.

## What is implemented

- Binary conversion intention-to-treat risk difference and 95% interval; arm event counts;
  standardized feature balance; SRM only with an externally supplied expected allocation.
- Constant-effect baseline; ordinary treated-arm conversion predictor; T-learner;
  three-fold cross-fitted doubly robust pseudo-outcome learner with scikit-learn.
- 60/20/20 train/validation/test split, stratified on assignment only. Explicit provenance.
- Model selection on validation net value at a predeclared budget; no-treatment fallback.
- Equal-cost capacity-limited policies; random and response-targeting comparators.
- Test IPW gain/AUUC/Qini; AIPW incremental policy value; pointwise bootstrap intervals;
  paired selected-policy versus response-policy comparison at the selection budget.
- SQL audit database; versioned run artifacts; trusted-model batch scoring and feature shifts.
- Streamlit experiment health, fixed-policy cost sensitivity, policy evidence and run audit.

Qini/AUUC are ranking diagnostics, not individual causal-effect accuracy. The exact
normalization is documented in `docs/SCIENTIFIC_SPEC.md`. Confidence intervals may
include zero; the UI reports inconclusive comparisons explicitly.

## Artifacts and batch scoring

Every run creates `manifest.json`, `experiment.json`, `policy_evaluation.csv`,
`gain_curves.csv`, `audit.sqlite` and `model.joblib`. Keep runs isolated and preserve
the runtime versions in their manifests. Models are serialized with joblib: load
only trusted files created by your project, never arbitrary uploaded models.

```bash
counterlift score --model runs/criteo-001/model.joblib --data data/new_eligible.csv --out data/scored.csv
```

Input requires numeric finite f0–f11. Scores estimate conditional average assignment
effects; no claim is made about a person's unobserved true causal effect.
`sql/audit.sql` contains arm/split, record-isolation and policy queries.

## Operational boundary

The public app should read aggregate run artifacts. Do not train on a small web
instance or expose a model-file upload. Streamlit deployment configuration, automated
release checks, drift thresholds and rollback are specified in `docs/BUILD_WITH_CODEX.md`.
See `docs/OPERATIONS.md` for aggregate export, container build, batch idempotency and
rollback instructions. Local container and UI checks are recorded in `docs/STATUS.md`.
Public hosting, calibrated drift alerts and real-data validation remain unfinished.

## Sources and data attribution

- Criteo AI Lab: https://ailab.criteo.com/criteo-uplift-prediction-dataset/
- Publisher mirror: https://huggingface.co/datasets/criteo/criteo-uplift
- Diemert, Betlei, Renaudin and Amini (2018), *A Large Scale Benchmark for Uplift Modeling*, AdKDD.
- EconML DR learner reference: https://www.pywhy.org/EconML/_autosummary/econml.dr.DRLearner.html
- Industry application: https://github.com/uber/causalml

Data is not bundled. Criteo publishes dataset terms on its source page, including
CC BY-NC-SA 4.0 terms; inspect those terms before redistributing data or derived data.
The implementation is independent and is not endorsed by Criteo, Uber or another employer.

## Verified evidence and limitations

See [decision memo](docs/DECISION_MEMO.md), [scientific simulations](docs/simulation_results.json),
[EconML cross-check](docs/econml_crosscheck.json), [architecture](docs/ARCHITECTURE.md),
and [online experiment proposal](docs/ONLINE_EXPERIMENT.md). All current evaluated
results are explicitly synthetic. The synthetic selected-policy comparison with
response targeting is inconclusive. No real Criteo superiority is claimed.

`counterlift export --run runs/demo --out runs/public-demo` creates a checksummed,
aggregate-only read-only app bundle. Set `COUNTERLIFT_RUN=runs/public-demo` to use it.
EconML uses a separate optional lock because its scikit-learn constraint differs
from the app's lock. See the operations guide before installing it.

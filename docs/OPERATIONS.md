# Local operation, publication and rollback

## Reproduce the app

Use Python 3.12, the root `requirements-lock.txt`, then an editable `--no-deps`
installation. Bound OpenMP/BLAS to one thread on small machines. Generate a fresh
synthetic run, exercise the tests and UI, then export aggregates:

```bash
counterlift demo --out runs/demo --bootstrap 200
counterlift export --run runs/demo --out runs/public-demo
COUNTERLIFT_RUN=runs/public-demo python scripts/check_app.py
COUNTERLIFT_RUN=runs/public-demo streamlit run app.py --server.headless=true
```

Never overwrite evaluated runs. Failed training leaves no completed run directory;
retry in a new directory. A run is consumable only after `COMPLETE.json` is written
and all checksums pass. The public export excludes `model.joblib`, SQLite rows and
raw feature data. It retains aggregate provenance including source file name/hash.
Keep exported provenance suitable for publication. Checksums are not signatures:
only a trusted operator may replace artifacts. Do not upload untrusted joblib files.

## Container

```bash
docker build -t counterlift:local .
docker run --rm -p 8501:8501 -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 \
  -v "$PWD/runs/public-demo:/app/runs/demo:ro" counterlift:local
```

In restricted build networks, prepare verified wheels on the cloud machine first:

```bash
python -m pip download -r requirements-lock.txt setuptools wheel -d wheels
docker build --build-arg PIP_NO_INDEX=1 -t counterlift:local .
```

Wheels and datasets are ignored by Git. The image is nonroot, exposes a healthcheck,
and trains nothing at startup. Pin a base-image digest in a production release after
reviewing updates; the included moving Python 3.12 tag is for local development.

## Read-only host deployment

Hosting is not executed. Select a host, verify its authentication and cost limits,
then publish only aggregate artifacts and the app dependencies. For Streamlit
Community Cloud, configure Python 3.12 and `app.py`; provide aggregate artifacts in
a reviewed deployment repository or supported persistent artifact storage. This
repository ignores `runs/`, so a plain clone intentionally has no precomputed run.
Do not claim a working hosted demo until its actual page, tabs and interactions
have been checked. Local loopback checks do not prove external hosting.

## Rollback drill

Preserve both run directories. Verify the earlier export, stop only the app process
you started, restart with `COUNTERLIFT_RUN` set to the earlier export, and repeat
`scripts/check_app.py` plus an HTTP health request. Compare the displayed run ID
with the selected manifest. Never rerun training to simulate rollback. The supplied
`scripts/check_rollback.py` performs an A → B → A aggregate selection drill using
AppTest, checks the run ID and restores the caller's environment variable.

## Batch scoring

`counterlift score --model runs/demo/model.joblib --data data/eligible.csv --out data/scored.csv`
requires finite numeric f0–f11. A checksum-verified trusted run and schema version
are required. A JSON sidecar binds the output to its input/model checksums and job
ID. Repeating the same completed job is idempotent; conflicting or incomplete files
are rejected. Do not overwrite input data. CSV publication is atomic; a crash
between CSV publication and sidecar creation requires a fresh output path.

Mean feature shift is descriptive only. The current 0.2 standardized-mean threshold
is a transparent heuristic, **not** a calibrated alert or causal drift monitor.
Real-data/historical threshold calibration is unfinished.

## Operating cost assumptions

No paid APIs are required. Local CPU time, memory, disk and an optional host incur
provider-specific costs. No hosting bill, free-tier guarantee or production budget
is claimed. Resource measurements in run manifests are process-level peak RSS
(bytes, when available) and elapsed time, not a full-data performance forecast.

## Optional maintained-library check

EconML 0.16 requires scikit-learn <1.7, while the app lock uses 1.8. Use a separate
environment with `requirements-causal-lock.txt` and run
`python scripts/crosscheck_econml.py` from the repository root. The script imports
CounterLift source directly; do not install the app lock into that environment.
The resolved optional check currently produces scikit-learn column-vector warnings;
it completes, but is not part of the app runtime or real-data evaluation.

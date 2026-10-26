# Synthetic reproducible-results table

**SYNTHETIC ONLY — no Criteo or real campaign results.**

Executed source commit: `06033b5c77edea6dc35564ea89a8e2cb041b64bc`; seed 42; 20,000 rows; 20% capacity.

| Policy | Selected fraction | Incremental conversions per eligible user | 95% fixed-policy interval |
|---|---:|---:|---:|
| constant_ate | 0.20 | 0.008643 | [-0.003433, 0.017509] |
| response | 0.20 | 0.022867 | [0.014967, 0.030252] |
| t_learner | 0.20 | 0.025645 | [0.015704, 0.033649] |
| dr_learner | 0.20 | 0.024376 | [0.014025, 0.033737] |
| random | 0.20 | 0.014146 | [0.005682, 0.022911] |
| treat_none | 0.00 | 0.000000 | [0.000000, 0.000000] |

Validation selected the T-learner. The paired test comparison with response targeting
is inconclusive. These pointwise intervals exclude learning/selection and estimated
propensity uncertainty. Do not select a different model from this test table.

Runtime 1.309 seconds; peak process RSS 220.7 MiB.
These are single synthetic-run measurements, not real-data scale benchmarks.

See [decision memo](DECISION_MEMO.md), [architecture image](architecture.svg), and
[actual CLI recording](demo.cast) (asciinema v2; `asciinema play docs/demo.cast`).

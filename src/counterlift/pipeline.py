import json
import platform
import sqlite3
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .data import FEATURES, validate
from .models import fit_models, predict
from .statistics import (bootstrap_mean, choose_policy, dr_signal,
                         experiment_report, gain_curve, interval, capacity_policy)

BUDGETS = [0, .05, .10, .20, .30, .50, .75, 1.0]


def arrays(df):
    return (df[FEATURES].to_numpy(), df.treatment.to_numpy(), df.conversion.to_numpy())


def _run(df, out, provenance, seed=42, repeats=200, propensity=None,
        expected_assignment=None, selection_budget=.20, cost=0., value=1.):
    validate(df)
    out = Path(out)
    if out.exists():
        raise ValueError("Use a new run directory to preserve earlier artifacts")
    if not np.isfinite([selection_budget, cost, value]).all() or not 0 < selection_budget <= 1 or cost < 0 or value <= 0:
        raise ValueError("Invalid predeclared selection objective")
    if "_source_row" not in df or df._source_row.isna().any() or not df._source_row.is_unique:
        raise ValueError("Unique nonmissing source-row identifiers are required")
    if repeats < 50:
        raise ValueError("Use at least 50 bootstrap replicates")
    train_idx, rest = train_test_split(np.arange(len(df)), test_size=.4,
                                      stratify=df.treatment, random_state=seed)
    valid_idx, test_idx = train_test_split(rest, test_size=.5,
                                         stratify=df.iloc[rest].treatment, random_state=seed)
    train, valid, test = [df.iloc[idx].copy() for idx in [train_idx, valid_idx, test_idx]]
    for partition in [train, valid, test]:
        if min(partition.groupby("treatment").conversion.sum()) < 10:
            raise ValueError("Fewer than 10 conversions in an arm/split; increase sample size")
    x, t, y = arrays(train)
    # The released experiment may be subsampled. Never assume its ratio is an original design ratio.
    e = float(t.mean()) if propensity is None else float(propensity)
    if not .01 < e < .99:
        raise ValueError("Insufficient overlap or invalid assignment probability")
    models = fit_models(x, t, y, e, seed)
    scores, m0, m1 = predict(models, arrays(valid)[0])
    phi_valid = dr_signal(*arrays(valid)[1:], m0, m1, e)
    selection = []
    for name in ["constant_ate", "t_learner", "dr_learner"]:
        pi = choose_policy(scores[name], selection_budget, cost, value)
        selection.append({"model": name, "validation_net_value_per_eligible_user":
                          float(np.mean(pi * (value * phi_valid - cost)))})
    # Include no-treatment: an optimizer is allowed to recommend no campaign.
    selection.append({"model": "treat_none", "validation_net_value_per_eligible_user": 0.})
    winner = max(selection, key=lambda r: r["validation_net_value_per_eligible_user"])["model"]
    out.mkdir(parents=True)
    # Test policies are now frozen; do not use test values to choose a model or threshold.
    x_test, t_test, y_test = arrays(test)
    scores, m0, m1 = predict(models, x_test)
    scores["random"] = np.random.default_rng(seed).random(len(test)) + 1
    scores["treat_none"] = np.zeros(len(test))
    # Response/random are fixed-capacity comparators; their scores are not treatment effects.
    phi = dr_signal(t_test, y_test, m0, m1, e)
    rows, curves, policy_vectors = [], [], {}
    for name, rank in scores.items():
        if name not in ["random", "treat_none"]:
            metrics, curve = gain_curve(rank, t_test, y_test, e)
            curve["model"] = name
            curves.append(curve)
        else:
            metrics = {"auuc_ipw": None, "qini_ipw": None}
        for budget in BUDGETS:
            if name in ["response", "random"]:
                pi = capacity_policy(rank, budget)
            else:
                pi = choose_policy(rank, budget, cost, value)
            policy_vectors[name, budget] = pi
            ci = bootstrap_mean(pi * phi, repeats, seed)
            net = interval(pi * (value * phi - cost))
            rows.append({"model": name, "budget_fraction": budget,
                         "selected_fraction": float(pi.mean()),
                         "incremental_per_user": ci["estimate"], "lower": ci["lower"],
                         "upper": ci["upper"], "net_value_per_user": net["estimate"],
                         "net_lower": net["lower"], "net_upper": net["upper"], **metrics})
    result = pd.DataFrame(rows)
    # Evaluate the predeclared selection budget even if it is not on the display grid.
    def fixed_policy(name):
        if name == "response":
            return capacity_policy(scores[name], selection_budget)
        return choose_policy(scores[name], selection_budget, cost, value)
    delta = (fixed_policy(winner) - fixed_policy("response")) * (value * phi - cost)
    comparison = bootstrap_mean(delta, repeats, seed)
    experiment = experiment_report(df, expected_assignment)
    manifest = {"schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "offline_evaluated", "provenance": provenance,
                "seed": seed, "features": FEATURES, "outcome": "conversion",
                "treatment": "randomized treatment assignment; not actual exposure",
                "split_sizes": {"train": len(train), "validation": len(valid), "test": len(test)},
                "propensity": e, "propensity_source": "training release marginal" if propensity is None
                else "user-supplied released-sample assignment probability",
                "selection_budget": selection_budget, "cost_per_assignment": cost,
                "value_per_conversion": value, "winner": winner,
                "validation_selection": selection,
                "split_arm_events": {label: {str(arm): {"n": len(group), "conversions": int(group.conversion.sum())} for arm, group in part.groupby("treatment")} for label, part in [("train", train), ("validation", valid), ("test", test)]},
                "duplicate_feature_outcome_rows": int(df.duplicated(FEATURES + ["treatment", "conversion"]).sum()),
                "dependence_note": "Source-row isolation does not establish independent users; no user identifiers are available.",
                "test_net_difference_vs_response_at_selection_budget": comparison,
                "uncertainty_scope": "fixed trained policy; does not include refitting, model selection or propensity estimation uncertainty",
                "causal_assumptions": ["random assignment in released sample", "consistency",
                                       "no interference", "overlap", "representative target population"],
                "runtime": {"python": platform.python_version(), **{p: version(p) for p in
                            ["numpy", "pandas", "scipy", "scikit-learn", "joblib"]}}}
    bundle = {"models": models, "winner": winner, "features": FEATURES,
              "reference_mean": x.mean(axis=0), "reference_std": x.std(axis=0),
              "manifest": manifest}
    joblib.dump(bundle, out / "model.joblib")
    result.to_csv(out / "policy_evaluation.csv", index=False)
    pd.concat(curves).to_csv(out / "gain_curves.csv", index=False)
    for name, content in [("manifest", manifest), ("experiment", experiment)]:
        (out / f"{name}.json").write_text(json.dumps(content, indent=2, allow_nan=False))
    audit = []
    for label, part in [("train", train), ("validation", valid), ("test", test)]:
        audit.append(part[["_source_row", "treatment", "conversion"]].assign(split=label))
    with sqlite3.connect(out / "audit.sqlite") as db:
        pd.concat(audit).to_sql("assignments", db, index=False)
        result.to_sql("policy_evaluation", db, index=False)
    return manifest


def score_file(model_path, input_path, output_path):
    from .artifacts import verify_run
    verify_run(Path(model_path).parent)
    # joblib/pickle can execute code: only load locally created trusted run artifacts.
    bundle = joblib.load(model_path)
    if bundle["manifest"].get("schema_version") != 1 or bundle["features"] != FEATURES:
        raise ValueError("Unsupported model schema")
    output_path = Path(output_path)
    if output_path.resolve() in [Path(input_path).resolve(), Path(model_path).resolve()]:
        raise ValueError("Scoring cannot overwrite inputs")
    df = pd.read_csv(input_path)
    validate(df, outcomes=False)
    scores, _, _ = predict(bundle["models"], df[FEATURES].to_numpy())
    scored = df.copy()
    winner = bundle["winner"]
    scored["estimated_uplift"] = scores.get(winner, np.zeros(len(df)))
    scored["run_created_at_utc"] = bundle["manifest"]["created_at_utc"]
    from .data import checksum
    import hashlib
    identity = {"schema_version": 1, "input_sha256": checksum(input_path),
                "model_sha256": checksum(model_path), "run_id": bundle["manifest"]["run_id"]}
    identity["job_id"] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    sidecar = output_path.with_suffix(output_path.suffix + ".json")
    if sidecar.resolve() in [Path(input_path).resolve(), Path(model_path).resolve()]:
        raise ValueError("Scoring metadata cannot overwrite inputs")
    if output_path.exists() or sidecar.exists():
        if not (output_path.exists() and sidecar.exists()):
            raise ValueError("Incomplete existing scoring output; use a fresh path")
        prior = json.loads(sidecar.read_text())
        if prior.get("job_id") != identity["job_id"] or prior.get("output_sha256") != checksum(output_path):
            raise ValueError("Output exists for a different or damaged scoring job")
    else:
        import os, tempfile
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output_path.parent, delete=False, suffix=".csv") as f:
            temporary = Path(f.name)
        try:
            scored.to_csv(temporary, index=False)
            os.replace(temporary, output_path)
        finally:
            temporary.unlink(missing_ok=True)
        identity["output_sha256"] = checksum(output_path)
        sidecar.write_text(json.dumps(identity, indent=2))
    scale = np.where(bundle["reference_std"] > 0, bundle["reference_std"], 1.)
    shifts = (df[FEATURES].mean().to_numpy() - bundle["reference_mean"]) / scale
    return {"rows": len(scored), "standardized_mean_shift": dict(zip(FEATURES, shifts)),
            "shift_alert": bool((np.abs(shifts) > .2).any()),
            "shift_threshold": .2, "threshold_basis": "heuristic screening threshold; not calibrated to historical data",
            "note": "Descriptive feature shift only; does not measure causal-effect drift"}


def run(df, out, provenance, *args, **kwargs):
    """Publish a run atomically; failed runs never appear complete."""
    import shutil
    import tempfile
    import time
    import uuid
    try:
        import resource
    except ImportError:
        resource = None
    from .artifacts import seal_run, source_identity
    out = Path(out)
    if out.exists():
        raise ValueError("Use a new run directory to preserve earlier artifacts")
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".counterlift-", dir=out.parent))
    target = staging / "artifacts"
    started = time.monotonic()
    try:
        manifest = _run(df, target, provenance, *args, **kwargs)
        manifest.update(run_id=str(uuid.uuid4()), source_code=source_identity(),
                        elapsed_seconds=time.monotonic() - started,
                        peak_process_rss_bytes=None if resource is None else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system() == "Darwin" else 1024))
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False))
        bundle = joblib.load(target / "model.joblib")
        bundle["manifest"] = manifest
        joblib.dump(bundle, target / "model.joblib")
        (target / "events.jsonl").write_text(json.dumps({"event": "evaluation_complete", "run_id": manifest["run_id"], "elapsed_seconds": manifest["elapsed_seconds"]}) + "\n")
        seal_run(target)
        target.rename(out)
        return manifest
    finally:
        shutil.rmtree(staging)

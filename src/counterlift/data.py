import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = [f"f{i}" for i in range(12)]
REQUIRED = FEATURES + ["treatment", "conversion"]


def checksum(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(frame, outcomes=True, require_both_arms=True):
    required = REQUIRED if outcomes else FEATURES
    missing = set(required) - set(frame)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if not np.isfinite(frame[required].to_numpy(dtype=float)).all():
        raise ValueError("Inputs contain missing, infinite or nonnumeric values")
    if outcomes:
        for col in ["treatment", "conversion"]:
            if not frame[col].isin([0, 1]).all():
                raise ValueError(f"{col} must be binary")
        if require_both_arms and frame.treatment.nunique() != 2:
            raise ValueError("Both randomized arms are required")
    if len(frame) == 0:
        raise ValueError("Empty input")


def load_sample(path, sample_size=250_000, seed=42):
    """Uniform priority sampling across the entire file; never take its first N rows."""
    if sample_size < 1000:
        raise ValueError("Use at least 1,000 rows; rare outcomes need substantially more")
    rng = np.random.default_rng(seed)
    retained = None
    total = 0
    for chunk in pd.read_csv(path, chunksize=100_000, usecols=REQUIRED):
        validate(chunk, require_both_arms=False)
        chunk["_source_row"] = np.arange(total, total + len(chunk))
        total += len(chunk)
        chunk["_priority"] = rng.random(len(chunk))
        retained = chunk if retained is None else pd.concat([retained, chunk], ignore_index=True)
        if len(retained) > sample_size:
            # Partial selection avoids sorting a million-row reservoir on every chunk.
            keep = np.argpartition(retained["_priority"].to_numpy(), sample_size - 1)[:sample_size]
            retained = retained.iloc[keep]
    if retained is None:
        raise ValueError("No source records")
    retained = retained.drop(columns="_priority").sort_values("_source_row").reset_index(drop=True)
    retained[FEATURES] = retained[FEATURES].astype("float32")
    validate(retained)
    return retained, {"source": str(Path(path).name), "source_rows": total,
                      "sample_rows": len(retained), "sha256": checksum(path),
                      "sampling": "uniform random priority across complete source"}


def synthetic(n=20_000, seed=42):
    """Software validation only; simulated effects are not Criteo findings."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, 12))
    p0 = 0.05 + 0.03 / (1 + np.exp(-x[:, 1]))
    tau = np.where(x[:, 0] > 0, 0.10, -0.025)
    t = rng.binomial(1, 0.85, n)
    y = rng.binomial(1, p0 + t * tau)
    frame = pd.DataFrame(x, columns=FEATURES)
    frame["treatment"], frame["conversion"] = t, y
    frame["_source_row"] = np.arange(n)
    return frame

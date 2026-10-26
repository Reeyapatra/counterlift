"""Download pinned publisher data, verify publisher-reported SHA-256, preserve original bytes."""
import hashlib
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

REVISION = "2424920019e49d52d72c13ac1143ec5d53af276b"
FILENAME = "criteo-research-uplift-v2.1.csv.gz"
# Publisher mirror LFS SHA-256 at the pinned revision, checked 2026-10-26.
SHA256 = "2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc"
URL = f"https://huggingface.co/datasets/criteo/criteo-uplift/resolve/{REVISION}/{FILENAME}"


def main():
    directory = Path("data")
    directory.mkdir(exist_ok=True)
    path = directory / FILENAME
    if path.exists():
        with path.open("rb") as f:
            existing = hashlib.file_digest(f, "sha256").hexdigest()
        if existing != SHA256:
            raise SystemExit("Existing file checksum mismatch; preserve it and use a separate location")
        print("Existing publisher file checksum verified")
        return
    temp = path.with_suffix(path.suffix + ".partial")
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(URL, timeout=60) as response, temp.open("wb") as f:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                digest.update(chunk)
                f.write(chunk)
        if digest.hexdigest() != SHA256:
            raise ValueError("Publisher checksum mismatch; source was not accepted")
        temp.replace(path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    metadata = {"url": URL, "publisher_revision": REVISION, "sha256": SHA256,
                "bytes": path.stat().st_size, "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
                "license": "CC BY-NC-SA 4.0; review publisher terms before redistribution",
                "citation": "Diemert et al. (2018), A Large Scale Benchmark for Uplift Modeling, AdKDD"}
    (directory / "source.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()

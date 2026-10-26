import argparse
import json

from .data import load_sample, synthetic
from .pipeline import run, score_file


def main():
    parser = argparse.ArgumentParser(description="Offline causal marketing decision support")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["demo", "train"]:
        p = sub.add_parser(name)
        p.add_argument("--out", required=True)
        p.add_argument("--rows", type=int, default=20_000 if name == "demo" else 1_000_000)
        p.add_argument("--seed", type=int, default=42)
        p.add_argument("--bootstrap", type=int, default=200)
        p.add_argument("--selection-budget", type=float, default=.20)
        p.add_argument("--cost", type=float, default=0.)
        p.add_argument("--value", type=float, default=1.)
        p.add_argument("--propensity", type=float)
        p.add_argument("--expected-assignment", type=float)
        if name == "train":
            p.add_argument("--data", required=True)
            p.add_argument("--corrected-release", action="store_true",
                           help="Assert source is corrected Criteo v2.1; row count will also be checked")
            p.add_argument("--expected-sha256", help="Verify against an independently trusted checksum")
    p = sub.add_parser("export")
    p.add_argument("--run", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("score")
    p.add_argument("--model", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.command == "export":
        from .artifacts import export_public
        export_public(args.run, args.out)
        print("Aggregate-only export verified")
        return
    if args.command == "score":
        print(json.dumps(score_file(args.model, args.data, args.out), indent=2))
        return
    if args.command == "demo":
        df = synthetic(args.rows, args.seed)
        provenance = {"dataset": "SYNTHETIC SOFTWARE DEMO", "not_criteo": True}
    else:
        if not args.corrected_release:
            parser.error("Use the corrected v2.1 source and explicitly pass --corrected-release")
        df, provenance = load_sample(args.data, args.rows, args.seed)
        if provenance["source_rows"] != 13_979_592:
            parser.error("Source row count does not match the corrected Criteo release")
        if args.expected_sha256 and args.expected_sha256.lower() != provenance["sha256"]:
            parser.error("Source checksum does not match independently supplied checksum")
        provenance["dataset"] = "Criteo v2.1 (user-declared source; complete row count checked)"
        provenance["checksum_verified"] = bool(args.expected_sha256)
    manifest = run(df, args.out, provenance, args.seed, args.bootstrap, args.propensity,
                   args.expected_assignment, args.selection_budget, args.cost, args.value)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

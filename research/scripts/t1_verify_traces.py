#!/usr/bin/env python3
"""T1 artifact verification: check every raw trace against results/run_manifest.json.

For each manifest run this checks that the trace file exists, that its SHA-256
equals the manifest value, and that task, snapshot, repetition, method,
config hash, protocol version and status/stop reason inside the trace agree
with the manifest. Nothing is repaired or excluded silently: every run gets a
verdict (verified / hash_mismatch / field_mismatch / missing).

Usage:
  python scripts/t1_verify_traces.py [--traces-dir results/raw/traces]
                                     [--output results/processed/t1_trace_verification.json]
Exit code 0 only if all manifest runs verify.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FIELD_MAP = {  # manifest field -> trace field
    "task_id": "task_id",
    "method": "method",
    "repetition": "repetition",
    "paired_trial_id": "paired_trial_id",
    "protocol_version": "protocol_version",
    "snapshot_sha": "snapshot_id",
    "index_build_id": "index_id",
    "config_hash": "config_hash",
    "stop_reason": "stop_reason",
}


def verify(manifest: dict, traces_dir: Path) -> dict:
    rows = []
    listed = set()
    for run in manifest["runs"]:
        listed.add(run["trace_file"])
        path = traces_dir / run["trace_file"]
        row = {"run_set": run["run_set"], "trace_file": run["trace_file"],
               "expected_sha256": run["trace_sha256"]}
        if not path.exists():
            row.update(verdict="missing")
            rows.append(row)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        row["actual_sha256"] = actual
        if actual != run["trace_sha256"]:
            row.update(verdict="hash_mismatch")
            rows.append(row)
            continue
        trace = json.loads(path.read_text(encoding="utf-8"))
        mism = {m: {"manifest": run.get(m), "trace": trace.get(t)}
                for m, t in FIELD_MAP.items() if run.get(m) != trace.get(t)}
        if run.get("status") != "completed" or trace.get("errors"):
            mism["status"] = {"manifest": run.get("status"), "trace_errors": trace.get("errors")}
        if not isinstance(trace.get("evidence_pack"), list) or not trace["evidence_pack"]:
            mism["evidence_pack"] = "missing or empty"
        row.update(verdict="field_mismatch" if mism else "verified", mismatches=mism)
        rows.append(row)
    extra = sorted(p.name for p in traces_dir.glob("*.json") if p.name not in listed) if traces_dir.exists() else []
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {"traces_dir": str(traces_dir), "manifest_runs": len(manifest["runs"]),
            "verdict_counts": counts, "unlisted_trace_files": extra, "runs": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=ROOT / "results" / "run_manifest.json")
    ap.add_argument("--traces-dir", type=Path, default=ROOT / "results" / "raw" / "traces")
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    report = verify(json.loads(a.manifest.read_text(encoding="utf-8")), a.traces_dir)
    text = json.dumps(report, indent=2)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("manifest_runs", "verdict_counts", "unlisted_trace_files")}, indent=2))
    return 0 if report["verdict_counts"].get("verified", 0) == report["manifest_runs"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

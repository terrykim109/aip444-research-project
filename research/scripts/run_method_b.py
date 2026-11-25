#!/usr/bin/env python3
"""Execute Method B once for a task (Stage 6 plumbing; not a Stage 7 pilot batch)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--repetition", type=int, default=1)
    parser.add_argument("--no-persist", action="store_true")
    parser.add_argument("--protocol-version", default="pilot-v1.0")
    args = parser.parse_args()
    _load_dotenv(ROOT / ".env")

    from repo_search.orchestrator import run_trial

    record = run_trial(
        task_id=args.task_id,
        method="agent_directed",
        repetition=args.repetition,
        persist_trace=not args.no_persist,
        protocol_version=args.protocol_version,
    )
    summary = {
        "task_id": record["task_id"],
        "method": record["method"],
        "snapshot_id": record["snapshot_id"],
        "tool_call_count": record["tool_call_count"],
        "evidence_tokens": record["evidence_tokens"],
        "planning_tokens": record["planning_tokens"],
        "stop_reason": record["stop_reason"],
        "pack_size": len(record["evidence_pack"]),
        "requested_model": record["method_detail"].get("requested_model"),
        "returned_model": record["method_detail"].get("returned_model"),
        "trace_path": record.get("trace_path"),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

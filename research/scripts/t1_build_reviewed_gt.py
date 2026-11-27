#!/usr/bin/env python3
"""Build the T1-reviewed ground-truth version (t1_reviewed_v1) for the main tasks.

T1 (Rehat) relevance review of T2's provisional ``t2_context_v1`` annotations
for the four main-experiment tasks. The source set is never modified: this
script copies each reviewed file, applies the documented changes below, and
writes ``benchmark/ground_truth/t1_reviewed_v1/`` plus a change record with
SHA-256 hashes of both the source (as used during the runs) and the result.

Single reviewer (T1); no second/peer reviewer participated. The review was
not fully blind: preliminary aggregate results from T3 had been seen. Raw
traces and per-run evidence packs were NOT available during the review.

Usage:  python scripts/t1_build_reviewed_gt.py
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "benchmark" / "ground_truth" / "t2_context_v1"
DST = ROOT / "benchmark" / "ground_truth" / "t1_reviewed_v1"
REVIEW = ROOT / "benchmark" / "reviews" / "t1_reviewed_v1"
MAIN_TASKS = [
    "pi_package_dedup_collisions",
    "pi_rpc_context_statistics",
    "pi_session_directory_config",
    "pi_cli_mode_validation",
]

# Each change is decided from the pinned parent snapshot and the task prompt only.
ADDITIONS = {
    "pi_rpc_context_statistics": [
        {
            "path": "packages/coding-agent/src/core/extensions/types.ts",
            "relevance": "supporting",
            "relevance_score": 1,
            "rationale": (
                "Defines the existing ContextUsage interface (tokens: number | null, "
                "contextWindow, percent: number | null). This is the 'existing "
                "representation for unknown usage' the prompt requires to be preserved, "
                "and the shape that SessionStats must expose; agent-session.ts only "
                "imports it."
            ),
            "symbols": ["ContextUsage"],
            "line_spans": [
                {
                    "symbol": "ContextUsage",
                    "start_line": 245,
                    "end_line": 251,
                    "anchor": "export interface ContextUsage",
                    "content_sha256": "7ea783c267274da8a6bb950e505422d8d43c68c595630d23c13ccd42dc15e209",
                }
            ],
            "blob_sha": "d4a34f1a96d608d7819b1258bec07275341db400",
            "content_sha256": "12ab5bd74a7c91b55a321402a43d859ed240f27fd653434fef361ae97cbf0bd5",
        }
    ]
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    record = {
        "annotation_set": "t1_reviewed_v1",
        "derived_from": "t2_context_v1",
        "reviewer": "T1 (single reviewer; no peer review performed)",
        "review_blindness": (
            "Not fully blind: T3's preliminary aggregate F1 tables had been seen. "
            "Raw traces/evidence packs were unavailable during review, so no per-run "
            "method output was consulted. Relevance was judged from the task prompt and "
            "the pinned parent snapshot only."
        ),
        "tasks": {},
    }
    for task in MAIN_TASKS:
        src = SRC / f"{task}.json"
        data = json.loads(src.read_text(encoding="utf-8"))
        out = copy.deepcopy(data)
        changes = []
        for add in ADDITIONS.get(task, []):
            out["files"].append(add)
            for span in add["line_spans"]:
                out["relevant_spans"].append(
                    {"path": add["path"], "start_line": span["start_line"],
                     "end_line": span["end_line"], "relevance": add["relevance"]}
                )
            for sym in add["symbols"]:
                out["relevant_symbols"].append(
                    {"path": add["path"], "symbol": sym, "relevance": add["relevance"]}
                )
            changes.append({"change": "add_file", "path": add["path"],
                            "relevance": add["relevance"], "rationale": add["rationale"]})
        out["annotation_set"] = "t1_reviewed_v1"
        out["annotation_version"] = "t1-1.0"
        out["review_status"] = "validated"          # schema enum
        out["human_review_status"] = "reviewed"     # schema enum
        out["review_detail"] = (
            "Reviewed by T1 only (single reviewer); no peer/second reviewer. "
            "Not fully blind (T3 preliminary aggregates seen; no traces consulted)."
        )
        out["annotation_notes"] = list(out.get("annotation_notes", [])) + [
            "T1 review (t1_reviewed_v1): "
            + ("changes recorded in benchmark/reviews/t1_reviewed_v1/changes.json."
               if changes else "all T2 judgments confirmed; no changes.")
        ]
        dst = DST / f"{task}.json"
        dst.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        record["tasks"][task] = {
            "source_file": str(src.relative_to(ROOT)).replace("\\", "/"),
            "source_sha256_as_used_in_runs": sha256_file(src),
            "reviewed_file": str(dst.relative_to(ROOT)).replace("\\", "/"),
            "reviewed_sha256": sha256_file(dst),
            "changes": changes,
            "essential": sorted(f["path"] for f in out["files"] if f["relevance"] == "essential"),
            "supporting": sorted(f["path"] for f in out["files"] if f["relevance"] == "supporting"),
        }
    (REVIEW / "changes.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({t: {"changes": len(v["changes"]), "sha": v["reviewed_sha256"][:16]}
                      for t, v in record["tasks"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

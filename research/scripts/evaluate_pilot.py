#!/usr/bin/env python3
"""File-level pilot evaluation: TP/FP/FN, precision, recall, F1 per trace.

T3 preliminary computation (implementation_origin: teammate_3). Reads persisted
experiment traces and evaluator-only ground truth. T1's independent evaluation
remains authoritative; results for different annotation sets are reported
separately and must never be combined.

Usage:
  python scripts/evaluate_pilot.py
  python scripts/evaluate_pilot.py --annotation-set t2_context_v1 --output results/processed/pilot_eval.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

GT_SETS = {
    "preliminary": ROOT / "benchmark" / "ground_truth",
    "t2_context_v1": ROOT / "benchmark" / "ground_truth" / "t2_context_v1",
}


def load_gt(gt_dir: Path, task_id: str) -> dict:
    path = gt_dir / f"{task_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    files = {f["path"]: f.get("relevance", "supporting") for f in data.get("files", [])}
    if not files:
        raise ValueError(f"ground truth has no files: {path}")
    return {
        "files": files,
        "essential": {p for p, rel in files.items() if rel == "essential"},
        "review_status": data.get("review_status", "unknown"),
        "annotation_version": data.get("annotation_version", "unknown"),
    }


def evaluate_trace(trace: dict, gt: dict) -> dict:
    retrieved = sorted({item["path"] for item in trace.get("evidence_pack", [])})
    gt_files = set(gt["files"])
    tp = sorted(set(retrieved) & gt_files)
    fp = sorted(set(retrieved) - gt_files)
    fn = sorted(gt_files - set(retrieved))
    precision = len(tp) / len(retrieved) if retrieved else 0.0
    recall = len(tp) / len(gt_files)  # GT is validated non-empty
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    essential = gt["essential"]
    essential_recall = (
        len(essential & set(retrieved)) / len(essential) if essential else None
    )
    return {
        "paired_trial_id": trace["paired_trial_id"],
        "task_id": trace["task_id"],
        "method": trace["method"],
        "repetition": trace["repetition"],
        "stop_reason": trace.get("stop_reason"),
        "errors": trace.get("errors") or [],
        "retrieved_files": len(retrieved),
        "tp": len(tp),
        "fp": len(fp),
        "fn": len(fn),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "essential_recall": (
            round(essential_recall, 4) if essential_recall is not None else None
        ),
        "evidence_tokens": trace.get("evidence_tokens"),
        "planning_tokens": trace.get("planning_tokens"),
        "tool_call_count": trace.get("tool_call_count"),
        "latency_ms": round(trace.get("latency_ms") or 0.0, 1),
        "false_positives": fp,
        "false_negatives": fn,
    }


def aggregate(rows: list[dict]) -> dict:
    by_group: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        by_group[(r["task_id"], r["method"])].append(r)
    means = {}
    for (task, method), group in sorted(by_group.items()):
        means[f"{task}::{method}"] = {
            "runs": len(group),
            "mean_precision": round(sum(r["precision"] for r in group) / len(group), 4),
            "mean_recall": round(sum(r["recall"] for r in group) / len(group), 4),
            "mean_f1": round(sum(r["f1"] for r in group) / len(group), 4),
        }
    pairs: dict[str, dict] = defaultdict(dict)
    for r in rows:
        pairs[r["paired_trial_id"]][r["method"]] = r
    pair_diffs = []
    for pid, methods in sorted(pairs.items()):
        if "one_shot_rag" in methods and "agent_directed" in methods:
            pair_diffs.append(
                {
                    "paired_trial_id": pid,
                    "f1_a": methods["one_shot_rag"]["f1"],
                    "f1_b": methods["agent_directed"]["f1"],
                    "f1_b_minus_a": round(
                        methods["agent_directed"]["f1"] - methods["one_shot_rag"]["f1"], 4
                    ),
                }
            )
    return {"per_task_method_means": means, "matched_pairs": pair_diffs}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--traces-dir", type=Path, default=ROOT / "results" / "raw" / "traces"
    )
    parser.add_argument(
        "--annotation-set", choices=[*GT_SETS, "both"], default="both"
    )
    parser.add_argument(
        "--task-id",
        action="append",
        dest="task_ids",
        help="Evaluate only these tasks (repeatable). Prevents mixing pilot "
        "and main-experiment traces in one report.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    trace_files = sorted(args.traces_dir.glob("*.json"))
    if not trace_files:
        print(f"ERROR: no traces found in {args.traces_dir}", file=sys.stderr)
        return 1
    loaded = [
        (p, json.loads(p.read_text(encoding="utf-8"))) for p in trace_files
    ]
    if args.task_ids:
        loaded = [(p, t) for p, t in loaded if t["task_id"] in args.task_ids]
        if not loaded:
            print("ERROR: no traces match the requested task ids", file=sys.stderr)
            return 1
    trace_files = [p for p, _ in loaded]
    traces = [t for _, t in loaded]

    sets = list(GT_SETS) if args.annotation_set == "both" else [args.annotation_set]
    report: dict = {
        "note": (
            "Preliminary T3 computation; T1's independent evaluation is "
            "authoritative. Annotation sets are reported separately — do not "
            "combine across sets."
        ),
        "trace_count": len(traces),
        "trace_files": [p.name for p in trace_files],
        "by_annotation_set": {},
    }
    for set_name in sets:
        gt_dir = GT_SETS[set_name]
        rows, skipped = [], []
        for trace in traces:
            try:
                gt = load_gt(gt_dir, trace["task_id"])
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                skipped.append({"task_id": trace["task_id"], "reason": str(exc)})
                continue
            rows.append(evaluate_trace(trace, gt))
        report["by_annotation_set"][set_name] = {
            "gt_dir": str(gt_dir),
            "review_status": sorted(
                {
                    load_gt(gt_dir, t["task_id"])["review_status"]
                    for t in traces
                    if (gt_dir / f"{t['task_id']}.json").exists()
                }
            ),
            "per_run": rows,
            "skipped": skipped,
            "aggregate": aggregate(rows),
        }

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

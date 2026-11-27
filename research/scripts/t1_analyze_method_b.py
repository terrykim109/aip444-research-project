#!/usr/bin/env python3
"""T1 analysis of Method B (agent-directed) search behaviour from verified traces.

For every verified Method B trace in a run set this reconstructs, call by call
(from method_detail.tool_trace): tool name and arguments (queries/refinements),
errors, files returned, files new at that call, ground-truth files new at that
call, duplicate evidence (evidence_id already returned earlier), evidence tokens
charged, and cumulative precision/recall/F1 of the union of files seen so far.
It also compares, for the same paired trial: Method A's final pack, Method B's
initial semantic_search (call 1) and Method B's final pack.

Ground truth is used only here, offline. Provenance: every row carries the
trace file name and its manifest SHA-256.

Usage:
  python scripts/t1_analyze_method_b.py --run-set main-v1.0 --annotation-set t1_reviewed_v1
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mod(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # type: ignore[union-attr]
    return m


EV = _mod("t1_evaluate")
LLM_SELECTED = {"evidence_sufficient", "no_new_relevant_evidence"}


def prf(files: set[str], gt: set[str]) -> tuple[float, float, float]:
    tp = len(files & gt)
    p = tp / len(files) if files else 0.0
    r = tp / len(gt)
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def analyze_trace(trace: dict, gt: dict) -> dict:
    wt = trace.get("worktree_path")
    gt_files = set(gt["files"])
    calls = (trace.get("method_detail") or {}).get("tool_trace") or []
    seen_files: set[str] = set()
    seen_ids: set[str] = set()
    rows = []
    for c in calls:
        res = c.get("result") or {}
        ev = res.get("evidence") or []
        files = [EV.normalize_path(e["path"], wt) for e in ev]
        fset = set(files)
        new = fset - seen_files
        dup = sum(1 for e in ev if e.get("evidence_id") in seen_ids)
        seen_files |= fset
        seen_ids |= {e.get("evidence_id") for e in ev}
        p, r, f = prf(seen_files, gt_files)
        rows.append({
            "call_index": c.get("call_index"), "tool": c.get("tool_name"),
            "arguments": c.get("arguments"), "ok": res.get("ok"),
            "error_message": None if res.get("ok") else res.get("message"),
            "chunks_returned": len(ev), "files_returned": sorted(fset),
            "new_files": sorted(new), "new_relevant_files": sorted(new & gt_files),
            "duplicate_chunks": dup,
            "evidence_tokens_charged": sum(int(e.get("token_count") or 0) for e in ev),
            "cumulative_precision": p, "cumulative_recall": r, "cumulative_f1": f,
        })
    final_files = set(EV.ranked_files(trace["evidence_pack"], wt))
    initial = set(rows[0]["files_returned"]) if rows else set()
    stop = trace.get("stop_reason")
    return {
        "calls": rows,
        "tool_sequence": [r["tool"] for r in rows],
        "queries": [r["arguments"] for r in rows],
        "errors": [r for r in rows if r["ok"] is False],
        "post_initial_inspection_calls": sum(1 for r in rows[1:] if r["tool"] in {"read_file", "find_symbol", "grep"}),
        "calls_adding_relevant_files": sum(1 for r in rows if r["new_relevant_files"]),
        "relevant_files_found_after_call_1": sorted(set().union(*[set(r["new_relevant_files"]) for r in rows[1:]]) if len(rows) > 1 else set()),
        "stop_reason": stop,
        "final_pack_source": "llm_selected_evidence_ids" if stop in LLM_SELECTED else "fallback_all_charged_excerpts (per method_b.py)",
        "initial_semantic_files": sorted(initial), "final_pack_files": sorted(final_files),
        "initial_prf": prf(initial, gt_files), "final_prf": prf(final_files, gt_files),
        "union_seen_prf": prf(seen_files, gt_files),
        "relevant_seen_but_dropped_from_final": sorted((seen_files & gt_files) - final_files),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=ROOT / "results" / "run_manifest.json")
    ap.add_argument("--traces-dir", type=Path, default=ROOT / "results" / "raw" / "traces")
    ap.add_argument("--run-set", required=True, choices=["main-v1.0", "pilot-v1.0"])
    ap.add_argument("--annotation-set", required=True, choices=list(EV.GT_SETS))
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "processed")
    a = ap.parse_args()
    manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    ver = {r["trace_file"]: r["verdict"] for r in _mod("t1_verify_traces").verify(manifest, a.traces_dir)["runs"]}
    runs = [r for r in manifest["runs"] if r["run_set"] == a.run_set]
    a_files = {}
    for r in runs:
        if r["method"] == "one_shot_rag" and ver.get(r["trace_file"]) == "verified":
            t = json.loads((a.traces_dir / r["trace_file"]).read_text(encoding="utf-8"))
            a_files[r["paired_trial_id"]] = set(EV.ranked_files(t["evidence_pack"], t.get("worktree_path")))
    out, skipped = [], []
    for r in runs:
        if r["method"] != "agent_directed":
            continue
        if ver.get(r["trace_file"]) != "verified":
            skipped.append({"trace_file": r["trace_file"], "verdict": ver.get(r["trace_file"], "missing")})
            continue
        t = json.loads((a.traces_dir / r["trace_file"]).read_text(encoding="utf-8"))
        gt = EV.load_gt(a.annotation_set, r["task_id"])
        res = analyze_trace(t, gt)
        af = a_files.get(r["paired_trial_id"])
        if af is not None:
            res["a_final_files"] = sorted(af)
            res["a_final_prf"] = prf(af, set(gt["files"]))
            res["a_final_equals_b_initial"] = af == set(res["initial_semantic_files"])
            res["a_final_equals_b_final"] = af == set(res["final_pack_files"])
        out.append({"trace_file": r["trace_file"], "trace_sha256": r["trace_sha256"],
                    "task_id": r["task_id"], "repetition": r["repetition"], **res})
    summary = {
        "b_runs_analyzed": len(out), "skipped": skipped,
        "tool_usage": Counter(x for o in out for x in o["tool_sequence"]),
        "tool_errors": sum(len(o["errors"]) for o in out),
        "stop_reasons": Counter(o["stop_reason"] for o in out),
        "final_pack_source": Counter(o["final_pack_source"] for o in out),
        "runs_with_relevant_file_found_after_call_1": sum(1 for o in out if o["relevant_files_found_after_call_1"]),
        "runs_dropping_seen_relevant_files": sum(1 for o in out if o["relevant_seen_but_dropped_from_final"]),
        "mean_post_initial_inspection_calls": (sum(o["post_initial_inspection_calls"] for o in out) / len(out)) if out else None,
    }
    by_task = defaultdict(list)
    for o in out:
        by_task[o["task_id"]].append({k: o[k] for k in ("repetition", "tool_sequence", "stop_reason", "initial_prf", "final_prf", "union_seen_prf")})
    rep = {"run_set": a.run_set, "annotation_set": a.annotation_set, "summary": summary, "by_task": by_task, "runs": out,
           "authoritative": not skipped and bool(out)}
    a.output_dir.mkdir(parents=True, exist_ok=True)
    p = a.output_dir / f"t1_method_b_behaviour__{a.run_set}__{a.annotation_set}.json"
    p.write_text(json.dumps(rep, indent=2, default=list) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, default=dict))
    print(f"wrote {p}")
    return 0 if rep["authoritative"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

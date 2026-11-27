#!/usr/bin/env python3
"""T1 independent file-level evaluation of verified experiment traces.

Independent of T3's scripts/evaluate_pilot.py (audited, not reused). Only runs
whose trace verifies against results/run_manifest.json (SHA-256 + fields, see
t1_verify_traces.py) are scored; every other manifest run is reported with its
verdict, never silently dropped or repaired.

Conventions (documented in docs/t1_evaluation.md):
* Unit = unique repository file. Chunks/lines/symbols are collapsed to files.
* Path normalisation: backslashes -> '/', worktree prefix stripped if absolute,
  leading './' and '/' removed, repeated '/' collapsed. Case is preserved
  (Git paths are case-sensitive).
* File ranking = order of first appearance in the evidence pack (by 'rank'
  when present, else list order).
* TP/FP/FN over unique files; precision = TP/(TP+FP), recall = TP/(TP+FN),
  F1 = 2PR/(P+R). Empty pack -> precision 0 (flagged), recall 0. P+R=0 -> F1 0.
  Ground truth is non-empty by construction.
* Essential recall = essential files retrieved / essential files.
* MRR = 1/rank of the first ground-truth file in the file ranking (0 if none).
* nDCG@10 with graded gains essential=2, supporting=1, unjudged=0,
  DCG = sum gain_i / log2(i+1); IDCG from the ideal ordering of GT gains.
* Unjudged files count as non-relevant (closed-world convention; disclosed).
* Macro = mean of per-task means; pooled (micro) = P/R/F1 from summed TP/FP/FN.

Usage:
  python scripts/t1_evaluate.py --run-set main-v1.0 --annotation-set t1_reviewed_v1
  python scripts/t1_evaluate.py --run-set main-v1.0 --annotation-set t2_context_v1
  python scripts/t1_evaluate.py --run-set pilot-v1.0 --annotation-set preliminary
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GT_SETS = {
    "preliminary": ROOT / "benchmark" / "ground_truth",
    "t2_context_v1": ROOT / "benchmark" / "ground_truth" / "t2_context_v1",
    "t1_reviewed_v1": ROOT / "benchmark" / "ground_truth" / "t1_reviewed_v1",
}
GAIN = {"essential": 2, "supporting": 1}
NDCG_K = 10


def _load_verifier():
    spec = importlib.util.spec_from_file_location("t1_verify_traces", ROOT / "scripts" / "t1_verify_traces.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def normalize_path(path: str, worktree: str | None = None) -> str:
    p = path.replace("\\", "/")
    if worktree:
        w = worktree.replace("\\", "/").rstrip("/") + "/"
        if p.lower().startswith(w.lower()):
            p = p[len(w):]
    p = re.sub(r"/+", "/", p)
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def ranked_files(evidence_pack: list[dict], worktree: str | None = None) -> list[str]:
    items = sorted(enumerate(evidence_pack), key=lambda t: (t[1].get("rank", t[0] + 1), t[0]))
    seen: list[str] = []
    for _, it in items:
        f = normalize_path(it["path"], worktree)
        if f not in seen:
            seen.append(f)
    return seen


def load_gt(set_name: str, task_id: str) -> dict:
    path = GT_SETS[set_name] / f"{task_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    files = {normalize_path(f["path"]): f["relevance"] for f in data["files"]}
    if not files:
        raise ValueError(f"empty ground truth: {path}")
    return {"files": files, "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "annotation_set": data.get("annotation_set", set_name),
            "review_status": data.get("review_status")}


def score(files: list[str], gt: dict) -> dict:
    g = gt["files"]
    ret = set(files)
    tp = sorted(ret & g.keys())
    fp = sorted(ret - g.keys())
    fn = sorted(g.keys() - ret)
    p = len(tp) / len(ret) if ret else 0.0
    r = len(tp) / len(g)
    f1 = 2 * p * r / (p + r) if p + r > 0 else 0.0
    ess = {k for k, v in g.items() if v == "essential"}
    ess_rec = len(ess & ret) / len(ess) if ess else None
    mrr = 0.0
    for i, f in enumerate(files, 1):
        if f in g:
            mrr = 1.0 / i
            break
    dcg = sum(GAIN.get(g.get(f, ""), 0) / math.log2(i + 1) for i, f in enumerate(files[:NDCG_K], 1))
    ideal = sorted((GAIN[v] for v in g.values()), reverse=True)[:NDCG_K]
    idcg = sum(x / math.log2(i + 1) for i, x in enumerate(ideal, 1))
    return {"retrieved_files": len(ret), "tp": len(tp), "fp": len(fp), "fn": len(fn),
            "precision": p, "recall": r, "f1": f1, "essential_recall": ess_rec,
            "mrr": mrr, "ndcg_at_10": dcg / idcg if idcg else 0.0,
            "empty_pack": not ret, "tp_files": tp, "fp_files": fp, "fn_files": fn,
            "file_ranking": files}


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def evaluate(manifest: dict, traces_dir: Path, run_set: str, set_name: str) -> dict:
    ver = _load_verifier().verify(manifest, traces_dir)
    verdict = {r["trace_file"]: r["verdict"] for r in ver["runs"]}
    runs = [r for r in manifest["runs"] if r["run_set"] == run_set]
    rows, excluded = [], []
    for run in runs:
        v = verdict.get(run["trace_file"], "missing")
        if v != "verified":
            excluded.append({"trace_file": run["trace_file"], "verdict": v})
            continue
        trace = json.loads((traces_dir / run["trace_file"]).read_text(encoding="utf-8"))
        gt = load_gt(set_name, run["task_id"])
        files = ranked_files(trace["evidence_pack"], trace.get("worktree_path"))
        s = score(files, gt)
        acct = (trace.get("method_detail") or {}).get("evidence_accounting") or {}
        rows.append({
            "run_set": run_set, "task_id": run["task_id"], "method": run["method"],
            "repetition": run["repetition"], "paired_trial_id": run["paired_trial_id"],
            "trace_file": run["trace_file"], "trace_sha256": run["trace_sha256"],
            "gt_file": gt["path"], **s,
            "pack_chunks": len(trace["evidence_pack"]),
            "pack_tokens": sum(int(i.get("token_count") or 0) for i in trace["evidence_pack"]),
            "cumulative_evidence_tokens": trace.get("evidence_tokens"),
            "final_pack_tokens_reported": acct.get("final_evidence_pack_tokens"),
            "planning_tokens": trace.get("planning_tokens"),
            "tool_call_count": trace.get("tool_call_count"),
            "latency_ms": trace.get("latency_ms"), "stop_reason": trace.get("stop_reason"),
        })
    by_tm = defaultdict(list)
    for r in rows:
        by_tm[(r["task_id"], r["method"])].append(r)
    metrics = ["precision", "recall", "f1", "essential_recall", "mrr", "ndcg_at_10",
               "retrieved_files", "pack_tokens", "cumulative_evidence_tokens",
               "planning_tokens", "tool_call_count", "latency_ms"]
    per_task = {f"{t}::{m}": {"runs": len(g), **{f"mean_{k}": _mean([x[k] for x in g]) for k in metrics}}
                for (t, m), g in sorted(by_tm.items())}
    pairs = defaultdict(dict)
    for r in rows:
        pairs[r["paired_trial_id"]][r["method"]] = r
    pair_rows, incomplete = [], []
    for pid in sorted({r["paired_trial_id"] for r in runs}):
        m = pairs.get(pid, {})
        if "one_shot_rag" in m and "agent_directed" in m:
            a, b = m["one_shot_rag"], m["agent_directed"]
            pair_rows.append({"paired_trial_id": pid, "task_id": a["task_id"], "repetition": a["repetition"],
                              "f1_a": a["f1"], "f1_b": b["f1"], "f1_b_minus_a": b["f1"] - a["f1"],
                              "same_file_set": set(a["file_ranking"]) == set(b["file_ranking"])})
        else:
            incomplete.append(pid)
    tasks = sorted({r["task_id"] for r in rows})
    winners = {}
    for t in tasks:
        fa = per_task.get(f"{t}::one_shot_rag", {}).get("mean_f1")
        fb = per_task.get(f"{t}::agent_directed", {}).get("mean_f1")
        if fa is None or fb is None:
            winners[t] = "incomplete"
        else:
            winners[t] = "tie" if abs(fb - fa) < 1e-9 else ("B" if fb > fa else "A")
    agg = {}
    for meth in ("one_shot_rag", "agent_directed"):
        g = [r for r in rows if r["method"] == meth]
        TP, FP, FN = (sum(r[k] for r in g) for k in ("tp", "fp", "fn"))
        pp = TP / (TP + FP) if TP + FP else 0.0
        pr = TP / (TP + FN) if TP + FN else 0.0
        agg[meth] = {
            "runs": len(g),
            "macro_f1_over_tasks": _mean([per_task[f"{t}::{meth}"]["mean_f1"] for t in tasks if f"{t}::{meth}" in per_task]),
            "macro_precision_over_tasks": _mean([per_task[f"{t}::{meth}"]["mean_precision"] for t in tasks if f"{t}::{meth}" in per_task]),
            "macro_recall_over_tasks": _mean([per_task[f"{t}::{meth}"]["mean_recall"] for t in tasks if f"{t}::{meth}" in per_task]),
            "pooled_micro_precision": pp, "pooled_micro_recall": pr,
            "pooled_micro_f1": 2 * pp * pr / (pp + pr) if pp + pr else 0.0,
        }
    diffs = [p["f1_b_minus_a"] for p in pair_rows]
    return {
        "run_set": run_set, "annotation_set": set_name,
        "planned_runs": len(runs), "scored_runs": len(rows), "excluded_runs": excluded,
        "complete_pairs": len(pair_rows), "incomplete_pairs": incomplete,
        "per_run": rows, "per_task_method": per_task, "matched_pairs": pair_rows,
        "pair_diff_summary": {"n": len(diffs), "mean": _mean(diffs),
                              "positive": sum(d > 1e-9 for d in diffs),
                              "negative": sum(d < -1e-9 for d in diffs),
                              "zero": sum(abs(d) <= 1e-9 for d in diffs)},
        "task_winner_by_mean_f1": winners, "aggregate": agg,
        "authoritative": len(rows) == len(runs) and len(runs) > 0,
    }


def to_markdown(rep: dict) -> str:
    L = [f"# T1 evaluation — {rep['run_set']} vs `{rep['annotation_set']}`", "",
         f"Scored {rep['scored_runs']}/{rep['planned_runs']} runs; complete pairs {rep['complete_pairs']}; "
         f"authoritative: {rep['authoritative']}", ""]
    if rep["excluded_runs"]:
        L += ["Excluded (not verified): " + ", ".join(f"{e['trace_file']} ({e['verdict']})" for e in rep["excluded_runs"]), ""]
    L += ["| Task | Method | runs | P | R | F1 | Ess.R | MRR | nDCG@10 | files | plan tok | calls | latency ms |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda x: "—" if x is None else f"{x:.3f}"
    for k, v in rep["per_task_method"].items():
        t, m = k.split("::")
        L.append(f"| {t} | {'A' if m == 'one_shot_rag' else 'B'} | {v['runs']} | {f(v['mean_precision'])} | {f(v['mean_recall'])} | "
                 f"{f(v['mean_f1'])} | {f(v['mean_essential_recall'])} | {f(v['mean_mrr'])} | {f(v['mean_ndcg_at_10'])} | "
                 f"{f(v['mean_retrieved_files'])} | {f(v['mean_planning_tokens'])} | {f(v['mean_tool_call_count'])} | {f(v['mean_latency_ms'])} |")
    L += ["", "| Pair | F1 A | F1 B | B−A | same files |", "|---|---|---|---|---|"]
    for p in rep["matched_pairs"]:
        L.append(f"| {p['paired_trial_id']} | {p['f1_a']:.3f} | {p['f1_b']:.3f} | {p['f1_b_minus_a']:+.3f} | {p['same_file_set']} |")
    s = rep["pair_diff_summary"]
    L += ["", f"Pair differences: n={s['n']}, mean={f(s['mean'])}, +{s['positive']} / −{s['negative']} / 0={s['zero']}",
          f"Task winners (mean F1): {rep['task_winner_by_mean_f1']}", "", "Aggregate:", "```", json.dumps(rep["aggregate"], indent=2), "```"]
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=ROOT / "results" / "run_manifest.json")
    ap.add_argument("--traces-dir", type=Path, default=ROOT / "results" / "raw" / "traces")
    ap.add_argument("--run-set", required=True, choices=["main-v1.0", "pilot-v1.0"])
    ap.add_argument("--annotation-set", required=True, choices=list(GT_SETS))
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "processed")
    a = ap.parse_args()
    rep = evaluate(json.loads(a.manifest.read_text(encoding="utf-8")), a.traces_dir, a.run_set, a.annotation_set)
    stem = f"t1_eval__{a.run_set}__{a.annotation_set}"
    a.output_dir.mkdir(parents=True, exist_ok=True)
    (a.output_dir / f"{stem}.json").write_text(json.dumps(rep, indent=2) + "\n", encoding="utf-8")
    (a.output_dir / f"{stem}.md").write_text(to_markdown(rep), encoding="utf-8")
    print(f"scored {rep['scored_runs']}/{rep['planned_runs']} runs -> {a.output_dir / stem}.json/.md")
    if not rep["authoritative"]:
        print("NOT AUTHORITATIVE: some runs are missing or unverified; see excluded_runs.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

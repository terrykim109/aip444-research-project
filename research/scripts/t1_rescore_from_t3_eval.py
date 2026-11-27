#!/usr/bin/env python3
"""Rescore T3's per-run evaluation output against any ground-truth version.

Used because the raw traces were not transferred; T3 supplied his evaluator
outputs (results/processed/main_v1_eval.json, pilot_eval.json). Each per-run
row lists false_positives and false_negatives against the GT set it was scored
with, so the retrieved file SET is reconstructable exactly:

    retrieved = (GT_source - FN) | FP

Checks performed (any failure aborts):
  * reconstructed TP count == row tp, |retrieved| == row retrieved_files;
  * every run in the manifest's run set appears exactly once, and stop_reason,
    planning_tokens, tool_call_count, evidence_tokens, latency_ms match the
    committed run_manifest.json (the eval file itself is not hash-pinned).

Limits: file ORDER is not in T3's output, so MRR/nDCG cannot be computed;
per-call Method B behaviour needs the traces.

Usage:
  python scripts/t1_rescore_from_t3_eval.py --eval results/processed/main_v1_eval.json \
      --source-set t2_context_v1 --run-set main-v1.0 --target-set t1_reviewed_v1
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("t1_evaluate", ROOT / "scripts" / "t1_evaluate.py")
EV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(EV)  # type: ignore[union-attr]

MANIFEST_FIELDS = ("stop_reason", "planning_tokens", "tool_call_count", "evidence_tokens")


def reconstruct(row: dict, gt_src: dict) -> set[str]:
    g = set(gt_src["files"])
    fn = {EV.normalize_path(p) for p in row["false_negatives"]}
    fp = {EV.normalize_path(p) for p in row["false_positives"]}
    if not fn <= g:
        raise SystemExit(f"{row['paired_trial_id']}/{row['method']}: FN not in source GT")
    files = (g - fn) | fp
    if len(g - fn) != row["tp"] or len(files) != row["retrieved_files"] or len(fp) != row["fp"]:
        raise SystemExit(f"{row['paired_trial_id']}/{row['method']}: counts do not reconstruct")
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eval", type=Path, required=True)
    ap.add_argument("--source-set", required=True, choices=list(EV.GT_SETS))
    ap.add_argument("--run-set", required=True, choices=["main-v1.0", "pilot-v1.0"])
    ap.add_argument("--target-set", required=True, action="append", choices=list(EV.GT_SETS))
    ap.add_argument("--manifest", type=Path, default=ROOT / "results" / "run_manifest.json")
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "processed")
    a = ap.parse_args()
    src_eval = json.loads(a.eval.read_text(encoding="utf-8"))
    rows = src_eval["by_annotation_set"][a.source_set]["per_run"]
    manifest = {(r["paired_trial_id"], r["method"]): r for r in json.loads(a.manifest.read_text(encoding="utf-8"))["runs"]
                if r["run_set"] == a.run_set}
    seen = defaultdict(int)
    for r in rows:
        k = (r["paired_trial_id"], r["method"])
        seen[k] += 1
        m = manifest.get(k)
        if m is None:
            raise SystemExit(f"{k} not in manifest run set {a.run_set}")
        bad = {f: (m[f], r[f]) for f in MANIFEST_FIELDS if m[f] != r[f]}
        if abs(m["latency_ms"] - r["latency_ms"]) > 0.11:
            bad["latency_ms"] = (m["latency_ms"], r["latency_ms"])
        if bad:
            raise SystemExit(f"{k} disagrees with manifest: {bad}")
    if set(seen) != set(manifest) or any(v != 1 for v in seen.values()):
        raise SystemExit("eval rows do not cover the manifest run set exactly once")
    files_by_run = {}
    for r in rows:
        gt_src = EV.load_gt(a.source_set, r["task_id"])
        files_by_run[(r["paired_trial_id"], r["method"])] = (r, reconstruct(r, gt_src))
    out = {"source_eval": str(a.eval.resolve().relative_to(ROOT.resolve())).replace("\\", "/"), "source_set": a.source_set,
           "run_set": a.run_set, "checks": "reconstruction + manifest cross-check passed for all rows",
           "limitations": "no file order (no MRR/nDCG); not trace-verified (traces not transferred)",
           "by_target_set": {}}
    for tgt in a.target_set:
        per_run = []
        for (pid, meth), (r, files) in sorted(files_by_run.items()):
            gt = EV.load_gt(tgt, r["task_id"])
            s = EV.score(sorted(files), gt)
            for k in ("mrr", "ndcg_at_10", "file_ranking"):
                s.pop(k)
            per_run.append({"paired_trial_id": pid, "task_id": r["task_id"], "method": meth,
                            "repetition": r["repetition"], "stop_reason": r["stop_reason"],
                            "planning_tokens": r["planning_tokens"], "tool_call_count": r["tool_call_count"],
                            "latency_ms": r["latency_ms"], "files": sorted(files), **s})
        by_tm = defaultdict(list)
        for x in per_run:
            by_tm[(x["task_id"], x["method"])].append(x)
        means = {f"{t}::{m}": {k: sum(x[k] for x in g) / len(g) for k in ("precision", "recall", "f1", "essential_recall", "retrieved_files")}
                 for (t, m), g in sorted(by_tm.items())}
        pairs = defaultdict(dict)
        for x in per_run:
            pairs[x["paired_trial_id"]][x["method"]] = x
        diffs = [{"paired_trial_id": p, "f1_a": v["one_shot_rag"]["f1"], "f1_b": v["agent_directed"]["f1"],
                  "f1_b_minus_a": v["agent_directed"]["f1"] - v["one_shot_rag"]["f1"],
                  "same_file_set": v["one_shot_rag"]["files"] == v["agent_directed"]["files"],
                  "b_superset_of_a": set(v["one_shot_rag"]["files"]) <= set(v["agent_directed"]["files"])}
                 for p, v in sorted(pairs.items())]
        tasks = sorted({x["task_id"] for x in per_run})
        winners = {}
        for t in tasks:
            fa, fb = means[f"{t}::one_shot_rag"]["f1"], means[f"{t}::agent_directed"]["f1"]
            winners[t] = "tie" if abs(fa - fb) < 1e-9 else ("B" if fb > fa else "A")
        agg = {}
        for meth in ("one_shot_rag", "agent_directed"):
            g = [x for x in per_run if x["method"] == meth]
            TP, FP, FN = (sum(x[k] for x in g) for k in ("tp", "fp", "fn"))
            p, rr = TP / (TP + FP), TP / (TP + FN)
            agg[meth] = {"macro_f1": sum(means[f"{t}::{meth}"]["f1"] for t in tasks) / len(tasks),
                         "macro_precision": sum(means[f"{t}::{meth}"]["precision"] for t in tasks) / len(tasks),
                         "macro_recall": sum(means[f"{t}::{meth}"]["recall"] for t in tasks) / len(tasks),
                         "pooled_precision": p, "pooled_recall": rr, "pooled_f1": 2 * p * rr / (p + rr)}
        d = [x["f1_b_minus_a"] for x in diffs]
        # Method B: finalised (LLM-selected) vs fallback packs
        b = [x for x in per_run if x["method"] == "agent_directed"]
        grp = defaultdict(list)
        for x in b:
            grp["llm_selected" if x["stop_reason"] in ("evidence_sufficient", "no_new_relevant_evidence") else "fallback_all_charged"].append(x)
        b_pack = {k: {"runs": len(v), "mean_files": sum(x["retrieved_files"] for x in v) / len(v),
                      "mean_precision": sum(x["precision"] for x in v) / len(v),
                      "mean_recall": sum(x["recall"] for x in v) / len(v),
                      "mean_f1": sum(x["f1"] for x in v) / len(v)} for k, v in grp.items()}
        out["by_target_set"][tgt] = {
            "per_run": per_run, "per_task_method_means": means, "matched_pairs": diffs,
            "pair_diff_summary": {"n": len(d), "mean": sum(d) / len(d), "positive": sum(x > 1e-9 for x in d),
                                  "negative": sum(x < -1e-9 for x in d), "zero": sum(abs(x) <= 1e-9 for x in d)},
            "task_winner_by_mean_f1": winners, "aggregate": agg, "method_b_pack_type": b_pack}
    p = a.output_dir / f"t1_rescore__{a.run_set}.json"
    p.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for tgt, v in out["by_target_set"].items():
        print(f"\n## {a.run_set} vs {tgt}")
        for k, m in v["per_task_method_means"].items():
            print(f"  {k:55s} P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} essR={m['essential_recall']:.3f} files={m['retrieved_files']:.1f}")
        print("  pairs", v["pair_diff_summary"], "\n  winners", v["task_winner_by_mean_f1"])
        print("  agg", json.dumps(v["aggregate"]))
        print("  B pack type", json.dumps(v["method_b_pack_type"]))
        print("  same_file_set", [x["paired_trial_id"] for x in v["matched_pairs"] if x["same_file_set"]],
              "\n  B superset of A", sum(x["b_superset_of_a"] for x in v["matched_pairs"]), "/", len(v["matched_pairs"]))
    print("wrote", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

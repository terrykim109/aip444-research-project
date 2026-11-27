#!/usr/bin/env python3
"""Replay one completed A/B pair for the presentation demo (no API calls).

Reads two verified traces from results/raw/traces/, prints the shared task
prompt, Method A's single search result (files), Method B's tool-call
sequence (tool, arguments, files returned, tokens charged) and final pack,
then the offline file-level score of each pack. Nothing is re-run; the demo
only replays recorded experiment artifacts. Refuses to replay a trace whose
SHA-256 does not match results/run_manifest.json.

Usage:
  python scripts/t1_demo_replay.py --task-id pi_cli_mode_validation --repetition 1
         [--annotation-set t1_reviewed_v1] [--no-scores]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _mod(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # type: ignore[union-attr]
    return m


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--repetition", type=int, default=1)
    ap.add_argument("--annotation-set", default="t1_reviewed_v1")
    ap.add_argument("--no-scores", action="store_true", help="hide ground-truth scoring")
    ap.add_argument("--manifest", type=Path, default=ROOT / "results" / "run_manifest.json")
    ap.add_argument("--traces-dir", type=Path, default=ROOT / "results" / "raw" / "traces")
    a = ap.parse_args()
    ev, ver = _mod("t1_evaluate"), _mod("t1_verify_traces")
    manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    pid = f"{a.task_id}__r{a.repetition}"
    runs = {r["method"]: r for r in manifest["runs"] if r["paired_trial_id"] == pid}
    if set(runs) != {"one_shot_rag", "agent_directed"}:
        print(f"No complete pair {pid} in manifest.")
        return 1
    verdicts = {r["trace_file"]: r["verdict"] for r in ver.verify({"runs": list(runs.values())}, a.traces_dir)["runs"]}
    if any(v != "verified" for v in verdicts.values()):
        print(f"Cannot replay: trace verification failed {verdicts}")
        return 2
    ta, tb = (json.loads((a.traces_dir / runs[m]["trace_file"]).read_text(encoding="utf-8"))
              for m in ("one_shot_rag", "agent_directed"))
    gt = None if a.no_scores else ev.load_gt(a.annotation_set, a.task_id)
    mark = (lambda f: "") if gt is None else (lambda f: f"  [{gt['files'].get(f, 'not in GT')}]")
    print(f"=== Pair {pid}  (run set {runs['one_shot_rag']['run_set']}, config {runs['one_shot_rag']['config_hash']})")
    print("Task prompt (identical for both methods):")
    print(textwrap.fill(ta["task_prompt"], 100, initial_indent="  ", subsequent_indent="  "))
    print("\n--- Method A: one semantic search -> final pack")
    for f in ev.ranked_files(ta["evidence_pack"], ta.get("worktree_path")):
        print(f"  {f}{mark(f)}")
    print(f"  ({len(ta['evidence_pack'])} chunks, {ta.get('latency_ms', 0):.0f} ms, 0 LLM tokens)")
    print("\n--- Method B: agent-directed tool calls")
    for c in (tb.get("method_detail") or {}).get("tool_trace") or []:
        res = c.get("result") or {}
        files = sorted({ev.normalize_path(e['path'], tb.get('worktree_path')) for e in res.get("evidence") or []})
        tok = sum(int(e.get("token_count") or 0) for e in res.get("evidence") or [])
        args = json.dumps(c.get("arguments"))[:90]
        print(f"  #{c.get('call_index')} {c.get('tool_name')}({args}) ok={res.get('ok')} files={len(files)} tokens={tok}")
    print(f"  stop_reason={tb.get('stop_reason')}  planning_tokens={tb.get('planning_tokens')}  latency={tb.get('latency_ms', 0):.0f} ms")
    print("  Final pack:")
    for f in ev.ranked_files(tb["evidence_pack"], tb.get("worktree_path")):
        print(f"    {f}{mark(f)}")
    if gt is not None:
        print(f"\n--- Offline score vs {a.annotation_set} (evaluator-only labels)")
        for name, t in (("A", ta), ("B", tb)):
            s = ev.score(ev.ranked_files(t["evidence_pack"], t.get("worktree_path")), gt)
            print(f"  {name}: P={s['precision']:.2f} R={s['recall']:.2f} F1={s['f1']:.2f} essential-recall={s['essential_recall']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

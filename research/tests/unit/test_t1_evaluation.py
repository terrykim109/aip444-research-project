"""Synthetic-trace tests for T1's verifier, evaluator and Method B analysis.

No real run data is used or fabricated here: traces are tiny hand-made
fixtures in a temp directory, scored against a real reviewed GT file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


EV = _mod("t1_evaluate")
MB = _mod("t1_analyze_method_b")
TASK = "pi_cli_mode_validation"  # GT: args.ts (essential), args.test.ts, main.ts (supporting)
ARGS = "packages/coding-agent/src/cli/args.ts"
MAIN = "packages/coding-agent/src/main.ts"
OTHER = "packages/coding-agent/src/other.ts"


def _item(path, rank, eid, tok=10):
    return {"path": path, "rank": rank, "evidence_id": eid, "token_count": tok}


def _write(tmp: Path, method: str, pack, tool_trace=None, stop="completed"):
    trace = {"task_id": TASK, "method": method, "repetition": 1, "paired_trial_id": f"{TASK}__r1",
             "protocol_version": "main-v1.0", "snapshot_id": "s", "index_id": "i", "config_hash": "c",
             "stop_reason": stop, "errors": [], "evidence_pack": pack, "worktree_path": "C:\\wt",
             "evidence_tokens": 1, "planning_tokens": 0, "tool_call_count": 1, "latency_ms": 1.0,
             "method_detail": {"tool_trace": tool_trace or []}}
    name = f"{TASK}__r1__{method}.json"
    (tmp / name).write_text(json.dumps(trace), encoding="utf-8")
    run = {k: trace[k] for k in ("task_id", "method", "repetition", "paired_trial_id", "protocol_version",
                                 "config_hash", "stop_reason")}
    run.update(run_set="main-v1.0", snapshot_sha="s", index_build_id="i", status="completed",
               trace_file=name, trace_sha256=hashlib.sha256((tmp / name).read_bytes()).hexdigest())
    return run


def test_normalize_and_dedup():
    assert EV.normalize_path("C:\\wt\\packages\\a.ts", "C:\\wt") == "packages/a.ts"
    assert EV.normalize_path("./packages//a.ts") == "packages/a.ts"
    pack = [_item(ARGS, 2, "x"), _item(MAIN, 1, "y"), _item(ARGS, 3, "z")]
    assert EV.ranked_files(pack) == [MAIN, ARGS]


def test_scores_known_values():
    gt = EV.load_gt("t1_reviewed_v1", TASK)
    s = EV.score([OTHER, ARGS], gt)
    assert (s["tp"], s["fp"], s["fn"]) == (1, 1, 2)
    assert math.isclose(s["precision"], 0.5) and math.isclose(s["recall"], 1 / 3)
    assert math.isclose(s["f1"], 0.4)
    assert s["essential_recall"] == 1.0 and s["mrr"] == 0.5
    ideal = 2 + 1 / math.log2(3) + 1 / math.log2(4)
    assert math.isclose(s["ndcg_at_10"], (2 / math.log2(3)) / ideal)
    e = EV.score([], gt)
    assert e["f1"] == 0 and e["empty_pack"]


def test_end_to_end_verify_eval_and_b_analysis(tmp_path):
    ra = _write(tmp_path, "one_shot_rag", [_item(ARGS, 1, "a1")])
    calls = [
        {"call_index": 1, "tool_name": "semantic_search", "arguments": {"query": "q"},
         "result": {"ok": True, "evidence": [{"path": ARGS, "evidence_id": "a1", "token_count": 5}]}},
        {"call_index": 2, "tool_name": "grep", "arguments": {"pattern": "parseArgs"},
         "result": {"ok": True, "evidence": [{"path": "C:\\wt\\" + MAIN.replace('/', '\\'), "evidence_id": "m1", "token_count": 5},
                                              {"path": ARGS, "evidence_id": "a1", "token_count": 5}]}},
        {"call_index": 3, "tool_name": "read_file", "arguments": {"path": "x"},
         "result": {"ok": False, "message": "invalid path", "evidence": []}},
    ]
    rb = _write(tmp_path, "agent_directed", [_item(ARGS, 1, "a1"), _item(MAIN, 2, "m1")], calls, "evidence_sufficient")
    manifest = {"runs": [ra, rb]}
    assert _mod("t1_verify_traces").verify(manifest, tmp_path)["verdict_counts"] == {"verified": 2}
    rep = EV.evaluate(manifest, tmp_path, "main-v1.0", "t1_reviewed_v1")
    assert rep["authoritative"] and rep["complete_pairs"] == 1
    assert math.isclose(rep["matched_pairs"][0]["f1_a"], 0.5)
    assert math.isclose(rep["matched_pairs"][0]["f1_b"], 0.8)
    assert rep["task_winner_by_mean_f1"][TASK] == "B"
    gt = EV.load_gt("t1_reviewed_v1", TASK)
    trace_b = json.loads((tmp_path / rb["trace_file"]).read_text())
    res = MB.analyze_trace(trace_b, gt)
    assert res["tool_sequence"] == ["semantic_search", "grep", "read_file"]
    assert res["calls"][1]["new_relevant_files"] == [MAIN] and res["calls"][1]["duplicate_chunks"] == 1
    assert len(res["errors"]) == 1 and res["relevant_files_found_after_call_1"] == [MAIN]
    assert res["final_pack_source"].startswith("llm_selected")


def test_tampered_trace_is_not_scored(tmp_path):
    ra = _write(tmp_path, "one_shot_rag", [_item(ARGS, 1, "a1")])
    (tmp_path / ra["trace_file"]).write_text("{}", encoding="utf-8")
    rep = EV.evaluate({"runs": [ra]}, tmp_path, "main-v1.0", "t1_reviewed_v1")
    assert rep["scored_runs"] == 0 and rep["excluded_runs"][0]["verdict"] == "hash_mismatch"
    assert not rep["authoritative"]


def test_demo_replay_runs_on_verified_pair(tmp_path, capsys, monkeypatch):
    import sys
    ra = _write(tmp_path, "one_shot_rag", [_item(ARGS, 1, "a1")])
    ra_trace = json.loads((tmp_path / ra["trace_file"]).read_text())
    ra_trace["task_prompt"] = "demo prompt"
    (tmp_path / ra["trace_file"]).write_text(json.dumps(ra_trace))
    ra["trace_sha256"] = hashlib.sha256((tmp_path / ra["trace_file"]).read_bytes()).hexdigest()
    rb = _write(tmp_path, "agent_directed", [_item(MAIN, 1, "m1")], [], "evidence_sufficient")
    mf = tmp_path / "manifest.json"
    mf.write_text(json.dumps({"runs": [ra, rb]}))
    demo = _mod("t1_demo_replay")
    monkeypatch.setattr(sys, "argv", ["x", "--task-id", TASK, "--repetition", "1",
                                      "--manifest", str(mf), "--traces-dir", str(tmp_path)])
    assert demo.main() == 0
    out = capsys.readouterr().out
    assert "Method A" in out and "F1=" in out

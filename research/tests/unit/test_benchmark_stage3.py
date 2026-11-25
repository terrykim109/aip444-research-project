"""Stage 3: task/GT schema, snapshot consistency, isolation, span checks."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from repo_search.benchmark_loader import (
    AGENT_VISIBLE_TASK_FIELDS,
    assert_no_evaluator_leakage,
    iter_agent_tasks,
    load_agent_task,
    load_ground_truth,
    method_input_bundle,
)

ROOT = Path(__file__).resolve().parents[2]
GT_DIR = ROOT / "benchmark" / "ground_truth"
TASKS_PATH = ROOT / "benchmark" / "tasks.json"
CANDIDATES_PATH = ROOT / "benchmark" / "candidates.json"
SNAPSHOTS_PATH = ROOT / "benchmark" / "manifests" / "snapshots.json"

@pytest.fixture(scope="module")
def tasks_doc() -> dict:
    return json.loads(TASKS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def snapshots_by_task() -> dict:
    doc = json.loads(SNAPSHOTS_PATH.read_text(encoding="utf-8"))
    return {s["task_id"]: s for s in doc["snapshots"]}


@pytest.fixture(scope="module")
def candidates_doc() -> dict:
    return json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))


def test_agent_tasks_only_permitted_fields(tasks_doc: dict) -> None:
    tasks = iter_agent_tasks(tasks_doc)
    assert {t["task_id"] for t in tasks} == {
        # pilot-v1.0 tasks
        "pi_lazy_extension_loading",
        "pi_package_filtering",
        # main-v1.0 tasks (config/main_experiment.yaml)
        "pi_package_dedup_collisions",
        "pi_rpc_context_statistics",
        "pi_session_directory_config",
        "pi_cli_mode_validation",
    }
    for task in tasks:
        assert set(task.keys()) == AGENT_VISIBLE_TASK_FIELDS
        assert isinstance(task["task_prompt"], str) and len(task["task_prompt"]) > 20
        assert task["context_budget"] == 6000
        assert task["agent_call_limit"] == 5


def test_tasks_json_has_no_sha_or_gt_fields(tasks_doc: dict) -> None:
    blob = json.dumps(tasks_doc)
    for needle in (
        "40c256cccbce062f6af5f2cacb85d0ce1ab4224d",
        "bfa6862400d0aaa3ebf3c09a44a2479487f470f1",
        "ef1fc3103ee869244800f301993bd4952125db78",
        "dd838d0fe09db079dcf2f57bab1d79d4df5a0e4c",
        "ground_truth",
        "relevant_spans",
        "required_files",
    ):
        assert needle not in blob


@pytest.mark.parametrize(
    "task_id",
    ["pi_lazy_extension_loading", "pi_package_filtering"],
)
def test_method_input_isolation(task_id: str, tasks_doc: dict) -> None:
    payload = method_input_bundle(task_id, tasks_doc)
    assert set(payload["task"].keys()) == AGENT_VISIBLE_TASK_FIELDS
    assert "ground_truth" not in payload
    assert_no_evaluator_leakage(payload)
    # Loader must not attach GT even if available on disk
    _ = load_ground_truth(task_id)
    payload2 = method_input_bundle(task_id, tasks_doc)
    assert "files" not in payload2
    assert "required_files" not in payload2


@pytest.mark.parametrize(
    "task_id",
    ["pi_lazy_extension_loading", "pi_package_filtering"],
)
def test_ground_truth_schema_and_status(task_id: str, snapshots_by_task: dict) -> None:
    gt = load_ground_truth(task_id)
    assert gt["task_id"] == task_id
    assert gt["annotation_version"] == "1.0"
    assert gt["review_status"] == "preliminary_self_validated"
    assert gt["snapshot_sha"] == snapshots_by_task[task_id]["parent_sha"]
    assert isinstance(gt["required_files"], list) and gt["required_files"]
    assert isinstance(gt["relevant_symbols"], list)
    assert isinstance(gt["relevant_spans"], list)
    assert isinstance(gt["existing_tests"], list)
    assert isinstance(gt["target_added_tests"], list)
    assert isinstance(gt["annotation_notes"], list)
    assert "files" in gt

    for f in gt["files"]:
        assert f["relevance"] in {"essential", "supporting"}
        assert f["relevance_score"] in {1, 2}
        assert f["rationale"]
        assert f["path"]
        for span in f["line_spans"]:
            assert span["start_line"] >= 1
            assert span["end_line"] >= span["start_line"]


@pytest.mark.parametrize(
    "task_id",
    ["pi_lazy_extension_loading", "pi_package_filtering"],
)
def test_parent_snapshot_file_existence_and_spans(task_id: str, snapshots_by_task: dict) -> None:
    # Optional real-source check. Self-contained Git integrity tests live in
    # test_benchmark_integrity.py; the CLI validates all tasks without worktrees.
    from repo_search.snapshot_paths import resolve_worktree_path, verify_worktree
    if not os.environ.get("PI_WORKTREE_ROOT"):
        pytest.skip("set PI_WORKTREE_ROOT for real detached-parent integration checks")
    gt = load_ground_truth(task_id)
    snap = snapshots_by_task[task_id]
    root = resolve_worktree_path(snap)
    verify_worktree(root, snap["parent_sha"])

    for f in gt["files"]:
        path = root / f["path"]
        assert path.is_file(), f"annotated file missing on parent snapshot: {f['path']}"
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        n = len(lines)
        for span in f["line_spans"]:
            assert span["end_line"] <= n, (
                f"{f['path']} span {span} exceeds file length {n}"
            )

    for path in gt.get("target_added_files_not_retrievable", []):
        assert not (root / path).exists(), (
            f"target-added file unexpectedly present on parent: {path}"
        )


@pytest.mark.parametrize(
    "task_id",
    ["pi_lazy_extension_loading", "pi_package_filtering"],
)
def test_relevance_labels_and_required_subset(task_id: str) -> None:
    gt = load_ground_truth(task_id)
    by_path = {f["path"]: f for f in gt["files"]}
    for req in gt["required_files"]:
        assert by_path[req]["relevance"] == "essential"
    essentials = [f for f in gt["files"] if f["relevance"] == "essential"]
    assert essentials, "need at least one essential file"


def test_candidate_e_resolved_without_substitution(candidates_doc: dict, snapshots_by_task: dict) -> None:
    e = next(c for c in candidates_doc["primary_candidates"] if c["letter_id"] == "E")
    assert e["validation_status"] == "verified"
    assert e["target_commit"].startswith("37067e0")
    assert e["verified_target_sha"] == snapshots_by_task[e["task_id"]]["target_sha"]
    assert e["verified_parent_sha"].startswith("4860665")


def test_pilot_task_validation_statuses(candidates_doc: dict) -> None:
    for letter in ("A", "B"):
        c = next(x for x in candidates_doc["primary_candidates"] if x["letter_id"] == letter)
        assert c["snapshot_verification_status"] == "verified"
        assert c["task_validation_status"] == "preliminary_self_validated"
        assert c["benchmark_acceptance_status"] == "pilot_accepted_preliminary"


def test_load_agent_task_helper() -> None:
    t = load_agent_task("pi_lazy_extension_loading")
    assert t["task_id"] == "pi_lazy_extension_loading"

"""Shared orchestration for Method A / Method B single runs (not bulk Stage 7 trials)."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from repo_search.benchmark_loader import assert_no_evaluator_leakage, method_input_bundle
from repo_search.chat_client import (
    DEFAULT_MAX_COMPLETION_TOKENS,
    DEFAULT_PRIMARY_CHAT_MODEL,
    OpenRouterChatClient,
)
from repo_search.embeddings import (
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingCache,
    OpenRouterEmbedder,
)
from repo_search.evidence import EvidenceLedger
from repo_search.method_a import MethodAResult, run_method_a
from repo_search.method_b import MethodBResult, run_method_b
from repo_search.protocol_config import load_experiment_config, research_root
from repo_search.repo_tools import SnapshotToolEnvironment
from repo_search.retriever import SemanticRetriever
from repo_search.traces import default_trace_dir, write_trace
from repo_search.vector_index import NumpyVectorIndex

MethodName = Literal["one_shot_rag", "agent_directed"]


@dataclass(frozen=True)
class SnapshotContext:
    task_id: str
    snapshot_sha: str
    worktree_path: Path
    index_dir: Path
    index_build_id: str


def load_snapshot_context(task_id: str) -> SnapshotContext:
    manifest = json.loads(
        (research_root() / "benchmark" / "manifests" / "snapshots.json").read_text(
            encoding="utf-8"
        )
    )
    for snap in manifest.get("snapshots") or []:
        if snap.get("task_id") != task_id:
            continue
        if snap.get("verification_status") != "verified":
            raise ValueError(f"snapshot not verified for {task_id}")
        sha = snap["parent_sha"]
        wt = Path(snap["worktree_path"])
        index_dir = research_root() / "artifacts" / "indexes" / sha[:12]
        if not (index_dir / "meta.json").exists():
            raise FileNotFoundError(f"missing Stage 5 index at {index_dir}")
        meta = json.loads((index_dir / "meta.json").read_text(encoding="utf-8"))
        return SnapshotContext(
            task_id=task_id,
            snapshot_sha=sha,
            worktree_path=wt,
            index_dir=index_dir,
            index_build_id=str(meta.get("index_build_id") or ""),
        )
    raise KeyError(f"unknown or non-pilot task_id: {task_id}")


def _config_hash(cfg: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "protocol_version": (cfg.get("meta") or {}).get("protocol_version"),
            "budgets": cfg.get("budgets"),
            "retrieval": {
                k: (cfg.get("retrieval") or {}).get(k)
                for k in (
                    "embedding_model",
                    "tokenizer",
                    "top_k",
                    "max_tokens_per_search",
                )
            },
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_retriever(*, index_dir: Path, embedder: OpenRouterEmbedder) -> SemanticRetriever:
    index = NumpyVectorIndex.load(index_dir)
    cfg = load_experiment_config()
    top_k = int((cfg.get("retrieval") or {}).get("top_k") or 10)
    max_tokens = int((cfg.get("retrieval") or {}).get("max_tokens_per_search") or 6000)
    return SemanticRetriever(
        index=index,
        embedder=embedder,
        default_top_k=top_k,
        default_max_tokens=max_tokens,
    )


def run_trial(
    *,
    task_id: str,
    method: MethodName,
    repetition: int = 1,
    persist_trace: bool = True,
    chat_client: OpenRouterChatClient | None = None,
    embedder: OpenRouterEmbedder | None = None,
    dry_run_chat: Any | None = None,
    protocol_version: str = "pilot-v1.0",
) -> dict[str, Any]:
    """
    Execute one method once for a task. Does not loop the 12 pilot records.
    Ground truth is never loaded into the method path.
    """
    cfg = load_experiment_config()
    bundle = method_input_bundle(task_id)
    assert_no_evaluator_leakage(bundle)
    task = bundle["task"]
    prompt = task["task_prompt"]
    ctx = load_snapshot_context(task_id)
    paired_trial_id = f"{task_id}__r{repetition}"

    owned_embedder = embedder is None
    emb = embedder or OpenRouterEmbedder(
        cache=EmbeddingCache(research_root() / "artifacts" / "embedding_cache"),
        model=DEFAULT_EMBEDDING_MODEL,
    )
    owned_chat = False
    chat = chat_client or dry_run_chat
    if method == "agent_directed" and chat is None:
        chat = OpenRouterChatClient(
            model=DEFAULT_PRIMARY_CHAT_MODEL,
            temperature=0,
            max_completion_tokens=int(
                ((cfg.get("models") or {}).get("agent_llm") or {}).get("max_output_tokens")
                or DEFAULT_MAX_COMPLETION_TOKENS
            ),
        )
        owned_chat = True

    t0 = time.perf_counter()
    try:
        retriever = build_retriever(index_dir=ctx.index_dir, embedder=emb)
        if method == "one_shot_rag":
            result_a: MethodAResult = run_method_a(
                task_prompt=prompt,
                retriever=retriever,
                top_k=int((cfg.get("retrieval") or {}).get("top_k") or 10),
                max_tokens=int((cfg.get("budgets") or {}).get("evidence_token_budget") or 6000),
            )
            method_payload = result_a.to_dict()
            stop_reason = result_a.stop_reason
            tool_call_count = result_a.tool_call_count
            planning_tokens = 0
            evidence_tokens = result_a.evidence_pack.token_count
            evidence_pack = result_a.evidence_pack.to_dict()["items"]
        else:
            assert chat is not None
            ledger = EvidenceLedger(
                evidence_budget=int(
                    (cfg.get("budgets") or {}).get("evidence_token_budget") or 6000
                )
            )
            tools = SnapshotToolEnvironment(
                worktree=ctx.worktree_path,
                snapshot_sha=ctx.snapshot_sha,
                retriever=retriever,
                ledger=ledger,
                max_tool_calls=int(
                    (cfg.get("budgets") or {}).get("agent_tool_call_limit") or 5
                ),
                top_k=int((cfg.get("retrieval") or {}).get("top_k") or 10),
                max_tokens_per_search=int(
                    (cfg.get("retrieval") or {}).get("max_tokens_per_search") or 6000
                ),
            )
            result_b: MethodBResult = run_method_b(
                task_prompt=prompt,
                tools=tools,
                chat=chat,
            )
            method_payload = result_b.to_dict()
            stop_reason = result_b.stop_reason
            tool_call_count = result_b.tool_call_count
            planning_tokens = result_b.planning_tokens
            evidence_tokens = result_b.ledger.cumulative_evidence_tokens
            evidence_pack = result_b.evidence_pack.to_dict()["items"]

        record = {
            "record_type": "experiment_trial",
            "stage": "6",
            "protocol_version": protocol_version,
            "task_id": task_id,
            "paired_trial_id": paired_trial_id,
            "method": method,
            "repetition": repetition,
            "snapshot_id": ctx.snapshot_sha,
            "index_id": ctx.index_build_id,
            "index_dir": str(ctx.index_dir),
            "worktree_path": str(ctx.worktree_path),
            "task_prompt": prompt,
            "config_hash": _config_hash(cfg),
            "embedding_model": DEFAULT_EMBEDDING_MODEL,
            "evidence_pack": evidence_pack,
            "evidence_tokens": evidence_tokens,
            "planning_tokens": planning_tokens,
            "tool_call_count": tool_call_count,
            "latency_ms": (time.perf_counter() - t0) * 1000,
            "stop_reason": stop_reason,
            "method_detail": method_payload,
            "implementation_origin": "independent",
            "errors": method_payload.get("errors") or [],
        }
        if persist_trace:
            path = write_trace(
                record,
                directory=default_trace_dir(research_root()),
                filename=f"{paired_trial_id}__{method}.json",
            )
            record["trace_path"] = str(path)
        return record
    finally:
        if owned_embedder:
            emb.close()
        if owned_chat and isinstance(chat, OpenRouterChatClient):
            chat.close()

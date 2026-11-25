"""Build deterministic corpora and NumPy vector indexes for pilot snapshots."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

from repo_search.chunking import (
    CHUNKER_VERSION,
    DEFAULT_MAX_CHUNK_TOKENS,
    DEFAULT_OVERLAP_TOKENS,
    DEFAULT_TOKENIZER,
    CodeChunk,
    chunk_file,
    get_encoder,
)
from repo_search.corpus_scan import scan_repository
from repo_search.embeddings import (
    DEFAULT_EMBEDDING_MODEL,
    EmbeddingCache,
    EmbeddingUsage,
    OpenRouterEmbedder,
    usage_to_dict,
)
from repo_search.protocol_config import research_root
from repo_search.vector_index import NumpyVectorIndex

CHUNKING_CONFIG = {
    "max_chunk_tokens": DEFAULT_MAX_CHUNK_TOKENS,
    "overlap_tokens": DEFAULT_OVERLAP_TOKENS,
    "tokenizer": DEFAULT_TOKENIZER,
    "strategy": "symbol_aware_with_line_fallback",
}


@dataclass
class CorpusStats:
    snapshot_sha: str
    task_id: str
    worktree_path: str
    files_scanned: int
    files_excluded_notes: int
    files_chunked: int
    total_chunks: int
    total_chunk_tokens: int
    embedding_usage: dict[str, int]
    embedding_cached: int
    embedding_fetched: int
    embedding_dimensions: int
    embedding_model: str
    index_build_id: str
    index_dir: str
    index_size_bytes: int
    build_seconds: float
    chunker_version: str
    chunking: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_index_build_id(
    *,
    snapshot_sha: str,
    embedding_model: str,
    dimensions: int,
    chunking: dict[str, Any],
    corpus_fingerprint: str,
) -> str:
    raw = json.dumps(
        {
            "snapshot_sha": snapshot_sha,
            "embedding_model": embedding_model,
            "dimensions": dimensions,
            "chunking": chunking,
            "chunker_version": CHUNKER_VERSION,
            "corpus_fingerprint": corpus_fingerprint,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"idx-{snapshot_sha[:12]}-{digest}"


def corpus_fingerprint(chunks: list[CodeChunk]) -> str:
    h = hashlib.sha256()
    for c in chunks:
        h.update(f"{c.path}|{c.start_line}|{c.end_line}|{c.content_hash}\n".encode())
    return h.hexdigest()


def build_chunks_for_snapshot(
    *,
    root: Path,
    snapshot_sha: str,
    max_chunk_tokens: int = DEFAULT_MAX_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
    tokenizer_name: str = DEFAULT_TOKENIZER,
) -> tuple[list[CodeChunk], list[str], int]:
    files, excluded = scan_repository(root)
    encoder = get_encoder(tokenizer_name)
    chunks: list[CodeChunk] = []
    files_chunked = 0
    for f in files:
        file_chunks = chunk_file(
            abs_path=f.abs_path,
            rel_path=f.path,
            snapshot_sha=snapshot_sha,
            max_chunk_tokens=max_chunk_tokens,
            overlap_tokens=overlap_tokens,
            tokenizer_name=tokenizer_name,
            encoder=encoder,
        )
        if file_chunks:
            files_chunked += 1
            chunks.extend(file_chunks)
    return chunks, excluded, files_chunked


def default_index_dir(snapshot_sha: str, artifacts_root: Path | None = None) -> Path:
    base = Path(artifacts_root) if artifacts_root is not None else (research_root() / "artifacts")
    return base / "indexes" / snapshot_sha[:12]


def build_snapshot_index(
    *,
    worktree: Path,
    snapshot_sha: str,
    task_id: str,
    embedder: OpenRouterEmbedder,
    index_dir: Path | None = None,
    dry_run_chunks_only: bool = False,
) -> CorpusStats:
    t0 = time.perf_counter()
    worktree = Path(worktree)
    chunks, excluded, files_chunked = build_chunks_for_snapshot(
        root=worktree,
        snapshot_sha=snapshot_sha,
    )
    if not chunks:
        raise RuntimeError(f"No chunks produced for {snapshot_sha}")

    fp = corpus_fingerprint(chunks)
    out_dir = index_dir or default_index_dir(snapshot_sha)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Persist chunk manifest before embeddings for auditability
    chunks_path = out_dir / "chunks_manifest.jsonl"
    with chunks_path.open("w", encoding="utf-8") as fh:
        for c in chunks:
            fh.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")

    scan_report = {
        "snapshot_sha": snapshot_sha,
        "task_id": task_id,
        "worktree": str(worktree),
        "files_included_estimate": files_chunked,
        "exclusion_notes_count": len(excluded),
        "exclusion_notes_sample": excluded[:50],
        "total_chunks": len(chunks),
        "chunking": CHUNKING_CONFIG,
        "chunker_version": CHUNKER_VERSION,
        "corpus_fingerprint": fp,
    }
    (out_dir / "scan_report.json").write_text(
        json.dumps(scan_report, indent=2), encoding="utf-8"
    )

    if dry_run_chunks_only:
        build_id = make_index_build_id(
            snapshot_sha=snapshot_sha,
            embedding_model=embedder.model,
            dimensions=0,
            chunking=CHUNKING_CONFIG,
            corpus_fingerprint=fp,
        )
        return CorpusStats(
            snapshot_sha=snapshot_sha,
            task_id=task_id,
            worktree_path=str(worktree),
            files_scanned=files_chunked,
            files_excluded_notes=len(excluded),
            files_chunked=files_chunked,
            total_chunks=len(chunks),
            total_chunk_tokens=sum(c.token_count for c in chunks),
            embedding_usage=usage_to_dict(EmbeddingUsage()),
            embedding_cached=0,
            embedding_fetched=0,
            embedding_dimensions=0,
            embedding_model=embedder.model,
            index_build_id=build_id,
            index_dir=str(out_dir),
            index_size_bytes=0,
            build_seconds=time.perf_counter() - t0,
            chunker_version=CHUNKER_VERSION,
            chunking=CHUNKING_CONFIG,
        )

    texts = [c.text for c in chunks]
    hashes = [c.content_hash for c in chunks]
    result = embedder.embed_texts(
        texts,
        snapshot_sha=snapshot_sha,
        content_hashes=hashes,
    )
    build_id = make_index_build_id(
        snapshot_sha=snapshot_sha,
        embedding_model=result.model,
        dimensions=result.dimensions,
        chunking=CHUNKING_CONFIG,
        corpus_fingerprint=fp,
    )
    index = NumpyVectorIndex.build(
        chunk_objs=chunks,
        embeddings=result.vectors,
        snapshot_sha=snapshot_sha,
        embedding_model=result.model,
        tokenizer=DEFAULT_TOKENIZER,
        chunking=CHUNKING_CONFIG,
        index_build_id=build_id,
        chunker_version=CHUNKER_VERSION,
    )
    index.save(out_dir)
    size = index.size_bytes_on_disk(out_dir)

    usage_path = out_dir / "embedding_usage.json"
    usage_payload = {
        "phase": "corpus_indexing",
        "shared_preparation_cost": True,
        "not_assigned_to_method": True,
        "snapshot_sha": snapshot_sha,
        "task_id": task_id,
        "model": result.model,
        "dimensions": result.dimensions,
        "usage": usage_to_dict(result.usage),
        "cached_count": result.cached_count,
        "fetched_count": result.fetched_count,
        "index_build_id": build_id,
    }
    usage_path.write_text(json.dumps(usage_payload, indent=2), encoding="utf-8")

    stats = CorpusStats(
        snapshot_sha=snapshot_sha,
        task_id=task_id,
        worktree_path=str(worktree),
        files_scanned=files_chunked,
        files_excluded_notes=len(excluded),
        files_chunked=files_chunked,
        total_chunks=len(chunks),
        total_chunk_tokens=sum(c.token_count for c in chunks),
        embedding_usage=usage_to_dict(result.usage),
        embedding_cached=result.cached_count,
        embedding_fetched=result.fetched_count,
        embedding_dimensions=result.dimensions,
        embedding_model=result.model,
        index_build_id=build_id,
        index_dir=str(out_dir),
        index_size_bytes=size,
        build_seconds=time.perf_counter() - t0,
        chunker_version=CHUNKER_VERSION,
        chunking=CHUNKING_CONFIG,
    )
    (out_dir / "build_stats.json").write_text(
        json.dumps(stats.to_dict(), indent=2), encoding="utf-8"
    )
    return stats


def load_pilot_snapshot_specs(
    task_ids: Sequence[str] | None = None,
) -> list[dict[str, str]]:
    """Default: verified pilots. With task_ids: those verified tasks instead
    (main-experiment builds); still requires worktree_path and parent_sha."""
    manifest = research_root() / "benchmark" / "manifests" / "snapshots.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    out: list[dict[str, str]] = []
    for snap in data.get("snapshots") or []:
        if task_ids is not None:
            if snap.get("task_id") not in task_ids:
                continue
        elif snap.get("pilot_status") != "pilot":
            continue
        if snap.get("verification_status") != "verified":
            continue
        wt = snap.get("worktree_path")
        sha = snap.get("parent_sha")
        tid = snap.get("task_id")
        if not wt or not sha or not tid:
            continue
        out.append({"task_id": tid, "snapshot_sha": sha, "worktree_path": wt})
    return out


def build_all_pilot_indexes(
    *,
    embedder: OpenRouterEmbedder | None = None,
    artifacts_root: Path | None = None,
    dry_run_chunks_only: bool = False,
    task_ids: Sequence[str] | None = None,
) -> list[CorpusStats]:
    artifacts_base = Path(artifacts_root) if artifacts_root is not None else (
        research_root() / "artifacts"
    )
    cache_root = artifacts_base / "embedding_cache"
    owned = embedder is None
    emb = embedder or OpenRouterEmbedder(
        cache=EmbeddingCache(cache_root),
        model=DEFAULT_EMBEDDING_MODEL,
    )
    try:
        stats_list: list[CorpusStats] = []
        for spec in load_pilot_snapshot_specs(task_ids):
            idx_dir = default_index_dir(spec["snapshot_sha"], artifacts_base)
            stats = build_snapshot_index(
                worktree=Path(spec["worktree_path"]),
                snapshot_sha=spec["snapshot_sha"],
                task_id=spec["task_id"],
                embedder=emb,
                index_dir=idx_dir,
                dry_run_chunks_only=dry_run_chunks_only,
            )
            stats_list.append(stats)
        artifacts_base.mkdir(parents=True, exist_ok=True)
        (artifacts_base / "corpus_build_summary.json").write_text(
            json.dumps([s.to_dict() for s in stats_list], indent=2),
            encoding="utf-8",
        )
        return stats_list
    finally:
        if owned:
            emb.close()

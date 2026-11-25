#!/usr/bin/env python3
"""Build Stage 5 corpora and NumPy indexes for both pilot snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load_dotenv(path: Path) -> None:
    import os

    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chunks-only",
        action="store_true",
        help="Scan and chunk only; skip OpenRouter embeddings and index write.",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=None,
        help="Artifacts root (default: research/artifacts).",
    )
    parser.add_argument(
        "--task-id",
        action="append",
        dest="task_ids",
        help="Build these verified tasks instead of the pilots (repeatable). "
        "Requires worktree_path set in the manifest (prepare_worktrees --write-paths).",
    )
    args = parser.parse_args()
    _load_dotenv(ROOT / ".env")

    from repo_search.corpus_build import build_all_pilot_indexes
    from repo_search.embeddings import (
        DEFAULT_EMBEDDING_MODEL,
        EmbeddingCache,
        OpenRouterEmbedder,
        resolve_openrouter_api_key,
    )

    artifacts = args.artifacts or (ROOT / "artifacts")
    if args.chunks_only:
        # Dummy embedder unused for API when chunks-only
        embedder = OpenRouterEmbedder(
            api_key="unused",
            model=DEFAULT_EMBEDDING_MODEL,
            cache=None,
        )
        stats = build_all_pilot_indexes(
            embedder=embedder,
            artifacts_root=artifacts,
            dry_run_chunks_only=True,
            task_ids=args.task_ids,
        )
        embedder.close()
    else:
        if not resolve_openrouter_api_key():
            print(
                "ERROR: OPENROUTER_API_KEY (or LLM_API_KEY) is not set. "
                "Use --chunks-only to build chunk manifests without embeddings.",
                file=sys.stderr,
            )
            return 1
        cache = EmbeddingCache(artifacts / "embedding_cache")
        with OpenRouterEmbedder(cache=cache, model=DEFAULT_EMBEDDING_MODEL) as emb:
            if emb.model != DEFAULT_EMBEDDING_MODEL:
                print(
                    f"ERROR: refusing silent model substitution; got {emb.model}",
                    file=sys.stderr,
                )
                return 1
            stats = build_all_pilot_indexes(
                embedder=emb,
                artifacts_root=artifacts,
                dry_run_chunks_only=False,
                task_ids=args.task_ids,
            )

    print(json.dumps([s.to_dict() for s in stats], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

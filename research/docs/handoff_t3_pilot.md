# T3 Handoff — Integration, Validation, and Pilot Status

**Workstream:** T3 — Integration, Validation, and Experiment Execution
**Author:** Arman Ataeipour
**Date:** 2026-11-24
**Branch:** `t3/experiment-integration` (based on central `main` @ `54de01a`)
**Protocol:** `pilot-v1.0` (frozen; nothing in this delivery changes it)

This document records what was independently verified on a second machine, the
disposition of prior contributions, and the exact state of the pilot. Nothing
below is claimed beyond what was actually executed.

---

## 1. Repository findings (verified against the repo, not logs)

| Claim | Verified? | Evidence |
|---|---|---|
| T0 core implementation complete through Stage 6 | **Yes** | All Stage 1–6 modules present (`src/repo_search/`: methods, orchestrator, retriever, embeddings, index, tools, traces); unit suite passes (§4) |
| T2 context-engineering contribution present | **Yes** | Merged via PR #1 (`t2/context-engineering`): 8-task set `benchmark/task_sets/t2_context_v1.json`, ground truth `benchmark/ground_truth/t2_context_v1/`, reviews under `benchmark/reviews/t2_context_v1/`, `scripts/prepare_worktrees.py`, `scripts/validate_benchmark.py` |
| T2's separate RAG implementation | **Not present** (consistent with "will not be delivered") — Stage 5 retriever is the only retrieval backend in the repo |
| T0 Stage 5 retrieval is the canonical baseline | **Yes** | `retriever.py` / `embeddings.py` / `vector_index.py` unchanged on `main`; no competing implementation exists |
| Experiment runs exist | **Yes (as of this delivery)** | At inspection time `results/raw/` was empty — no runs had ever been executed. The 12 pilot runs were then executed as part of this T3 work (§4) |
| Evaluator (file-level P/R/F1) exists | **Added in this delivery** | No evaluator existed; `scripts/evaluate_pilot.py` added as a minimal T3 computation. T1's independent evaluation remains authoritative (§8) |

### Method compliance (code inspection)

- **Method A** (`method_a.py`): exactly one `retriever.search()` call, query is the
  exact task prompt (`query_unchanged: true` recorded in trace), zero LLM calls.
- **Method B** (`method_b.py`): tool-call limit enforced with
  `call_limit_reached` stop reason; the initial `semantic_search` counts toward
  the limit of 5; evidence budget tracked cumulatively.
- **Ground-truth isolation** (`benchmark_loader.py`): GT loads through a separate
  evaluator-only function; `method_input_bundle` content is screened for
  leakage markers (diff headers, commit URLs, "ground truth").

---

## 2. Arman's prior contribution (PR #2) — audit and disposition

**What it is:** branch `t1/semantic-retrieval` → PR #2
(https://github.com/terrykim109/aip444-research-project/pull/2), commit
`dea0d1f`. Adds `scripts/search_index.py` (search CLI),
`src/repo_search/search_cli.py` (helpers + embedder/index model-mismatch
guard), `tests/unit/test_retrieval_t1.py` (7 smoke tests),
`docs/retrieval_backend_notes.md`, and log updates.

**Audit performed:**

- Confirmed the branch touches **zero lines** of the Stage 5 retrieval stack or
  frozen protocol — it only adds parallel modules, tests, and docs.
- Test verification: on that branch, `python -m pytest tests/unit -q` →
  **106 passed, 2 skipped** (reproduced in-session). On `main` (without it):
  **99 passed, 2 skipped** — so the 7 added tests account exactly for the delta.
- The claim "no live API calls" is accurate: its tests use fake embedders; the
  CLI requires a key only at runtime.

**Disposition: KEEP, pending review as its own PR.** It is compatible with this
branch (no file conflicts in code; the two log files will append-merge
trivially). It is *not* duplicated or rolled into `t3/experiment-integration`,
so reviewers can evaluate each contribution separately. Nothing in the T3 work
depends on it.

---

## 3. Operational validation performed on this machine (2026-11-24)

Environment: Windows 11, Python 3.14, fresh venv, `pip install -e ".[dev]"`.
Pi upstream cloned from `https://github.com/earendil-works/pi` to a local path
(`--no-checkout`), worktrees under a separate local root.

| Check | Command | Result |
|---|---|---|
| Snapshot SHA verification, all 8 candidates | `scripts/verify_benchmark.py --repo-path <pi-clone> --dry-run` | **8/8 verified**, exit 0 (A–H incl. resolved Candidate E) |
| Pilot worktrees at pinned parents | `scripts/prepare_worktrees.py --repo-path <pi-clone> --worktree-root <root>` | **passed** — both pilots created detached + clean; HEAD == parent SHA; same Git object store |
| Offline benchmark/GT structural validation | `scripts/validate_benchmark.py --repo-path <pi-clone>` | **passed** — 8 tasks, 34 file judgments, 49 source spans, all `structural_validation: passed`; human relevance review `pending_student_and_peer_review` |
| Deterministic corpus reproduction | `scripts/build_corpus_indexes.py --chunks-only` | **Exact match** with Stage 5 record: lazy 1,787 files / 14,964 chunks; packages 564 files / 3,992 chunks |
| Unit tests (this branch / `main`) | `python -m pytest tests/unit -q` | **99 passed, 2 skipped** (2 skips pre-existing, unrelated) |

### Finding: Candidate E requires fetch-by-SHA

`pi_network_retry` target `37067e0…` and parent `4860665…` are **not reachable
from any upstream branch/tag** — a fresh clone does not contain them, and
`validate_benchmark.py` fails with `git cat-file … bad file` until you run:

```powershell
git -C <pi-clone> fetch origin 37067e0166dbbcd9362797d84ab44c6f98e6cc40
```

After that explicit fetch, both objects exist and all validation passes. This
confirms T2's "resolved without substitution" claim (the commits are genuine
GitHub objects in the Pi repository network) **but** reproduction on any new
machine needs this extra step. Recorded as a benchmark limitation; if Candidate
E is used in a main experiment, the fetch step must be part of the setup
procedure.

### Note: manifest `worktree_path` is machine-local

`benchmark/manifests/snapshots.json` records the original EXP machine's
worktree paths. `prepare_worktrees.py --write-paths` rewrites them to verified
local paths; this was done locally for the corpus build and then **reverted**
before commit so the committed manifest is unchanged. Every runner must
re-run `--write-paths` locally before building indexes or running methods.

---

## 4. Pilot status: **EXECUTED — 12/12 runs completed (2026-11-24)**

Per the frozen protocol: 2 tasks × 2 methods × 3 repetitions = **12 runs / 6
matched pairs**, evidence budget 6,000 tokens, top-k 10, Method B limit 5 tool
calls, temperature 0, primary model `openai/gpt-6-luna`, prompt
`pilot-v1.0-agent-system-1`.

After an API key was provided, the full prerequisite chain was completed live
on this machine: embedding probe passed (1536 dims, correct model), both
indexes built (`idx-bfa6862400d0-…`, `idx-dd838d0fe09d-…`), index smoke
validation passed, chat probe returned `openai/gpt-6-luna` live.

### Run record

- **12 of 12 runs completed, exit 0; zero failures, zero retries, zero
  fabrications.** All 6 matched pairs complete.
- All 12 traces share one config hash (`46b0be2d77a99062`) — identical frozen
  configuration; each task used its own correct snapshot index.
- Protocol compliance observed in traces: Method A exactly 1 tool call and
  `stop=completed` in all 6 runs with identical evidence packs per task
  (deterministic, as designed); Method B used 4–5 tool calls (never >5), stop
  reasons `evidence_budget_exhausted` ×2, `evidence_sufficient` ×2,
  `call_limit_reached` ×2; evidence budgets never exceeded 6,000 tokens.
- Resource use: Method A mean latency ~0.1 s, 0 planning tokens; Method B mean
  latency ~4.3 s, planning tokens 2,192–7,671 per run. Total API spend for the
  entire session (probes + indexing + 12 runs) ≈ **$0.13 USD**.
- Traces: `results/raw/traces/{task}__r{rep}__{method}.json` + `runs.jsonl`
  (gitignored; preserved locally, share with T1 out-of-band).

### Preliminary file-level results (T3 computation; T1's independent evaluation is authoritative)

Computed with `scripts/evaluate_pilot.py` from the actual traces, against each
ground-truth set **separately** (both sets currently
`preliminary_self_validated`; output: `results/processed/pilot_eval.json`).

Mean over 3 repetitions, **preliminary (EXP) GT set**:

| Task | Method | Precision | Recall | F1 |
|---|---|---|---|---|
| `pi_lazy_extension_loading` | A (one-shot) | 0.167 | 0.333 | 0.222 |
| `pi_lazy_extension_loading` | B (agent) | 0.444 | 0.333 | **0.315** |
| `pi_package_filtering` | A (one-shot) | 0.667 | 0.400 | **0.500** |
| `pi_package_filtering` | B (agent) | 0.462 | 0.400 | 0.406 |

Matched-pair F1 differences (B − A), preliminary GT: `+0.000, +0.000, +0.278`
(lazy r1–r3); `−0.214, +0.100, −0.167` (packages r1–r3). The
`t2_context_v1` GT set gives the same qualitative picture (B better on lazy,
A better or equal on packages).

**Honest interpretation (exploratory only, n=2 tasks):** neither method
dominates. Method B beat Method A on the lazy-extension task (higher precision;
one rep stopped early with a single highly relevant file), while Method A was
better on the package-filtering task, where Method B's extra searches added
false-positive files. Method B is also ~40× slower and spends thousands of
planning tokens per run. No statistical significance is claimed or claimable
from 6 pairs.

### Reproduction

```powershell
cd research; .\.venv\Scripts\activate
# .env: OPENROUTER_API_KEY + PI_REPO_PATH   (never commit)
python scripts/prepare_worktrees.py --repo-path <pi-clone> --worktree-root <root> --write-paths
python scripts/build_corpus_indexes.py
python scripts/validate_stage5_indexes.py
# 12 runs: per task, per rep 1..3, A then B:
python scripts/run_method_a.py --task-id <task> --repetition <rep>
python scripts/run_method_b.py --task-id <task> --repetition <rep>
python scripts/evaluate_pilot.py --output results/processed/pilot_eval.json
```

---

## 5. Main experiment readiness

> **Superseded (T1, 2026-11-26):** the main experiment was frozen and executed on 2026-11-25 (24/24 runs). See `handoff_t3_main_experiment.md`. The text below is the 2026-11-24 snapshot.

See `docs/handoff_t3_main_experiment.md`. Summary: the pilot blocker is now
cleared; main execution remains **blocked on team decisions**, not machinery —
task-set selection (≥4 of the 8 verified tasks, C/D overlap decision) and
ground-truth human review / version freeze. The benchmark itself is main-ready
on the structural level: 8/8 snapshots verified, structurally validated GT for
all 8 tasks.

---

## 6. Tests — commands and actual results

| Where | Command | Result |
|---|---|---|
| `t3/experiment-integration` (= `main` content) | `python -m pytest tests/unit -q` | 99 passed, 2 skipped |
| `t1/semantic-retrieval` (PR #2) | `python -m pytest tests/unit -q` | 106 passed, 2 skipped |

Mocked tests do not establish live API behavior. **Timeline correction
(2026-11-25):** the statement that no live OpenRouter calls occurred applied
only to the initial validation pass, before a key was available. It is
superseded by §4: the embedding/chat probes and all 12 pilot runs were
subsequently executed live on 2026-11-24.

---

## 7. Artifact locations

| Artifact | Location | Committed? |
|---|---|---|
| Pi clone (objects incl. Candidate E after fetch) | local, outside repo | No (never commit Pi trees) |
| Pilot worktrees (detached, clean, pinned parents) | local `<worktree-root>/<task_id>` | No |
| Chunk manifests + scan reports | `research/artifacts/indexes/<sha12>/` | No (gitignored, reproducible) |
| Validation outputs (verify/validate/corpus) | summarized in this doc §3 | This doc |
| Embedded indexes (`vectors.npy`, `chunks.json`, `meta.json`) | `research/artifacts/indexes/{bfa6862400d0,dd838d0fe09d}/` | No (gitignored, reproducible) |
| 12 run traces + `runs.jsonl` | `research/results/raw/traces/` | No (gitignored; preserve locally, deliver to T1 out-of-band) |
| Pilot evaluation output | `research/results/processed/pilot_eval.json` | No (gitignored; regenerate via `evaluate_pilot.py`) |

---

## 8. What T1 (Rehat) needs to resolve or complete

> **Status (T1, 2026-11-26):** items 1, 2 and 4 are addressed. See `docs/t1_ground_truth_review.md`, `scripts/t1_evaluate.py` and `docs/t1_evaluation.md`. An evaluator now exists (T3's preliminary one and T1's independent one).

1. **Human relevance review** of T2's ground truth (all 8 tasks are
   `pending_student_and_peer_review`); any changes after runs begin require a
   new benchmark version, and results evaluated against different versions
   must not be combined.
2. **Evaluator implementation** — file-level TP/FP/FN, precision, recall, F1
   (+ essential-file recall, MRR/nDCG with essential=2/supporting=1 labels).
   No evaluator exists in the repo yet; traces and GT formats are stable inputs.
3. **Candidate E setup caveat** (§3) if E is included in the main task set.
4. Benchmark version labeling for the main experiment task selection (≥4 of
   the 8 verified tasks; do not present the selection as already T1-validated).

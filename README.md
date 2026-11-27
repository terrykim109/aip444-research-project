# Repository-Level Context for Coding Agents

**Status (2026-11-26, T1):** Both experiments are executed. Pilot `pilot-v1.0` completed 12/12 runs and main `main-v1.0` completed 24/24 runs (4 tasks), with zero failures and a single config hash. T1 has finished the ground-truth review (`t1_reviewed_v1`), the independent evaluator and trace-analysis scripts, the report draft, the presentation outline, the demo guide and the submission checklist. Results were rescored by T1 from T3's per-run evaluation files, cross-checked against the manifest, against the reviewed ground truth (`research/results/findings.md`). Raw traces were not transferred, so MRR/nDCG and per-call analysis are unavailable.  
**Start here:** `research/docs/handoff_t1_final.md` · report draft `research/report.md` · findings `research/results/findings.md` · evaluation procedure `research/docs/t1_evaluation.md` · GT review `research/docs/t1_ground_truth_review.md` · slides `research/docs/presentation_outline.md` · demo `research/docs/demo.md` · checklist `research/docs/final_submission_checklist.md`.  
**Earlier handoffs (historical):** `research/docs/handoff_t3_integration.md`, `handoff_t3_pilot.md`, `handoff_t3_main_experiment.md`; `research/results/run_manifest.json` (36 runs + trace hashes); `research/config/main_experiment.yaml`.  
**Requirements to reproduce runs:** an OpenRouter API key in `research/.env`, a local Pi clone, and machine-local worktrees (`prepare_worktrees.py --write-paths`). Raw traces are gitignored and must be transferred out-of-band, then verified with `research/scripts/t1_verify_traces.py`.

---

## Members

- Arman Ataeipour 
- Nirajan Bhandari 
- Rehat Preet Kaur
- Terry Kim 


## 1. Project overview

This directory (`research/`) holds the experimental framework for our researech group project. It compares two ways of gathering **repository-level code context** for coding agents on realistic software-engineering tasks drawn from the [Pi](https://github.com/earendil-works/pi) monorepo.

My part is **Experimental design, implementation, and results analysis**, which owns the integrated experiment: snapshot verification, preliminary prompts/GT, local semantic retrieval (code embeddings), Methods A/B, LLM env adapter, logging, core metrics, and primary analysis.

Teammate workstreams remain assigned (T1 semantic retrieval; T2 repository validation; T3 agent-directed search/synthesis/comparative evaluation), not prerequisites. Contracts: `docs/handoff_contract.md`, `docs/ownership_matrix.md`.

---

## 2. Research topic and fixed research question

**Topic:** Repository-Level Context for Coding Agents.

**Research question:**

> Does agent-directed code search outperform one-shot code RAG for repository-level software engineering tasks?

We investigate whether LLM-directed iterative repository search and source inspection can retrieve more useful context than conventional one-shot code RAG.

**Primary outcome:** retrieval quality (evidence pack vs evaluator-only ground truth).  
**Not the primary outcome:** whether generated code successfully implements the change.

---

## 3. Why repository-level context matters

Modern coding agents work in large repositories where behaviour is split across packages, configs, and tests. A single file rarely explains “how extensions load” or “how packages are filtered.” Useful context is **cross-file**. If retrieval misses those links, agents reason from incomplete or misleading evidence.

---

## 4. What repository-level RAG is

**RAG (Retrieval-Augmented Generation)** retrieves relevant text from a corpus, then (typically) supplies it to an LLM. **Repository-level RAG** indexes a whole repository snapshot—here, the Pi monorepo at a task-specific pre-change commit—so queries can surface chunks from anywhere in that tree, not just an open buffer.

In this project we emphasise the **retrieval** side: building a ranked **evidence pack** under a shared token budget.

---

## 5. Benchmark vs experiment

| | Benchmark | Experiment |
|---|---|---|
| **Role** | Tasks, snapshots, prompts, ground truth | Running Method A vs Method B and scoring packs |
| **Independent owner** | EXP (preliminary self-validated prompts/GT; Git-verified snapshots) | EXP (retriever, methods, logging, core evaluation) |
| **Optional enhancement** | T2 review / gold upgrade | T1 retriever upgrade; T3 extra metrics/viz |
| **Current (2026-11-26)** | 8/8 snapshots verified (E resolved); pilot GT `preliminary`; main GT `t2_context_v1` (as run) + T1-reviewed `t1_reviewed_v1` | Methods A/B built and executed: 36 runs (pilot + main); T1 evaluator ready, scores pending trace transfer |
| *Historical (Stage 5)* | *Pilots A/B prompts + preliminary GT; E unresolved; other GT deferred* | *Shared semantic retriever ready; Method A/B runners not built* |

The benchmark defines *what* is asked and *what counts as relevant*. The experiment measures *which search strategy* gathers better evidence under shared controls.

---

## 6. One-shot RAG vs agent-directed search

**Method A — One-shot code RAG**  
Receives a task, performs **exactly one** retrieval against a shared code index, returns a ranked evidence pack.

**Method B — Agent-directed code search**  
Receives the **same** task, searches, inspects files/symbols, identifies missing context, refines queries, and searches again within resource limits, then returns a ranked evidence pack.

**Shared (intended):** snapshots, corpus construction, chunking, embedding/index backend, task prompts, evidence budgets, evaluation criteria.  
**Difference:** search strategy.

Method B is inspired by iterative retrieval (e.g. RepoCoder) but is **not** an exact reproduction. RepoBench / Repoformer principles inform evaluation and caution about irrelevant context; they are **not** extra methods.

---

## 7. Why Pi was selected

[Pi](https://github.com/earendil-works/pi) is a real, evolving monorepo with cross-cutting concerns (extensions, packages, RPC, CLI, networking). That makes repository-level retrieval nontrivial and closer to agent workloads than toy single-file tasks. We use **task-specific pre-change snapshots** so methods search the tree as it existed before the target change.

**Pi clone (outside this research folder):** machine-local. The paths below are the original EXP machine's, kept for history. Each runner creates its own with `prepare_worktrees.py --write-paths`.  
**Pilot worktrees (detached pre-change parents, original machine):**

| Task | Worktree | HEAD |
|---|---|---|
| `pi_lazy_extension_loading` | `C:\Users\froze\Desktop\pi-task-lazy` | `bfa6862400d0aaa3ebf3c09a44a2479487f470f1` |
| `pi_package_filtering` | `C:\Users\froze\Desktop\pi-task-packages` | `dd838d0fe09db079dcf2f57bab1d79d4df5a0e4c` |

Do not modify upstream Pi or mix experimental code into these trees. Details: `docs/snapshot_verification.md`, `docs/pi_repository_notes.md`.

---

## 8. Eight candidates and two pilots

| ID | Task ID | Target (preliminary) | Parent prefix | Focus | Status |
|---|---|---|---|---|---|
| A | `pi_lazy_extension_loading` | `40c256c` | `bfa6862` | Lazy extension loading | **pilot** |
| B | `pi_package_filtering` | `ef1fc31` | `dd838d0` | Package configuration and filtering | **pilot** |
| C | `pi_package_progress_conflicts` | `4058680` | `b846a4b` | Package progress and conflict detection | candidate (overlap watch with D) |
| D | `pi_package_dedup_collisions` | `50c8323` | `c5c515f` | Package deduplication and collisions | candidate (overlap watch with C) |
| E | `pi_network_retry` | `37067e0` | `4860665` | Network retry handling | candidate |
| F | `pi_rpc_context_statistics` | `835296b…` | `9a0be02` | RPC context statistics | candidate |
| G | `pi_session_directory_config` | `8191d59…` | `8632e1b` | Session directory configuration | candidate |
| H | `pi_cli_mode_validation` | `e40126f…` | `1a584a7` | CLI mode validation | candidate |

**Advanced reserve (not one of the eight):** `32bcdc9` — investigate reported CI issue before acceptance.

**Verification (current):** all **8/8 verified** (full target/parent SHAs in `benchmark/manifests/snapshots.json`). Candidate E was resolved by T2; its commits are unreachable from upstream branch heads, so fresh clones need `git fetch origin <target-sha>` first.  
**Run sets:** A/B = `pilot-v1.0` pilots (executed); D/F/G/H = frozen `main-v1.0` main-experiment set (executed) — selection rationale and C/E exclusions in `research/config/main_experiment.yaml`.  
Agent-visible `benchmark/tasks.json` still omits SHAs (evaluator-side only).

---

## 9. Why pre-change snapshots are necessary

If methods search the commit that already contains the fix, they can “retrieve the answer” from the future. Pre-change (parent) snapshots force retrieval to find the **context needed to understand or solve the task**, matching a developer’s starting point. Stage 2 resolves full parent/target SHAs and pins pilot worktrees at the **parent** commits.

---

## 10. What ground truth means

Ground truth is the **evaluator-only** map of relevant files, essential vs supporting evidence, symbols, and line spans (plus test metadata). It scores evidence packs. It must **never** be fed into Method A or B. Schema notes: `benchmark/ground_truth/README.md`. **No fabricated gold annotations in Stage 1.**

---

## 11. Individual responsibilities (experimental design owner)

Independently owns and must be able to deliver alone:

- Experimental protocol and configuration  
- Integrated Python experiment architecture (`src/repo_search`)  
- Shared schemas/interfaces  
- Pi commit/snapshot verification and benchmark loader  
- Preliminary prompts and self-validated ground truth (from diffs vs parent snapshots)  
- Corpus preparation and **local code-embedding** semantic retrieval backend  
- One-shot RAG and agent-directed controller (same retriever)  
- LLM provider adapter via environment configuration  
- Experiment runner, logging, **core** metrics, paired comparisons, primary interpretation  
- Integration testing and technical methodology documentation  

**Fallback labels:** local embeddings = semantic path; BM25 = smoke-test only (not semantic RAG); GT = `preliminary`/`self_validated` until reviewed; agent dry-run = plumbing only (real LLM required for claimable Method B results).

---

## 12. Teammate workstreams 

| Teammate | Contribution | Integration rule |
|---|---|---|
| **1 — Semantic Code Retrieval** | Alternate embeddings/index/ranking | Same `search()` interface; test before replace; keep EXP backend |
| **2 — Repository Context Engineering & Validation** | Reviewed snapshots/prompts/gold/leakage | Schema-validate; do not invent; preserve EXP preliminary path |
| **3 — Synthesis, comparative evaluation, presentation** | MRR/nDCG, extra viz, synthesis, polish | Consume EXP JSONL/CSV; do not redefine core P/R/F1 |

No empty modules pretend teammate work exists.

---

## 13. Intended architecture

```text
EXP verified snapshots  (+ optional T2 review)
        ↓
EXP preliminary prompts + self-validated GT  (+ optional T2 gold)
        ↓
EXP corpus + local semantic index  (identical for A and B)
   optional T1 backend behind same search()
        ↓
        ├── EXP Method A — one-shot orchestration
        │
        └── EXP Method B — agent controller + LLM env adapter
                    ↓
             Evidence packs + traces
                    ↓
             EXP run logger (JSONL / CSV)
                    ↓
             EXP core evaluation + primary interpretation
                    ↓
             optional T3 extras / presentation
```

Hard rules: same retriever/index for both methods; no hidden gold; BM25 ≠ semantic RAG; dry-run ≠ LLM experiment. Stage 5 implemented the shared retriever and Stage 6 the Method A/B orchestration. Both were exercised live in the pilot and main runs (2026-11-24/25).

---

## 14. Project structure

```text
research/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/experiment.yaml
├── schemas/          # integration JSON Schemas (contracts only)
├── benchmark/
│   ├── tasks.json
│   ├── candidates.json
│   ├── manifests/snapshots.json
│   └── ground_truth/README.md
├── src/repo_search/  # scan, chunk, embeddings, index, retriever, loaders
├── scripts/          # verify_benchmark, build_corpus_indexes, probes
├── tests/unit/       # Stage 2–5 unit tests (mocked embeddings)
├── artifacts/        # chunk manifests + indexes (gitignored)
├── results/          # raw JSONL / processed CSV / charts + findings.md
└── docs/             # methodology, corpus_and_retrieval, protocol_freeze, …
```

---

## 15. Planned setup and dependencies

**Executable now (lightweight):**

```bash
cd research
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Dependencies: `pyyaml`, `numpy`, `tiktoken`, `httpx` (+ optional `pytest`, `mypy`). Embeddings via OpenRouter HTTP — no local GPU stack.

Copy `.env.example` → `.env` and set `PI_REPO_PATH`, `OPENROUTER_API_KEY`, and related OpenRouter fields. Never commit secrets.

---

## 16. Execution workflow (actual, as run)

See `docs/EXECUTION_CHECKLIST.md` and the T3 handoffs. All commands run from `research/` with the venv active and `.env` set (`OPENROUTER_API_KEY`, `PI_REPO_PATH`).

```bash
pip install -e ".[dev]"
python -m pytest tests/unit -q                      # 106 passed, 2 skipped

# Snapshots + worktrees (machine-local; manifest paths are not committed)
python scripts/verify_benchmark.py --repo-path <pi-clone> --dry-run
python scripts/prepare_worktrees.py --repo-path <pi-clone> --worktree-root <root> \
  --task-id <task> ... --write-paths

# Indexes (pilots by default; --task-id for main-v1.0 tasks)
python scripts/build_corpus_indexes.py
python scripts/build_corpus_indexes.py --task-id pi_cli_mode_validation  # etc.

# Runs (per task, per repetition 1..3, Method A then B)
python scripts/run_method_a.py --task-id <task> --repetition <rep> --protocol-version main-v1.0
python scripts/run_method_b.py --task-id <task> --repetition <rep> --protocol-version main-v1.0

# Preliminary file-level evaluation (T3)
python scripts/evaluate_pilot.py --annotation-set t2_context_v1 --task-id <task> ...

# T1 independent evaluation (authoritative once traces are present and verified)
python scripts/t1_verify_traces.py
python scripts/t1_evaluate.py --run-set main-v1.0 --annotation-set t1_reviewed_v1
python scripts/t1_evaluate.py --run-set pilot-v1.0 --annotation-set preliminary
python scripts/t1_analyze_method_b.py --run-set main-v1.0 --annotation-set t1_reviewed_v1
python scripts/t1_demo_replay.py --task-id pi_cli_mode_validation --repetition 1
```

Artifacts: traces `results/raw/traces/` (gitignored), manifest + hashes `results/run_manifest.json` (committed), evaluation outputs `results/processed/` (gitignored).

---

## 17. Evaluation metrics

See `config/experiment.yaml` and `docs/methodology.md`.

**Primary (EXP, required):** **file-level F1** (primary metric); also report precision/recall, essential-file recall; evidence vs planning token accounting; tool-call counts; latency; paired comparisons. Final evidence pack is the primary outcome object; cumulative unique exposure is supplementary.

**Secondary (T3, optional, same relevance labels):** MRR; nDCG; additional statistics; advanced visualizations; broader synthesis. Stage 10 can finish without T3.

Also track cumulative unique evidence exposure and newly discovered relevant files per iteration. Do not assume Method B is superior; report improvements and regressions; avoid overstated significance with few tasks/reps.

---

## 18. Reproducibility requirements

- Follow frozen `pilot-v1.0` design; new protocol version required for budget/rule changes  
- Bind every run to snapshot ID, index ID, method, repetition, `paired_trial_id`  
- Log Method B iterations  
- Keep ground truth out of method inputs  
- Prefer tested teammate upgrades when available, but **never block** on them; keep the independent path  
- Label BM25, preliminary GT, dry-runs, and `implementation_origin` honestly  
- Do not commit indexes, raw dumps, or `.env`  

---

## 19. Research limitations

Summary (updated 2026-11-26): main ground truth reviewed by T1 (single, non-blind reviewer) → `t1_reviewed_v1` (1 added supporting file in F; `t2_context_v1` preserved as run); raw traces not yet transferred, so all scores are preliminary; pilot and main use different prompt/annotation versions and are not combined; 4-task main set limits generalization and no statistical significance is claimed; C and E excluded from the main set for overlap (decisions recorded in `config/main_experiment.yaml`, open to revisit); G/H essential-file containment caveat; Candidate E needs fetch-by-SHA on fresh clones; raw traces are local-only until transferred to T1; retrieval quality ≠ implementation success. Full list: `docs/limitations.md`.

---

## Status board (honest)

| Item | State |
|---|---|
| Scaffolding & docs | **Created (Stage 1)** |
| Ownership / integration alignment | **Documented (Stage 1.5)** |
| Pi clone + pilot worktrees | **Prepared (Stage 2)**; re-verified independently on a second machine (T3) |
| Snapshot verification | **8/8 verified** (E resolved by T2; fetch-by-SHA caveat) |
| Protocol freeze | `pilot-v1.0` frozen; `main-v1.0` frozen (`config/main_experiment.yaml`) — pilot pins inherited unchanged |
| Integration schemas & contracts | **Documented** (`schemas/`, handoff) |
| Ground-truth annotations | All 8 structurally validated (`t2_context_v1`); main 4 **reviewed by T1** → `t1_reviewed_v1` (2026-11-26) |
| Semantic retriever / index | **Verified live** — 6 snapshot indexes built (2 pilot + 4 main) |
| Method A / Method B / chat adapter / runner | **Implemented (Stage 6)** and exercised live |
| Pilot (Stage 7) | **Executed 2026-11-24** — 12/12 runs, 6/6 pairs, zero failures |
| Main experiment (`main-v1.0`) | **Executed 2026-11-25** — 24/24 runs, 12/12 pairs, zero failures; preliminary mixed result (B wins 2 tasks, A wins 1, 1 tie) |
| Raw trace transfer to T1 | **Not transferred.** T3's per-run evaluation files were received instead, and T1 rescored all 36 runs from them (no MRR/nDCG, no per-call analysis) |
| Evaluation tooling (T1) | **Done**: verifier, evaluator, Method B analysis, demo replay, tests |
| Findings / synthesis / report | **Draft done (T1)** with final rescored results: `research/report.md` (+ `report.docx`), `research/results/findings.md`; group editing, reflections and Appendix D pending |
| Presentation / demo / checklist | **Outline + guide done (T1)**; slides, recording, upload, submission are group actions |
| Teammate contributions merged | T2 benchmark (PR #1), retrieval delivery (PR #2), T3 validation + pilot (PR #3) |

---

## Documentation index

| Doc | Purpose |
|---|---|
| [BEGINNER_GUIDE.md](research/docs/BEGINNER_GUIDE.md) | Concepts from scratch |
| [EXECUTION_CHECKLIST.md](research/docs/EXECUTION_CHECKLIST.md) | Ten-stage roadmap (+ 1.5) |
| [methodology.md](research/docs/methodology.md) | Controlled design |
| [literature_review.md](research/docs/literature_review.md) | RepoBench, RepoCoder, Repoformer, CodeRAG-Bench, SWE-agent (T1-verified) |
| [report.md](research/report.md) | Research report draft (APA, Appendices A–D) |
| [handoff_t1_final.md](research/docs/handoff_t1_final.md) | T1 final handoff |
| [t1_ground_truth_review.md](research/docs/t1_ground_truth_review.md) | GT review, `t1_reviewed_v1` |
| [t1_evaluation.md](research/docs/t1_evaluation.md) | Evaluation procedure, artifact status, T3 evaluator audit |
| [presentation_outline.md](research/docs/presentation_outline.md) | 10-slide outline |
| [demo.md](research/docs/demo.md) | 1–2 min demo guide |
| [final_submission_checklist.md](research/docs/final_submission_checklist.md) | Requirement → status map |
| [findings.md](research/results/findings.md) | Final results summary (rescored, reviewed GT) |
| [run_manifest.json](research/results/run_manifest.json) | All 36 runs with statuses and trace hashes |
| [main_experiment.yaml](research/config/main_experiment.yaml) | Frozen main-v1.0 configuration |
| [handoff_final.md](handoff_final.md) | EXP onboarding / coordination handoff |
| [retrieval_backend_notes.md](research/docs/retrieval_backend_notes.md) | Retrieval backend notes (PR #2) |
| [t2_integration.md](research/docs/t2_integration.md) | T2 integration and handoff |
| [t2_benchmark_review.md](research/docs/t2_benchmark_review.md) | T2 benchmark review |
| [t2_snapshot_review.md](research/docs/t2_snapshot_review.md) | T2 snapshot review |
| [t2_task_cards.md](research/docs/t2_task_cards.md) | T2 task cards (8 tasks) |
| [t2_validation_results.md](research/docs/t2_validation_results.md) | T2 validation results |
| [snapshot_verification.md](research/docs/snapshot_verification.md) | Stage 2 SHA / worktree report |
| [benchmark_validation.md](research/docs/benchmark_validation.md) | Stage 3 prompts / GT / isolation |
| [protocol_freeze.md](research/docs/protocol_freeze.md) | Stage 4 frozen pilot protocol |
| [corpus_and_retrieval.md](research/docs/corpus_and_retrieval.md) | Stage 5 corpus, embeddings, index, retriever |
| [methods_stage6.md](research/docs/methods_stage6.md) | Stage 6 Method A/B, chat client, traces |
| [handoff_t3_integration.md](research/docs/handoff_t3_integration.md) | T3 umbrella handoff to T1 |
| [handoff_t3_pilot.md](research/docs/handoff_t3_pilot.md) | Validation + executed pilot record |
| [handoff_t3_main_experiment.md](research/docs/handoff_t3_main_experiment.md) | Frozen main-v1.0 + executed main run record |
| [pi_repository_notes.md](research/docs/pi_repository_notes.md) | Pinned AGENTS.md / toolchain notes |
| [task_cards.md](research/docs/task_cards.md) | Human-readable tasks |
| [limitations.md](research/docs/limitations.md) | Threats to validity |
| [report_plan.md](research/docs/report_plan.md) | ~1,500-word APA plan |
| [ai_use_log.md](research/docs/ai_use_log.md) | AI interaction log |
| [contribution_log.md](research/docs/contribution_log.md) | Contribution tracker |
| [appendix_templates.md](research/docs/appendix_templates.md) | Appendices A–D |
| [schemas/README.md](research/schemas/README.md) | JSON Schema contracts |

---

## Literature links

- RepoBench (2024): https://proceedings.iclr.cc/paper_files/paper/2024/file/d191ba4c8923ed8fd8935b7c98658b5f-Paper-Conference.pdf  
- RepoCoder (2023): https://aclanthology.org/2023.emnlp-main.151/  
- Repoformer (2024): https://proceedings.mlr.press/v235/wu24a.html  
- CodeRAG-Bench (2025): https://doi.org/10.18653/v1/2025.findings-naacl.176  
- SWE-agent (2024): https://doi.org/10.52202/079017-1601  

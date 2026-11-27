# Contribution Log

**Purpose:** Track real work for Appendix C and group coordination.  
**Rule:** Do not invent teammate participation. Update when work is actually done.

---

## Workstream legend

| Code | Workstream |
|---|---|
| EXP | Experimental design, implementation, results analysis (this owner) |
| T1 | Semantic Code Retrieval (RAG) |
| T2 | Repository Context Engineering and Validation |
| T3 | Synthesis, comparative evaluation extras, presentation & documentation |

---

## Entries

| Date | Workstream | Member (name) | Activity | Artifacts | Hours (approx.) |
|---|---|---|---|---|---|
| 2026-11-18 | EXP | *(fill name)* | Stage 1: create `research/` foundation, configs, docs | `research/**` scaffolding | *(fill)* |
| 2026-11-18 | EXP | *(fill name)* | Stage 1.5: ownership matrix, handoff contracts, schemas, metric ownership alignment | `docs/ownership_matrix.md`, `docs/handoff_contract.md`, `schemas/**`, aligned docs/config | *(fill)* |
| 2026-11-18 | EXP | *(fill name)* | Stage 2: Pi clone, SHA verification, pilot worktrees, verify script + tests + docs | `snapshots.json`, `scripts/verify_benchmark.py`, `docs/snapshot_verification.md`, `docs/pi_repository_notes.md` | *(fill)* |
| 2026-11-18 | EXP | *(fill name)* | Stage 3: pilot prompts + preliminary GT, loader isolation, Stage 3 tests | `tasks.json`, `ground_truth/*.json`, `benchmark_loader.py`, `docs/benchmark_validation.md` | *(fill)* |
| 2026-11-18 | EXP | *(fill name)* | Stage 4: freeze pilot-v1.0 protocol, accounting, metrics, config tests | `config/experiment.yaml`, `docs/protocol_freeze.md`, `protocol_config.py`, Stage 4 tests | *(fill)* |
| 2026-11-19 | EXP | *(fill name)* | Stage 5: corpus scan/chunking, OpenRouter embeddings, NumPy indexes, shared retriever | `src/repo_search/{corpus_*,chunking,embeddings,vector_index,retriever}.py`, `docs/corpus_and_retrieval.md`, Stage 5 tests | *(fill)* |
| 2026-11-19 | EXP | *(fill name)* | Stage 6: Method A/B, tools, OpenRouter chat, orchestration, traces | `method_a/b.py`, `repo_tools.py`, `chat_client.py`, `orchestrator.py`, `docs/methods_stage6.md` | *(fill)* |
| 2026-11-24 | T1 | Arman Ataeipour | T1 delivery: retrieval validation, search CLI, smoke tests, embedding-model review, backend notes; Stage 5 retriever unchanged (no protocol changes) | `src/repo_search/search_cli.py`, `scripts/search_index.py`, `tests/unit/test_retrieval_t1.py`, `docs/retrieval_backend_notes.md` | *(fill)* |
| 2026-11-24 | T3 | Arman Ataeipour | T3 integration/validation: independent 8/8 snapshot re-verification on a second machine, pilot worktree creation, offline benchmark/GT validation, exact deterministic corpus reproduction (14,964 + 3,992 chunks), method-compliance inspection, PR #2 audit; pilot documented as blocked on `OPENROUTER_API_KEY` (no runs executed, none fabricated) | `docs/handoff_t3_pilot.md`, `docs/handoff_t3_main_experiment.md` | *(fill)* |
| 2026-11-24 | T3 | Arman Ataeipour | Stage 7 pilot executed live: embedding/chat probes passed, both pilot indexes built and validated, **12/12 runs completed (6 matched pairs, zero failures)** under frozen `pilot-v1.0` (single config hash); minimal file-level evaluator added; preliminary results computed against both GT sets separately (mixed outcome — neither method dominates; ~$0.13 total API cost) | `scripts/evaluate_pilot.py`, traces `results/raw/traces/` (local, gitignored), `results/processed/pilot_eval.json` (local), updated handoff docs | *(fill)* |
| 2026-11-25 | T3 | Arman Ataeipour | Main experiment frozen and executed: `main-v1.0` task selection from T2 overlap evidence (D/F/G/H selected; C excluded 0.5 essential overlap, E excluded 1.0 overlap + fetch caveat), GT version frozen by SHA-256 (provisional pending T1 review), 4 worktrees + indexes built (31k chunks), **24/24 runs completed (12 matched pairs, zero failures)**, trace audit + preliminary evaluation (B wins 2 tasks, A wins 1, 1 tie), run manifest with trace hashes, timeline corrections in docs/PR, README status updates | `config/main_experiment.yaml`, `results/run_manifest.json`, `docs/handoff_t3_integration.md`, updated handoffs/READMEs/tasks.json, minimal code extensions (`--task-id` builds, `--protocol-version` labeling, evaluator task filter) | *(fill)* |

---

## Teammate receipt tracker

| Deliverable | Expected from | Received? | Location | Notes |
|---|---|---|---|---|
| Retrieval API + index README | T1 | In review | branch `t1/semantic-retrieval` (PR) | Search CLI + T1 smoke tests + `docs/retrieval_backend_notes.md`; embedding pin kept (no protocol change) |
| Snapshot verification + ground truth | T2 | No | — | EXP performed Stage 2 Git verification; T2 gold/task validation still pending |
| Commit identity cross-check vs T2 handoff | T2 | No | — | No T2 SHA artifact present to compare |
| Synthesis / charts / presentation | T3 | No | — | Needs Stage 9–10 EXP outputs |

---

## Notes

- Stage 1 establishes EXP scaffolding only.  
- Mark fallbacks clearly if EXP substitutes for T1/T2 later.

## T2 local integration — 20 November 2026

| Member | Workstream | Delivered work | Status |
| --- | --- | --- | --- |
| Nirajan Bhandari, AI-assisted preparation | Repository Context Engineering and Benchmark Validation | Eight original snapshot identities cross-checked against GitHub/local Git; original Candidate E resolved; versioned task/annotation set adapted to central IDs and schemas | Source/schema checks complete |
| Nirajan Bhandari, AI-assisted preparation | T2 implementation | Benchmark loader isolation, offline provenance validation, deterministic builder, detached-worktree reproduction and T2 regression tests | Local implementation |
| Nirajan Bhandari, AI-assisted preparation | T2 documentation | Benchmark and overlap record, additional scholarly connection, reproduction instructions and validation record | Local delivery |

The retrieval stack, agent controller/tools, orchestration, token accounting and
analysis code are unchanged. No experimental runs or completed human relevance
review are claimed. Time spent is not recorded. This entry records local work;
GitHub publication is performed manually by the student.

## T1 final evaluation and synthesis — 26 November 2026

| Date | Workstream | Member (name) | Activity | Artifacts | Hours (approx.) |
|---|---|---|---|---|---|
| 2026-11-26 | T1 | Rehat Preet Kaur (AI-assisted, see AI use log) | Verified T3 manifest/GT freeze; documented missing traces; GT relevance review → `t1_reviewed_v1`; independent evaluator, trace verifier, Method B analysis, demo replay (+ tests); literature verification + SWE-agent; report draft with appendices; presentation outline; demo guide; submission checklist; README/limitations reconciliation | `docs/t1_ground_truth_review.md`, `docs/t1_evaluation.md`, `docs/handoff_t1_final.md`, `benchmark/ground_truth/t1_reviewed_v1/`, `scripts/t1_*.py`, `tests/unit/test_t1_evaluation.py`, `report.md`, `docs/presentation_outline.md`, `docs/demo.md`, `docs/final_submission_checklist.md` | *(fill)* |

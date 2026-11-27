# Execution Checklist — Ten-Stage Roadmap

**Current position:** Stage **6 complete** (Method A/B + orchestration + traces; no pilot batch yet) → **Stage 7 is next**.  
Future stages are **not** complete. Do not mark them done until their completion criteria are met.

---

## Stage 1 — Initialize the research workspace

| | |
|---|---|
| **Objective** | Establish `./research` scaffolding, research identity, configs, candidate registry, and documentation. |
| **Activities** | Create directory tree; write README and docs; add provisional `experiment.yaml`; register candidates/tasks; define ground-truth schema notes; set up `pyproject.toml`, `.env.example`, `.gitignore`. |
| **Expected artifacts** | Structure under `research/`; docs listed in README; `benchmark/*.json`; empty/provisional snapshot manifest; package stub `src/repo_search`. |
| **Independent completion criteria** | Docs consistent with fixed research question; candidates honestly labelled; no fabricated gold/results; no Stage 2+ work claimed done. |
| **Status** | **Complete** |

---

## Stage 1.5 — Align foundation with team ownership (documentation)

| | |
|---|---|
| **Objective** | Document ownership, integration contracts, and independent-execution posture. |
| **Activities** | Clarify EXP vs teammate roles; document retriever/benchmark/run-output contracts; add ownership matrix and JSON Schemas; split primary vs secondary metrics; state that teammate deliverables are optional. |
| **Expected artifacts** | Updated README/methodology/handoff/checklist; `docs/ownership_matrix.md`; `schemas/*`. |
| **Independent completion criteria** | Research question unchanged; contracts documented; independent path explicit; no fake teammate modules. |
| **Status** | **Complete** |

---

## Stage 2 — Prepare and verify Pi snapshots

| | |
|---|---|
| **Objective** | Independently verify Pi commits, parent SHAs, and repository snapshots; pin pilot worktrees. |
| **Activities** | Clone Pi outside the research tree; fetch history; resolve full target/parent SHAs; create detached pilot worktrees; run `scripts/verify_benchmark.py`. |
| **Expected artifacts** | `benchmark/manifests/snapshots.json`; pilot worktrees; `docs/snapshot_verification.md`; `docs/pi_repository_notes.md`. |
| **Independent completion criteria** | Pilot parent/target SHAs verified by EXP against Git history; worktrees clean/detached at parent SHAs; failures recorded honestly. |
| **Optional teammate enhancement** | T2 may later cross-check SHAs / add validation notes; integrate only after comparison to Git-authoritative records. |
| **Status** | **Complete** — 7/8 verified; **E** `pi_network_retry` (`37067e0`) **verification_failed**. |

---

## Stage 3 — Create the benchmark and validate ground truth

| | |
|---|---|
| **Objective** | Independently author neutral pilot prompts and preliminary evaluator-only ground truth from historical diffs, verified against parent snapshots. |
| **Activities** | Updated agent-visible `tasks.json`; authored GT for A/B from diffs; verified paths/spans on parent worktrees; separated existing vs target-added tests; added loader isolation + Stage 3 unit tests; documented in `docs/benchmark_validation.md`. |
| **Expected artifacts** | `benchmark/ground_truth/pi_lazy_extension_loading.json`, `pi_package_filtering.json`; `benchmark_loader.py`; Stage 3 tests. |
| **Independent completion criteria** | Pilot prompts free of answer leakage; GT files exist with `preliminary_self_validated`; parent-snapshot checks pass; evaluator isolation tests pass. |
| **Optional teammate enhancement** | T2 may review/replace annotations after schema checks. |
| **Status** | **Complete** — pilots A/B only; E unresolved; C–D/F–H GT deferred. |

---

## Stage 4 — Freeze experimental settings

| | |
|---|---|
| **Objective** | Lock shared controls, budgets, accounting, stopping rules, metrics, and paired-trial design. |
| **Activities** | Defined Method A/B operations; froze `pilot-v1.0` budgets (6000 / 5 / top-k 10 / 3 reps); documented evidence vs planning tokens; wrote `docs/protocol_freeze.md`; marked model/index IDs `pending_configuration`. |
| **Expected artifacts** | `config/experiment.yaml` (design frozen); `docs/protocol_freeze.md`; Stage 4 config tests. |
| **Independent completion criteria** | Protocol doc exists; methods precisely defined; shared controls listed; tests pass; unverified technical settings explicitly pending. |
| **Status** | **Complete** — design frozen; Stage 5 must pin/working-verify embeddings & index. |

---

## Stage 5 — Build corpus preparation and indexing

| | |
|---|---|
| **Objective** | Independently build snapshot → corpus → chunks → **local semantic** index implementing the shared retriever protocol. |
| **Activities** | EXP implements corpus builder, chunking, **local code embeddings**, index write, `search(query, top_k, max_tokens)`; record provenance (`implementation_origin: independent`). BM25 may be used only as a **pipeline smoke-test** backend and **must not** be labelled semantic code RAG. |
| **Expected artifacts** | Working local semantic retriever + index metadata; rebuild commands; smoke tests. |
| **Independent completion criteria** | Same snapshot yields reproducible `index_id`; identical semantic retriever callable by Methods A and B; replace `pending_configuration` fields with verified pins.|
| **Optional teammate enhancement** | T1 may supply an alternate semantic backend; integrate behind the same interface after tests; keep independent backend available. |
| **Status** | **Complete** — live OpenRouter probe verified; both NumPy indexes built/validated; `SemanticRetriever.search` smoke-tested on both pilots; unit tests passing. |

---

## Stage 6 — Implement search methods and experiment infrastructure

| | |
|---|---|
| **Objective** | Implement Method A and Method B, shared orchestration, OpenRouter chat client, and reproducible traces. |
| **Activities** | One-shot path; agent tool loop (`semantic_search`/`read_file`/`find_symbol`/`grep`); budgets; evidence packs; JSON traces; unit/integration tests; live chat probe. |
| **Expected artifacts** | `method_a.py`, `method_b.py`, `orchestrator.py`, `repo_tools.py`, `chat_client.py`, `docs/methods_stage6.md`, Stage 6 tests. |
| **Independent completion criteria** | Both methods independently executable against Stage 5 indexes; constraints enforced; traces written; tests pass. **No 12-record pilot batch.** |
| **Status** | **Complete** |

---

---

## Stage 7 — Integrate components, validate and run pilot experiments

| | |
|---|---|
| **Objective** | Integrate teammate contributions, validate shared interfaces and execute the planned paired pilot records under frozen `pilot-v1.0` settings. |
| **Activities** | Integrate T1/T2 contributions; shared runner and dry-run modes; unit/integration tests with fixtures; validate evidence-pack schemas, logging, ground-truth isolation and component provenance; execute Method A/B with three repetitions per task using real LLM calls for claimable agent results; persist raw traces; review pilot results and document failures or gaps. |
| **Expected artifacts** | Integrated components; tests under `tests/`; integration notes; provenance log; 12 individual method-run records organized into 6 matched A/B pairs under `results/raw/`; pilot validation report. |
| **Completion criteria** | Both methods execute against the same snapshots and retrieval infrastructure; integration tests pass; all planned pilot repetitions are complete or gaps documented; seeds, configuration hashes, model identifiers and `implementation_origin` recorded; pilot results reviewed. |
| **Ownership** | T1: retrieval validation. T2: benchmark and ground-truth validation. T3: integration, pilot execution and validation. |
| **Status** | **Complete** (2026-11-24, T3): 12/12 runs, 6/6 pairs; see `handoff_t3_pilot.md`. *(Was "Not started"; updated by T1 2026-11-26.)* |

---

## Stage 8 — Run main experiment, analyze results and prepare reporting

| | |
|---|---|
| **Objective** | Complete the main comparative experiment, evaluate retrieval quality and computational efficiency, and prepare the final research findings and academic deliverables. |
| **Activities** | Expand benchmark to at least four independently validated tasks, preferably six; validate task independence and ground truth; freeze main-experiment configuration; execute Method A/B; calculate file-level precision/recall/F1 and essential-file recall; calculate MRR/nDCG where annotations permit; compare evidence/planning tokens, tool calls, latency and API costs; conduct paired comparisons, repeated-run analysis and failure analysis; investigate diminishing returns; prepare charts, tables, research synthesis and final documentation. |
| **Expected artifacts** | Main experiment records; processed evaluation tables; paired comparisons; resource-consumption analysis; Method B trace-analysis scripts; charts under `results/charts/`; `results/findings.md`; `docs/limitations.md`; final academic report, references, presentation and appendices A–D. |
| **Completion criteria** | Main experiment completed or gaps documented; primary and applicable secondary metrics calculated from actual experimental records; paired comparisons reproducible; findings supported by recorded evidence; limitations documented; final academic report and presentation completed. |
| **Ownership** | T3: comparative evaluation, agent-search analysis and research synthesis. T1: retrieval diagnostics. T2: benchmark expansion and ground-truth validation. |
| **Status** | **Partial** (2026-11-26). Main experiment executed (24/24, T3, 2026-11-25). T1 GT review, evaluator, trace-analysis scripts, report draft, presentation outline and demo guide done. Authoritative scores and trace analysis blocked on raw-trace transfer; slides, video and submission pending (group). See `docs/handoff_t1_final.md`. |

---

## Quick status board

| Stage | Name | Independent? | Status |
|---|---|---|---|
| 1 | Initialize research workspace | Yes | **Complete** |
| 1.5 | Align ownership & integration contracts | Yes | **Complete** |
| 2 | Prepare and verify Pi snapshots | Yes | **Complete** (E outstanding) |
| 3 | Benchmark and ground truth | Yes | **Complete** (A/B preliminary) |
| 4 | Freeze experimental protocol | Yes | **Complete** (`pilot-v1.0`) |
| 5 | Corpus + local semantic indexing | Yes | **Complete** (live indexes verified) |
| 6 | Methods A/B + experiment infrastructure | Yes | **Complete** |
| 7 | Integration, validation and pilot experiments | No | **Complete** (12/12 runs) |
| 8 | Main experiment, comparative analysis and reporting | No | **Partial**: runs done; T1 evaluation blocked on traces; reporting drafted |
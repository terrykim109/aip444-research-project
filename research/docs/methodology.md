# Methodology (Proposed Controlled Design)

**Stage:** 6 complete → Stage 7 next *(historical header; as of 2026-11-26 the pilot (12 runs) and main-v1.0 (24 runs) are executed. See `docs/handoff_t1_final.md`.)*  
**Status:** Design frozen (`pilot-v1.0`); methods implemented; 12 pilot trial records not yet run *(superseded: executed 2026-11-24)*  
**Config:** `config/experiment.yaml` (`design_frozen: true`; `technical_configuration_status: configured_stage_5`)  
**Protocol:** `docs/protocol_freeze.md`  
**Corpus:** `docs/corpus_and_retrieval.md`  
**Contracts:** `schemas/`

---

## 0. Execution requirement

Teammate workstreams (Semantic Code Retrieval; Repository Context Engineering and Validation; Research Synthesis / Comparative Evaluation / Presentation) remain assigned. 

| Capability | Independent EXP path | Potential teammate enhancement |
|---|---|---|
| Commit / snapshot verification | EXP verifies against Git | T2 cross-check |
| Prompts + ground truth | Preliminary, self-validated from diffs vs parent snapshot | T2 reviewed gold |
| Semantic retrieval | Local code embeddings behind shared protocol | T1 backend swap-in |
| Pipeline smoke only | BM25 (not labelled semantic RAG) | — |
| Methods A / B + LLM adapter | EXP implementation; env-based LLM config | — |
| Core metrics + paired analysis | EXP | T3 MRR/nDCG/viz/synthesis |
| Agent validity | Real configured LLM for claimable results; dry-run = plumbing only | — |

Do not invent teammate contributions. Record `implementation_origin` per component.

---

## 1. Fixed research question

> Does agent-directed code search outperform one-shot code RAG for repository-level software engineering tasks?

Do not rename, reframe, or replace this question.

**Research topic:** Repository-Level Context for Coding Agents.

---

## 2. Operational definitions

| Term | Definition for this study |
|---|---|
| **Repository snapshot** | Fixed Pi checkout at a verified pre-change commit (EXP Git verification; optional T2 review). |
| **Corpus** | Indexable source from that snapshot (full monorepo unless later constrained). |
| **Code chunk** | Addressable source unit for embedding/indexing. |
| **Evidence pack** | **Final** ranked retrieved spans/files within the evidence-token budget. **Primary retrieval-quality outcome.** |
| **Cumulative unique evidence exposure** | All distinct repository excerpts supplied during a trial (tracked separately from the final pack). |
| **One-shot code RAG (Method A)** | Exactly one retrieval against the shared semantic index; EXP orchestrates. |
| **Agent-directed code search (Method B)** | Iterative search + inspection + refinement within budgets; same retriever; LLM via env adapter. |
| **Retrieval quality** | Agreement between the final evidence pack and evaluator-only ground truth. |
| **Implementation success** | Downstream patch correctness — **not** the primary outcome. |
| **Planning tokens** | Agent planning/reasoning tokens; recorded separately from evidence tokens. |
| **Preliminary / self-validated GT** | EXP annotations from diffs, checked on the parent snapshot, labelled honestly until external review. |

---

## 3. Independent variable

**Search strategy** (`pilot-v1.0`):

1. **Method A — One-shot code RAG** — exact task prompt as query; **exactly one** semantic retrieval; no LLM query rewrite; dedupe/rank → final evidence pack → stop.  
2. **Method B — Agent-directed code search** — identical prompt; initial semantic search with that exact prompt; LLM inspect/refine + read-only tools (`semantic_search`, `read_file`, `find_symbol`, `grep`) within **5** total tool calls and cumulative evidence budget → ranked pack + trace.

See `docs/protocol_freeze.md` for stopping reasons and forbidden actions.

---

## 4. Primary outcome

**Retrieval quality of the final evidence pack.**

Downstream code implementation success is out of scope as the primary dependent variable (RepoBench-inspired separation).

---

## 5. Shared controls

Both methods use identical:

- Repository snapshots  
- Corpus construction / chunking / embedding index (`index_id`)  
- Task prompts  
- Evidence-token budget and evaluation criteria  

**Forbidden:** different embedder/index for Method B; hidden ground truth; labelling BM25 runs as semantic code RAG.

---

## 6. Frozen pilot budgets and repetitions (`pilot-v1.0`)

From `config/experiment.yaml` (**predetermined pilot settings, not optimized**):

| Setting | Frozen pilot value |
|---|---|
| Evidence-token budget | 6,000 (final pack for both; cumulative repo excerpts for B; repeats count) |
| Agent tool-call limit (Method B) | 5 total counted tool calls |
| Retrieval top-k | 10 per search |
| Repetitions | 3 per method per task (12 paired records) |
| Temperature | 0 where supported |
| Execution mode | Paired trials (`{task_id}__r{repetition}`) |

Design freeze: **Stage 4**. Embedding/tokenizer/chunking/index pins: **Stage 5** (`openai/text-embedding-3-small`, `cl100k_base`, NumPy cosine). Chat models reserved for **Stage 6**.

---

## 7. Methodological principles

1. Retrieval quality and implementation success are different outcomes.  
2. The **final evidence pack** is the primary retrieval-quality outcome.  
3. Track **cumulative unique evidence exposure** separately from the final pack.  
4. Count **all repository excerpts** supplied to the agent against its evidence budget.  
5. Record **agent planning tokens** separately.  
6. Measure **newly discovered relevant files** from additional searches.  
7. Investigate diminishing returns from iterative search.  
8. Report improvements **and** regressions.  
9. Do **not** assume agent-directed search is inherently superior.  
10. Avoid claims of statistical significance from insufficient tasks or repetitions.  
11. Independent path first; teammate upgrades only after tested integration.  
12. Deterministic agent dry-runs validate plumbing only; claimable Method B results need a real configured LLM.

Literature: RepoBench → (1)(2) + multi-file annotations; RepoCoder → (3)(6)(7); Repoformer → (7)(8)(9).

---

## 8. Evaluation ownership

### Primary (EXP — required)

- **File-level F1** (primary metric)  
- File-level precision and recall (reported with F1)  
- Essential-file recall  
- Evidence vs planning token accounting (never mixed)  
- Tool-call counts, latency  
- Paired comparisons and primary interpretation  

### Secondary / additional (T3 — optional)

- MRR, nDCG (file-level ranks; essential=2, supporting=1)  
- Extra statistics and advanced visualizations  
- Broader comparative synthesis / presentation polish  

**File-level scoring rules:** precision = relevant∩retrieved / retrieved; recall = relevant∩retrieved / gold relevant; F1 = harmonic mean; essential-file recall over essential gold only. Multiple chunks from one file count once. Evaluate **final evidence pack** (primary) and **cumulative unique evidence exposure** (supplementary). Do not claim significance from the two-task pilot; more material ≠ better quality.

**Rule:** one definition per metric family; same relevance labels for A and B. Stage 10 completes without T3.

---

## 9. Benchmark validation requirements

1. Parent/target commits resolved and verified by EXP (Stage 2; Git authoritative).  
2. Snapshots in `benchmark/manifests/snapshots.json`.  
3. Neutral task prompts without answer leakage (EXP; optional T2 review).  
4. Pilot ground truth authored as `preliminary_self_validated` (Stage 3) and verified on parent snapshots.  
5. Overlap watch for candidates C and D (full GT deferred).  
6. Reserve `32bcdc9` excluded unless accepted after investigation.  
7. Design/protocol freeze `pilot-v1.0` (Stage 4); technical pins in Stage 5.  
8. Candidate E remains unusable until a resolvable SHA exists.

---

## 10. Implementation posture

- EXP ships a working **local code-embedding** semantic retriever; optional T1 upgrade behind the same interface.  
- BM25 = smoke-test only; never labelled semantic code RAG.  
- EXP authors preliminary GT; optional T2 review may replace it after testing.  
- EXP owns Methods A/B, LLM env adapter, logging, and core evaluation.  
- Preserve the independent implementation when integrating teammate code.  
- Do not create empty modules pretending teammate work exists.  
- Do not invent teammate contributions.

Details: `docs/EXECUTION_CHECKLIST.md`.

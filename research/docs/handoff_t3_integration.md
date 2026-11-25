# T3 Handoff — Integration Summary and T1 Delivery

**Author:** Arman Ataeipour · **Date:** 2026-11-25 · **Branch:** `t3/experiment-integration`

This is the umbrella T3 handoff. Details live in
`handoff_t3_pilot.md` (validation + pilot) and
`handoff_t3_main_experiment.md` (main-v1.0). This file records what was
integrated, what changed in code, the disposition of prior contributions, and
exactly what T1 receives.

## 1. What T3 changed in code (all merged-history preserved; Stage 5 untouched)

| Change | Files | Why |
|---|---|---|
| Main-task index builds | `corpus_build.py` (`task_ids` param), `build_corpus_indexes.py` (`--task-id`) | Build script previously handled pilots only; smallest documented extension — retrieval method and pinned settings unchanged |
| Run-set labeling | `orchestrator.py` (`protocol_version` param), `run_method_a.py` / `run_method_b.py` (`--protocol-version`) | Trace records previously hardcoded `pilot-v1.0`; main runs must be labeled `main-v1.0` for provenance. Default unchanged (`pilot-v1.0`) |
| Evaluation scoping | `evaluate_pilot.py` (`--task-id` filter) | Prevents mixing pilot and main traces in one report |
| Task registry | `benchmark/tasks.json` (+4 records, verbatim from T2's `task_sets/t2_context_v1.json`) | Agent-visible prompts for the selected main tasks; loader leakage screens validated them |
| Frozen main config | `config/main_experiment.yaml` (new) | main-v1.0: task selection + rationale, GT version + SHA-256, run plan |
| Test expectation | `test_benchmark_stage3.py` | Task-registry assertion updated from "pilots only" to pilots + frozen main-v1.0 set |

Frozen `pilot-v1.0` values in `config/experiment.yaml` were not modified.

## 2. Disposition of Arman's earlier contribution (PR #2)

Audited before merge (reproduced its 106-passed/2-skipped test claim; verified
additive-only, no Stage 5/protocol changes). **Kept and merged** to `main` via
PR #2 after rebase. The search CLI (`scripts/search_index.py`) and smoke tests
(`tests/unit/test_retrieval_t1.py`) are complementary diagnostics; nothing in
the experiment path depends on them, and nothing was duplicated or rolled back.

## 3. Verification state (actual commands and outcomes)

| Check | Result |
|---|---|
| `python -m pytest tests/unit -q` (after all T3 changes) | **106 passed, 2 skipped** |
| Snapshot SHAs vs fresh Pi clone (`verify_benchmark.py --dry-run`) | 8/8 verified |
| Offline GT structural validation (`validate_benchmark.py`) | 8 tasks passed; human relevance review pending (T1) |
| Pilot trace audit (12 runs) | compliant; see `handoff_t3_pilot.md` §4 |
| Main trace audit (24 runs) | compliant; see `handoff_t3_main_experiment.md` |
| Metric spot-verification | all per-run P/R/F1 rows independently recomputed in-session; exact match |

## 4. What T1 receives

**Committed in the repo:**
- Frozen configs: `config/experiment.yaml` (pilot-v1.0), `config/main_experiment.yaml` (main-v1.0, incl. GT SHA-256 freeze)
- Task prompts: `benchmark/tasks.json` (6 tasks: 2 pilot + 4 main)
- Ground truth: `benchmark/ground_truth/` (pilot preliminary) and `benchmark/ground_truth/t2_context_v1/` (all 8, provisional pending T1 review)
- `results/run_manifest.json` — all 36 runs with status, config hash, stop reason, resource use, and **SHA-256 of every trace file**
- Evaluator: `scripts/evaluate_pilot.py` (preliminary T3 computations; T1's independent evaluation is authoritative)
- Handoffs: this file + pilot + main-experiment docs

**Local-only (gitignored by project policy) — requires out-of-band transfer:**
- 36 trace files: `results/raw/traces/*.json` + `runs.jsonl`
- Evaluation outputs: `results/processed/pilot_eval.json`, `results/processed/main_v1_eval.json`
- Indexes: `artifacts/indexes/<sha12>/` (reproducible from pinned settings)

Until the trace files are actually transferred, they are **not accessible to
T1** — verify any received copy against the SHA-256 hashes in
`results/run_manifest.json`. Everything else is reproducible from the repo
with an OpenRouter key (`handoff_t3_main_experiment.md` §Reproduction).

## 5. Remaining T1-owned work (not claimed complete)

1. Human relevance review of the frozen `t2_context_v1` annotations (incl. the
   G/H essential-containment caveat); version any changes; re-evaluate traces
   per version without combining.
2. Independent/authoritative evaluation (the committed evaluator is T3's
   preliminary tool, not the final word) + secondary metrics (MRR, nDCG) using
   essential=2 / supporting=1.
3. Research synthesis and the ~1,500-word draft; findings in
   `results/findings.md` (currently results-free).
4. Benchmark questions: C/E exclusions are T3 decisions open to revisit for a
   future run set; Candidate E needs fetch-by-SHA if ever included.

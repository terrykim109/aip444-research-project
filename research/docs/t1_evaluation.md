# T1 Independent Evaluation — Procedure, Artifact Status and Audit

**Author:** Rehat Preet Kaur (T1), AI-assisted · **Date:** 2026-11-26
**Status (updated 2026-11-26 evening):** T3 supplied his per-run evaluation files, but not the raw traces. T1 rescored all 36 runs from them (§8). Results are final for file-set metrics. They are **not trace-hash-verified**, and MRR, nDCG and the per-call Method B analysis remain unavailable.

## 1. Artifact verification

| Claim (T3 handoff) | How checked | Result |
|---|---|---|
| 12 pilot + 24 main runs, 36 total | `results/run_manifest.json` | **Verified (manifest):** 36 runs; 12 `pilot-v1.0`, 24 `main-v1.0`; all `status: completed`, `errors: []` |
| One configuration hash | manifest | **Verified (manifest):** `46b0be2d77a99062` on all 36 |
| Complete matched pairs | manifest: same task, snapshot, repetition, index build, config within each `paired_trial_id` | **Verified (manifest):** 18/18 pairs complete (6 pilot, 12 main), no mismatches |
| Distinct trace per run | manifest | 36 unique SHA-256 values |
| Main GT frozen | SHA-256 of `t2_context_v1/{D,F,G,H}.json` vs `config/main_experiment.yaml` | **Verified:** all four match |
| Raw traces + evaluation outputs available | searched `results/raw/`, `results/processed/`, git history and branches, stash, the connected project folder, and visible sibling folders | **MISSING:** only `.gitkeep` present; never committed (gitignored by design) |
| Trace SHA-256 = manifest | `python scripts/t1_verify_traces.py` | **Not possible:** 36/36 `missing` (command run 2026-11-26) |

**Effect (superseded in part by §8, where T3's per-run evaluation files were received and rescored):** every manifest field above is T3-recorded metadata. It is internally consistent but not independently checked against trace contents. All per-run precision, recall and F1 values, Method B behaviour, prompt-leakage and protocol-compliance claims stay **preliminary (T3)** until the traces arrive. No experiment was rerun: the completed runs are valid by their record, and rerunning would create a different dataset.

## 2. Ground-truth versions used
- `t2_context_v1` is the version frozen for and used during the main runs (provisional).
- `t1_reviewed_v1` is T1's reviewed version for the four main tasks. It adds one supporting file to F (`docs/t1_ground_truth_review.md`).
- `preliminary` (`benchmark/ground_truth/*.json`, v1.0) is the only set aligned with the pilot prompts.

Metrics are always computed and reported **per version**. Versions are never combined.

## 3. Evaluation procedure (`scripts/t1_evaluate.py`)
Written independently of T3's `evaluate_pilot.py`. It reuses no code from it and was audited against it (§4).

1. **Verify first.** Each manifest run is scored only if its trace exists, its SHA-256 matches, and task, method, repetition, pair id, protocol, snapshot, index, config and stop reason all agree with the manifest (`t1_verify_traces.py`). Other runs are listed under `excluded_runs` with a verdict (`missing`, `hash_mismatch` or `field_mismatch`). They are never repaired, replaced or silently dropped. A failed run with no evidence pack is a status issue, not a set of false negatives.
2. **Unit = unique file.** Evidence-pack chunks are collapsed to files. The file ranking is the order of first appearance (by `rank`).
3. **Path normalisation.** `\` becomes `/`, an absolute worktree prefix is stripped, and leading `./` or `/` and repeated `/` are removed. Case is preserved because Git paths are case-sensitive.
4. **Scores.** TP = retrieved files in GT, FP = retrieved files not in GT, FN = GT files not retrieved. P = TP/(TP+FP), R = TP/(TP+FN), F1 = 2PR/(P+R). An empty pack gets P = 0 (flagged `empty_pack`), and P+R = 0 gives F1 = 0. GT is non-empty by construction.
5. **Secondary.** Essential-file recall. MRR = 1/rank of the first GT file. nDCG@10 uses gains essential = 2, supporting = 1, unjudged = 0, with DCG = Σ gain/log₂(i+1) normalised by the ideal ordering. Also reported: pack chunks, files and tokens, cumulative evidence tokens, planning tokens, tool calls, latency and stop reason.
6. **Closed world.** Unjudged files count as non-relevant (disclosed limitation).
7. **Aggregation.** Per run, per task × method (mean of 3 repetitions), and per matched pair with F1(B) − F1(A). The summary of pair differences gives n, mean and sign counts. The task winner is decided by mean F1, with a tie when the difference is under 1e-9. **Macro** = mean of per-task means. **Pooled (micro)** = P/R/F1 from summed TP/FP/FN. No significance test is run: with n = 4 tasks and repetitions at temperature 0, the design does not support inferential claims.
8. **Separation.** One run set (`main-v1.0` or `pilot-v1.0`) and one annotation version per report. Output goes to `results/processed/t1_eval__<run_set>__<annotation_set>.{json,md}` and the report records `authoritative: true|false`.

Tests: `tests/unit/test_t1_evaluation.py` uses synthetic fixtures only, with no real-run data. It covers normalisation, deduplication, hand-computed P/R/F1/MRR/nDCG, end-to-end verify→evaluate→B-analysis, tampered-trace exclusion and the demo replay. **5 passed** (2026-11-26).

## 4. Audit of T3's preliminary evaluator (`scripts/evaluate_pilot.py`)
| Aspect | T3 | T1 | Consequence |
|---|---|---|---|
| Trace verification | none (reads whatever is in the folder) | SHA-256 + field match vs manifest | T1 cannot score unverified copies |
| Unit / dedup | unique `path` set | unique normalised path | identical when paths are already canonical |
| Path normalisation | none | yes | only matters if a trace holds non-canonical paths |
| Zero-denominator | P = 0 for empty pack, F1 = 0 | same, plus `empty_pack` flag | identical |
| Ranking metrics | not computed | MRR, nDCG@10 | new |
| GT sets | `preliminary`, `t2_context_v1` | + `t1_reviewed_v1` | new version |

The definitions agree, so T1's `t2_context_v1` scores should reproduce T3's numbers if the traces are intact. That reproduction is the first check to run once traces arrive.

**Internal-consistency check of T3's reported numbers** (arithmetic only, not a verification against traces): the main per-task means imply a mean pair difference of ((0.754−0.545)+(0.312−0.222)+(0.207−0.308)+0)·3/12 = **+0.049**, which matches T3's reported +0.049. The pilot pair differences (0, 0, +0.278; −0.214, +0.100, −0.167) match the reported task means (0.315−0.222; 0.406−0.500).

## 5. T3's combined "B 3 tasks, A 2, 1 tie" summary — not adopted
The tally is arithmetically right: pilot B and A under the `preliminary` GT, plus main H B, F B, D A and G tie under `t2_context_v1`. But it combines **two annotation versions and two prompt versions** (the pilot used the original short prompts, the main runs used the T2 prompts). The protocol forbids combining across annotation versions, and a single reviewed version cannot cover the pilot because `t2_context_v1`/`t1_reviewed_v1` annotate different prompt text. T1 therefore reports pilot and main **separately** and makes no combined win count.

## 6. Facts that are verifiable without traces
- **Method B final-pack construction (code, `method_b.py`):** if the agent finalises (`evidence_sufficient`/`no_new_relevant_evidence`), the pack holds the evidence ids it selected. If the loop stops on `call_limit_reached` or `evidence_budget_exhausted`, no ids are selected, and the pack **falls back to every excerpt charged during the run** (deduplicated and trimmed to 6,000 tokens). In the manifest, 7 of 12 main B runs stopped this way (F ×3 and G ×3 `call_limit_reached`, H r3 `evidence_budget_exhausted`). For those runs, B's final pack is its whole search history rather than a curated selection. That matters for interpreting precision.
- **Method B's first call** is a `semantic_search` with the unchanged task prompt and the same top-k (10) and index as Method A. So B's initial retrieval should equal A's final pack whenever the 6,000-token per-search cap binds equally. This can be confirmed per run only from traces (`a_final_equals_b_initial` in the B-analysis output).
- **Manifest-recorded resource use (T3-recorded, not trace-verified):**

| Run set | Method | Runs | Mean latency (ms) | Median latency (ms) | Planning tokens (mean / total) | Tool calls | Stop reasons |
|---|---|---|---|---|---|---|---|
| main-v1.0 | A | 12 | 716 | 246 | 0 / 0 | 1 ×12 | completed ×12 |
| main-v1.0 | B | 12 | 4,044 | 3,280 | 3,899 / 46,785 | 5×6, 4×4, 3×1, 2×1 | call_limit 6, sufficient 5, budget 1 |
| pilot-v1.0 | A | 6 | 144 | 145 | 0 / 0 | 1 ×6 | completed ×6 |
| pilot-v1.0 | B | 6 | 4,292 | 4,702 | 4,502 / 27,010 | 4×4, 5×2 | budget 2, sufficient 2, call_limit 2 |

The manifest `evidence_tokens` field is the **final-pack** size for A but the **cumulative charged** tokens for B, so the two are not directly comparable. T3 reports about $0.13 total API spend for the pilot session. No cost figure for the main runs is recorded in the repository.

## 7. To finish once traces are received (exact commands, from `research/`)
```sh
# copy the 36 *.json traces (+ runs.jsonl) into results/raw/traces/
python scripts/t1_verify_traces.py --output results/processed/t1_trace_verification.json   # expect 36 verified, exit 0
python scripts/t1_evaluate.py --run-set main-v1.0  --annotation-set t2_context_v1    # reproduce T3 (provisional GT)
python scripts/t1_evaluate.py --run-set main-v1.0  --annotation-set t1_reviewed_v1   # authoritative main result
python scripts/t1_evaluate.py --run-set pilot-v1.0 --annotation-set preliminary      # pilot, reported separately
python scripts/t1_analyze_method_b.py --run-set main-v1.0 --annotation-set t1_reviewed_v1
python scripts/t1_analyze_method_b.py --run-set pilot-v1.0 --annotation-set preliminary
```
If the traces are ever received, these commands add hash verification, MRR/nDCG and the per-call Method B analysis on top of the §8 results.

## 8. Rescore from T3's per-run evaluation files (done 2026-11-26)
- Received: `results/processed/main_v1_eval.json` (SHA-256 `cc232001…0441`) and `pilot_eval.json` (`e1bf67d2…bbe3`). Both are gitignored.
- Method (`scripts/t1_rescore_from_t3_eval.py`): retrieved set = (source GT − FN) ∪ FP for every row. It asserts that the rebuilt TP/FP/file counts equal the row values, and that every manifest run appears exactly once with matching stop reason, planning tokens, tool calls, evidence tokens and latency. **All 36 rows passed.** It then rescores with T1's `score()` against each GT version.
- Reproduction: against `t2_context_v1` and `preliminary`, the rescore equals T3's means and pair differences exactly.
- Outputs: `results/processed/t1_rescore__main-v1.0.json` (targets `t2_context_v1`, `t1_reviewed_v1`) and `t1_rescore__pilot-v1.0.json` (target `preliminary`). Results summary: `results/findings.md`.
- Remaining limits: no file order (no MRR/nDCG), no per-call trace data, and the eval files are not hash-pinned (mitigated by the manifest cross-check).

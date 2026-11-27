# Findings

**Status (2026-11-26, T1).** Both experiments were executed (36 runs). T3 sent his per-run evaluation files (`results/processed/main_v1_eval.json`, `pilot_eval.json`) but not the raw traces. T1 rebuilt each run's retrieved file set from those files, cross-checked all 36 rows against `run_manifest.json`, and rescored them independently (`scripts/t1_rescore_from_t3_eval.py` → `results/processed/t1_rescore__main-v1.0.json`, `t1_rescore__pilot-v1.0.json`). Against `t2_context_v1`, the rescore reproduces T3's numbers exactly. The results are not trace-hash-verified, and file order is unavailable, so there is no MRR or nDCG.

## Main experiment (`main-v1.0`), reviewed GT `t1_reviewed_v1` (primary)
| Task | A P / R / F1 | B P / R / F1 | Ess. recall A / B | Higher |
|---|---|---|---|---|
| H `pi_cli_mode_validation` | 0.375 / 1.000 / 0.545 | 0.767 / 0.889 / 0.754 | 1.00 / 1.00 | B |
| F `pi_rpc_context_statistics` | 0.333 / 0.500 / 0.400 | 0.290 / 0.833 / 0.426 | 1.00 / 1.00 | B |
| D `pi_package_dedup_collisions` | 0.333 / 0.286 / 0.308 | 0.389 / 0.143 / 0.207 | 0.33 / 0.33 | A |
| G `pi_session_directory_config` | 0.200 / 0.400 / 0.267 | 0.200 / 0.400 / 0.267 | 0.33 / 0.33 | tie |

- Pairs (B − A): +4 / −5 / 0×3, mean **+0.034**.
- Macro F1: A 0.380, B 0.413. Pooled F1: A 0.367, B 0.375 (equal pooled recall 0.474).
- Under `t2_context_v1` (as run): F A 0.222, B 0.312; pairs mean +0.049; other tasks unchanged; same winners.
- The F change raises both methods, because every A and B run retrieved `extensions/types.ts`. The GT decision was made and recorded before the per-run file lists were available.

## Method B behaviour (from file sets + manifest + code)
| B pack type | Runs | Mean files | P | R | F1 |
|---|---|---|---|---|---|
| Agent-selected (`evidence_sufficient`) | 5 | 2.6 | 0.63 | 0.42 | 0.48 |
| Fallback: all charged excerpts (call/token limit) | 7 | 10.6 | 0.25 | 0.67 | 0.36 |

- B's pack is a superset of A's pack in exactly the 7 fallback runs. This confirms that B's first search equals A's retrieval.
- G (3 runs): B's extra calls added no new file, so its pack is identical to A's.
- D: the agent's selected packs (2–3 files) dropped core files that A had found (`settings-manager.ts`), so recall fell from 0.29 to 0.14.
- Not available without traces: per-call queries, new files per call, duplicates, cumulative F1 by call.

## Pilot (`pilot-v1.0`, preliminary GT, separate prompts — not combined)
Lazy extension loading: A 0.222, B 0.315. Package filtering: A 0.500, B 0.406. Pairs +2 / −2 / 0×2, mean −0.001.

## Cost (manifest)
Main means: A 0.7 s and 0 planning tokens; B 4.0 s and about 3,900 planning tokens (latency medians 0.25 s vs 3.3 s).

## Interpretation
There is no reliable overall advantage for agent-directed search: 2 tasks won, 1 lost, 1 tied, near-equal pooled F1, at much higher cost. B does well when it finalises a curated pack and degrades to "A plus noise" when it runs out of budget. No significance is claimed (n = 4 tasks).

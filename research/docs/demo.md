# Demo Guide (1–2 minutes) — Method A vs Method B on the same task

Prepared by T1 (Rehat Preet Kaur), AI-assisted. **Default mode: replay of completed experiment artifacts.** The replay makes no API calls, costs nothing and does not touch the dataset.

## 1. Task and snapshot
- **Task:** H, `pi_cli_mode_validation`, repetition 1 (paired trial `pi_cli_mode_validation__r1`, run set `main-v1.0`).
- **Snapshot:** Pi parent commit `1a584a7a56eb5e7b4ff8ccbd46430f1533282eed` (target `e40126f…`, *fix(coding-agent): reject invalid --mode values*).
- **Why this task:** it is the easiest to explain (`--mode` should only accept `text`, `json` or `rpc`), and it has a small three-file ground truth. Because its preliminary result favours B, the optional counterexample (task D, where the preliminary result favours A) keeps the demo balanced.

## 2. Setup (no secrets needed for replay)
```sh
cd research
python -m venv .venv            # Windows: .venv\Scripts\activate ; macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
# Raw traces must be present (obtained from T3 out-of-band):
#   results/raw/traces/pi_cli_mode_validation__r1__one_shot_rag.json
#   results/raw/traces/pi_cli_mode_validation__r1__agent_directed.json
```
No `.env` is needed for replay. Never show `.env` on screen.

## 3. Commands
| Step | Command | Tested? |
|---|---|---|
| a. Prove the traces are the experiment's | `python scripts/t1_verify_traces.py` | **Tested 2026-11-26.** Runs correctly. With no traces present it reports `missing: 36` and exits 2. Expected with traces: `verified: 36`, exit 0. |
| b. Replay the pair | `python scripts/t1_demo_replay.py --task-id pi_cli_mode_validation --repetition 1` | **Tested on synthetic fixture traces** (`tests/unit/test_t1_evaluation.py::test_demo_replay_runs_on_verified_pair`, passed). On the real repo it currently stops with "Cannot replay: trace verification failed … missing" (exit 2), because the traces are absent. **Not yet run on the real traces.** |
| c. Same, without ground-truth labels (pure behaviour view) | add `--no-scores` | Same status as (b) |
| d. Optional counterexample | `python scripts/t1_demo_replay.py --task-id pi_package_dedup_collisions --repetition 1` | Same status as (b) |

## 4. What the presenter shows and says (≈1:40 total)
| Time | Screen | Say |
|---|---|---|
| 0:00–0:15 | Step (a) output | "These are the actual run files. Each one matches the SHA-256 recorded in our run manifest, so we are replaying the experiment, not re-running it." |
| 0:15–0:35 | Replay header + task prompt | "Both methods get exactly this prompt and search the same pre-change snapshot with the same index and the same 6,000-token budget." |
| 0:35–0:55 | "Method A" block | "Method A does one semantic search with the prompt and stops. Here are the files it returned: one call, no LLM tokens, well under a second." |
| 0:55–1:20 | "Method B" block (call list) | "Method B starts with that same search, then the LLM chooses more tools, like grep and read_file. Each line shows the tool, its arguments, the files found and the tokens charged. It stops when it judges the evidence sufficient or hits the 5-call or token limit." Point out `stop_reason` and `planning_tokens`. |
| 1:20–1:40 | "Offline score" block | "Only now do we compare against the evaluator-only labels. Here are each pack's precision, recall and F1. This is one task. On task D the preliminary result went the other way, which is why our conclusion is task-dependent." |

**A single search vs an iterative search:** A's whole output is the top-10 chunks of one embedding query. B's output depends on the tool calls the model chose. If B finalises, its pack is the evidence it selected. If it hits a limit, the pack falls back to every excerpt it was charged for (`method_b.py`).

## 5. Fallback (no traces, no laptop, or a failure while recording)
1. If the raw traces are ever received: use screenshots of a successful replay.
2. **Traces not received (current situation): use the recorded file sets.** `results/processed/t1_rescore__main-v1.0.json` (target `t1_reviewed_v1`) lists, for `pi_cli_mode_validation__r1`, A's 8 files (P 0.38, R 1.00, F1 0.55) and B's 2 files (P 1.00, R 0.67, F1 0.80, `evidence_sufficient`). Show them side by side with the manifest rows below. This is real recorded data, but it cannot show B's individual tool calls.
3. Otherwise, do not demo outputs. Show the committed artifacts instead: the task prompt (`benchmark/tasks.json`), the manifest rows for `pi_cli_mode_validation__r1` (`results/run_manifest.json`: A 1 call, 2,579 evidence tokens, 1.1 s; B 4 calls, 10,192 planning tokens, 9.2 s, `evidence_sufficient`), and the Method A/B code paths (`src/repo_search/method_a.py`, `method_b.py`). Label all of it "recorded metadata".

## 6. Optional separate live run — DEMO-ONLY, not part of the dataset
Use this only if the group explicitly wants a live call. It needs `.env` with `OPENROUTER_API_KEY` and `PI_REPO_PATH`, a Pi clone, a worktree (`scripts/prepare_worktrees.py … --task-id pi_cli_mode_validation --write-paths`) and the H index (`scripts/build_corpus_indexes.py --task-id pi_cli_mode_validation`).
```sh
python scripts/run_method_a.py --task-id pi_cli_mode_validation --repetition 99 --no-persist --protocol-version demo-only
python scripts/run_method_b.py --task-id pi_cli_mode_validation --repetition 99 --no-persist --protocol-version demo-only
```
- **Always pass `--no-persist`.** Without it the runner writes `results/raw/traces/<task>__r<rep>__<method>.json`, which pollutes the trace folder (and would overwrite a real trace if rep 1–3 were used).
- Label the output on screen "demo-only, not in the results". Never add it to the manifest or the metrics.
- Expected cost: one embedding call (A), plus up to six chat calls of a few thousand tokens each (B). That is a small fraction of T3's reported ≈$0.13 for the entire 12-run pilot session. **Untested by T1:** no API key or index was available in T1's environment, so these two commands have not been run.

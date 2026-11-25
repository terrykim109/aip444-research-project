# T3 Handoff — Main Experiment (main-v1.0)

**Author:** Arman Ataeipour · **Executed:** 2026-11-25 · **Branch:** `t3/experiment-integration`

## Status: EXECUTED — 24/24 runs completed, 12/12 matched pairs

The frozen configuration is `config/main_experiment.yaml` (`main-v1.0`). It
inherits every technical pin from `pilot-v1.0` unchanged — the single config
hash `46b0be2d77a99062` across all 36 project runs (12 pilot + 24 main) is the
machine-checkable evidence of that inheritance.

## Task selection (decided and frozen by T3, as assigned)

Selected from the 8 verified candidates using T2's pairwise overlap
measurements (`benchmark/reviews/t2_context_v1/overlap.csv`):

| Letter | Task | Decision | Evidence |
|---|---|---|---|
| D | `pi_package_dedup_collisions` | **selected** | distinct enough from remaining set (≤0.2 essential overlap vs selected tasks) |
| F | `pi_rpc_context_statistics` | **selected** | fully reachable snapshot; distinct essential set vs D/G/H |
| G | `pi_session_directory_config` | **selected** | distinct prompts/changes; see H caveat |
| H | `pi_cli_mode_validation` | **selected** | distinct prompts/changes; see caveat below |
| A, B | pilots | excluded | would duplicate pilot data under identical settings |
| C | `pi_package_progress_conflicts` | **excluded** | essential-file Jaccard **0.5** with D and 0.5 with pilot B — least distinct of the package cluster |
| E | `pi_network_retry` | **excluded** | essential-file Jaccard **1.0** with F (identical essential set: `agent-session.ts`) — not a distinct retrieval task; E also carries the fetch-by-SHA reproduction caveat |

**Caveat for T1:** H's single essential file (`cli/args.ts`) is contained in
G's essential set (Jaccard 0.33). Prompts and target changes are distinct
(CLI `--mode` validation vs session-directory env), so both were retained;
flagged for relevance review.

**Ground truth:** `t2_context_v1` set, **provisional pending T1 review**,
frozen by SHA-256 per task in `config/main_experiment.yaml`. Never exposed to
either method (verified: prompt leakage scan clean on all 24 traces). If T1's
review changes annotations, re-evaluate traces against the new version and
report versions separately — reruns are NOT required unless prompts,
snapshots, or execution conditions change (they are frozen).

## Execution record

- Plan: 4 tasks × 3 repetitions × 2 methods = **24 runs / 12 pairs**. All 24
  completed on the first attempt, exit 0 — no failures, retries, incomplete,
  or invalid runs. Statuses per run: `results/run_manifest.json` (committed,
  includes SHA-256 of each gitignored trace for transfer verification).
- Protocol compliance verified from the traces (not assumed): Method A exactly
  1 search / 0 LLM calls per run; Method B ≤5 tool calls; every evidence pack
  ≤6,000 tokens; identical prompt/snapshot/index/config within each pair;
  `protocol_version: main-v1.0` recorded on every trace.
- Indexes built with the pinned Stage 5 settings via the documented minimal
  extension (`build_corpus_indexes.py --task-id …`): D 4,012 / F 5,451 /
  G 6,250 / H 15,242 chunks.
- Worktrees: detached, clean, HEAD == pinned parent for all four snapshots
  (`prepare_worktrees.py --task-id … --write-paths`; manifest paths are
  machine-local and not committed).

## Preliminary results (T3 computation — T1's independent evaluation is authoritative)

File-level means over 3 repetitions vs frozen `t2_context_v1` GT
(`results/processed/main_v1_eval.json`; regenerate with
`scripts/evaluate_pilot.py --annotation-set t2_context_v1 --task-id …`):

| Task | Method A F1 | Method B F1 | Winner |
|---|---|---|---|
| `pi_cli_mode_validation` | 0.545 | **0.754** | B (precision 0.77 vs 0.38) |
| `pi_rpc_context_statistics` | 0.222 | **0.312** | B (recall 0.78 vs 0.33) |
| `pi_package_dedup_collisions` | **0.308** | 0.207 | A |
| `pi_session_directory_config` | 0.267 | 0.267 | tie (B's packs matched A's in all 3 reps) |

Matched-pair F1 differences (B − A), 12 pairs: positive 4, negative 5, zero 3;
mean ≈ **+0.049**. Combined with the pilot (B won 1 task, A won 1), the
cross-experiment picture: **B wins 3 tasks, A wins 2, 1 tie — a mild,
task-dependent advantage for agent-directed search, not a uniform one.**
Method B remains ~1–2 orders of magnitude slower and spends thousands of
planning tokens per run; Method A is free of LLM cost. No statistical
significance is claimed (n=4 tasks; GT provisional).

## Reproduction

```powershell
cd research; .\.venv\Scripts\activate   # .env: OPENROUTER_API_KEY, PI_REPO_PATH
python scripts/prepare_worktrees.py --repo-path <pi-clone> --worktree-root <root> `
  --task-id pi_package_dedup_collisions --task-id pi_rpc_context_statistics `
  --task-id pi_session_directory_config --task-id pi_cli_mode_validation --write-paths
python scripts/build_corpus_indexes.py --task-id pi_package_dedup_collisions `
  --task-id pi_rpc_context_statistics --task-id pi_session_directory_config `
  --task-id pi_cli_mode_validation
# per task, per rep 1..3: A then B
python scripts/run_method_a.py --task-id <task> --repetition <rep> --protocol-version main-v1.0
python scripts/run_method_b.py --task-id <task> --repetition <rep> --protocol-version main-v1.0
python scripts/evaluate_pilot.py --annotation-set t2_context_v1 --task-id <the 4 tasks> `
  --output results/processed/main_v1_eval.json
```

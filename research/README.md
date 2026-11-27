# Research package

The [project overview](../README.md) and [team handoff](../handoff_final.md)
live at the repository root. Run Python commands from this `research/` folder.

```sh
python -m venv .venv
# Activate .venv for your operating system.
python -m pip install -e ".[dev]"
python -m pytest tests/unit -q
```

See [T2 integration](docs/t2_integration.md) for benchmark review, portable Pi
worktree setup, source validation and the handoff to Arman and Rehat.

## Current status (2026-11-26, T1)

Experiments executed (36 runs). T1 has completed the ground-truth review
(`benchmark/ground_truth/t1_reviewed_v1/`), the independent evaluator and
trace-analysis tooling, the report draft, the presentation outline and the demo guide.
Results were rescored by T1 from T3's per-run evaluation files
(`scripts/t1_rescore_from_t3_eval.py`; summary in `results/findings.md`). Raw
traces were not transferred, so MRR/nDCG and per-call analysis are unavailable.

| Deliverable | Path |
|---|---|
| Research report (draft, APA, Appendices A–D) | [report.md](report.md) |
| Findings summary | [results/findings.md](results/findings.md) |
| T1 handoff | [docs/handoff_t1_final.md](docs/handoff_t1_final.md) |
| GT review + versions | [docs/t1_ground_truth_review.md](docs/t1_ground_truth_review.md) |
| Evaluation procedure, audit, completion commands | [docs/t1_evaluation.md](docs/t1_evaluation.md) |
| Presentation outline / demo guide | [docs/presentation_outline.md](docs/presentation_outline.md) · [docs/demo.md](docs/demo.md) |
| Submission checklist | [docs/final_submission_checklist.md](docs/final_submission_checklist.md) |
| Scripts | `scripts/t1_verify_traces.py`, `t1_evaluate.py`, `t1_analyze_method_b.py`, `t1_demo_replay.py`, `t1_build_reviewed_gt.py` |

Evaluate once traces are in `results/raw/traces/`:

```sh
python scripts/t1_verify_traces.py
python scripts/t1_evaluate.py --run-set main-v1.0 --annotation-set t1_reviewed_v1
python scripts/t1_evaluate.py --run-set main-v1.0 --annotation-set t2_context_v1
python scripts/t1_evaluate.py --run-set pilot-v1.0 --annotation-set preliminary
python scripts/t1_analyze_method_b.py --run-set main-v1.0 --annotation-set t1_reviewed_v1
```

## Status as of 2026-11-25 (T3, historical)

Both experiments are **executed**: `pilot-v1.0` (2 tasks, 12/12 runs) and
`main-v1.0` (4 tasks, 24/24 runs), zero failures, preliminary file-level
results computed. Start here:

- [handoff_t3_integration.md](docs/handoff_t3_integration.md) — umbrella T3 handoff (what T1 receives, what remains)
- [handoff_t3_main_experiment.md](docs/handoff_t3_main_experiment.md) — frozen `main-v1.0` config, task selection, results, reproduction
- [config/main_experiment.yaml](config/main_experiment.yaml) — frozen main config incl. ground-truth SHA-256
- [results/run_manifest.json](results/run_manifest.json) — all 36 runs with statuses and trace hashes

To reproduce runs you need `.env` (`OPENROUTER_API_KEY`, `PI_REPO_PATH`), a
local Pi clone, and machine-local worktrees
(`scripts/prepare_worktrees.py … --write-paths`). Raw traces and evaluation
outputs are gitignored — obtain them from Arman and verify against the
manifest hashes. Ground truth was provisional pending T1 relevance review
(superseded 2026-11-26: reviewed version `t1_reviewed_v1`; `t2_context_v1`
preserved as run).

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

## Current status (2026-11-25)

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
manifest hashes. Ground truth is provisional pending T1 relevance review.

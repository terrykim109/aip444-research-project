# T1 Final Handoff — Evaluation, Report, Presentation and Demo

**Author:** Rehat Preet Kaur (T1), AI-assisted (Claude Opus 5.5) · **Date:** 2026-11-26 · **Base:** central `main` @ `6f48982`

## T3 work verified
Verified from the repo: 36 completed runs (12 pilot, 24 main), all `completed` with no errors; 18/18 complete pairs matched on task, snapshot, repetition, index and config; one config hash `46b0be2d77a99062`; main GT SHA-256 equals the pins in `config/main_experiment.yaml`; `validate_benchmark.py` passes (8 tasks / 34 judgments / 49 spans) against a fresh Pi clone. T3's reported means are internally consistent (mean pair difference +0.049). No experiment was rerun.

## Benchmark and ground truth (**Done**)
- Main prompts D/F/G/H checked: no leakage, identical in `tasks.json` and the T2 task set.
- `t1_reviewed_v1` created (single reviewer, not fully blind, no traces seen). H, G and D are confirmed. F gains `core/extensions/types.ts` (supporting, the `ContextUsage` type). The original `t2_context_v1` is untouched. Hashes and change record: `benchmark/reviews/t1_reviewed_v1/changes.json`. Strict hash validation against Pi Git passes. Record: `docs/t1_ground_truth_review.md`.
- Validity finding: pilot and main used different prompt and annotation versions, so no combined pilot+main comparison is made. T3's "3/2/1" tally is not adopted.

## Artifact verification (**Partial**: traces never received; see the update at the end)
Raw traces and evaluation JSONs are **missing** (`results/raw/` and `results/processed/` hold only `.gitkeep`; nothing in history, branches or stash). `t1_verify_traces.py` reports 36/36 missing. No score is authoritative yet.

## Evaluation and findings (**Done** from T3's per-run files; see the update at the end)
`scripts/t1_evaluate.py` (verify-first, file-level P/R/F1, essential recall, MRR, nDCG@10, macro and pooled, pair diffs, per GT version) and `docs/t1_evaluation.md` (conventions, T3 evaluator audit, manifest cost table, exact completion commands). `results/findings.md` was rewritten. Preliminary values are labelled T3.

## Search-behaviour analysis (**Partial**)
`scripts/t1_analyze_method_b.py` covers per-call tools and queries, errors, new and relevant files, duplicates, tokens, cumulative P/R/F1, A vs B-initial vs B-final, and fallback detection. Verified now from code plus manifest: 7/12 main B packs are the "all charged excerpts" fallback. Trace-level findings are blocked.

## Literature and report (**Done (draft)**)
Four foundation papers verified against publisher records, and SWE-agent (NeurIPS 2024) added to `docs/literature_review.md`. `research/report.md` is a ≈1,540-word APA draft with 8 references (5 required scholarly papers, plus Järvelin & Kekäläinen, the Pi repository and OpenRouter docs) and Appendices A–D.

## Presentation and demo (**Done (outline/guide)**)
`docs/presentation_outline.md` (10 slides, ≈6:00, YouTube privacy inconsistency flagged) and `docs/demo.md`. Commands tested: `t1_verify_traces.py` (real repo; reports missing), `t1_demo_replay.py` (synthetic fixtures; real run blocked by missing traces), `validate_benchmark.py` (passed), `pytest tests/unit/test_t1_evaluation.py` (5 passed). Full unit suite in T1's Linux sandbox: 105 passed, 2 skipped, 6 failed only because the sandbox blocks tiktoken's encoding download (environmental, not a code defect). Not tested: the live `run_method_a/b.py --no-persist` demo-only commands (no key or index available).

## Appendices and documentation
Appendix A drafted (Rehat to annotate); B placeholders; C from commits; D structure only. `docs/ai_use_log.md`, `docs/contribution_log.md`, `docs/limitations.md`, the root `README.md` and `research/README.md` are updated. `docs/final_submission_checklist.md` is created.

## Remaining group actions
Trace transfer (Arman) → T1 completes evaluation and fills placeholders; reflections (all 4); report review; slides; dry run plus AI critique; YouTube privacy decision; recording; incognito link test; Blackboard submission.

## Update — 2026-11-26 evening: T3 evaluation files received
Arman sent `main_v1_eval.json` and `pilot_eval.json`, but not the raw traces. `scripts/t1_rescore_from_t3_eval.py` rebuilt all 36 file sets, cross-checked every row against the manifest (all pass), reproduced T3's numbers exactly, and rescored against `t1_reviewed_v1`.
- **Main (reviewed GT):** H B 0.754 / A 0.545; F B 0.426 / A 0.400; D A 0.308 / B 0.207; G tie 0.267. Pairs +4 / −5 / 0×3, mean +0.034. Pooled F1 B 0.375 vs A 0.367.
- **Method B:** agent-selected packs (5 runs) average 2.6 files, F1 0.48. Fallback packs (7 runs) average 10.6 files, F1 0.36, and always contain A's full pack.
- The report, findings, slide outline, demo fallback and checklist are updated. Result placeholders are gone; only group items remain.
- Still unavailable without traces: MRR/nDCG, per-call analysis, live replay demo.

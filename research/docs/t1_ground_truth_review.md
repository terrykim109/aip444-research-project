# T1 Benchmark and Ground-Truth Review (`t1_reviewed_v1`)

**Reviewer:** Rehat Preet Kaur (T1), with AI assistance (see Appendix A of `research/report.md`) · **Date:** 2026-11-26
**Reviewer count:** one. No second reviewer or peer review took part, so no inter-annotator agreement exists.
**Blindness:** not fully blind. T3's preliminary aggregate F1 tables (handoffs) had been read before the review. The raw traces and per-run evidence packs were **not available** during the review, so no file was judged with knowledge of which method retrieved it. Relevance was decided from the task prompt and the pinned parent snapshot only.

## 1. What was checked

| Item | Check | Result |
|---|---|---|
| Task prompts (`benchmark/tasks.json`, `task_sets/t2_context_v1.json`) | Main prompts D/F/G/H are byte-identical in both files; no SHAs, file paths, diffs or "ground truth" text in prompts | Pass |
| Input/evaluator separation | `benchmark_loader.method_input_bundle` + leakage screen; GT lives only under `benchmark/ground_truth/` | Pass (code inspection; T3 reports a clean leakage scan of all 24 traces — not re-verified, traces unavailable) |
| Pinned snapshots | Fresh public clone of `earendil-works/pi`; parent/target SHAs from `manifests/snapshots.json`; `git diff parent target` inspected for D, F, G, H and both pilots | Pass — targets have the recorded parents |
| GT integrity (`t2_context_v1`) | `scripts/validate_benchmark.py --repo-path <clone> --annotation-set t2_context_v1` | **passed** — 8 tasks, 34 file judgments, 49 spans (run 2026-11-26) |
| GT freeze | SHA-256 of the four main GT files vs `config/main_experiment.yaml` pins | All four match |
| Blob identity | `git rev-parse <parent>:<path>` vs `blob_sha` for every `t2_context_v1` file judgment | All match |
| Format | essential/supporting labels, rationales, symbols, line spans with content hashes | Complete for all judged files |

## 2. Relevance review — main tasks (pre-change parent snapshot)

Judging rule used: a file is relevant if a developer starting from the parent snapshot needs that pre-existing **code** to make the requested change (essential) or to preserve the stated compatibility constraint (supporting). Documentation/CHANGELOG edits made by the target are not counted as code evidence (prompts ask for "ranked code evidence"); files created by the target cannot be retrieved and are excluded.

| Task | T2 judgment | T1 decision | Reason (from parent code) |
|---|---|---|---|
| **H** `pi_cli_mode_validation` | `cli/args.ts` essential; `test/args.test.ts`, `main.ts` supporting | **Confirmed** | Target edits only the `--mode` branch of `parseArgs` in `args.ts`. `main.ts` lines 607–615 already print `parsed.diagnostics` and exit on error, so it is the propagation mechanism. Existing `--mode` tests are the compatibility baseline. |
| **G** `pi_session_directory_config` | `config.ts`, `main.ts`, `cli/args.ts` essential; `settings-manager.ts`, `session-manager.ts` supporting | **Confirmed** | Target adds `ENV_SESSION_DIR` + `expandTildePath` in `config.ts`, precedence in `main.ts` (`parsed.sessionDir ?? env ?? settings`), help text in `args.ts`. `SettingsManager.getSessionDir()` holds the existing tilde fallback; `session-manager.ts` holds the default per-cwd directory. `docs/settings.md`/`docs/usage.md` are docs, not code evidence. |
| **F** `pi_rpc_context_statistics` | `agent-session.ts` essential; `rpc-mode.ts`, `rpc-types.ts` supporting | **Changed: add `core/extensions/types.ts` (supporting)** | The fix adds `contextUsage?: ContextUsage` to `SessionStats` and fills it from `getContextUsage()`. The `ContextUsage` interface (`tokens: number \| null`, `contextWindow`, `percent: number \| null`, lines 245–251) is defined in `core/extensions/types.ts`; `agent-session.ts` only imports it. The prompt explicitly requires preserving "the existing representation for unknown usage", which is exactly this type. `rpc-client.ts` was considered and **not** added: like `rpc-types.ts` it only forwards `SessionStats`, so it adds no information beyond an already-judged file. |
| **D** `pi_package_dedup_collisions` | `package-manager.ts`, `resource-loader.ts`, `interactive-mode.ts` essential; `skills.ts`, `prompt-templates.ts`, `settings-manager.ts`, `extensions/loader.ts` supporting | **Confirmed** | Identity dedup + precedence live in `package-manager.ts`; collision aggregation (incl. themes, loaded via `loadThemeFromPath`) in `resource-loader.ts`; startup/reload listing in `interactive-mode.ts`. Considered and not added: `main.ts` (target changes the `pi list` command output, which the prompt does not ask for), `agent-session.ts` (type-adapter edit only), `theme.ts` (unchanged; theme collisions are handled in `resource-loader.ts`). |

### G/H containment caveat
H's single essential file (`cli/args.ts`) is also essential in G. The prompts and target changes differ (`--mode` validation vs session-directory precedence), and G needs four other files, so both tasks were kept. Effect: the two tasks are not fully independent retrieval problems, which slightly reduces the effective task count. Recorded as a limitation. The task set was not changed.

### C and E exclusions (T3 decisions)
Checked against `benchmark/reviews/t2_context_v1/overlap.csv`: E's essential set equals F's (`agent-session.ts`, Jaccard 1.0), and E needs fetch-by-SHA. C has essential-file Jaccard 0.5 with D and with pilot B. The exclusions are documented and reasonable. They were made before any main run, so they are not outcome-driven. Not revisited, because changing the task set after seeing results is prohibited.

## 3. Pilot annotations — not reviewed for a combined comparison

The pilot (`pilot-v1.0`) ran with the **original short pilot prompts** in `benchmark/tasks.json`. `t2_context_v1` annotates the **T2 prompts**, which are different text. The pilot GT (`benchmark/ground_truth/*.json`, version 1.0) is therefore the only set aligned with the pilot prompts. Because pilot and main differ in both prompt version and annotation version, T1 reports **no combined pilot+main comparison** (see `docs/t1_evaluation.md` §5). The pilot GT keeps its `preliminary_self_validated` status.

## 4. Versioned artifacts

| Artifact | Path | SHA-256 |
|---|---|---|
| Source set as used during the runs (unchanged) | `benchmark/ground_truth/t2_context_v1/` | pins in `config/main_experiment.yaml` |
| Reviewed set | `benchmark/ground_truth/t1_reviewed_v1/` (4 main tasks) | see table below |
| Change record | `benchmark/reviews/t1_reviewed_v1/changes.json` | — |
| Builder (deterministic, re-runnable) | `scripts/t1_build_reviewed_gt.py` | — |

| Task | Source SHA-256 (as run) | Reviewed SHA-256 | Changes |
|---|---|---|---|
| `pi_package_dedup_collisions` | `efd397fc56f65d58b85c0f9bf75db1ded12890c0a81ad75fe21acbea782486dd` | `6a1fbada1fba4ecefbc304c4ede2451d159bca9d9bd150761553611d9971b55f` | 0 (metadata only) |
| `pi_rpc_context_statistics` | `c0752cde3124ae769f4c45a29074988d76d67e0de9802c7fa915e16a53fdd60c` | `fbf0a18ad3a5d0093802b2b556868ad0012ecd208c99aa524456cc2c0ea1acb4` | +1 supporting file |
| `pi_session_directory_config` | `81f21a490e669578ff7d159fb6db3617d3daa0a522842cdaf05a98d140a7420a` | `848c9b8f41a229bd319e08a70c6d90fb691eb55f391c87313656f6e3a38560bd` | 0 (metadata only) |
| `pi_cli_mode_validation` | `af7193921a16351553a1ec229615064efd92301dbde245215d6d213e6c5b1b03` | `8afe60c73627e2e227348e7b15569df7c3d11ca098e9e0ce21af5dc73c150805` | 0 (metadata only) |

"Metadata only" means that `annotation_set`, `annotation_version` (`t1-1.0`), `review_status` (`validated`), `human_review_status` (`reviewed`), `review_detail` and one note were updated. No relevance judgment changed. All four reviewed files pass the project's strict integrity check against Pi Git: schema, blob SHAs, file and span content hashes, and parent/target identity (`benchmark_integrity.validate_annotation`, run 2026-11-26).

## 5. Limitations of this review
- One reviewer, so agreement could not be measured. A second independent review would strengthen validity.
- Not fully blind (preliminary aggregates were known).
- Under the closed-world convention, unjudged files count as non-relevant. A useful file outside the GT therefore lowers precision.
- Only the 4 main tasks were reviewed. The pilot and the C/E annotations remain T2's provisional judgments.

## 6. Timing note (added 2026-11-26 evening)
T3's per-run file lists arrived **after** `t1_reviewed_v1` was created and recorded. They show that every Method A and Method B run for F retrieved `core/extensions/types.ts`, so the review change raises F's scores for both methods equally in kind. Because the decision predates the file lists, it was not influenced by them. The change is kept, and results are reported for both versions.

---
title: "Agent-Directed Code Search Versus One-Shot Code RAG for Repository-Level Evidence Retrieval: A Controlled Study on the Pi Monorepo"
authors: "Arman Ataeipour, Nirajan Bhandari, Rehat Preet Kaur, Terry (Hyun Joon) Kim"
course: "AIP444 — Research Project"
date: "[TO BE COMPLETED — submission date]"
status: "DRAFT for group review. Prepared by T1 (Rehat Preet Kaur) with AI assistance; see Appendix A. Results rescored by T1 from T3 per-run evaluation files (raw traces not transferred)."
---

# Agent-Directed Code Search Versus One-Shot Code RAG for Repository-Level Evidence Retrieval

## Introduction

Coding agents increasingly operate inside large repositories where the behaviour relevant to a change is spread across configuration code, command-line parsing, core services and tests. Before an agent can modify such a system, it must first gather the right context, and an evidence pack that misses an essential file, or buries it among irrelevant ones, undermines everything that follows. Two families of context-gathering strategies dominate current practice. One-shot retrieval-augmented generation (RAG) embeds the task description, runs a single semantic search over a code index and passes the top results to the model. Agent-directed search instead lets a language model issue repository tools iteratively—searching, reading files, grepping and refining queries—before deciding what evidence to keep.

Agent-directed search is widely assumed to be better because it can follow leads, but it costs more time and model tokens, and extra searching can add noise. This project asks: **Does agent-directed code search outperform one-shot code RAG on repository-level software engineering tasks?** We compare Method A (one semantic search produces the final evidence pack) with Method B (an LLM uses repository-search tools iteratively to produce the final evidence pack) under identical snapshots, index, prompts and budgets. The primary outcome is evidence retrieval quality, measured by file-level F1 against evaluator-only relevance annotations; implementation success is out of scope.

Our contribution is a small, fully pinned benchmark of six real tasks from the open-source Pi monorepo (Earendil Works, n.d.), a reproducible two-method harness, and an evaluation that distinguishes provisional from reviewed ground truth. The evidence is exploratory: four main tasks cannot support general claims, and we report it that way.

## Background and Literature Review

Repository-level code intelligence has mainly been studied through code completion. RepoBench (Liu et al., 2024) separates repository-level completion into a retrieval task (finding relevant cross-file snippets), a completion task and an end-to-end pipeline, and scores retrieval on its own with accuracy@k. This separation directly motivates our decision to score the evidence pack rather than downstream code. RepoCoder (Zhang et al., 2023) shows that iterating retrieval and generation—using a first draft to retrieve better context—can outperform a single retrieval pass for completion. Method B is inspired by this idea of iterative refinement, but it is an agent-driven search strategy, not a reimplementation of RepoCoder.

Two further studies caution against assuming that more retrieval is better. Repoformer (Wu et al., 2024) reports that many retrieved contexts are unhelpful or even harmful and that retrieving selectively preserves quality while substantially reducing inference cost; we therefore track precision and resource use alongside recall. CodeRAG-Bench (Wang et al., 2025) evaluates retrieval separately from generation using annotated canonical documents and finds that retrievers often fail to surface useful context; its annotation practice informed T2's essential/supporting labels with written rationales and pre-change existence checks.

The closest setting to Method B is SWE-agent (Yang et al., 2024), in which an LM agent resolves repository issues through an agent–computer interface that includes file and directory search commands. Its ablations show that interface design matters: an interactive "step through each match" search performed worse than providing no search tools, because agents spent their budget stepping through results. This warns that an agent's benefit depends on its tools and limits, not only on iteration.

These works differ from ours in an important way. RepoBench, RepoCoder and Repoformer study code completion, CodeRAG-Bench studies retrieval for code generation, and SWE-agent measures end-to-end issue resolution. None isolates search strategy while holding the retriever, index and evidence budget fixed and scoring task-based evidence retrieval. We borrow their principles—separate retrieval evaluation, caution about irrelevant context, attention to cost and interface design—but their reported results are not our results, and none is an experimental arm here. For ranking quality we use normalized discounted cumulative gain with graded relevance (Järvelin & Kekäläinen, 2002).

## Methodology, Implementation, and Results

**Benchmark.** Eight candidate tasks were derived from real Pi commits. Prompts describe the required behaviour without naming files, and methods search the Git-verified *parent* (pre-change) snapshot, so the answer cannot be retrieved from the future. Two tasks formed the pilot (`pilot-v1.0`: lazy extension loading, package filtering). Four tasks formed the main experiment (`main-v1.0`): package deduplication/collisions (D), RPC context statistics (F), session-directory configuration (G) and CLI mode validation (H). Two candidates were excluded before the main runs because their essential files overlapped heavily with selected tasks (Jaccard 0.5 and 1.0).

**Ground truth.** Annotations list each relevant pre-existing file as *essential* or *supporting*, with rationale, symbols and hashed line spans. They are never visible to either method. The main runs used T2's provisional set `t2_context_v1`, frozen by SHA-256. T1 reviewed it against the pinned snapshots and confirmed three tasks. For F, T1 added `core/extensions/types.ts` as supporting, because it defines the `ContextUsage` representation the prompt requires to be preserved. The reviewed set is stored separately as `t1_reviewed_v1`.

**Shared controls.** Both methods use the same Stage 5 retriever: code chunks embedded with `text-embedding-3-small` through OpenRouter (OpenRouter, n.d.) and cosine search in a NumPy index built per snapshot. They also share the same prompt, top-k = 10 and a 6,000-token evidence budget. Method A issues exactly one search with the unchanged prompt and makes no LLM calls. Method B begins with that same search and then lets `openai/gpt-6-luna` (temperature 0) call `semantic_search`, `read_file`, `find_symbol` and `grep`, up to five tool calls in total, with every returned excerpt charged cumulatively to the budget. If the agent does not finalise before a limit is reached, its pack falls back to all charged excerpts.

**Design.** Three repetitions per task and method gave 24 main runs (12 matched pairs) and 12 pilot runs. All 36 completed without errors under one configuration hash.

**Evaluation.** Files are deduplicated per pack, and precision, recall, F1 and essential-file recall are computed over unique files. The raw traces stayed on T3's machine. From T3's per-run evaluation files, which list each run's matched, extra and missed files, T1 rebuilt every retrieved file set, checked all 36 rows against the run manifest, and rescored each set independently. Rescoring against `t2_context_v1` reproduced T3's numbers exactly. Results below use the reviewed set, `t1_reviewed_v1`.

*Table 1. Main results, mean of 3 repetitions (`t1_reviewed_v1`).*

| Task | A: P / R / F1 | B: P / R / F1 | Higher F1 |
|---|---|---|---|
| H — CLI mode validation | 0.38 / 1.00 / 0.55 | 0.77 / 0.89 / 0.75 | B |
| F — RPC context statistics | 0.33 / 0.50 / 0.40 | 0.29 / 0.83 / 0.43 | B |
| D — Package dedup/collisions | 0.33 / 0.29 / 0.31 | 0.39 / 0.14 / 0.21 | A |
| G — Session directory | 0.20 / 0.40 / 0.27 | 0.20 / 0.40 / 0.27 | tie |

Matched-pair differences F1(B) − F1(A) were positive in 4 pairs, negative in 5 and zero in 3, with a mean of +0.034 (+0.049 under the provisional set). Macro F1 was 0.41 for B and 0.38 for A. Pooled over all runs, the two methods were nearly identical (0.375 vs 0.367) with equal recall. The review changed F's scores for both methods, because every run had retrieved the newly judged file, but no task's winner changed. The pilot, which used different prompts and preliminary labels, also split: B scored higher on lazy extension loading (0.32 vs 0.22) and A on package filtering (0.50 vs 0.41), with a mean pair difference of −0.001.

**Cost.** Method B was far more expensive. Main-experiment latency averaged 4.0 s versus 0.7 s for A (medians 3.3 s versus 0.25 s), and B used about 3,900 planning tokens per run, whereas A used none.

## Critical Analysis

The decisive factor was not iteration itself but how Method B ended. In the five runs where the agent chose its evidence, its packs were small and precise: 2.6 files on average, with mean precision 0.63 and F1 0.48. In the seven runs that hit the call or token limit, the pack defaulted to everything the agent had retrieved: 10.6 files, with precision 0.25 and F1 0.36. Each of those seven packs contained Method A's complete pack, confirming that B's first search reproduces A. In the three G runs, B's later calls added no new file, so its pack was identical to A's. Selection could also discard relevant evidence: on task D, the agent's three-file packs dropped core files that the one-shot search had returned. B's value therefore depends on its stopping rule and selection step, echoing SWE-agent's finding that interface design shapes agent behaviour (Yang et al., 2024).

The evidence is limited. There are four main tasks from one repository, with three deterministic repetitions each, so no significance test is meaningful. The ground truth was reviewed by one non-blind reviewer, and unjudged files count against precision. Tasks G and H share an essential file. MRR, nDCG and call-by-call analysis require the raw traces, which T1 did not receive. Retrieval quality is also only a proxy for implementation success.

## Conclusion

We compared one-shot semantic retrieval with agent-directed iterative search under tightly shared controls on real Pi tasks. Agent-directed search did not reliably outperform one-shot RAG: it won two tasks, lost one and tied one, and pooled F1 was almost identical. Meanwhile it cost about 6× the mean latency (13× the median) plus thousands of planning tokens per run. Its strongest results came when the agent finalised a short, curated pack; when it ran out of budget it simply returned an enlarged version of the one-shot result. For practitioners, this suggests using agent-directed search selectively, and investing in its stopping and selection logic rather than in more search calls. Future work should add tasks and repositories, a second annotator, ranked metrics from full traces, and a link between evidence quality and patch success.

## References

Earendil Works. (n.d.). *Pi* [Computer software]. GitHub. Retrieved November 26, 2026, from https://github.com/earendil-works/pi

Järvelin, K., & Kekäläinen, J. (2002). Cumulated gain-based evaluation of IR techniques. *ACM Transactions on Information Systems, 20*(4), 422–446. https://doi.org/10.1145/582415.582418

Liu, T., Xu, C., & McAuley, J. (2024). RepoBench: Benchmarking repository-level code auto-completion systems. In *Proceedings of the Twelfth International Conference on Learning Representations (ICLR 2024)*. https://proceedings.iclr.cc/paper_files/paper/2024/file/d191ba4c8923ed8fd8935b7c98658b5f-Paper-Conference.pdf

OpenRouter. (n.d.). *Embeddings* [API documentation]. Retrieved November 26, 2026, from https://openrouter.ai/docs/api/reference/embeddings

Wang, Z. Z., Asai, A., Yu, X. V., Xu, F. F., Xie, Y., Neubig, G., & Fried, D. (2025). CodeRAG-Bench: Can retrieval augment code generation? In *Findings of the Association for Computational Linguistics: NAACL 2025* (pp. 3199–3214). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.findings-naacl.176

Wu, D., Ahmad, W. U., Zhang, D., Ramanathan, M. K., & Ma, X. (2024). Repoformer: Selective retrieval for repository-level code completion. In *Proceedings of the 41st International Conference on Machine Learning* (Proceedings of Machine Learning Research, Vol. 235, pp. 53270–53290). PMLR. https://proceedings.mlr.press/v235/wu24a.html

Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., & Press, O. (2024). SWE-agent: Agent-computer interfaces enable automated software engineering. In *Advances in Neural Information Processing Systems 37 (NeurIPS 2024)*. https://doi.org/10.52202/079017-1601

Zhang, F., Chen, B., Zhang, Y., Keung, J., Liu, J., Zan, D., Mao, Y., Lou, J.-G., & Chen, W. (2023). RepoCoder: Repository-level code completion through iterative retrieval and generation. In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing* (pp. 2471–2484). Association for Computational Linguistics. https://doi.org/10.18653/v1/2023.emnlp-main.151

---

# Appendices

## Appendix A — AI Use Documentation

### AI Tools Used
| Tool / model | Used by | Recorded in |
|---|---|---|
| Cursor agent (Composer) | Terry (Hyun Joon) Kim | `docs/ai_use_log.md` (Stages 1–6) |
| ChatGPT / Codex (model id not recorded) | Nirajan Bhandari | `docs/ai_use_log.md` (T2 section) |
| Claude Code (Claude Fable 5) | Arman Ataeipour | `docs/ai_use_log.md` (T1 PR #2, T3, Stages 7–8) |
| Claude (Claude Opus 5.5), Claude app linked to the local repository | Rehat Preet Kaur | `docs/ai_use_log.md` (T1 final) |
| `openai/gpt-6-luna` via OpenRouter | Experiment only (Method B agent) | `config/experiment.yaml`; an experimental component, not writing assistance |
| `openai/text-embedding-3-small` via OpenRouter | Experiment only (shared retriever) | `config/experiment.yaml` |

### AI Use Log
Rows are taken from the project's AI use log. Text in [brackets] must be completed by the named member, because the exact prompts were not recorded in the repository.

| Stage | Tool | Purpose | What You Asked | How You Used the Output |
|---|---|---|---|---|
| Design / setup (Stages 1–4) — Terry | Cursor (Composer) | Scaffold the research workspace, protocol, schemas, snapshot verification, pilot prompts and GT | [Terry: add a representative prompt] | Reviewed the generated code/docs; verified Pi SHAs and pilot annotations against parent worktrees; froze protocol `pilot-v1.0` |
| Code (Stages 5–6) — Terry | Cursor (Composer) | Build the corpus/embedding retriever, Methods A/B, orchestration and tests | [Terry: add a representative prompt] | Reviewed the code; verified with a live embedding probe and unit tests before any runs |
| Benchmark (T2) — Nirajan | ChatGPT / Codex | Build the 8-task annotation set, validation tooling and worktree reproduction | [Nirajan: add a representative prompt] | Checked task identities against GitHub/Git objects; recorded validation results; human relevance sign-off left to review |
| Research (T2) — Nirajan | ChatGPT / Codex | Verify CodeRAG-Bench and its relevance | [Nirajan: add prompt] | Checked the ACL Anthology record and PDF sections before citing |
| Code / experiment (T3) — Arman | Claude Code (Claude Fable 5) | Integrate and re-verify, run pilot and main experiments, preliminary evaluator, handoffs | [Arman: add a representative prompt] | Reviewed traces, evaluator code and reported numbers before merging; all 36 runs real, single config hash |
| Analysis (T1) — Rehat | Claude (Opus 5.5) | Verify T3's artifacts; support the GT review; write the evaluator, rescoring and analysis scripts | Task brief: "Complete T1's remaining research and presentation-preparation work… verify T3's completed work… do not fabricate results" (full brief kept by Rehat) | Every GT decision checked against Pi source; scripts tested on fixtures; rescore reproduced T3's numbers exactly before use. [Rehat: confirm you reviewed the F annotation change] |
| Research (T1) — Rehat | Claude (Opus 5.5) | Verify the 4 foundation papers and find a 5th | Same brief, section 5 (literature) | Bibliographic details checked against NeurIPS/ACL/PMLR/ICLR pages; SWE-agent added after reading its ablation section |
| Writing (T1) — Rehat | Claude (Opus 5.5) | Draft the report, slide outline, demo guide and checklist | Same brief, sections 6–9 | Used as a first draft. [Group: describe which sections you rewrote in your own words and what you changed or rejected] |
| Presentation dry run — group | [tool] | Critique the dry-run transcript and slides | [prompt — see Appendix D] | [see Appendix D] |

Integrity statement: experimental results come from the recorded runs. No AI-generated number was accepted without a source artifact. All citations were checked against primary records.

## Appendix B — Individual Reflections

Each member writes and approves their own 200–300-word reflection. Nothing below has been written on anyone's behalf.

- **Arman Ataeipour** — [TO BE COMPLETED by Arman]
- **Nirajan Bhandari** — [TO BE COMPLETED by Nirajan]
- **Rehat Preet Kaur** — [TO BE COMPLETED by Rehat]
- **Terry (Hyun Joon) Kim** — [TO BE COMPLETED by Terry]

Prompts: your responsibilities and what you actually delivered; one technical or coordination challenge; what you learned about repository-level retrieval or experimental design; how AI assistance affected your work; what you would change in a follow-up study.

## Appendix C — Group Contribution Breakdown

### Research and implementation (from commits and project logs)
| Member | Role | Recorded contributions |
|---|---|---|
| Terry (Hyun Joon) Kim | T0 / EXP — experimental design and core implementation | Commits `e710d62`, `beacd86`: Stages 1–6 (protocol freeze, snapshot verification, pilot prompts/GT, corpus and Stage 5 retriever, Methods A/B, orchestration, tests) |
| Nirajan Bhandari | T2 — repository context engineering and validation | PR #1 (`eb9c0f3`): 8-task `t2_context_v1` set and annotations, Candidate E resolution, overlap analysis, loader isolation, validation tooling, CodeRAG-Bench source. Separate RAG implementation not delivered. |
| Arman Ataeipour | T3 — integration and experiment execution (also authored retrieval PR #2) | PRs #2–#4: search CLI and smoke tests; independent re-verification; pilot (12 runs) and main (24 runs) execution; preliminary evaluator; main-v1.0 freeze; run manifest; handoffs; supplied the per-run evaluation files |
| Rehat Preet Kaur | T1 — final evaluation, research synthesis, presentation preparation | GT review (`t1_reviewed_v1`); verifier, evaluator, rescoring, Method B analysis and demo scripts with tests; final results from T3's per-run files; literature verification and SWE-agent; report draft; presentation outline; demo guide; submission checklist; documentation reconciliation (AI-assisted, see Appendix A) |

### Report, slides and video
Fill in this table with what each person actually did. Do not pre-assign.

| Task | Arman | Nirajan | Rehat | Terry |
|---|---|---|---|---|
| Report: drafting | — | — | First full draft (AI-assisted) | — |
| Report: editing / rewriting sections | [ ] | [ ] | [ ] | [ ] |
| Report: APA formatting and PDF | [ ] | [ ] | [ ] | [ ] |
| Slides: outline | — | — | Outline (AI-assisted) | — |
| Slides: building the deck | [ ] | [ ] | [ ] | [ ] |
| Dry run: participation | [ ] | [ ] | [ ] | [ ] |
| Dry run: AI critique and Appendix D | [ ] | [ ] | [ ] | [ ] |
| Video: presenting (slide numbers) | [ ] | [ ] | [ ] | [ ] |
| Video: demo segment | [ ] | [ ] | [ ] | [ ] |
| Video: recording / editing / upload | [ ] | [ ] | [ ] | [ ] |
| Blackboard submission | [ ] | [ ] | [ ] | [ ] |

Effort percentages are not recorded in the project logs. [Group: add agreed shares, if you want to include them.]

## Appendix D — AI Dry-Run Feedback

The group has not yet completed a presentation dry run or AI critique.

| Item | Status |
|---|---|
| Dry-run recording or transcript link | [TO BE COMPLETED] |
| AI tool(s) and prompt(s) used for critique | [TO BE COMPLETED] |
| Feedback received | [TO BE COMPLETED] |
| Improvements made | [TO BE COMPLETED] |
| Suggestions not adopted, with reasons | [TO BE COMPLETED] |

# Literature Foundation

This document summarises the scholarly papers that inform our methodology (originally three; CodeRAG-Bench was added by T2 and SWE-agent by T1 — see the final sections). It does **not** invent numerical performance results or treat these systems as additional experimental arms. Our primary experiment remains the two-method comparison:

- **Method A — One-shot code RAG**
- **Method B — Agent-directed code search**

The papers originally study **repository-level code completion**. Our study investigates **issue-based / task-based retrieval quality** for coding agents. We borrow evaluation and design principles, not their exact task formulations or reported scores.

---

## 1. RepoBench (2024)

**Title:** RepoBench: Benchmarking Repository-Level Code Auto-Completion Systems  
**Link:** https://proceedings.iclr.cc/paper_files/paper/2024/file/d191ba4c8923ed8fd8935b7c98658b5f-Paper-Conference.pdf

### What it contributes (high level)

RepoBench is a benchmark aimed at repository-level code auto-completion. It emphasises that useful context often spans multiple files, and that retrieval and completion should be evaluated carefully rather than collapsed into a single opaque score.

### Design decisions it motivates for us

| Principle | How we apply it |
|---|---|
| Separate retrieval evaluation from downstream completion | Primary outcome is **retrieval quality**, not whether generated code passes tests or compiles. |
| Repository-level / cross-file context | Tasks and annotations assume evidence may live across multiple Pi packages and modules. |
| Explicit relevance annotations | Ground truth (evaluator-only) will record required files, essential vs supporting relevance, symbols, and line spans. |
| Multiple relevant files and sections | Annotation schema supports multi-file, multi-span gold sets. |

### Limitations relative to our study

RepoBench targets code auto-completion benchmarks. We do not reproduce its datasets or claim equivalence. Our prompts are issue-style investigation tasks on Pi snapshots, not completion masks from RepoBench.

---

## 2. RepoCoder (2023)

**Title:** Repository-Level Code Completion Through Iterative Retrieval and Generation  
**Link:** https://aclanthology.org/2023.emnlp-main.151/

### What it contributes (high level)

RepoCoder studies iterative retrieval interleaved with generation for repository-level completion: retrieve, use retrieved context, refine, and retrieve again rather than relying on a single static retrieval pass.

### Design decisions it motivates for us

| Principle | How we apply it |
|---|---|
| Iterative retrieval and query refinement | Method B may search, inspect files/symbols, notice gaps, refine queries, and search again. |
| Record each retrieval iteration | Planned logging will capture per-iteration queries, hits, and inspections. |
| Define stopping conditions | Agent tool-call limit and evidence-token budget bound Method B (preliminary: 5 tool calls; 6,000 evidence tokens). |
| Ask whether extra searches add useful context | Evaluation will examine whether later iterations introduce new relevant evidence or noise. |

### Important distinction

**Our agent-directed approach is inspired by iterative retrieval but is not an exact reproduction of RepoCoder.** We do not claim to reimplement RepoCoder’s full pipeline, generation loop, or reported completion metrics. Method B is an agent-directed *search* strategy under shared corpus/index controls; generation success is not the primary outcome.

### Limitations relative to our study

RepoCoder couples iterative retrieval with code generation for completion. We isolate search strategy and score the evidence pack against annotations. Shared controls (snapshot, chunking, index, budgets) keep the comparison focused on search behaviour.

---

## 3. Repoformer (2024)

**Title:** Repoformer: Selective Retrieval for Repository-Level Code Completion  
**Link:** https://proceedings.mlr.press/v235/wu24a.html

### What it contributes (high level)

Repoformer addresses selective retrieval: more context is not automatically better. Irrelevant retrieved material can hurt, so systems should consider when and what to retrieve, and evaluate quality alongside cost.

### Design decisions it motivates for us

| Principle | How we apply it |
|---|---|
| Do not assume more retrieval always helps | Method B’s extra searches are a hypothesis to test, not a guaranteed improvement. |
| Account for irrelevant context | Evidence-pack quality and precision-oriented metrics complement recall. |
| Measure quality with resource consumption | Log tool-call counts, unique files inspected, and evidence-token usage. |
| Investigate diminishing returns | Analysis will ask whether later iterations add essential evidence or mostly redundancy/noise. |

### Limitations relative to our study

Repoformer proposes selective retrieval mechanisms in a completion setting. We do not implement Repoformer as Method C. Its caution about irrelevant context and cost informs our metrics and interpretation only.

---

## Synthesis for this project

| Paper | Motivates | Does **not** become |
|---|---|---|
| RepoBench | Retrieval-vs-downstream separation; multi-file relevance annotations | Our benchmark dataset |
| RepoCoder | Iterative search logging, refinement, stopping rules | A third experimental method or exact reimplementation |
| Repoformer | Scepticism about “more context”; quality + cost; diminishing returns | A selective-retrieval baseline arm |

**Fixed research question (unchanged):**  
Does agent-directed code search outperform one-shot code RAG for repository-level software engineering tasks?

**Primary outcome:** retrieval quality of the **final evidence pack** under identical shared controls (same T1 retriever/index for Methods A and B).

### Evaluation ownership note (Stage 1.5)

Literature motivates *what* to measure; team roles decide *who* implements which metric family:

| Principle source | Example measures | Owner |
|---|---|---|
| RepoBench | Explicit relevance annotations; retrieval vs completion separation | T2 annotations; EXP scores pack quality (P/R/F1, essential-file recall) |
| RepoCoder | Iteration traces, refinement, stopping | EXP Method B logging |
| Repoformer | Usefulness + efficiency; diminishing returns | EXP primary cost/quality; T3 may add MRR/nDCG/viz without redefining core P/R/F1 |

---

## Citation integrity note

This document summarises methodological *principles* drawn from the named papers and public links above (Stage 1 foundation; Stage 1.5 ownership note added). It does **not** invent abstract findings, benchmark leaderboard numbers, or statistical results. When writing the group report, cite the original papers directly and verify claims against the PDFs.

## T2 additional source: CodeRAG-Bench

Wang et al. (2025), Sections 2.3–2.4, describe canonical-document annotations and separate retrieval evaluation from generation correctness. Their repository examples include RepoEval snippets and SWE-bench edited files. For our historical Pi tasks, an edited-file proxy can include future-created files and omit useful unchanged context. T2 therefore checks pre-change existence and source spans, records essential/supporting rationales, and keeps retrieval scoring separate from application-test execution. These are our adaptations, not a reproduction or evidence that Method B wins. Human label agreement remains a separate requirement.

Wang, Z. Z., Asai, A., Yu, X. V., Xu, F. F., Xie, Y., Neubig, G., & Fried, D. (2025). CodeRAG-Bench: Can retrieval augment code generation? In *Findings of the Association for Computational Linguistics: NAACL 2025* (pp. 3199–3214). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.findings-naacl.176

Primary record and PDF verified: https://aclanthology.org/2025.findings-naacl.176/

---

## T1 verification of the scholarly foundation (2026-11-26)

T1 checked each entry against its primary publisher record. Bibliographic details below are as verified; claims used in the report are limited to what the primary record supports.

| Paper | Verified record | Claim the project relies on | Status |
|---|---|---|---|
| Liu, Xu & McAuley (2024) RepoBench | ICLR 2024 proceedings PDF (link above) | Three tasks — RepoBench-R (retrieval of cross-file snippets), -C (next-line completion), -P (pipeline); retrieval scored separately with accuracy@k | Verified |
| Zhang et al. (2023) RepoCoder | EMNLP 2023, pp. 2471–2484, doi:10.18653/v1/2023.emnlp-main.151 | Iterative retrieval–generation loop for repository-level completion; reported to beat in-file and vanilla-RAG baselines | Verified (authors: F. Zhang, B. Chen, Y. Zhang, J. Keung, J. Liu, D. Zan, Y. Mao, J.-G. Lou, W. Chen) |
| Wu et al. (2024) Repoformer | ICML 2024, PMLR 235, pp. 53270–53290 | Always-retrieve is wasteful: many retrieved contexts are unhelpful or harmful; selective retrieval keeps quality while cutting inference cost | Verified (authors: D. Wu, W. U. Ahmad, D. Zhang, M. K. Ramanathan, X. Ma) |
| Wang et al. (2025) CodeRAG-Bench | Findings of NAACL 2025, pp. 3199–3214, doi:10.18653/v1/2025.findings-naacl.176 | Retrieval evaluated separately from generation with canonical-document annotations; retrievers often fail to fetch useful context | Verified (T2 entry above confirmed) |

Correction note: the RepoCoder title in Section 2 omits the "RepoCoder:" prefix; the verified full title is *RepoCoder: Repository-level code completion through iterative retrieval and generation*.

## T1 additional source: SWE-agent (agent-directed repository search)

Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., & Press, O. (2024). SWE-agent: Agent-computer interfaces enable automated software engineering. In *Advances in Neural Information Processing Systems 37 (NeurIPS 2024)*. https://doi.org/10.52202/079017-1601

Primary records checked: NeurIPS 2024 proceedings abstract page (https://papers.neurips.cc/paper_files/paper/2024/hash/5a7c947568c1b1328ccc5230172e1e7c-Abstract-Conference.html) and the paper full text.

**Why it is relevant.** The four foundation papers study code *completion*; SWE-agent studies an LM *agent* resolving repository-level issues through tools, which is the closest prior setting to our Method B. Its agent–computer interface gives the agent repository search commands (`find_file`, `search_file`, `search_dir`) whose output format is designed for the model, and its ablation on SWE-bench Lite reports that a summarised search interface outperformed an interactive "step through each match" interface — which did worse than having no search tools — because agents exhausted their budget stepping through matches. This motivates two things in our study: (1) treating Method B's tool interface (top-k semantic search, `grep`, `read_file`, `find_symbol`, call limit, shared evidence budget) as a design factor that limits how far our results generalise, and (2) analysing Method B's traces for budget exhaustion and redundant evidence rather than assuming more agent steps help.

**Limits.** SWE-agent's outcome is end-to-end issue resolution (pass@1), not file-level retrieval quality; we do not reuse its numbers, interface or benchmark, and it is not an experimental arm.

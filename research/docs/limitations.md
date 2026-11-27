# Research Limitations

Documented constraints and threats to validity. Update as the project progresses; do not delete early limitations when results arrive.

---

## Design and scope

1. **Primary outcome is retrieval quality**, not patch success. Strong retrieval does not prove an agent would implement the change correctly.  
2. **Two methods only.** RepoBench / RepoCoder / Repoformer inform design; they are not extra experimental arms.  
3. **Agent-directed search ≠ RepoCoder.** Iterative inspiration only; no claim of exact reproduction.  
4. **Pilot budgets** (6,000 evidence tokens; 5 tool calls; top-k 10; 3 repetitions; temperature 0) are predetermined in `pilot-v1.0`, not optimized. Stage 5 pins embeddings/chunking/index without retuning to method scores.

---

## Benchmark and data

5. **Stage 2:** 7/8 primary candidates have verified commit identities; **E (`37067e0`) is unresolved** in upstream history. Do not treat E as usable until a resolvable SHA is supplied.  
6. **Pre-change snapshots** are required for ecological validity; until verified, no experimental claims.  
7. **Pilot GT is preliminary_self_validated only** (A/B); non-pilot GT deferred.  
8. **Candidates C and D** may overlap (related package-management work); risk of non-independent tasks.  
9. **Reserve `32bcdc9`** excluded pending CI investigation.  
10. **Single repository (Pi).** Results may not generalise to other monorepos or languages.

---

## Team and implementation

11. **Teammate deliverables** Independent EXP path includes Stage 5 retriever; T1 may later swap backends behind the same interface.  
12. **Full vector indexes depend on OpenRouter embeddings**; live probe and both pilot indexes are verified for Stage 5, but rebuilds still require a valid local API key.  
13. **No Method A/B experiments yet.** `results/findings.md` must stay empty of invented results.  
13b. **Metric split:** EXP owns core P/R/F1; T3 owns additional MRR/nDCG — both must share T2 relevance labels to avoid conflicting scores.  
13c. **Small pilot N:** avoid claims of statistical significance from insufficient tasks or repetitions.

---

## Measurement

14. **Evidence-pack quality** needs a fixed rubric before Stage 9; subjective components introduce annotator variance.  
15. **LLM non-determinism** may remain even at temperature 0 depending on provider.  
16. **Token accounting** across models/tokenisers may not be perfectly comparable.  
17. **Irrelevant context** can inflate pack size while hurting usefulness; recall-only reporting would mislead (Repoformer-motivated caution).

---

## Reporting integrity

18. Do not generalise from two pilots to all repository-level SE tasks.  
19. Do not cite fabricated paper statistics.  
20. Distinguish scaffolding, planned work, unverified candidates, and completed experiments in every status update.

## T2 benchmark status

The original Candidate E is now resolved. T2 source/schema checks cover all eight
candidate annotations. Human relevance sign-off and main-set acceptance are pending.
The package cluster and the E/F shared essential file are recorded in the overlap
assessment. The T2 set is versioned separately from the frozen A/B pilot.

## T1 update — 2026-11-26 (supersedes stale items above; originals kept for history)

- Items 5, 7 and 13 are **superseded**. E is resolved; all eight annotations exist; both experiments were executed (36 runs).
- **Raw traces not transferred to T1.** File-set scores were rescored from T3's per-run evaluation files (cross-checked against the manifest). Per-call Method B behaviour, MRR/nDCG, leakage and compliance claims stay T3-reported, unverified until they are hash-verified (`docs/t1_evaluation.md`).
- **Single, non-blind GT review.** `t1_reviewed_v1` was reviewed by T1 only, after seeing T3's preliminary aggregates (no traces). There is no inter-annotator agreement.
- **Closed-world scoring.** Unjudged files count as non-relevant, so a useful unannotated file lowers precision.
- **Pilot/main not comparable as one set.** They differ in prompt version and annotation version, so there is no combined win count.
- **Method B fallback packs.** When B stops on a limit, its pack is every charged excerpt (7/12 main runs per manifest), so its precision reflects search breadth rather than selection.
- **G/H share an essential file** (`cli/args.ts`), so the effective number of independent tasks is slightly below four.
- **Tool interface as a factor.** Method B's tools, top-k, 5-call limit and shared budget shape its performance (cf. SWE-agent's interface ablations). Results may not transfer to other agent designs.

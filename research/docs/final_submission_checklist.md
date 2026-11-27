# Final Submission Checklist

Updated 2026-11-26 by T1 (Rehat Preet Kaur), AI-assisted. Status key: **Done** (verified in repo) · **Partial** · **Blocked** · **Group action** (needs real people). Nothing is marked Done unless it was verified.

## Research report
| Requirement | Status | Evidence / location |
|---|---|---|
| ~1,500-word APA paper (excl. refs/appendices) | **Partial**: complete draft, ≈1,540 body words | `research/report.md` |
| Sections: Intro ≈250 / Background ≈350 / Main ≈550 / Critical ≈200 / Conclusion ≈150 | **Done (draft)**: 265 / 361 / 592 / 196 / 128 | `research/report.md` |
| Research question, methods, design, findings, interpretation, costs, limitations, contribution | **Done (draft)**: results rescored from T3 per-run files | `research/report.md` |
| Pilot vs main and provisional vs reviewed GT clearly separated | **Done** | report §Results; `results/findings.md`; `docs/t1_evaluation.md` |
| ≥5 credible sources incl. academic, technical documentation, industry | **Done**: 8 references (6 scholarly, Pi repository, OpenRouter docs) | report §References |
| 5 reviewed scholarly papers verified and cited (RepoBench, RepoCoder, Repoformer, CodeRAG-Bench, + SWE-agent) | **Done** | `docs/literature_review.md` (T1 verification + SWE-agent); report |
| APA in-text citations and reference list | **Done (draft)**; group should proofread | report |
| No fabricated results or citations | **Done**: results rescored from T3's per-run files; limits stated | report, findings |
| Evaluation | **Done** from T3 per-run files, cross-checked against the manifest; not trace-hash-verified; no MRR/nDCG | `docs/t1_evaluation.md` §8, `results/findings.md` |
| Method B search-behaviour analysis | **Partial**: pack-type and A-vs-B analysis done; per-call analysis needs traces | `results/findings.md` |
| Word document required? | No course/project requirement found; Markdown kept | — |

## Appendices
| Requirement | Status | Location |
|---|---|---|
| A — AI use | **Partial**: drafted from logs; Rehat must add accepted/rejected notes | report Appendix A; `docs/ai_use_log.md` |
| B — Individual reflections, 200–300 words, written and approved by each member | **Group action**: 4 placeholders | report Appendix B |
| C — Group contributions | **Partial**: from commits/logs; shares not recorded | report Appendix C; `docs/contribution_log.md` |
| D — AI dry-run feedback | **Group action**: no dry run yet | report Appendix D |

## Presentation video
| Requirement | Status | Location |
|---|---|---|
| ≤10 slides (1 title + 9 content) | **Partial**: outline done; slides not built | `docs/presentation_outline.md` |
| 5–7 min recording (target ≈6 min) | **Group action** | — |
| Covers problem, RQ, methods, design, verified results, limitations, conclusion | **Partial**: verified results pending | outline |
| 1–2 min demo comparing both methods on the same task | **Partial**: guide + replay script tested on fixtures; real replay needs traces | `docs/demo.md`, `scripts/t1_demo_replay.py` |
| AI dry run + critique, improvements recorded | **Group action** | Appendix D |
| YouTube privacy setting | **Group action, needs decision**: the course text says both *Private* and *Unlisted* and requires the link to work in incognito. Private videos do not play for viewers who aren't signed in, so confirm with the instructor. | outline "Notes for the group" |
| Upload, test link in incognito, submit link | **Group action**: not done by T1 | — |
| Blackboard submission (report + link) | **Group action** | — |

## Real group actions still required (in order)
1. ~~Arman: send evaluation files~~ **Done**: results filled in. Optional: the raw traces would add MRR/nDCG, per-call analysis and a live replay demo.
2. Each member writes and approves their own reflection (Appendix B).
3. Group reviews and edits the report draft and agrees on contribution shares, if needed.
4. Build the slides from `docs/presentation_outline.md` and assign presenters.
5. Capture demo screenshots from a real replay (fallback).
6. Hold a dry run, get an AI critique, and record it in Appendix D.
7. Resolve the YouTube privacy setting, then record the 5–7 min video and upload it.
8. Test the link in an incognito window.
9. Submit the report and video link on Blackboard.

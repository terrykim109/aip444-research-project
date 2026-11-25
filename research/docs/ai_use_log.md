# AI Use Log

**Purpose:** Record actual AI-assisted work for Appendix A and research integrity.  
**Rule:** Do not invent interactions. Add rows only when work happens.

| Date | Tool / model | Stage | Task summary | Human oversight | Output used? | Notes |
|---|---|---|---|---|---|---|
| 2026-11-18 | Cursor agent (Composer) | 1 | Initialise `./research` scaffolding, configs, and documentation | Author reviews all generated files before relying on them | Pending review | Stage 1 foundation only; no experiments run |
| 2026-11-18 | Cursor agent (Composer) | 1.5 | Align ownership, integration contracts, schemas, metric split | Author reviews edits before relying on them | Pending review | Docs/schemas only; no Stage 2 implementation |
| 2026-11-18 | Cursor agent (Composer) | 2 | Clone/verify Pi snapshots, pilot worktrees, verify_benchmark.py | Author reviews SHAs, docs, and script output | Pending review | Candidate E unresolved; no corpus/RAG built |
| 2026-11-18 | Cursor agent (Composer) | docs | Independent-execution rule across checklist/handoff/README/methodology | Author reviews before relying | Pending review | Docs only; no Stage 3 implementation |
| 2026-11-18 | Cursor agent (Composer) | 3 | Construct pilot tasks/GT from diffs; loader + tests | Author verifies annotations vs parent worktrees | Pending review | preliminary_self_validated only; no RAG |
| 2026-11-18 | Cursor agent (Composer) | 4 | Freeze pilot-v1.0 protocol; config + tests | Author reviews freeze vs Stage 3 artifacts | Pending review | Design freeze only; no trials |
| 2026-11-19 | Cursor agent (Composer) | 5 | Corpus, OpenRouter embeddings, NumPy index, shared retriever | Author reviews code/docs; set API key for live probe | Pending review | Live API pending without key; no Method A/B |
| 2026-11-19 | Cursor agent (Composer) | 6 | Method A/B, chat client, orchestration, tests | Author reviews before pilot runs | Pending review | No 12-record pilot batch executed |
| 2026-11-24 | Claude Code (Claude Fable 5) | T1 | Search CLI, T1 smoke tests, retrieval backend notes, qualitative embedding-model review | Author (Arman Ataeipour) reviews code/tests/docs before merge | Pending review | Mocked tests only (106 passed, 2 skipped); no live API calls; no protocol or Stage 5 changes |
| 2026-11-24 | Claude Code (Claude Fable 5) | T3 | Repo inspection, snapshot/benchmark re-verification, worktree + corpus validation, T3 handoff docs | Author (Arman Ataeipour) reviews docs and validation evidence before merge | Pending review | 99 passed/2 skipped on main; no live API calls (no key); no pilot runs executed; frozen protocol untouched |
| 2026-11-24 | Claude Code (Claude Fable 5) | T3 / Stage 7 | Executed pilot after key provided: index builds, 12/12 method runs, minimal evaluator, results write-up | Author (Arman Ataeipour) reviews traces, evaluator code, and reported numbers before merge | Pending review | All runs real (`gpt-6-luna`, single config hash, ~$0.13 API spend); no retries or substitutions; frozen protocol untouched |
| 2026-11-25 | Claude Code (Claude Fable 5) | T3 / Stage 8 | Main-v1.0 freeze (task selection from T2 overlap data, GT SHA-256), minimal code extensions, 4 index builds, 24/24 main runs, trace audit, preliminary evaluation, manifest + documentation reconciliation | Author (Arman Ataeipour) reviews config, selection rationale, traces, and reported numbers before merge | Pending review | All runs real (`gpt-6-luna`); pilot pins inherited unchanged (same config hash); no failed/retried runs; GT provisional pending T1 review |

---

## Guidance

- Log planning, coding, editing, and literature-summary assistance separately when material.  
- Note when AI drafts were rejected or heavily rewritten.  
- Never paste API keys or secrets into prompts or this log.  
- Link to files touched when helpful (`research/...`).

## T2 local integration — 20 November 2026

| Tool | Actual assistance | Verification | Human review |
| --- | --- | --- | --- |
| ChatGPT / Codex, GitHub connector and local Git | Read the central README, handoff, benchmark files and interfaces; selectively adapt the existing Ni handoff | Original candidate identities checked against GitHub and Git objects | Student review pending |
| ChatGPT / Codex | Implement T2 benchmark validation, input isolation, deterministic generation, worktree reproduction, tests and documentation | Command exits and saved results recorded in the T2 validation record | Student and independent peer relevance sign-off pending |
| ChatGPT / Codex with primary-source reading | Verify CodeRAG-Bench bibliographic data and annotation/evaluation connection | ACL Anthology record and relevant PDF sections checked | Student critical reading remains personal work |

No model identifier beyond ChatGPT/Codex was recorded. No retrieval implementation,
agent controller, behavior-analysis utility, experimental result, personal reflection
or human review was fabricated. No GitHub push is performed in this delivery.

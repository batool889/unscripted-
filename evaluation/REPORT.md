# Evaluation report

Executed locally on 7 November 2026 against the supplied academic documents.

## Verified checks

- 43 Python checks passed: prerequisites, elective caps, real PDF/CSV provenance, duplicate handling, SQLite persistence, citation validation, session bounds, API setup errors, and mocked Gemini contracts.
- React TypeScript checking and Vite production build passed.
- Four real-browser checks passed on Microsoft Edge: Arabic navigation, mocked missing-key UI, real course selection/calculations and source dialog, original PDF/library conflict visibility, and mobile overflow checks.

## Retrieval measurements

| Set | Answerable questions scored | Lexical evidence-group recall@8 | Hybrid evidence-group recall@8 |
| --- | ---: | ---: | ---: |
| Reference | 12 | 91.7% | 100.0% |
| Original held-out, now regression | 4 | 100.0% | 100.0% |
| Fresh validation | 4 | 100.0% | 100.0% |

Evidence groups are annotated pages/records, with alternatives accepted where appropriate. These are not exhaustive chunk-level recall annotations. The lexical comparison retains the same exact-code and known-conflict routing as hybrid.

The first reference run achieved 95.8% hybrid evidence-group recall; the first held-out run achieved 75%. The latter exposed repeated-header interference with the engineering warning rule. After those failures were inspected, that set became regression data. The original results remain in *_initial.json. A fresh five-case set (four answerable retrieval cases) was then created and evaluated without further tuning. These samples are small and do not demonstrate universal reliability.

## Not established

- Live Gemini answer correctness, completeness, groundedness, refusal quality, and end-to-end generation latency have not been measured: no replacement API key was configured.
- Provider contract tests and the second model support check are not substitutes for independent human review.
- Questions without annotated evidence groups are deliberately excluded from retrieval recall. Their expected refusal/clarification statuses have not been established by an offline retrieval score.
- Dialect retrieval cases include Palestinian/Shami and a Lebanese phrasing; coverage of all regional expressions is not established.
- Optional reranking and alternative embedding/chunking experiments have not been benchmarked.

## Required live acceptance pass

Configure a replacement key, then run `python -m evaluation.evaluate --live`. Review every returned academic claim against its sources. Record correctness and groundedness manually in the saved report. Check correct refusals and unnecessary refusals separately; test source conflicts, engineering GPA exceptions, hypothetical follow-ups, and irrelevant/instruction-like retrieved text. Measure token usage and latency before quoting operating costs.

## Live smoke checks after configuring the key

The original configured model returned provider 503/504 errors. Model listing and
a bounded generation probe identified gemini-3.1-flash-lite as responsive. The
running server was also restarted because it retained settings from before the
key was added. Its health endpoint now confirms generation_configured=true.

Two actual /api/chat checks passed: a Palestinian prerequisite question returned
the correct parenthesized AND/OR expression with two validated citations; an
unavailable exam-date question returned insufficient_evidence without a date.
The first request took 51.8 seconds including model warmup; the second took 10.6
seconds. See reports/live_smoke.json. The full live reference evaluation remains
uncompleted; prior statements about unmeasured general answer quality still apply.
All 43 backend regression tests passed after the provider configuration change.

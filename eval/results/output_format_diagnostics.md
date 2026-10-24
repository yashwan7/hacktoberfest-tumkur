# Output-format diagnostics

These counts come directly from saved production answer strings. They supplement, and do not overwrite, LLM correctness labels. The answering model and application files were not modified by the evaluation laptop.

| Run | In-scope cases | SDK-object dumps | MAX_TOKENS markers | Unparsed JSON fences | In-scope refusals | Judge-CORRECT SDK dumps |
|---|---:|---:|---:|---:|---:|---:|
| baseline v1 | 20 | 9 | 9 | 2 | 6 | 1 |
| ablation/rag | 20 | 15 | 15 | 1 | 0 | 1 |
| ablation/no_rag | 20 | 0 | 0 | 0 | 20 | 0 |
| experiment/chunk_size=400 | 20 | 15 | 15 | 1 | 0 | 0 |
| experiment/chunk_size=1200 | 20 | 10 | 10 | 5 | 0 | 0 |
| experiment/top_k=2 | 20 | 14 | 14 | 1 | 0 | 0 |
| experiment/top_k=6 | 20 | 15 | 15 | 1 | 0 | 1 |
| experiment/hybrid=false | 20 | 13 | 13 | 3 | 0 | 1 |
| experiment/threshold=0.20 | 20 | 16 | 16 | 2 | 0 | 1 |
| experiment/threshold=0.40 | 20 | 14 | 14 | 3 | 0 | 0 |

## Why the observed failure occurs

The saved SDK dumps explicitly contain thought=True and finish_reason=MAX_TOKENS. In the inspected application, _generate returns str(response) when response.text is empty; _parse_generation then treats that string as the answer after JSON parsing fails. This exposes a response object instead of final user-facing content. Other responses contain incomplete JSON. Source membership can remain correct despite these output failures.

The judge sometimes finds expected facts inside the object dump and labels it CORRECT. Such labels do not certify usable output. Flagged observations: baseline v1/q04, ablation/rag/q04, experiment/top_k=6/q03, experiment/hybrid=false/q09, experiment/threshold=0.20/q07.

## Proposed application-owner fixes

- Control the generation thinking/output budget and request enough room for a final answer; verify on the unchanged test set. The Gemma API documents minimal thinking at https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api. This evaluation used that setting only for the judge.
- Extract final non-thought content; if none exists or generation terminates before a valid final answer, return an explicit structured generation failure instead of str(response).
- Validate the required JSON keys and the boolean refused field. Do not silently present truncated JSON as an answer.
- Add bounded timeouts and distinct service-error reporting, so connectivity outages are not confused with evidence-based refusals.
- Retain semantic judgment but add output-format checks and human review; test source entailment rather than only file-level hits.

Reused default-anchor rows are excluded from this diagnostic table to avoid duplicate observations. The counts describe repeated configuration-question observations, not additional independent test questions.

# RAG vs no-RAG

Both modes were run over the same test set with `top_k=4`, `threshold=0.30`, and the same Gemma model configuration. The no-RAG mode is expected to answer from the model without retrieved passages; this report does not treat that mode as a baseline that can cite documents.

Limitation: disabling retrieval retains the application instruction to answer only from passages and refuse otherwise. Refusals are failures on in-scope cases, not hallucinations. This is an implemented-path ablation, not an unrestricted pretrained-model baseline.

### With RAG

| Metric | Value |
|---|---:|
| Questions | 25 |
| In-scope judged | 20 / 20 |
| Correct | 4 |
| Partial | 1 |
| Wrong | 15 |
| Accuracy among judged | 0.200 |
| Confirmed correct / all in-scope | 0.200 |
| Unavailable judgments | 0 |
| Graded score (correct + 0.5×partial) | 0.225 |
| Citation hit rate | 1.000 |
| Out-of-scope refusal accuracy | 1.000 |
| Average latency (s) | 10.331 |

### Without RAG

| Metric | Value |
|---|---:|
| Questions | 25 |
| In-scope judged | 20 / 20 |
| Correct | 0 |
| Partial | 0 |
| Wrong | 20 |
| Accuracy among judged | 0.000 |
| Confirmed correct / all in-scope | 0.000 |
| Unavailable judgments | 0 |
| Graded score (correct + 0.5×partial) | 0.000 |
| Citation hit rate | 0.000 |
| Out-of-scope refusal accuracy | 1.000 |
| Average latency (s) | 9.657 |

## Candidate hallucinations: non-refused no-RAG answers judged WRONG

No non-refused no-RAG answers judged WRONG were observed. Inspect judge coverage before interpreting this result. The application retains its evidence-only refusal prompt even with retrieval disabled, so this is not an unrestricted model baseline.

## Three side-by-side answers

| Question | With RAG | Without RAG |
|---|---|---|
| What is currently the most valuable way for an outside contributor to help Gradio? | sdk_http_response=HttpResponse(   headers=<dict len=12> ) candidates=[Candidate(   content=Content(     parts=[       Part(         text="""*   User Question: "What is currently the most valuable way for an outside contributor to help Gradio?"     *   Constraint 1: Use only the provided documentation.     *   Constraint 2: If unsupported or unrelated, refuse.     *   Constraint 3: Return valid JSON only with `answer` (string) and `refused` (boolean).     *   Constraint 4: Include compact inline citations like `[CONTRIBUTING.md#3]`.     *   Constraint 5: For refusal, answer briefly that the question is outside the indexed guide.      *   `gradio/CONTRIBUTING.md [chunk_id=0]`: "the best way to help us today is by **opening a detailed issue** rather than a pull request."     *   `gradio/CONTRIBUTING.md [chunk_id=1]`: "So the single most valuable thing you can do is **file a clear, detailed, reproducible issue.**"     *   `gradio/CONTRIBUTING.md [chunk_id=4]`: Mentions setup for maintainers and suggests outside contributors open a detailed issue.     *   `gradio/CONTRIBUTING.md [chunk_id=5]`: "If you're an outside contributor, the most helpful thing you can do is [open a detailed issue](#-the-best-way-to-contribute-open-a-great-issue)..."      *   The most valuable thing for an outside contributor is to file a clear, detailed, and reproducible issue [CONTRIBUTING.md#0, CONTRIBUTING.md#1].     *   The documentation specifically states that Gradio has paused accepting pull requests from outside the maintainer team, so opening a detailed issue is preferred over a pull request [CONTRIBUTING.md#0].      *   `answer`: "The single most valuable thing an outside contributor can do is file a clear, detailed, and reproducible issue [CONTRIBUTING.md#1]. Gradio has paused accepting pull requests from outside the maintainer team, so opening a detailed issue is preferred over submitting a pull request [CONTRIBUTING.md#0]."     *   `refused`: `false`.      *   Valid JSON? Yes.     *   Only provided passages? Yes.     *   Compact inline citations? Yes.     *   """,         thought=True       ),     ],     role='model'   ),   finish_reason=<FinishReason.MAX_TOKENS: 'MAX_TOKENS'>,   index=0 )] create_time=None model_version='gemma-4-26b-a4b-it' prompt_feedback=None response_id='0HHcap3tOuiq694P1qnAkQE' usage_metadata=GenerateContentResponseUsageMetadata(   prompt_token_count=1053,   prompt_tokens_details=[     ModalityTokenCount(       modality=<MediaModality.TEXT: 'TEXT'>,       token_count=1053     ),   ],   thoughts_token_count=509,   total_token_count=1562 ) model_status=None automatic_function_calling_history=[] parsed=None **Sources:** gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md | The question is outside the indexed guide. **Sources:** — |
| What should a Gradio bug report's title contain? | A bug report should include a clear, descriptive title that summarizes the problem [CONTRIBUTING.md#1, CONTRIBUTING.md#2]. **Sources:** gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md | The question is outside the indexed guide. **Sources:** — |
| What two behaviors should a Gradio bug report compare? | sdk_http_response=HttpResponse(   headers=<dict len=12> ) candidates=[Candidate(   content=Content(     parts=[       Part(         text="""*   Role: Open-source contributor guide assistant.     *   Constraint: Use *only* the provided documentation passages.     *   Constraint: If unsupported or unrelated, refuse.     *   Constraint: Return *valid JSON only* with `answer` (string) and `refused` (boolean).     *   Constraint: Use compact inline citations (e.g., `[CONTRIBUTING.md#3]`).     *   Constraint: For refusal, answer briefly that the question is outside the indexed guide.     *   Question: "What two behaviors should a Gradio bug report compare?"      *   `gradio/CONTRIBUTING.md [chunk_id=3]`: Discusses bug report components (screenshots, etc.) and feature requests.     *   `gradio/CONTRIBUTING.md [chunk_id=2]`: Lists bug report steps. Specifically, step 2: "**What you expected to happen** vs. **what actually happened.**"     *   `gradio/CONTRIBUTING.md [chunk_id=1]`: Discusses the importance of clear issues and the start of the bug reporting section.     *   `gradio/README.md [chunk_id=17]`: Discusses installing skills and where to ask questions.      *   The question asks what two behaviors should be compared in a bug report.     *   From `gradio/CONTRIBUTING.md [chunk_id=2]`, point 2 says: "**What you expected to happen** vs. **what actually happened.**"     *   From `gradio/CONTRIBUTING.md [chunk_id=1]`, point 2 says: "**What you expected to happen** vs. **what actually happened.**"      *   `answer`: "A Gradio bug report should compare what you expected to happen vs. what actually happened [CONTRIBUTING.md#2]." (Note: chunk_id 1 and 2 both have it, I'll pick one or both, but usually, one is enough).     *   `refused`: `false`.      *   Valid JSON? Yes.     *   Only provided passages? Yes.     *   Compact inline citations? Yes.     *   `answer` and `refused` keys? Yes.      *Self-correction*: Looking""",         thought=True       ),     ],     role='model'   ),   finish_reason=<FinishReason.MAX_TOKENS: 'MAX_TOKENS'>,   index=0 )] create_time=None model_version='gemma-4-26b-a4b-it' prompt_feedback=None response_id='9HHcaqHcNP-z694P6ovPgAE' usage_metadata=GenerateContentResponseUsageMetadata(   prompt_token_count=1011,   prompt_tokens_details=[     ModalityTokenCount(       modality=<MediaModality.TEXT: 'TEXT'>,       token_count=1011     ),   ],   thoughts_token_count=509,   total_token_count=1520 ) model_status=None automatic_function_calling_history=[] parsed=None **Sources:** gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/README.md | The question is outside the indexed guide. **Sources:** — |

Raw data: [`rag_vs_norag.json`](rag_vs_norag.json)

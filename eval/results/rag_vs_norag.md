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

SDK-object dumps are summarized for readability; the raw JSON preserves the complete returned strings.

| Question | With RAG | Without RAG |
|---|---|---|
| What is currently the most valuable way for an outside contributor to help Gradio? | [SDK-response object returned instead of final answer; MAX_TOKENS] **Sources:** gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md | The question is outside the indexed guide. **Sources:** none |
| What should a Gradio bug report's title contain? | A bug report should include a clear, descriptive title that summarizes the problem [CONTRIBUTING.md#1, CONTRIBUTING.md#2]. **Sources:** gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md | The question is outside the indexed guide. **Sources:** none |
| What two behaviors should a Gradio bug report compare? | [SDK-response object returned instead of final answer; MAX_TOKENS] **Sources:** gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/CONTRIBUTING.md, gradio/README.md | The question is outside the indexed guide. **Sources:** none |

Raw data: [rag_vs_norag.json](rag_vs_norag.json)

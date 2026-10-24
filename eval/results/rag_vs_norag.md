# RAG vs no-RAG

Both modes were run over the same test set with `top_k=4`, `threshold=0.30`, and the same Gemma model configuration. The no-RAG mode is expected to answer from the model without retrieved passages; this report does not treat that mode as a baseline that can cite documents.

### With RAG

| Metric | Value |
|---|---:|
| Questions | 25 |
| In-scope judged | 0 / 20 |
| Correct | 0 |
| Partial | 0 |
| Wrong | 0 |
| Accuracy | n/a |
| Graded score (correct + 0.5×partial) | n/a |
| Citation hit rate | 0.000 |
| Out-of-scope refusal accuracy | 1.000 |
| Average latency (s) | 0.000 |

### Without RAG

| Metric | Value |
|---|---:|
| Questions | 25 |
| In-scope judged | 0 / 20 |
| Correct | 0 |
| Partial | 0 |
| Wrong | 0 |
| Accuracy | n/a |
| Graded score (correct + 0.5×partial) | n/a |
| Citation hit rate | 0.000 |
| Out-of-scope refusal accuracy | 1.000 |
| Average latency (s) | 0.000 |

## Confidently wrong no-RAG answers

No judged hallucination examples are available in this run. This is expected when the Gemma judge or production rag.py is unavailable; it is not evidence that no hallucinations exist.

## Three side-by-side answers

| Question | With RAG | Without RAG |
|---|---|---|
| What is currently the most valuable way for an outside contributor to help Gradio? | The production rag.py has not been pushed yet; no answer is available from the local stub. **Sources:** — | The production rag.py has not been pushed yet; no answer is available from the local stub. **Sources:** — |
| What should a Gradio bug report's title contain? | The production rag.py has not been pushed yet; no answer is available from the local stub. **Sources:** — | The production rag.py has not been pushed yet; no answer is available from the local stub. **Sources:** — |
| What two behaviors should a Gradio bug report compare? | The production rag.py has not been pushed yet; no answer is available from the local stub. **Sources:** — | The production rag.py has not been pushed yet; no answer is available from the local stub. **Sources:** — |

Raw data: [`rag_vs_norag.json`](rag_vs_norag.json)

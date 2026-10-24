# Gemma 4 model comparison

Both models use the same index, test set, retrieval configuration, and judge. Latency is the value returned by the application for each answer; quality is judged by the configured Gemma judge.

| Model | Accuracy | Graded score | Citation hit rate | Refusal accuracy | Avg latency (s) |
|---|---:|---:|---:|---:|---:|
| `gemma-4-26b-a4b-it` | n/a | n/a | 0.000 | 1.000 | 0.000 |
| `gemma-4-31b-it` | n/a | n/a | 0.000 | 1.000 | 0.000 |

No quality comparison is claimed yet: production `rag.py`, `data/`, or the Gemma judge was unavailable for this committed run.

Raw data: [`model_comparison.json`](model_comparison.json)

### Verified live baseline

| Metric | Value |
|---|---:|
| Questions | 25 |
| In-scope judged | 13 / 20 |
| Correct | 5 |
| Partial | 4 |
| Wrong | 4 |
| Accuracy | 0.385 |
| Graded score (correct + 0.5×partial) | 0.538 |
| Citation hit rate | 1.000 |
| Out-of-scope refusal accuracy | 1.000 |
| Average latency (s) | 68.416 |

Judgment coverage: 13/20. Unavailable judgments: 7. Accuracy above uses only successfully judged cases. Confirmed correct across all 20 in-scope cases: 5/20.

Network failures and output truncation are part of this observed run. A 1488.34-second application call during the outage strongly inflates the 68.42-second average; this is not steady-state serving latency. Raw SDK-response strings and incomplete JSON appear in multiple answers. See per-question rows and audit.

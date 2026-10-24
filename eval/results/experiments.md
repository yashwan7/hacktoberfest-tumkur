# One-factor-at-a-time experiments

The default anchor is `chunk_size=800`, `overlap=120`, `top_k=4`, `hybrid=true`, and `threshold=0.30`. Each row changes one factor while holding the others at that anchor; this avoids a full Cartesian grid and conserves API quota.

| Run | Factor | Value | Accuracy | Graded score | Citation hit rate | Avg latency (s) |
|---|---|---:|---:|---:|---:|---:|
| default | default | 800/4/true/0.30 | n/a | n/a | 0.000 | 0.000 |
| chunk_size=400 | chunk_size | 400 | n/a | n/a | 0.000 | 0.000 |
| chunk_size=1200 | chunk_size | 1200 | n/a | n/a | 0.000 | 0.000 |
| top_k=2 | top_k | 2 | n/a | n/a | 0.000 | 0.000 |
| top_k=6 | top_k | 6 | n/a | n/a | 0.000 | 0.000 |
| hybrid=false | hybrid | False | n/a | n/a | 0.000 | 0.000 |
| threshold=0.20 | threshold | 0.2 | n/a | n/a | 0.000 | 0.000 |
| threshold=0.40 | threshold | 0.4 | n/a | n/a | 0.000 | 0.000 |

Charts were not rendered: matplotlib is not installed in this environment. Re-run after installing matplotlib.

Raw data: [`experiments.json`](experiments.json)

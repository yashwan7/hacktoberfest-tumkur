# One-factor-at-a-time experiments

The default anchor is `chunk_size=800`, `overlap=120`, `top_k=4`, `hybrid=true`, and `threshold=0.30`. Each row changes one factor while holding the others at that anchor; this avoids a full Cartesian grid and conserves API quota.

| Run | Factor | Value | Accuracy (judged) | Graded score | Citation hit rate | Avg latency (s) |
|---|---|---:|---:|---:|---:|---:|
| default | default | 800/4/true/0.30 | 0.200 | 0.225 | 1.000 | 10.331 |
| chunk_size=400 | chunk_size | 400 | 0.200 | 0.200 | 1.000 | 10.718 |
| chunk_size=1200 | chunk_size | 1200 | 0.400 | 0.450 | 1.000 | 10.262 |
| top_k=2 | top_k | 2 | 0.200 | 0.200 | 1.000 | 10.336 |
| top_k=6 | top_k | 6 | 0.300 | 0.350 | 1.000 | 10.539 |
| hybrid=false | hybrid | False | 0.250 | 0.300 | 0.950 | 10.299 |
| threshold=0.20 | threshold | 0.2 | 0.200 | 0.250 | 1.000 | 12.376 |
| threshold=0.40 | threshold | 0.4 | 0.250 | 0.275 | 1.000 | 10.107 |

Judgment coverage: default: 20/20; chunk_size=400: 20/20; chunk_size=1200: 20/20; top_k=2: 20/20; top_k=6: 20/20; hybrid=false: 20/20; threshold=0.20: 20/20; threshold=0.40: 20/20

Default anchor reuse, if any, is recorded in the raw JSON. Table accuracy is among judged cases; charts use confirmed CORRECT/20, retaining unavailable cases in the denominator. Inspect coverage before comparing.

Charts: `eval\results\accuracy_vs_chunk_size.png`, `eval\results\accuracy_vs_top_k.png`

Raw data: [`experiments.json`](experiments.json)

## Retrieved-context changes relative to default

This compares ordered (file, chunk_id, passage text) selections for the 20 in-scope questions. Identical contexts with differing answer grades do not establish a retrieval-parameter effect.

| Configuration | Same contexts /20 | Changed returned strings despite same context | Changed grades despite same context |
|---|---:|---:|---:|
| default | 20 | 0 | 0 |
| chunk_size=400 | 0 | 0 | 0 |
| chunk_size=1200 | 0 | 0 | 0 |
| top_k=2 | 0 | 0 | 0 |
| top_k=6 | 0 | 0 | 0 |
| hybrid=false | 1 | 1 | 0 |
| threshold=0.20 | 20 | 20 | 7 |
| threshold=0.40 | 19 | 19 | 6 |

Returned-string differences may include SDK request metadata; changed-grade counts are shown separately. No fixed generation seed was imposed.

# Failure analysis

No baseline evaluation JSON exists yet. Run `python eval/run_eval.py --run-name baseline` after Laptop A pushes `rag.py` and `data/`; this report is intentionally not a fabricated zero-failure result.

| Category | Count | Proposed fix |
|---|---:|---|
| Retrieval miss | n/a | Tune hybrid retrieval and query rewriting. |
| Chunk split | n/a | Add overlap or structure-aware chunking. |
| Wrong synthesis | n/a | Tighten grounded synthesis and evidence checks. |
| Bad refusal threshold | n/a | Calibrate against out-of-scope and borderline prompts. |

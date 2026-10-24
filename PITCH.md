# Five-minute demo script

## 0:00–0:35 — Problem

“Contributor documentation is accurate but distributed across long pages. A new contributor needs a setup command, a testing command, a PR rule, or a community-safety answer immediately. A generic LLM can sound confident while making up a command. We built an open-source contributor guide that answers from Gradio and REsq Mesh documentation, shows the evidence, and refuses unrelated questions.”

## 0:35–1:45 — Live Q&A with citations and passages

Ask: **“How do I run Gradio's Python backend tests?”**

Expected demo flow:

1. The answer says to run `bash scripts/run_backend_tests.sh` on macOS/Linux.
2. The source citation points to `CONTRIBUTING.md`.
3. The passages panel shows the testing section and its score.
4. Point out the latency field and that the answer is inspectable rather than a black-box paragraph.

Then ask: **“Against which branch should a Gradio PR be submitted?”** The grounded answer is `main`, ideally addressing an open issue; the citation should remain `CONTRIBUTING.md`.

## 1:45–2:15 — Refusal demo

Ask: **“What is the weather in Bengaluru tomorrow?”**

The app should return a refusal because weather is outside the indexed contributor-guide scope. Emphasize that refusal is evaluated as a product behavior: the test set has five out-of-scope prompts, not just happy-path documentation questions.

## 2:15–2:55 — “Where do I start?” checklist

Use the guide to walk through this newcomer checklist:

1. Outside contributors should open a clear, detailed, reproducible issue because Gradio has paused outside pull requests.
2. Include expected versus actual behavior, numbered reproduction steps, a minimal reproduction, environment details, and relevant screenshots/tracebacks.
3. Clone the repo and run `bash scripts/install_gradio.sh` on macOS/Linux.
4. Use a Python 3.10 virtual environment for pinned dependencies.
5. Run `bash scripts/run_backend_tests.sh` and `bash scripts/format_backend.sh` before maintainer PR review.
6. Target `main` and make sure initial CI checks pass.

## 2:55–3:35 — Evaluation numbers and RAG vs no-RAG

Open `eval/results/` and explain the measurement split:

- correctness is judged by Gemma as `CORRECT`, `PARTIAL`, or `WRONG`;
- citation hit checks whether the expected source file is returned;
- refusal accuracy is scored on the five out-of-scope cases;
- average latency is taken from the answer contract.

The committed reports currently show `n/a` quality values because the production `rag.py`, `data/`, and `GOOGLE_API_KEY` were not available in this checkout. This is intentional honesty, not a tuned benchmark. After Laptop A pushes, run `python eval/run_eval.py --run-name baseline` and then `python eval/rag_vs_norag.py` to populate the real numbers. The side-by-side report is designed to show where no-RAG answers become confidently wrong and where retrieved evidence prevents that.

## 3:35–4:10 — Experiments and failure cases

Show `experiments.md`. It changes one variable at a time around `chunk_size=800`, `top_k=4`, `hybrid=true`, and `threshold=0.30`; it does not spend quota on a full grid. The planned charts are accuracy versus chunk size and accuracy versus `top_k`.

Show `failure_analysis.md`. Wrong or partial answers are categorized as retrieval miss, chunk split, wrong synthesis, or bad refusal threshold, each with a proposed fix. That turns a bad answer into an engineering action instead of hiding it.

## 4:10–5:00 — Future work and close

“Next we would add heading-aware chunking, calibrated refusal thresholds, answer-level citation spans, a larger stratified test set, and the optional Gemma 26B versus 31B comparison. The core promise is simple: useful contributor guidance with evidence visible and scope boundaries explicit.”

## Ten likely judge questions

1. **Why RAG instead of prompting Gemma with a long README?** — Retrieval reduces irrelevant context, keeps prompts within a predictable budget, and lets us show exactly which passages supported an answer.
2. **How do you prevent hallucinations?** — We gate on retrieval evidence, instruct the model to stay within passages, return citations/passages, and score both correctness and citation hit rather than trusting fluent text.
3. **How do you test correctness?** — Twenty short answers are grounded in the two requested repositories, then Gemma judges each candidate as CORRECT, PARTIAL, or WRONG with a reason; raw rows are saved.
4. **Why include out-of-scope questions?** — A contributor assistant that answers unrelated questions confidently is unsafe and distracting, so five refusal cases measure that boundary directly.
5. **Why use hybrid retrieval?** — Exact commands and filenames benefit from lexical matching; paraphrased questions benefit from embeddings. The experiment runner measures whether the combination helps here.
6. **Why these chunk sizes and `top_k` values?** — They bracket the default 800-character/4-passage choice with smaller, larger, narrower, and broader context while avoiding a quota-heavy full grid.
7. **What happens when the model or API is unavailable?** — The evaluator records an explicit unavailable result; the application should preserve the refusal/fallback contract rather than inventing an answer, and `GOOGLE_API_KEY` is read only from the environment.
8. **What is REsq Mesh doing in a contributor guide?** — It is the second project document required by the problem and gives the benchmark cross-project questions about architecture, offline operation, and verification.
9. **What is the biggest current limitation?** — The committed integration checkout did not yet contain Laptop A's production RAG module, documents, or credentials, so no production quality number is claimed; the rerun commands are ready.
10. **What would you build next?** — Calibrated refusal, structure-aware chunking, sentence-level citations, a larger maintained test set, and a measured 26B/31B Gemma latency-quality comparison.

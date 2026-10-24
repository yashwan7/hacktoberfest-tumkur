# Five-minute demo script

## 0:00–0:35 — Problem

“Contributor documentation is accurate but distributed across long pages. A new contributor needs a setup command, a testing command, a PR rule, or a community-safety answer immediately. A generic LLM can sound confident while making up a command. We built an open-source contributor-guide prototype that retrieves Gradio and REsq Mesh evidence and attempts grounded Gemma answers. We will show a working case alongside measured output failures.”

## 0:35–1:45 — Live Q&A with citations and passages

Ask: **“How do I run Gradio's Python backend tests?”**

Expected demo flow:

1. The answer says to run `bash scripts/run_backend_tests.sh` on macOS/Linux.
2. The source citation points to `CONTRIBUTING.md`.
3. The passages panel shows the testing section and its score.
4. Point out latency and evidence. If the response is an SDK-object dump, explicitly demonstrate that recorded failure and inspect the retrieved passage; do not call it a successful answer.

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

“We froze 25 questions: 20 grounded answers and five outside scope. With judge v2, RAG scored 4 correct, 1 partial and 15 wrong: 20.0% confirmed accuracy. No-RAG scored 0 correct out of 20. Both refused 5/5 and 5/5 outside-scope cases respectively. Average answer latency was 10.33s with RAG and 9.66s without.”

Open rag_vs_norag.md and show its three actual side-by-side answers. Explain that no-RAG retains the evidence-only prompt and falsely refuses all 20 answerable questions; it is not an unrestricted-model comparison. No confident factual hallucinations were observed in that arm.

“The original default run also exposed an outage: only 13/20 judgments completed. We preserved it, including 5 correct answers and the 68.42s outage-inflated mean. Its judge protocol differs from this paired run.”

## 3:35–4:10 — Experiments and failure cases

Show the measured chunk-size and top-k charts. “Eight OFAT configurations isolate chunk size, retrieval breadth, hybrid matching and threshold. The largest observed confirmed-correct rate was 40.0% (chunk_size=1200); this small, unreplicated sweep does not prove an optimum.”

“Failures matter more than a flattering score: 15/20 paired RAG outputs were SDK dumps marked MAX_TOKENS. File hit was 100.0%, yet answer accuracy was only 20.0%. Fix final-response extraction and generation budgeting first.”

Open failure_analysis.md. Show counts by run and every classified wrong/partial, refusal and explicit service/judge failure. Separate outage handling from retrieval calibration. Do not read any historical stub values as model measurements.

## 4:10–5:00 — Future work and close

“First repair response extraction, output budgeting and bounded network timeouts. Then rerun this unchanged set, add an independent human-reviewed holdout, test real follow-up conversations, and separate the no-RAG refusal instruction from a true unrestricted-model baseline. After that, add heading-aware chunks, claim-level citations and calibrated abstention.”

Mention the 26B/31B comparison only if model_comparison.md contains completed live measurements. Otherwise say it was deferred for the hackathon time budget. Finish with the cited backend-test command and its supporting passage; if generation fails live, show the recorded failure rather than hiding it.

## Ten likely judge questions

1. **What did RAG achieve?** — In the paired run: 4/20 correct (20.0%), 1 partial, 15 wrong, with 20/20 judged. We report the failures too.
2. **Did you observe no-RAG hallucinations?** — No confident wrong factual examples in this implemented arm; it falsely refused 20/20 in-scope questions because its evidence-only prompt remained active.
3. **Why can citation hit be high with poor answers?** — It checks returned source-file membership. 100.0% citation hit coexisted with 15/20 SDK dumps, so it does not prove answer quality.
4. **How were ground truths verified?** — Against the actual Gradio and exact yashwan7/REsq-mesh docs in data/. Only source-path mismatches were corrected before measurement; no questions were tuned to observed outputs.
5. **How reliable is the judge?** — Imperfect. The same-family judge can reward facts embedded in malformed output. Raw responses, reasons, coverage and protocol labels are preserved for human review.
6. **Which parameters won?** — chunk_size=1200 reached the highest observed rate, 40.0%. With 20 answerable cases and no repeats or holdout, we do not claim optimality.
7. **Why OFAT rather than a grid?** — Eight configurations bracket defaults and reduce API use. They do not measure interactions. The audited default arm can be reused rather than called twice.
8. **What caused the biggest failures?** — MAX_TOKENS generations were returned as SDK objects; a separate network outage inflated the original baseline. These require generation/error-handling fixes, not altered test questions.
9. **Is 68 seconds normal latency?** — No. The original baseline mean includes a 1488.34-second outage-affected call; its median was 12.52s. The paired RAG mean was 10.33s.
10. **What would you build next?** — Repair final-output parsing and timeouts, add independent/human evaluation and an untouched holdout, correct the no-RAG control, then test conversation memory, chunk structure and citation entailment.

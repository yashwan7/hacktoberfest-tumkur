# Evaluation notes

- The target repository was an empty initial commit when this evaluation track started. The checkout is `main` at `47d37d6`.
- Laptop A has not yet pushed `rag.py` or `data/`. The local compatibility implementation is isolated in `eval/stub_rag.py`; it is not a replacement for the production RAG implementation.
- Ground truth was written from the current upstream source documents, fetched directly from the requested repositories:
  - Gradio `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` from `gradio-app/gradio`.
  - REsq Mesh `README.md` from `yashwan7/REsq-mesh`.
- Expected source labels assume Laptop A will preserve these document identities when copying them into `data/`: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `resqmesh/README.md`. The evaluator accepts normalized path suffixes and basenames to tolerate a different `data/` prefix.
- The 20 in-scope answers are short, directly verifiable paraphrases. The five out-of-scope prompts intentionally do not have expected answers or sources; only refusal behavior is scored.
- No API key is stored in this repository. Evaluation code reads `GOOGLE_API_KEY` from the environment (and optionally a local `.env` file that is not committed).

## Live evaluation session — 2026-10-24

- Followed the requested reset: previous local commits are retained on backup-eval only; live evaluation starts from origin/main and does not cherry-pick that branch. Repo-local identity is Yashwanth Gowda S N <yashwan7896@gmail.com>.
- Loaded the ignored root .env with python-dotenv. The credential was accepted by the model-list API and a real 26B generation preflight. No credential is printed, embedded in source, or staged.
- Application and corpus arrived at bc8590c; retrieval hardening arrived at 55a5823 before baseline execution. This laptop does not edit rag.py, app.py or data/.
- Reviewed all 25 existing cases against the shipped data. The ground-truth facts match. Corrected only expected_source paths for Gradio to gradio/CONTRIBUTING.md and gradio/CODE_OF_CONDUCT.md; committed and pushed before live results. Questions and expected answers were not tuned.
- Corrected evaluation citation matching to require the expected path or its full suffix, preventing gradio/README.md from being counted as a hit for resqmesh/README.md solely because both share a basename.
- Both exact models gemma-4-26b-a4b-it and gemma-4-31b-it are listed by the authenticated API. No model substitution is assumed. A scratch observer records requested/actual generation model names, input hashes and package versions in each audit JSON without altering application files or returned values.
- Important ablation limitation: use_rag=False removes retrieved passages but retains the application's instruction to answer only from supplied passages and refuse otherwise. It is an ablation of the implemented path, not a clean unrestricted pretrained-model baseline. A low no-RAG accuracy or lack of confident hallucinations must be interpreted with that confound.
- Existing score_rows accuracy divides by successfully judged in-scope rows. Reports must show judged coverage; unavailable judgments are not evidence of correctness. Average latency is the application's returned latency_s, not judge time or index construction time.
- CPU dependencies are installed locally for evaluation. No API calls are made by the stub; actual runs explicitly import production rag before invoking the existing evaluation CLI, so dependency errors cannot silently produce a stub benchmark.
- Small evaluation-only reporting corrections before measurements: include the default point in both OFAT charts; list every wrong/partial case in failure analysis; count in-scope refusals in the refusal-policy diagnostic family; and do not label refusals or merely PARTIAL answers as confident hallucinations. Application and corpus files remain untouched.
- The PyPI latest torch transfer stalled. Installed the official CPU wheel torch 2.9.1+cpu from download.pytorch.org instead; this meets the declared dependency. MiniLM weights are cached at upstream snapshot 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 and reused offline, avoiding model-download time in measured answer latency.
- User confirmed rag.py milestone 55a5823 is verified. On the requested second reset, synced to 1b83ceb (which includes that milestone plus UI/output-cap and conversation-memory follow-ups). The earlier in-progress run was stopped before reporting; its audit was retained only under work/interrupted_before_verified/, and its partial observations are not benchmark results.
- Rechecked the shipped test set after the reset: 20 in-scope, 5 out-of-scope; all source paths exist and all expected facts remain supported by the actual docs. No further question or ground-truth changes were needed. No baseline.json was committed on main at this point, so the default baseline was started on the verified implementation.
- To save quota, the subsequent RAG arm and OFAT default anchor may reuse the complete baseline only after checking exact cases, default configuration, input/code/corpus hashes, full 20-case judging coverage and a completed production audit. Raw reports explicitly mark reuse. If any input changes, those arms are measured again instead. This does not reuse stub results or observations from the interrupted run.

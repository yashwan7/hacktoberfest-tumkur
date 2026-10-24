# Evaluation notes

- The target repository was an empty initial commit when this evaluation track started. The checkout is `main` at `47d37d6`.
- Laptop A has not yet pushed `rag.py` or `data/`. The local compatibility implementation is isolated in `eval/stub_rag.py`; it is not a replacement for the production RAG implementation.
- Ground truth was written from the current upstream source documents, fetched directly from the requested repositories:
  - Gradio `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` from `gradio-app/gradio`.
  - REsq Mesh `README.md` from `yashwan7/REsq-mesh`.
- Expected source labels assume Laptop A will preserve these document identities when copying them into `data/`: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `resqmesh/README.md`. The evaluator accepts normalized path suffixes and basenames to tolerate a different `data/` prefix.
- The 20 in-scope answers are short, directly verifiable paraphrases. The five out-of-scope prompts intentionally do not have expected answers or sources; only refusal behavior is scored.
- No API key is stored in this repository. Evaluation code reads `GOOGLE_API_KEY` from the environment (and optionally a local `.env` file that is not committed).

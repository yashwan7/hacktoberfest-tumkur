# Production design decisions

## Fast local CPU path

The app uses `all-MiniLM-L6-v2` for local embeddings and BM25 for lexical matching. MiniLM keeps indexing and query embedding practical on CPU; BM25 protects exact commands, filenames, and identifiers such as `run_backend_tests.sh` that dense retrieval can blur.

## Evidence-first answers

`answer()` returns structured `sources` and `passages` directly from retrieval. The model is asked to answer only from those passages and to emit JSON. The UI renders the answer, source file/chunk IDs, passage scores, and full retrieved text side by side.

## Refusal gate

The engine refuses when retrieval falls below the configured threshold or when the question has no meaningful token overlap with the indexed corpus. Gemma also receives an explicit refusal instruction for evidence gaps. This gives the demo a deterministic first line of defense plus a model-level safety check.

## Scope and speed trade-offs

The corpus is eight Markdown files from the requested Gradio and REsq Mesh repositories. There is no vector database, reranker, or persistent index: the corpus is small enough that an in-memory NumPy matrix is simpler and faster for a hackathon demo.

## Model fallback

The requested default is `gemma-4-26b-a4b-it`. If Google AI Studio rejects that model name, the client lists available models and selects the closest Gemma instruct variant before retrying. The API key is loaded only from `GOOGLE_API_KEY` via `.env`/environment.

## Known limitations

- The fallback model selection depends on the models exposed to the configured API account.
- File-level citations and chunk IDs prove what was passed to Gemma, but not sentence-level entailment.
- Index construction downloads/loads the embedding model on first run.
- CPU embeddings are adequate for this small corpus, not for a large production knowledge base.

"""Small, local-first hybrid RAG engine for the contributor guide demo."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

load_dotenv()

TOKEN_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
STOPWORDS = {
    "about", "after", "again", "also", "answer", "could", "does", "from",
    "give", "have", "help", "how", "into", "more", "please", "should", "that",
    "the", "their", "there", "these", "this", "what", "when", "where", "which",
    "with", "would", "your", "you",
}


@dataclass(frozen=True)
class Chunk:
    file: str
    chunk_id: int
    text: str


@dataclass
class Index:
    docs_dir: str
    chunk_size: int
    overlap: int
    embed_model: str
    chunks: list[Chunk]
    embeddings: np.ndarray
    bm25: BM25Okapi
    encoder: SentenceTransformer
    vocabulary: set[str]


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        if end < len(text):
            boundary = max(text.rfind("\n\n", start + chunk_size // 2, end),
                           text.rfind("\n", start + chunk_size // 2, end),
                           text.rfind(" ", start + chunk_size // 2, end))
            if boundary > start:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(start + 1, end - max(0, overlap))
    return chunks


def build_index(docs_dir="data", chunk_size=800, overlap=120,
                embed_model="all-MiniLM-L6-v2") -> Index:
    """Read markdown files and build a CPU embedding + BM25 index."""
    root = Path(docs_dir)
    if not root.exists():
        raise FileNotFoundError(f"Document directory not found: {root}")
    chunks: list[Chunk] = []
    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(root).as_posix()
        for chunk_id, piece in enumerate(_chunk_text(text, chunk_size, overlap)):
            chunks.append(Chunk(relative, chunk_id, piece))
    if not chunks:
        raise ValueError(f"No markdown documents found under {root}")
    encoder = SentenceTransformer(embed_model, device="cpu")
    embeddings = encoder.encode(
        [chunk.text for chunk in chunks], normalize_embeddings=True,
        convert_to_numpy=True, show_progress_bar=False,
    )
    tokenized = [_tokens(chunk.text) for chunk in chunks]
    return Index(
        str(root), chunk_size, overlap, embed_model, chunks,
        np.asarray(embeddings), BM25Okapi(tokenized), encoder,
        {token for tokens in tokenized for token in tokens},
    )


def _retrieve(question: str, index: Index, top_k: int, threshold: float,
              hybrid: bool) -> list[dict[str, Any]]:
    query_tokens = _tokens(question)
    query_embedding = index.encoder.encode(
        [question], normalize_embeddings=True, convert_to_numpy=True,
        show_progress_bar=False,
    )[0]
    dense = np.clip(index.embeddings @ query_embedding, 0.0, 1.0)
    lexical = np.asarray(index.bm25.get_scores(query_tokens), dtype=float)
    if lexical.size and lexical.max() > 0:
        lexical = lexical / lexical.max()
    scores = 0.75 * dense + 0.25 * lexical if hybrid else dense
    order = np.argsort(scores)[::-1]
    hits: list[dict[str, Any]] = []
    for position in order[: max(top_k, 1)]:
        score = float(scores[position])
        if score < threshold:
            continue
        chunk = index.chunks[int(position)]
        hits.append({"file": chunk.file, "chunk_id": chunk.chunk_id,
                     "text": chunk.text, "score": round(score, 4)})
    return hits


def _has_corpus_overlap(question: str, index: Index) -> bool:
    query = {token for token in _tokens(question) if len(token) > 2 and token not in STOPWORDS}
    return bool(query & index.vocabulary)


def _client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set; add it to .env or the environment")
    from google import genai
    return genai.Client(api_key=api_key)


def _model_names(client) -> list[str]:
    names = []
    for item in client.models.list():
        name = str(getattr(item, "name", ""))
        if name.startswith("models/"):
            name = name.split("/", 1)[1]
        if name:
            names.append(name)
    return names


def _closest_gemma(client, requested: str) -> str | None:
    try:
        names = _model_names(client)
    except Exception:
        return None
    gemma = [name for name in names if "gemma" in name.lower() and "generatecontent" in " ".join([]).lower() or "gemma" in name.lower()]
    if not gemma:
        return None
    preferred = [name for name in gemma if "4" in name and ("it" in name or "instruct" in name)]
    preferred += [name for name in gemma if "it" in name or "instruct" in name]
    preferred += gemma
    return preferred[0] if preferred else requested


def _generate(client, prompt: str, model: str) -> tuple[str, str]:
    selected = model
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=selected, contents=prompt)
            text = getattr(response, "text", None)
            if text:
                return text, selected
            return str(response), selected
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            if attempt == 0 and any(token in message for token in ("not found", "404", "model")):
                fallback = _closest_gemma(client, selected)
                if fallback and fallback != selected:
                    selected = fallback
                    continue
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Gemma request failed: {last_error}")


def _parse_generation(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {"answer": text, "refused": False}


def answer(question, index, top_k=4, threshold=0.30, history=None,
           use_rag=True, hybrid=True, model="gemma-4-26b-a4b-it") -> dict:
    """Answer from retrieved evidence and return judge/UI-friendly metadata."""
    started = time.perf_counter()
    if not use_rag:
        hits = []
    else:
        hits = _retrieve(question, index, top_k, threshold, hybrid)
    refused = use_rag and (not hits or not _has_corpus_overlap(question, index))
    if refused:
        return {
            "answer": "I can only answer questions grounded in the indexed contributor guide. Try asking about setup, testing, pull requests, coding style, community standards, or REsq Mesh.",
            "sources": [], "passages": [], "refused": True,
            "latency_s": round(time.perf_counter() - started, 4),
        }
    if not use_rag:
        prompt_context = "No documentation passages were retrieved. Do not claim knowledge from the contributor guide."
    else:
        prompt_context = "\n\n".join(
            f"SOURCE: {hit['file']} [chunk_id={hit['chunk_id']}]\n{hit['text']}" for hit in hits
        )
    recent_history = (history or [])[-6:]
    history_text = "\n".join(
        f"{item.get('role', 'user')}: {item.get('content', '')}" if isinstance(item, dict)
        else str(item) for item in recent_history
    )
    prompt = f"""You are an open-source contributor guide assistant.
Answer the user's question using only the documentation passages below.
If the passages do not support an answer, or the question is unrelated to the guide, refuse.
Return valid JSON only with exactly: answer (string), refused (boolean).
For a supported answer, include compact inline citations like [CONTRIBUTING.md#3].
For a refusal, answer briefly that the question is outside the indexed guide.

Conversation history:
{history_text or '(none)'}

Documentation passages:
{prompt_context}

User question: {question}
"""
    try:
        text, _ = _generate(_client(), prompt, model)
        parsed = _parse_generation(text)
        answer_text = str(parsed.get("answer", text)).strip()
        model_refused = bool(parsed.get("refused", False))
    except Exception as exc:
        answer_text = f"I couldn't reach Gemma safely right now: {exc}"
        model_refused = True
    return {
        "answer": answer_text,
        "sources": [{"file": hit["file"], "chunk_id": hit["chunk_id"]} for hit in hits],
        "passages": hits,
        "refused": refused or model_refused,
        "latency_s": round(time.perf_counter() - started, 4),
    }

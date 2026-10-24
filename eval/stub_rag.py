"""Temporary local compatibility stub until Laptop A pushes rag.py.

This module deliberately does not pretend to be the production RAG system. It
loads no external model and returns a clear refusal-shaped placeholder so the
evaluation scripts can be imported and smoke-tested without credentials.
"""

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter


@dataclass
class Index:
    docs_dir: str
    chunk_size: int
    overlap: int
    embed_model: str


def build_index(docs_dir="data", chunk_size=800, overlap=120, embed_model="all-MiniLM-L6-v2"):
    return Index(docs_dir, chunk_size, overlap, embed_model)


def answer(question, index, top_k=4, threshold=0.30, history=None, use_rag=True,
           hybrid=True, model="gemma-4-26b-a4b-it"):
    started = perf_counter()
    return {
        "answer": "The production rag.py has not been pushed yet; no answer is available from the local stub.",
        "sources": [],
        "passages": [],
        "refused": True,
        "latency_s": perf_counter() - started,
    }

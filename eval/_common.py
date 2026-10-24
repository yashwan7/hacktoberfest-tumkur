"""Shared helpers for the evaluation scripts."""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEST_SET = ROOT / "eval" / "test_set.json"


def load_dotenv_if_present() -> None:
    """Load simple KEY=VALUE entries without requiring python-dotenv."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def load_test_set(path: Path = TEST_SET) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rag() -> tuple[Any, str]:
    """Return the production module when available, otherwise the local stub."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module("rag")
        if hasattr(module, "build_index") and hasattr(module, "answer"):
            return module, "rag"
    except Exception:
        pass
    from eval import stub_rag

    return stub_rag, "eval.stub_rag"


def normalized_source(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("file", "")
    return str(value or "").replace("\\", "/").strip().lower().lstrip("./")


def citation_hit(expected_source: str | None, sources: Any) -> bool:
    if not expected_source:
        return False
    expected = normalized_source(expected_source)
    for source in sources or []:
        actual = normalized_source(source)
        if actual == expected or actual.endswith("/" + expected):
            return True
    return False


def make_judge(model: str = "gemma-4-26b-a4b-it"):
    """Create a Gemma judge callable using GOOGLE_API_KEY from the environment."""
    load_dotenv_if_present()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None, "GOOGLE_API_KEY is not set"

    try:
        from google import genai  # type: ignore
        from google.genai import types

        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=45000, retry_options=types.HttpRetryOptions(attempts=1)))

        def modern(prompt: str) -> str:
            response = client.models.generate_content(model=model, contents=prompt, config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="minimal"), max_output_tokens=512, temperature=0))
            text = getattr(response, "text", "")
            if not text:
                raise RuntimeError("Judge temporarily returned no final text")
            return text

        return modern, "google-genai/minimal-thinking-temp0-512tokens-v2"
    except ImportError:
        pass

    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)

        def legacy(prompt: str) -> str:
            response = model_instance.generate_content(prompt)
            return getattr(response, "text", "") or str(response)

        return legacy, "google-generativeai"
    except ImportError:
        return None, "Install google-genai or google-generativeai"


def with_retries(callable_, *, retries: int = 4, base_delay: float = 2.0,
                 sleep_between: float = 1.0):
    last_error = None
    for attempt in range(retries + 1):
        try:
            value = callable_()
            if sleep_between:
                time.sleep(sleep_between)
            return value, None
        except Exception as exc:  # SDK exception types differ between versions.
            last_error = exc
            message = str(exc).lower()
            retryable = any(token in message for token in
                            ("429", "rate limit", "resource exhausted", "temporarily", "timeout", "500", "502", "503", "504", "internal error", "getaddrinfo"))
            if attempt >= retries or not retryable:
                break
            time.sleep(base_delay * (2 ** attempt))
    return None, str(last_error)


def judge_answer(judge, question: str, expected: str, actual: str,
                 *, retries: int = 4, sleep_between: float = 1.0) -> dict[str, str]:
    prompt = f"""You are a strict evaluator for a documentation-grounded RAG system.
Compare the candidate answer to the short ground-truth answer using only the facts in the ground truth.
Return exactly one label, CORRECT, PARTIAL, or WRONG, followed by a hyphen and one concise reason.
Do not reward extra unsupported claims. A response that answers only part of the ground truth is PARTIAL.

Question: {question}
Ground truth: {expected}
Candidate answer: {actual}
"""
    if judge is None:
        return {"label": "UNAVAILABLE", "reason": "Gemma judge unavailable"}
    raw, error = with_retries(lambda: judge(prompt), retries=retries,
                              sleep_between=sleep_between)
    if error:
        return {"label": "UNAVAILABLE", "reason": error}
    text = str(raw).strip()
    match = re.search(r"\b(CORRECT|PARTIAL|WRONG)\b", text.upper())
    label = match.group(1) if match else "UNPARSEABLE"
    reason = text[match.end():].lstrip(" :-") if match else text
    return {"label": label, "reason": reason[:300] or "No reason returned"}


def score_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    in_scope = [row for row in rows if not row["case"].get("expected_refused", False)]
    out_scope = [row for row in rows if row["case"].get("expected_refused", False)]
    judged = [row for row in in_scope if row["judge"].get("label") in {"CORRECT", "PARTIAL", "WRONG"}]
    counts = {label: sum(row["judge"].get("label") == label for row in judged)
              for label in ("CORRECT", "PARTIAL", "WRONG")}
    refusal_correct = sum(bool(row["response"].get("refused")) for row in out_scope)
    citation_count = sum(row["citation_hit"] for row in in_scope)
    return {
        "total": len(rows),
        "in_scope": len(in_scope),
        "out_of_scope": len(out_scope),
        "judged": len(judged),
        "unavailable": len(in_scope) - len(judged),
        "accuracy_all_in_scope": counts["CORRECT"] / len(in_scope) if in_scope else None,
        "graded_score_all_in_scope": (counts["CORRECT"] + 0.5 * counts["PARTIAL"]) / len(in_scope) if in_scope else None,
        "correct": counts["CORRECT"],
        "partial": counts["PARTIAL"],
        "wrong": counts["WRONG"],
        "accuracy": counts["CORRECT"] / len(judged) if judged else None,
        "graded_score": (counts["CORRECT"] + 0.5 * counts["PARTIAL"]) / len(judged) if judged else None,
        "citation_hits": citation_count,
        "citation_hit_rate": citation_count / len(in_scope) if in_scope else None,
        "refusal_correct": refusal_correct,
        "refusal_accuracy": refusal_correct / len(out_scope) if out_scope else None,
        "avg_latency_s": (sum(float(row["response"].get("latency_s", 0) or 0) for row in rows) / len(rows)) if rows else None,
    }


def markdown_table(summary: dict[str, Any], *, title: str = "Evaluation") -> str:
    def fmt(value):
        if value is None:
            return "n/a"
        if isinstance(value, float):
            return f"{value:.3f}"
        return str(value)

    return "\n".join([
        f"### {title}",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Questions | {summary['total']} |",
        f"| In-scope judged | {summary['judged']} / {summary['in_scope']} |",
        f"| Correct | {summary['correct']} |",
        f"| Partial | {summary['partial']} |",
        f"| Wrong | {summary['wrong']} |",
        f"| Accuracy among judged | {fmt(summary['accuracy'])} |",
        f"| Confirmed correct / all in-scope | {fmt(summary.get('accuracy_all_in_scope'))} |",
        f"| Unavailable judgments | {summary.get('unavailable', summary['in_scope']-summary['judged'])} |",
        f"| Graded score (correct + 0.5×partial) | {fmt(summary['graded_score'])} |",
        f"| Citation hit rate | {fmt(summary['citation_hit_rate'])} |",
        f"| Out-of-scope refusal accuracy | {fmt(summary['refusal_accuracy'])} |",
        f"| Average latency (s) | {fmt(summary['avg_latency_s'])} |",
    ])

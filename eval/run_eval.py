"""Run the 25-question RAG evaluation set.

Example:
    python eval/run_eval.py --run-name baseline
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Allow both `python eval/run_eval.py` and `python -m eval.run_eval`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval._common import (ROOT, citation_hit, load_rag, load_test_set,
                          make_judge, markdown_table, score_rows,
                          judge_answer, with_retries)


def evaluate_cases(*, cases: list[dict[str, Any]], rag_module, index,
                   judge, answer_kwargs: dict[str, Any] | None = None,
                   sleep_between: float = 1.0, judge_retries: int = 4) -> list[dict[str, Any]]:
    answer_kwargs = answer_kwargs or {}
    rows = []
    for case in cases:
        response, error = with_retries(
            lambda: rag_module.answer(case["question"], index, **answer_kwargs),
            retries=3, base_delay=1.5, sleep_between=sleep_between,
        )
        if error:
            response = {
                "answer": "Evaluation call failed: " + error,
                "sources": [], "passages": [], "refused": False, "latency_s": None,
            }
        response = dict(response or {})
        response.setdefault("answer", "")
        response.setdefault("sources", [])
        response.setdefault("passages", [])
        response.setdefault("refused", False)
        response.setdefault("latency_s", None)
        expected_refused = bool(case.get("expected_refused", False))
        judge_result = {"label": "NOT_APPLICABLE", "reason": "Out-of-scope refusal case"}
        if not expected_refused:
            judge_result = judge_answer(
                judge, case["question"], case["expected_answer"], response["answer"],
                retries=judge_retries, sleep_between=sleep_between,
            )
        rows.append({
            "case": case,
            "response": response,
            "citation_hit": citation_hit(case.get("expected_source"), response.get("sources")),
            "refusal_correct": bool(response.get("refused")) == expected_refused,
            "judge": judge_result,
            "error": error,
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default="baseline")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", default="gemma-4-26b-a4b-it")
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--use-rag", action="store_true", default=True)
    parser.add_argument("--no-hybrid", action="store_true")
    parser.add_argument("--threshold", type=float, default=0.30)
    parser.add_argument("--top-k", type=int, default=4)
    args = parser.parse_args()

    cases = load_test_set()
    if args.limit:
        cases = cases[:args.limit]
    rag_module, rag_name = load_rag()
    index = rag_module.build_index(args.data_dir)
    judge = None
    judge_backend = "disabled"
    if not args.no_judge:
        judge, judge_backend = make_judge(args.model)
    rows = evaluate_cases(
        cases=cases, rag_module=rag_module, index=index, judge=judge,
        answer_kwargs={"top_k": args.top_k, "threshold": args.threshold,
                       "use_rag": args.use_rag, "hybrid": not args.no_hybrid,
                       "model": args.model},
        sleep_between=args.sleep,
    )
    summary = score_rows(rows)
    result = {
        "run_name": args.run_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rag_module": rag_name,
        "judge_backend": judge_backend,
        "config": {"data_dir": args.data_dir, "top_k": args.top_k,
                   "threshold": args.threshold, "use_rag": args.use_rag,
                   "hybrid": not args.no_hybrid, "model": args.model},
        "summary": summary,
        "rows": rows,
    }
    output_dir = ROOT / "eval" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.run_name}.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(markdown_table(summary, title=f"Evaluation: {args.run_name}"))
    print(f"\nSaved {output_path}")


if __name__ == "__main__":
    main()

"""Compare Gemma 4 26B and 31B through the same RAG test protocol."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval._common import load_rag, load_test_set, make_judge, score_rows
from eval.run_eval import evaluate_cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--judge-model", default="gemma-4-26b-a4b-it")
    args = parser.parse_args()

    cases = load_test_set()
    if args.limit:
        cases = cases[:args.limit]
    rag_module, rag_name = load_rag()
    index = rag_module.build_index(args.data_dir)
    judge, judge_backend = (None, "disabled") if args.no_judge else make_judge(args.judge_model)
    models = ["gemma-4-26b-a4b-it", "gemma-4-31b-it"]
    results = {}
    for model in models:
        rows = evaluate_cases(
            cases=cases, rag_module=rag_module, index=index, judge=judge,
            answer_kwargs={"top_k": 4, "threshold": 0.30, "use_rag": True,
                           "hybrid": True, "model": model},
            sleep_between=args.sleep,
        )
        results[model] = {"summary": score_rows(rows), "rows": rows}

    output_dir = ROOT / "eval" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = {"rag_module": rag_name, "judge_backend": judge_backend,
           "config": {"top_k": 4, "threshold": 0.30, "hybrid": True},
           "models": results}
    (output_dir / "model_comparison.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Gemma 4 model comparison",
        "",
        "Both models use the same index, test set, retrieval configuration, and judge. Latency is the value returned by the application for each answer; quality is judged by the configured Gemma judge.",
        "",
        "| Model | Accuracy | Graded score | Citation hit rate | Refusal accuracy | Avg latency (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model, result in results.items():
        summary = result["summary"]
        def fmt(value): return "n/a" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value)
        lines.append(f"| `{model}` | {fmt(summary['accuracy'])} | {fmt(summary['graded_score'])} | {fmt(summary['citation_hit_rate'])} | {fmt(summary['refusal_accuracy'])} | {fmt(summary['avg_latency_s'])} |")
    if all(result["summary"]["accuracy"] is None for result in results.values()):
        lines.extend(["", "No quality comparison is claimed yet: production `rag.py`, `data/`, or the Gemma judge was unavailable for this committed run."])
    lines.extend(["", "Raw data: [`model_comparison.json`](model_comparison.json)"])
    (output_dir / "model_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

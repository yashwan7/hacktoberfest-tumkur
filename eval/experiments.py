"""Run one-factor-at-a-time RAG experiments around the default configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval._common import (load_rag, load_test_set, make_judge, score_rows,
                          markdown_table)
from eval.run_eval import evaluate_cases


DEFAULT = {
    "chunk_size": 800,
    "overlap": 120,
    "top_k": 4,
    "hybrid": True,
    "threshold": 0.30,
    "model": "gemma-4-26b-a4b-it",
}


def experiment_configs() -> list[dict[str, Any]]:
    configs = [{**DEFAULT, "name": "default", "factor": "default", "factor_value": "800/4/true/0.30"}]
    for value in (400, 1200):
        configs.append({**DEFAULT, "name": f"chunk_size={value}", "factor": "chunk_size", "factor_value": value, "chunk_size": value})
    for value in (2, 6):
        configs.append({**DEFAULT, "name": f"top_k={value}", "factor": "top_k", "factor_value": value, "top_k": value})
    configs.append({**DEFAULT, "name": "hybrid=false", "factor": "hybrid", "factor_value": False, "hybrid": False})
    for value in (0.20, 0.40):
        configs.append({**DEFAULT, "name": f"threshold={value:.2f}", "factor": "threshold", "factor_value": value, "threshold": value})
    return configs


def write_charts(results: list[dict[str, Any]], chart_dir: Path) -> str:
    chart_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError:
        return "Charts were not rendered: matplotlib is not installed in this environment. Re-run after installing matplotlib."

    chart_specs = [
        ("chunk_size", "Chunk size", "accuracy_vs_chunk_size.png"),
        ("top_k", "top_k", "accuracy_vs_top_k.png"),
    ]
    made = []
    for factor, label, filename in chart_specs:
        points = [(row["config"][factor], row["summary"]["accuracy"])
                  for row in results if row["factor"] in (factor, "default") and row["summary"]["accuracy"] is not None]
        fig, ax = plt.subplots(figsize=(6, 4))
        if points:
            points.sort(key=lambda item: item[0])
            ax.plot([p[0] for p in points], [p[1] for p in points], marker="o")
            ax.set_ylim(0, 1)
        else:
            ax.text(0.5, 0.5, "No judged data", ha="center", va="center")
        ax.set_xlabel(label)
        ax.set_ylabel("Accuracy")
        ax.set_title(f"Accuracy vs {label}")
        ax.grid(True, alpha=0.3)
        output = chart_dir / filename
        fig.tight_layout()
        fig.savefig(output, dpi=140)
        plt.close(fig)
        made.append(str(output.relative_to(ROOT)))
    return "Charts: " + ", ".join(f"`{path}`" for path in made)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    cases = load_test_set()
    if args.limit:
        cases = cases[:args.limit]
    rag_module, rag_name = load_rag()
    judge, judge_backend = (None, "disabled") if args.no_judge else make_judge(DEFAULT["model"])
    results = []
    for config in experiment_configs():
        index = rag_module.build_index(
            args.data_dir, chunk_size=config["chunk_size"], overlap=config["overlap"]
        )
        rows = evaluate_cases(
            cases=cases, rag_module=rag_module, index=index, judge=judge,
            answer_kwargs={"top_k": config["top_k"], "threshold": config["threshold"],
                           "use_rag": True, "hybrid": config["hybrid"], "model": config["model"]},
            sleep_between=args.sleep,
        )
        results.append({
            "name": config["name"], "factor": config["factor"],
            "factor_value": config["factor_value"], "config": config,
            "summary": score_rows(rows), "rows": rows,
        })

    output_dir = ROOT / "eval" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "experiments.json").write_text(
        json.dumps({"rag_module": rag_name, "judge_backend": judge_backend,
                    "results": results}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    chart_note = write_charts(results, output_dir)
    lines = [
        "# One-factor-at-a-time experiments",
        "",
        "The default anchor is `chunk_size=800`, `overlap=120`, `top_k=4`, `hybrid=true`, and `threshold=0.30`. Each row changes one factor while holding the others at that anchor; this avoids a full Cartesian grid and conserves API quota.",
        "",
        "| Run | Factor | Value | Accuracy | Graded score | Citation hit rate | Avg latency (s) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        summary = result["summary"]
        def fmt(value): return "n/a" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value)
        lines.append("| {name} | {factor} | {value} | {accuracy} | {graded} | {citation} | {latency} |".format(
            name=result["name"], factor=result["factor"], value=result["factor_value"],
            accuracy=fmt(summary["accuracy"]), graded=fmt(summary["graded_score"]),
            citation=fmt(summary["citation_hit_rate"]), latency=fmt(summary["avg_latency_s"]),
        ))
    lines.extend(["", f"{chart_note}", "", f"Raw data: [`experiments.json`](experiments.json)"])
    (output_dir / "experiments.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

"""Classify judged failures from a saved evaluation run."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


FIXES = {
    "service/generation availability": "Bound network timeouts and retry transient service failures; do not tune retrieval thresholds to fix an outage.",
    "judge unavailable": "Retry grading the same saved answer when the judge recovers and always show judged coverage; do not omit failures from the denominator silently.",
    "retrieval miss": "Inspect query rewriting and hybrid retrieval; add source-aware lexical signals and tune the threshold using held-out questions.",
    "chunk split": "Increase overlap or add structure-aware/heading-aware chunking so the evidence needed for one answer remains in a retrievable chunk.",
    "wrong synthesis": "Extract final non-thought text, allow a sufficient output budget, validate JSON and reject SDK dumps/truncated output; then verify each claim against passages.",
    "bad refusal threshold": "Calibrate false and missed refusals on a separate holdout. The no-RAG evidence-only prompt requires a separate control; threshold tuning cannot fix that confound.",
}


def classify(row: dict[str, Any]) -> str | None:
    case = row["case"]
    response = row.get("response", {})
    label = row.get("judge", {}).get("label")
    answer = str(response.get("answer", ""))
    if answer.startswith("I couldn\'t reach Gemma"):
        return "service/generation availability"
    if not case.get("expected_refused") and label in {"UNAVAILABLE", "UNPARSEABLE"}:
        return "judge unavailable"
    if case.get("expected_refused"):
        return "bad refusal threshold" if not row.get("refusal_correct") else None
    if label not in {"WRONG", "PARTIAL"}:
        return None
    if response.get("refused"):
        return "bad refusal threshold"
    if answer.startswith("sdk_http_response=") or answer.startswith("```json"):
        return "wrong synthesis"
    expected_source = str(case.get("expected_source", "")).lower()
    sources = [str(source.get("file", source)).lower() if isinstance(source, dict) else str(source).lower()
               for source in response.get("sources", [])]
    source_hit = any(source == expected_source or source.endswith("/" + expected_source)
                     for source in sources)
    if not source_hit:
        return "retrieval miss"
    passages = " ".join(str(p.get("text", "")) for p in response.get("passages", []) if isinstance(p, dict)).lower()
    expected_terms = [term.lower() for term in str(case.get("expected_answer", "")).split() if len(term) > 5]
    overlap = sum(term in passages for term in expected_terms)
    if passages and overlap < max(1, len(expected_terms) // 5):
        return "chunk split"
    return "wrong synthesis"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="eval/results/baseline.json")
    parser.add_argument("--output", default="eval/results/failure_analysis.md")
    parser.add_argument("--baseline-only", action="store_true", help="Exclude completed ablation/experiment/model arms")
    args = parser.parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        report = """# Failure analysis

No baseline evaluation JSON exists yet. Run `python eval/run_eval.py --run-name baseline` after Laptop A pushes `rag.py` and `data/`; this report is intentionally not a fabricated zero-failure result.

| Category | Count | Proposed fix |
|---|---:|---|
| Retrieval miss | n/a | Tune hybrid retrieval and query rewriting. |
| Chunk split | n/a | Add overlap or structure-aware chunking. |
| Wrong synthesis | n/a | Tighten grounded synthesis and evidence checks. |
| Bad refusal threshold | n/a | Calibrate against out-of-scope and borderline prompts. |
"""
        output_path.write_text(report, encoding="utf-8")
        print(report)
        return

    data = json.loads(input_path.read_text(encoding="utf-8"))
    runs = [("baseline", data.get("rows", []))]
    if not args.baseline_only:
        paired_path = ROOT / "eval/results/rag_vs_norag.json"
        if paired_path.exists():
            paired = json.loads(paired_path.read_text(encoding="utf-8"))
            if paired.get("rag_module") == "rag":
                runs += [("ablation/" + name, arm["rows"]) for name,arm in paired["modes"].items()]
        experiment_path = ROOT / "eval/results/experiments.json"
        if experiment_path.exists():
            experiment = json.loads(experiment_path.read_text(encoding="utf-8"))
            if experiment.get("rag_module") == "rag":
                runs += [("experiment/" + arm["name"], arm["rows"]) for arm in experiment["results"] if not arm.get("reused_from")]
        model_path = ROOT / "eval/results/model_comparison.json"
        if model_path.exists():
            comparison = json.loads(model_path.read_text(encoding="utf-8"))
            if comparison.get("rag_module") == "rag":
                runs += [("model/" + name, arm["rows"]) for name,arm in comparison["models"].items()]
    rows = [dict(row, evaluation_run=name) for name,entries in runs for row in entries]
    classified = [(row, classify(row)) for row in rows]
    counts = Counter(category for _, category in classified if category)
    judged_failures = sum(category is not None for _, category in classified)
    lines = [
        "# Failure analysis",
        "",
        f"Source run: `{input_path.relative_to(ROOT)}`. Rows judged `WRONG` or `PARTIAL`, incorrect refusals, and explicit service/judge failures are classified. Diagnostic labels are provisional; generation-format failures are grouped under wrong synthesis. Classified failures: **{judged_failures}**.",
        "",
        "Completed production arms are included below; reused default-anchor rows are excluded to avoid counting the same observation twice. Baseline judge v1 and subsequent judge v2 are distinct protocols; these diagnostic counts are not pooled quality estimates.",
        "",
        "| Category | Count | Proposed fix |",
        "|---|---:|---|",
    ]
    for category in FIXES:
        lines.append(f"| {category.title()} | {counts.get(category, 0)} | {FIXES[category]} |")
    lines.extend(["", "## Coverage by run", "", "| Run | Cases | Wrong/partial/unavailable/service/refusal failures |", "|---|---:|---:|"])
    for name,entries in runs:
        lines.append(f"| {name} | {len(entries)} | {sum(classify(row) is not None for row in entries)} |")
    lines.extend(["", "## All classified failures", ""])
    lines.append("Refusal-policy labels in no-RAG include its retained evidence-only prompt, not just numeric thresholds. Service failures require connectivity/timeouts fixes. Raw SDK dumps and truncated JSON are response-extraction/synthesis failures; validate final text and JSON rather than returning SDK repr strings.")
    lines.append("")
    examples = [(row, category) for row, category in classified if category]
    if not examples:
        lines.append("No judged failures were present in this run. This is only meaningful when the run has judged rows; otherwise check the judge backend and run metadata.")
    else:
        for row, category in examples:
            lines.append(f"- **{row.get('evaluation_run', 'baseline')}/{row['case']['id']} — {category} ({row['judge'].get('label')})**: {row['case']['question']} — {row['judge'].get('reason', '')}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

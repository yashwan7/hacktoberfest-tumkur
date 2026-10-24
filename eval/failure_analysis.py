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
    "retrieval miss": "Inspect query rewriting and hybrid retrieval; add source-aware lexical signals and tune the threshold using held-out questions.",
    "chunk split": "Increase overlap or add structure-aware/heading-aware chunking so the evidence needed for one answer remains in a retrievable chunk.",
    "wrong synthesis": "Tighten the grounded-answer prompt, require evidence-backed claims, and expose the retrieved passages to the judge/UI.",
    "bad refusal threshold": "Calibrate refusal against out-of-scope and borderline questions; raise the refusal threshold when unsupported answers are confident.",
}


def classify(row: dict[str, Any]) -> str | None:
    case = row["case"]
    response = row.get("response", {})
    label = row.get("judge", {}).get("label")
    if case.get("expected_refused"):
        return "bad refusal threshold" if not row.get("refusal_correct") else None
    if label not in {"WRONG", "PARTIAL"}:
        return None
    if response.get("refused"):
        return "bad refusal threshold"
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
    rows = data.get("rows", [])
    classified = [(row, classify(row)) for row in rows]
    counts = Counter(category for _, category in classified if category)
    judged_failures = sum(category is not None for _, category in classified)
    lines = [
        "# Failure analysis",
        "",
        f"Source run: `{input_path.relative_to(ROOT)}`. Only rows judged `WRONG` or `PARTIAL`, plus incorrect out-of-scope refusal rows, are classified. Judged failures: **{judged_failures}**.",
        "",
        "| Category | Count | Proposed fix |",
        "|---|---:|---|",
    ]
    for category in FIXES:
        lines.append(f"| {category.title()} | {counts.get(category, 0)} | {FIXES[category]} |")
    lines.extend(["", "## Examples", ""])
    examples = [(row, category) for row, category in classified if category]
    if not examples:
        lines.append("No judged failures were present in this run. This is only meaningful when the run has judged rows; otherwise check the judge backend and run metadata.")
    else:
        for row, category in examples:
            lines.append(f"- **{row['case']['id']} — {category} ({row['judge'].get('label')})**: {row['case']['question']} — {row['judge'].get('reason', '')}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

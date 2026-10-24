"""Compare the production answer path with and without retrieval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval._common import (load_rag, load_test_set, make_judge, markdown_table,
                          score_rows)
from eval.run_eval import evaluate_cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--model", default="gemma-4-26b-a4b-it")
    args = parser.parse_args()

    cases = load_test_set()
    if args.limit:
        cases = cases[:args.limit]
    rag_module, rag_name = load_rag()
    index = rag_module.build_index(args.data_dir)
    judge, judge_backend = (None, "disabled") if args.no_judge else make_judge(args.model)
    by_mode = {}
    for mode in (True, False):
        rows = evaluate_cases(
            cases=cases, rag_module=rag_module, index=index, judge=judge,
            answer_kwargs={"top_k": 4, "threshold": 0.30, "use_rag": mode,
                           "hybrid": True, "model": args.model},
            sleep_between=args.sleep,
        )
        by_mode["rag" if mode else "no_rag"] = {"summary": score_rows(rows), "rows": rows}

    rag_rows = {row["case"]["id"]: row for row in by_mode["rag"]["rows"]}
    no_rag_rows = {row["case"]["id"]: row for row in by_mode["no_rag"]["rows"]}
    hallucinations = []
    for case in cases:
        if case.get("expected_refused"):
            continue
        no_rag = no_rag_rows[case["id"]]
        if no_rag["judge"].get("label") == "WRONG" and not no_rag["response"].get("refused"):
            hallucinations.append({
                "id": case["id"], "question": case["question"],
                "answer": no_rag["response"].get("answer", ""),
                "judge": no_rag["judge"],
                "rag_label": rag_rows[case["id"]]["judge"].get("label"),
            })

    examples = [case for case in cases if not case.get("expected_refused")][:3]
    output_dir = ROOT / "eval" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = {"rag_module": rag_name, "judge_backend": judge_backend,
           "modes": by_mode, "hallucinations": hallucinations}
    (output_dir / "rag_vs_norag.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# RAG vs no-RAG",
        "",
        "Both modes were run over the same test set with `top_k=4`, `threshold=0.30`, and the same Gemma model configuration. The no-RAG mode is expected to answer from the model without retrieved passages; this report does not treat that mode as a baseline that can cite documents.",
        "",
        "Limitation: disabling retrieval retains the application instruction to answer only from passages and refuse otherwise. Refusals are failures on in-scope cases, not hallucinations. This is an implemented-path ablation, not an unrestricted pretrained-model baseline.",
        "",
        markdown_table(by_mode["rag"]["summary"], title="With RAG"),
        "",
        markdown_table(by_mode["no_rag"]["summary"], title="Without RAG"),
        "",
        "## Candidate hallucinations: non-refused no-RAG answers judged WRONG",
        "",
    ]
    if hallucinations:
        for item in hallucinations:
            lines.extend([f"- **{item['id']} — {item['question']}**: {item['answer']} _(judge: {item['judge'].get('label')}; RAG: {item['rag_label']})_"])
    else:
        lines.append("No non-refused no-RAG answers judged WRONG were observed. Inspect judge coverage before interpreting this result. The application retains its evidence-only refusal prompt even with retrieval disabled, so this is not an unrestricted model baseline.")
    lines.extend(["", "## Three side-by-side answers", "", "| Question | With RAG | Without RAG |", "|---|---|---|"])
    for case in examples:
        rag = rag_rows[case["id"]]["response"]
        no_rag = no_rag_rows[case["id"]]["response"]
        def compact(response: dict[str, Any]) -> str:
            answer = str(response.get("answer", "")).replace("|", "\\|").replace("\n", " ")
            sources = ", ".join(str(source.get("file", source)) if isinstance(source, dict) else str(source)
                                  for source in response.get("sources", [])) or "—"
            return f"{answer} **Sources:** {sources}"
        lines.append(f"| {case['question']} | {compact(rag)} | {compact(no_rag)} |")
    lines.extend(["", "Raw data: [`rag_vs_norag.json`](rag_vs_norag.json)"])
    (output_dir / "rag_vs_norag.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

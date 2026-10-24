"""Gradio demo for the open-source contributor guide."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from rag import answer, build_index


DATA_DIR = Path(__file__).parent / "data"
# Build the combined index once at startup. Project-specific indexes are lazy so
# the demo stays responsive when a judge only wants the default view.
INDEX = build_index(str(DATA_DIR))
INDEX_CACHE = {"both": INDEX}
PROJECT_DIRS = {"gradio": DATA_DIR / "gradio", "resqmesh": DATA_DIR / "resqmesh"}


def get_project_index(project: str):
    project = project or "both"
    if project not in INDEX_CACHE:
        INDEX_CACHE[project] = build_index(str(PROJECT_DIRS[project]))
    return INDEX_CACHE[project]


def _display_result(result: dict, heading: str = "Answer"):
    answer_text = result["answer"]
    rendered = f"### {'Refused' if result['refused'] else heading}\n\n{answer_text}"
    rendered += f"\n\n*Latency: {result['latency_s']:.2f}s*"
    source_rows = [[source["file"], source["chunk_id"]] for source in result["sources"]]
    passage_rows = [
        [passage["file"], passage["chunk_id"], passage["score"], passage["text"]]
        for passage in result["passages"]
    ]
    return rendered, source_rows, passage_rows


def respond(question, history, project, top_k, threshold):
    if not question or not question.strip():
        return "", history or [], "Ask a question to search the guide.", [], []
    clean_question = question.strip()
    result = answer(
        clean_question,
        get_project_index(project),
        top_k=int(top_k),
        threshold=float(threshold),
        history=history or [],
    )
    rendered, source_rows, passage_rows = _display_result(result)
    new_history = list(history or []) + [
        {"role": "user", "content": clean_question},
        {"role": "assistant", "content": result["answer"]},
    ]
    return "", new_history, rendered, source_rows, passage_rows


def _find_passage(index, file_suffix: str, needle: str) -> dict:
    for chunk in index.chunks:
        if chunk.file.endswith(file_suffix) and needle.lower() in chunk.text.lower():
            return {"file": chunk.file, "chunk_id": chunk.chunk_id,
                    "text": chunk.text, "score": 1.0}
    return {"file": file_suffix, "chunk_id": -1,
            "text": "The requested onboarding evidence was not found in this local snapshot.",
            "score": 0.0}


def where_do_i_start(project):
    """Render an evidence-linked, deterministic newcomer checklist."""
    # Use actual indexed chunks so the evidence panel is useful during a demo.
    index = get_project_index("both")
    evidence = [
        ("Fork the repository", "CONTRIBUTING.md", "best way to contribute"),
        ("Clone your fork and enter the repository", "CONTRIBUTING.md", "Clone this repo"),
        ("Set up the project", "CONTRIBUTING.md", "Install Gradio from `main`"),
        ("Find a good first issue or file a clear issue", "CONTRIBUTING.md", "good first issue"),
        ("Create a focused branch", "CONTRIBUTING.md", "branch"),
        ("Run the relevant tests", "CONTRIBUTING.md", "run_backend_tests.sh"),
        ("Open a pull request when the contribution path allows it", "CONTRIBUTING.md", "pull request"),
    ]
    passages = [_find_passage(index, file_suffix, needle)
                for _, file_suffix, needle in evidence]
    lines = ["### Where do I start?", "", "A cited newcomer checklist from the indexed Gradio contributor docs:"]
    for number, ((label, _, _), passage) in enumerate(zip(evidence, passages), start=1):
        citation = f"[{passage['file']}#{passage['chunk_id']}]"
        lines.append(f"{number}. **{label}** — follow the documented steps. {citation}")
    lines.append("\nNote: the current Gradio docs say outside pull requests are paused; file a detailed reproducible issue first unless you are on the maintainer team.")
    result = {
        "answer": "\n".join(lines),
        "sources": [{"file": item["file"], "chunk_id": item["chunk_id"]} for item in passages],
        "passages": passages,
        "refused": False,
        "latency_s": 0.0,
    }
    return _display_result(result, heading="Onboarding checklist")


def clear_all():
    return "", [], "Ask a question to search the guide.", [], []


with gr.Blocks(title="Open-Source Contributor Guide") as demo:
    gr.Markdown(
        """# Open-Source Contributor Guide
Ask about Gradio setup, testing, PRs, coding style, community standards, or REsq Mesh.\\
Every supported answer shows its retrieved source passages; unrelated questions are refused.
"""
    )
    with gr.Row():
        project = gr.Dropdown(
            choices=[("Gradio", "gradio"), ("REsq Mesh", "resqmesh"), ("Both projects", "both")],
            value="both", label="Project scope",
        )
        top_k = gr.Slider(2, 6, value=4, step=1, label="Retrieved passages (top_k)")
        threshold = gr.Slider(0.0, 0.8, value=0.30, step=0.05, label="Retrieval threshold")
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Conversation", type="messages", height=420)
            question = gr.Textbox(label="Question", placeholder="How do I run Gradio's backend tests?", lines=2)
            with gr.Row():
                ask = gr.Button("Ask Gemma", variant="primary")
                start = gr.Button("Where do I start?")
                clear = gr.Button("Clear")
            gr.Markdown("**Example questions**")
            example_questions = [
                "How do I install Gradio from main?",
                "How do I run Gradio's Python backend tests?",
                "What should be included in a bug report?",
                "What happens when an REsq Mesh case capsule is tampered with?",
                "What is the capital of France?",
            ]
            for example_question in example_questions:
                example_button = gr.Button(example_question, size="sm")
                example_button.click(
                    lambda value=example_question: value,
                    outputs=question,
                    api_name=False,
                )
        with gr.Column(scale=3):
            answer_box = gr.Markdown("Ask a question to search the guide.", label="Answer")
            sources = gr.Dataframe(headers=["file", "chunk_id"], label="Cited sources", interactive=False)
            passages = gr.Dataframe(
                headers=["file", "chunk_id", "score", "retrieved passage"],
                datatype=["str", "number", "number", "str"],
                label="Retrieved passages", wrap=True, interactive=False,
            )
    input_controls = [question, chatbot, project, top_k, threshold]
    output_controls = [question, chatbot, answer_box, sources, passages]
    ask.click(respond, inputs=input_controls, outputs=output_controls, api_name=False)
    question.submit(respond, inputs=input_controls, outputs=output_controls, api_name=False)
    start.click(where_do_i_start, inputs=[project], outputs=[answer_box, sources, passages], api_name=False)
    clear.click(clear_all, outputs=output_controls, api_name=False)


if __name__ == "__main__":
    # Older Gradio clients can fail while introspecting newer FastAPI/Pydantic
    # schemas even when the local UI itself is healthy.
    demo.launch(show_api=False)

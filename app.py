"""Gradio demo for the open-source contributor guide."""

from __future__ import annotations

import gradio as gr

from rag import answer, build_index


INDEX = build_index()


def respond(question, history):
    if not question or not question.strip():
        return "", history or [], "Ask a question to search the guide.", [], []
    result = answer(question.strip(), INDEX, history=history or [])
    answer_text = result["answer"]
    if result["refused"]:
        answer_text = "### Refused\n\n" + answer_text
    else:
        answer_text = "### Answer\n\n" + answer_text
    answer_text += f"\n\n*Latency: {result['latency_s']:.2f}s*"
    new_history = list(history or []) + [
        {"role": "user", "content": question.strip()},
        {"role": "assistant", "content": result["answer"]},
    ]
    source_rows = [[source["file"], source["chunk_id"]] for source in result["sources"]]
    passage_rows = [[passage["file"], passage["chunk_id"], passage["score"], passage["text"]]
                    for passage in result["passages"]]
    return "", new_history, answer_text, source_rows, passage_rows


def clear_all():
    return "", [], "Ask a question to search the guide.", [], []


with gr.Blocks(title="Open-Source Contributor Guide") as demo:
    gr.Markdown("""# Open-Source Contributor Guide
Ask about Gradio setup, testing, PRs, coding style, Code of Conduct, or REsq Mesh. Every supported answer shows its retrieved source passages; unrelated questions are refused.
""")
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Conversation", type="messages", height=420)
            question = gr.Textbox(label="Question", placeholder="How do I run Gradio's backend tests?", lines=2)
            with gr.Row():
                ask = gr.Button("Ask Gemma", variant="primary")
                clear = gr.Button("Clear")
            gr.Examples(
                examples=[
                    "How do I run Gradio's Python backend tests?",
                    "What should be included in a bug report?",
                    "What happens when an REsq Mesh case capsule is tampered with?",
                    "What is the weather in Bengaluru tomorrow?",
                ], inputs=question,
            )
        with gr.Column(scale=3):
            answer_box = gr.Markdown("Ask a question to search the guide.", label="Answer")
            sources = gr.Dataframe(headers=["file", "chunk_id"], label="Cited sources", interactive=False)
            passages = gr.Dataframe(
                headers=["file", "chunk_id", "score", "retrieved passage"],
                datatype=["str", "number", "number", "str"],
                label="Retrieved passages", wrap=True, interactive=False,
            )
    ask.click(respond, inputs=[question, chatbot], outputs=[question, chatbot, answer_box, sources, passages])
    question.submit(respond, inputs=[question, chatbot], outputs=[question, chatbot, answer_box, sources, passages])
    clear.click(clear_all, outputs=[question, chatbot, answer_box, sources, passages])


if __name__ == "__main__":
    demo.launch()

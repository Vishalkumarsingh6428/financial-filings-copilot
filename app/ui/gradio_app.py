import gradio as gr
from app.graph.build import build_graph
from app.graph.state import ChatState

graph = build_graph()


def ask(question: str):
    if not question.strip():
        return "Please enter a question.", "", ""

    state: ChatState = {
        "question": question,
        "standalone_question": None,
        "retrieved_docs": [],
        "docs_relevant": None,
        "retry_count": 0,
        "answer": None,
        "citations": [],
        "verification": None,
    }
    result = graph.invoke(state)

    citations_text = "\n".join(
        f"- {c['ticker']} {c['filing_type']} FY{c['fiscal_year']}, Item {c['item_number']} ({c['section_title']})"
        for c in result["citations"]
    ) or "No sources cited."

    verification = result["verification"]
    verification_text = f"**{verification['verdict']}** — {verification['reason']}"

    return result["answer"], citations_text, verification_text


demo = gr.Interface(
    fn=ask,
    inputs=gr.Textbox(label="Ask a question about SEC filings", placeholder="e.g. What was Apple's revenue in fiscal 2023?"),
    outputs=[
        gr.Textbox(label="Answer"),
        gr.Textbox(label="Sources"),
        gr.Markdown(label="Verification"),
    ],
    title="Financial Filings Copilot",
    description="Ask questions about 10-K/10-Q filings for 15 companies (AAPL, MSFT, GOOGL, NVDA, AMZN, META, TSLA, AMD, AXP, JPM, GS, MS, BAC, C, STT).",
)

if __name__ == "__main__":
    demo.launch()

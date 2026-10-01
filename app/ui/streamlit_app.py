import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from app.graph.build import build_graph
from app.graph.state import ChatState

st.set_page_config(page_title="Financial Filings Copilot", page_icon="📊")

@st.cache_resource
def get_graph():
    return build_graph()

graph = get_graph()

st.title("Financial Filings Copilot")
st.write(
    "Ask questions about 10-K/10-Q filings for 15 companies "
    "(AAPL, MSFT, GOOGL, NVDA, AMZN, META, TSLA, AMD, AXP, JPM, GS, MS, BAC, C, STT)."
)

question = st.text_input("Ask a question about SEC filings", placeholder="e.g. What was Apple's revenue in fiscal 2023?")

if st.button("Submit") and question.strip():
    with st.spinner("Retrieving and generating answer..."):
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

    st.subheader("Answer")
    st.write(result["answer"])

    st.subheader("Sources")
    if result["citations"]:
        for c in result["citations"]:
            st.markdown(f"- {c['ticker']} {c['filing_type']} FY{c['fiscal_year']}, Item {c['item_number']} ({c['section_title']})")
    else:
        st.write("No sources cited.")

    st.subheader("Verification")
    v = result["verification"]
    st.markdown(f"**{v['verdict']}** — {v['reason']}")
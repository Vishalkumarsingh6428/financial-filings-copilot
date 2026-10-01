import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from app.graph.build import build_graph
from app.graph.state import ChatState

st.set_page_config(page_title="Financial Filings Copilot", page_icon="📊", layout="centered")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 2.2rem; padding-bottom: 6rem; max-width: 800px; }
    .app-title { font-size: 1.9rem; font-weight: 700; color: #1a1a1a; margin-bottom: 0.2rem; }
    .app-subtitle { color: #6b6b6b; font-size: 0.92rem; margin-bottom: 1.2rem; }
    [data-testid="stChatMessage"] { padding: 0.9rem 1.1rem; border-radius: 14px; margin-bottom: 0.6rem; }
    [data-testid="stChatMessageContent"] { font-size: 0.96rem; line-height: 1.55; }
    div[data-testid="stChatInput"] textarea { border-radius: 14px !important; }
    details { border: 1px solid #e5e5e5 !important; border-radius: 10px !important; background-color: #fafafa !important; margin-top: 0.4rem; }
    summary { font-size: 0.85rem !important; font-weight: 500 !important; color: #555 !important; }
    .evidence-card { border: 1px solid #e5e5e5; border-radius: 10px; padding: 0.7rem 0.9rem; margin-bottom: 0.5rem; background: #fafafa; }
    .evidence-card .src-title { font-weight: 600; font-size: 0.85rem; color: #333; }
    .evidence-card .src-excerpt { font-size: 0.82rem; color: #666; margin-top: 0.3rem; font-style: italic; }
    .refusal-box { border: 1px solid #f0c36d; background: #fff8e8; border-radius: 10px; padding: 0.9rem 1.1rem; margin-top: 0.3rem; }
    .verified-badge { display: inline-block; font-size: 0.78rem; font-weight: 600; padding: 0.15rem 0.6rem; border-radius: 20px; margin-bottom: 0.5rem; }
    .verified-yes { background: #e6f4ea; color: #1e7e34; }
    .verified-no { background: #fdeaea; color: #b02a2a; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_graph():
    return build_graph()

graph = get_graph()

COMPANIES = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "META", "TSLA", "AMD"],
    "Financial Services": ["AXP", "JPM", "GS", "MS", "BAC", "C", "STT"],
}

EXAMPLE_QUESTIONS = [
    "What are Apple's major revenue segments?",
    "How did NVIDIA's revenue change?",
    "What risks does JPMorgan identify?",
    "What was Microsoft's operating income?",
]

with st.sidebar:
    st.markdown("### Coverage")
    st.caption("15 companies · 75 filings · 10-K + 10-Q")
    for category, tickers in COMPANIES.items():
        st.markdown(f"**{category}**")
        st.caption(" · ".join(tickers))
    st.divider()
    st.markdown("### Focus company (optional)")
    focus = st.selectbox("Narrow your question to one company", ["Any"] + sum(COMPANIES.values(), []))

st.markdown('<div class="app-title">Financial Filings Copilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Ask about 10-K/10-Q filings for AAPL, MSFT, GOOGL, NVDA, AMZN, META, '
    'TSLA, AMD, AXP, JPM, GS, MS, BAC, C, STT.</div>',
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if not st.session_state.messages:
    st.markdown("**Try asking:**")
    cols = st.columns(2)
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        if cols[i % 2].button(q, use_container_width=True):
            st.session_state.pending_question = q
            st.rerun()

USER_AVATAR = "🧑‍💼"
ASSISTANT_AVATAR = "📊"


def render_evidence_and_verification(citations, verification, evidence_sufficient, retries_used, elapsed):
    badge_class = "verified-yes" if verification["verdict"] == "SUPPORTED" else "verified-no"
    badge_label = "✓ Supported by evidence" if verification["verdict"] == "SUPPORTED" else "⚠ " + verification["verdict"]
    st.markdown(f'<span class="verified-badge {badge_class}">{badge_label}</span>', unsafe_allow_html=True)

    if citations:
        with st.expander(f"Key evidence ({len(citations)} source{'s' if len(citations) != 1 else ''})"):
            for c in citations:
                st.markdown(
                    f'<div class="evidence-card">'
                    f'<div class="src-title">{c["ticker"]} — FY{c["fiscal_year"]} {c["filing_type"]} · '
                    f'Item {c["item_number"]}: {c["section_title"]}</div>'
                    f'<div class="src-excerpt">"{c.get("excerpt", "")}"</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    with st.expander("Retrieval details"):
        st.markdown(
            f"- Evidence check: {'passed' if evidence_sufficient else 'insufficient, retried'}\n"
            f"- Query retries used: {retries_used}\n"
            f"- Pipeline: hybrid retrieval (BM25 + vector) → cross-encoder rerank → relevance grading → generation → citation verification\n"
            f"- Response time: {elapsed:.1f}s"
        )


def stream_words(text, delay=0.012):
    for word in text.split(" "):
        yield word + " "
        time.sleep(delay)


# Replay history (no streaming effect on replay)
for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else ASSISTANT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            if not msg.get("evidence_sufficient", True):
                st.markdown(
                    f'<div class="refusal-box">⚠ <b>Not found in the filings</b><br>{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(msg["content"])
            render_evidence_and_verification(
                msg.get("citations", []), msg["verification"],
                msg.get("evidence_sufficient", True), msg.get("retries_used", 0), msg.get("elapsed", 0.0),
            )

question = st.chat_input("Ask a question about SEC filings") or st.session_state.pending_question
st.session_state.pending_question = None

if question:
    if focus != "Any":
        question_for_graph = f"[Focus: {focus}] {question}"
    else:
        question_for_graph = question

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        start = time.time()
        with st.spinner("Retrieving and generating answer..."):
            state: ChatState = {
                "question": question_for_graph,
                "standalone_question": None,
                "retrieved_docs": [],
                "docs_relevant": None,
                "retry_count": 0,
                "answer": None,
                "citations": [],
                "verification": None,
                "evidence_sufficient": None,
            }
            result = graph.invoke(state)
        elapsed = time.time() - start

        if not result.get("evidence_sufficient", True):
            st.markdown('<div class="refusal-box">⚠ <b>Not found in the filings</b><br></div>', unsafe_allow_html=True)
            st.write_stream(stream_words(result["answer"]))
        else:
            st.write_stream(stream_words(result["answer"]))

        render_evidence_and_verification(
            result["citations"], result["verification"],
            result.get("evidence_sufficient", True), result["retry_count"], elapsed,
        )

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "citations": result["citations"],
        "verification": result["verification"],
        "evidence_sufficient": result.get("evidence_sufficient", True),
        "retries_used": result["retry_count"],
        "elapsed": elapsed,
    })
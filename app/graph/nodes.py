from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import INDEX_NAME
from app.graph.state import ChatState
from langchain_groq import ChatGroq
from app.config import LLM_MODEL
import re
from app.config import TICKERS
from app.config import TICKERS, COMPANY_NAME_TO_TICKER

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

def extract_filters(question: str) -> dict:
    filters = {}

    year_match = re.search(r'\b(20\d{2})\b', question)
    if year_match:
        filters["fiscal_year"] = year_match.group(1)

    q_upper = question.upper()

    # check tickers first (word-boundary safe)
    for ticker in TICKERS:
        if re.search(rf'\b{re.escape(ticker)}\b', q_upper):
            filters["ticker"] = ticker
            break

    # fall back to company name matching
    if "ticker" not in filters:
        for name, ticker in COMPANY_NAME_TO_TICKER.items():
            if name in q_upper:
                filters["ticker"] = ticker
                break

    return filters


from app.retrieval.rerank import hybrid_rerank_retrieve

def retrieve(state: ChatState) -> dict:
    query = state.get("standalone_question") or state["question"]
    docs = hybrid_rerank_retrieve(query, candidate_k=20, final_k=5)
    return {"retrieved_docs": docs}


llm = ChatGroq(model=LLM_MODEL, temperature=0)

GRADE_PROMPT = """You are checking whether retrieved document excerpts are relevant enough to answer a financial question.

Question: {question}

Retrieved excerpts:
{excerpts}

Do these excerpts contain information that could answer the question? Reply with exactly one word: YES or NO."""


def grade_docs(state: ChatState) -> dict:
    docs = state["retrieved_docs"]
    query = state.get("standalone_question") or state["question"]

    if not docs:
        return {"docs_relevant": False}

    excerpts = "\n---\n".join(d.page_content[:300] for d in docs)
    prompt = GRADE_PROMPT.format(question=query, excerpts=excerpts)

    response = llm.invoke(prompt).content.strip().upper()
    is_relevant = response.startswith("YES")

    return {"docs_relevant": is_relevant}

GENERATE_PROMPT = """You are a financial research assistant. Answer the question using ONLY the information in the excerpts below. Be precise with numbers. If the excerpts don't fully answer the question, say what's missing.

Question: {question}

Excerpts:
{excerpts}

Answer:"""


def generate(state: ChatState) -> dict:
    docs = state["retrieved_docs"]
    query = state.get("standalone_question") or state["question"]

    excerpts = "\n---\n".join(
        f"[Source: {d.metadata['ticker']} {d.metadata['filing_type']} FY{d.metadata['fiscal_year']}, "
        f"Item {d.metadata['item_number']} ({d.metadata['section_title']})]\n{d.page_content}"
        for d in docs
    )
    prompt = GENERATE_PROMPT.format(question=query, excerpts=excerpts)
    response = llm.invoke(prompt).content

    seen = set()
    citations = []
    for d in docs:
        key = (d.metadata["ticker"], d.metadata["filing_type"], d.metadata["fiscal_year"], d.metadata["item_number"])
        if key not in seen:
            seen.add(key)
            citations.append({
                "ticker": d.metadata["ticker"],
                "filing_type": d.metadata["filing_type"],
                "fiscal_year": d.metadata["fiscal_year"],
                "item_number": d.metadata["item_number"],
                "section_title": d.metadata["section_title"],
            })

    return {"answer": response, "citations": citations}

VERIFY_PROMPT = """You are fact-checking a generated answer against source excerpts.

Source excerpts:
{excerpts}

Generated answer:
{answer}

Check every factual claim in the answer. Is each claim directly supported by the excerpts, or does it contain information not present in the excerpts (fabricated, inferred, or from outside knowledge)?

Reply in this exact format:
VERDICT: SUPPORTED or UNSUPPORTED
REASON: <one sentence explaining why>"""


def verify_citations(state: ChatState) -> dict:
    docs = state["retrieved_docs"]
    answer = state["answer"]

    if not answer or not docs:
        return {"verification": {"verdict": "UNSUPPORTED", "reason": "No answer or evidence to verify."}}

    excerpts = "\n---\n".join(d.page_content for d in docs)
    prompt = VERIFY_PROMPT.format(excerpts=excerpts, answer=answer)

    response = llm.invoke(prompt).content.strip()

    verdict = "SUPPORTED" if "VERDICT: SUPPORTED" in response.upper() else "UNSUPPORTED"
    reason_line = next((line for line in response.split("\n") if line.upper().startswith("REASON:")), "")

    return {"verification": {"verdict": verdict, "reason": reason_line.replace("REASON:", "").strip()}}

if __name__ == "__main__":
    # Case 1: genuine correct answer (should verify as SUPPORTED)
    good_state: ChatState = {
        "question": "What was Apple's revenue in fiscal 2023?",
        "standalone_question": None,
        "retrieved_docs": [],
        "docs_relevant": None,
        "retry_count": 0,
        "answer": None,
        "citations": [],
        "verification": None,
    }
    good_state.update(retrieve(good_state))
    good_state.update(generate(good_state))
    good_state.update(verify_citations(good_state))
    print(f"[Genuine answer] {good_state['verification']}")

    # Case 2: same excerpts, but a deliberately fabricated answer
    bad_state = dict(good_state)
    bad_state["answer"] = "Apple's revenue in fiscal 2023 was $500 billion, driven primarily by strong sales in the Indian market."
    bad_verification = verify_citations(bad_state)
    print(f"\n[Fabricated answer] {bad_verification['verification']}")
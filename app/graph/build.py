from langgraph.graph import StateGraph, END
from app.graph.state import ChatState
from app.graph.nodes import retrieve, grade_docs, generate, llm
from app.graph.nodes import retrieve, grade_docs, generate, verify_citations, llm

MAX_RETRIES = 2


def rewrite_query(state: ChatState) -> dict:
    original = state.get("standalone_question") or state["question"]
    prompt = f"""The following question didn't retrieve relevant results from a financial filings database. Rewrite it to be more specific and searchable (mention company name/ticker, filing type, or year if implied but not stated).

Original question: {original}

Rewritten question (just the question, nothing else):"""
    rewritten = llm.invoke(prompt).content.strip()
    return {
        "standalone_question": rewritten,
        "retry_count": state["retry_count"] + 1,
    }


def route_after_grade(state: ChatState) -> str:
    if state["docs_relevant"]:
        return "generate"
    if state["retry_count"] >= MAX_RETRIES:
        return "generate"  # give up gracefully, let generate() explain insufficient evidence
    return "rewrite_query"


def build_graph():
    graph = StateGraph(ChatState)

    graph.add_node("retrieve", retrieve)
    graph.add_node("grade_docs", grade_docs)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("generate", generate)
    graph.add_node("verify_citations", verify_citations)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "grade_docs")
    graph.add_conditional_edges("grade_docs", route_after_grade, {
        "generate": "generate",
        "rewrite_query": "rewrite_query",
    })
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("generate", "verify_citations")
    graph.add_edge("verify_citations", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()

    test_state: ChatState = {
        "question": "What was Apple's revenue in fiscal 2023?",
        "standalone_question": None,
        "retrieved_docs": [],
        "docs_relevant": None,
        "retry_count": 0,
        "answer": None,
        "citations": [],
        "verification": None,
    }

    result = app.invoke(test_state)
    print(f"Retries used: {result['retry_count']}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nVerification: {result['verification']}")
    print(f"\nCitations: {len(result['citations'])} sources")
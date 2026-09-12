from app.graph.build import build_graph

graph = build_graph()
state = {
    "question": "What was Apple's revenue in fiscal 2023?",
    "standalone_question": None,
    "retrieved_docs": [],
    "docs_relevant": None,
    "retry_count": 0,
    "answer": None,
    "citations": [],
    "verification": None,
}
result = graph.invoke(state)
for c in result["citations"]:
    print(c)

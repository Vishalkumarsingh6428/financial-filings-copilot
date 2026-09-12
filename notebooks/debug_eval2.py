# notebooks/debug_eval2.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import INDEX_NAME
from app.graph.nodes import extract_filters

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

test_questions = [
    ("What cybersecurity risks did Apple identify in its 2023 10-K?", "AAPL", "1C"),
    ("What legal proceedings is Microsoft involved in?", "MSFT", "3"),
]

for question, expected_ticker, expected_item in test_questions:
    filters = extract_filters(question)
    docs = vector_store.similarity_search(question, k=5, filter=filters if filters else None)
    print(f"Q: {question}")
    print(f"Filters used: {filters}")
    print(f"Expected: ticker={expected_ticker}, item={expected_item}\n")
    for d in docs:
        m = d.metadata
        print(f"  ticker={m['ticker']} filing={m['filing_type']} item={m['item_number']} section={m['section_title'][:40]}")
    print("=" * 60)
# notebooks/debug_amzn_meta.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import INDEX_NAME
from app.graph.nodes import extract_filters

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

for question, expected_ticker, expected_item in [
    ("What controls and procedures does Amazon describe?", "AMZN", "9A"),
    ("What does Meta's MD&A say about its financial results?", "META", "7"),
]:
    filters = extract_filters(question)
    docs = vector_store.similarity_search(question, k=5, filter=filters if filters else None)
    print(f"Q: {question}")
    print(f"Filters: {filters}  (expected ticker={expected_ticker})\n")
    for d in docs:
        m = d.metadata
        print(f"  ticker={m['ticker']} item={m['item_number']} section={m['section_title'][:40]}")
    print("=" * 60)
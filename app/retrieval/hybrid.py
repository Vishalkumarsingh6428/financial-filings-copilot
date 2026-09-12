from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import INDEX_NAME
from app.retrieval.chunking import load_all_documents
from app.graph.nodes import extract_filters

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

print("Loading all documents for BM25 indexing...")
ALL_DOCS = load_all_documents()
print(f"Loaded {len(ALL_DOCS)} documents")


def matches_filter(doc, filters: dict) -> bool:
    return all(doc.metadata.get(k) == v for k, v in filters.items())


def hybrid_retrieve(query: str, k: int = 5, rrf_k: int = 60):
    filters = extract_filters(query)

    filtered_docs = [d for d in ALL_DOCS if matches_filter(d, filters)] if filters else ALL_DOCS
    if not filtered_docs:
        filtered_docs = ALL_DOCS  # filter too narrow, fall back to everything

    bm25 = BM25Retriever.from_documents(filtered_docs)
    bm25.k = 10
    bm25_results = bm25.invoke(query)

    vector_results = vector_store.similarity_search(query, k=10, filter=filters if filters else None)

    scores = {}
    doc_map = {}
    for rank, doc in enumerate(bm25_results):
        key = doc.page_content
        scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank + 1)
        doc_map[key] = doc
    for rank, doc in enumerate(vector_results):
        key = doc.page_content
        scores[key] = scores.get(key, 0) + 1 / (rrf_k + rank + 1)
        doc_map[key] = doc

    ranked_keys = sorted(scores, key=lambda k_: -scores[k_])
    return [doc_map[k_] for k_ in ranked_keys[:k]]


if __name__ == "__main__":
    results = hybrid_retrieve("What controls and procedures does Amazon describe?")
    for d in results:
        m = d.metadata
        print(f"ticker={m['ticker']} item={m['item_number']} section={m['section_title'][:40]}")
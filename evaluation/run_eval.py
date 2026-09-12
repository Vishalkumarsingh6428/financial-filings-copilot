# evaluation/run_eval.py
import json
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import INDEX_NAME
from app.graph.nodes import extract_filters
from app.retrieval.hybrid import hybrid_retrieve

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)


def load_questions():
    path = Path(__file__).parent / "questions.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_hit(doc, q) -> bool:
    m = doc.metadata
    return (
        m["ticker"] == q["expected_ticker"]
        and m["item_number"] == q["expected_item"]
        and m["filing_type"] == q.get("expected_filing_type", "10-K")
    )


def evaluate_vector_only(k: int = 5):
    questions = load_questions()
    hits = 0
    results = []

    for q in questions:
        filters = extract_filters(q["question"])
        docs = vector_store.similarity_search(q["question"], k=k, filter=filters if filters else None)
        hit = any(is_hit(d, q) for d in docs)
        hits += hit
        results.append({"id": q["id"], "question": q["question"], "hit": hit})

    recall_at_k = hits / len(questions)
    print(f"Vector-only Recall@{k}: {recall_at_k:.2%}  ({hits}/{len(questions)})\n")
    for r in results:
        status = "✓" if r["hit"] else "✗"
        print(f"  {status} {r['id']}: {r['question']}")

    return recall_at_k


def evaluate_hybrid(k: int = 5):
    questions = load_questions()
    hits = 0
    results = []

    for q in questions:
        docs = hybrid_retrieve(q["question"], k=k)
        hit = any(is_hit(d, q) for d in docs)
        hits += hit
        results.append({"id": q["id"], "question": q["question"], "hit": hit})

    recall_at_k = hits / len(questions)
    print(f"Hybrid Recall@{k}: {recall_at_k:.2%}  ({hits}/{len(questions)})\n")
    for r in results:
        status = "✓" if r["hit"] else "✗"
        print(f"  {status} {r['id']}: {r['question']}")

    return recall_at_k

from app.retrieval.rerank import hybrid_rerank_retrieve

def evaluate_reranked(k: int = 5, candidate_k: int = 20):
    questions = load_questions()
    hits = 0
    results = []

    for q in questions:
        docs = hybrid_rerank_retrieve(q["question"], candidate_k=candidate_k, final_k=k)
        hit = any(is_hit(d, q) for d in docs)
        hits += hit
        results.append({"id": q["id"], "question": q["question"], "hit": hit})

    recall_at_k = hits / len(questions)
    print(f"Hybrid+Reranked Recall@{k}: {recall_at_k:.2%}  ({hits}/{len(questions)})\n")
    for r in results:
        status = "✓" if r["hit"] else "✗"
        print(f"  {status} {r['id']}: {r['question']}")

    return recall_at_k


if __name__ == "__main__":
    print("=== Vector-only (Phase 5 baseline) ===")
    evaluate_vector_only()
    print("\n=== Hybrid (BM25 + Vector, RRF) ===")
    evaluate_hybrid()
    print("\n=== Hybrid + Reranked (Phase 7) ===")
    evaluate_reranked()
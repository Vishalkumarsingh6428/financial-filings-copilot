from sentence_transformers import CrossEncoder
from app.retrieval.hybrid import hybrid_retrieve

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
reranker = CrossEncoder(RERANKER_MODEL)


def rerank(query: str, docs: list, top_k: int = 5) -> list:
    if not docs:
        return docs

    pairs = [
        (query, f"[Section: {d.metadata['section_title']}] {d.page_content}")
        for d in docs
    ]
    scores = reranker.predict(pairs)

    scored_docs = list(zip(scores, docs))
    scored_docs.sort(key=lambda x: -x[0])

    return [doc for _, doc in scored_docs[:top_k]]


def hybrid_rerank_retrieve(query: str, candidate_k: int = 20, final_k: int = 5) -> list:
    candidates = hybrid_retrieve(query, k=candidate_k)
    return rerank(query, candidates, top_k=final_k)


if __name__ == "__main__":
    results = hybrid_rerank_retrieve("What is JPMorgan's business overview?")
    for d in results:
        m = d.metadata
        print(f"ticker={m['ticker']} filing={m['filing_type']} item={m['item_number']} section={m['section_title'][:40]}")
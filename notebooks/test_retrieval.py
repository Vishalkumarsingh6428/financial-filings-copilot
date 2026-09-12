# notebooks/test_retrieval.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import INDEX_NAME

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

results = vector_store.similarity_search(
    "What was Apple's revenue?",
    k=3,
    filter={"ticker": "AAPL", "item_number": "8"},
)

for r in results:
    print(r.metadata)
    print(r.page_content[:200])
    print("-" * 40)
# notebooks/debug_filter.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import INDEX_NAME

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

query = "What was Apple's revenue?"

print("--- No filter ---")
r = vector_store.similarity_search(query, k=3)
print(f"{len(r)} results")

print("\n--- ticker=AAPL only ---")
r = vector_store.similarity_search(query, k=3, filter={"ticker": "AAPL"})
print(f"{len(r)} results")

print("\n--- fiscal_year=2023 only ---")
r = vector_store.similarity_search(query, k=3, filter={"fiscal_year": "2023"})
print(f"{len(r)} results")

print("\n--- both combined ---")
r = vector_store.similarity_search(query, k=3, filter={"ticker": "AAPL", "fiscal_year": "2023"})
print(f"{len(r)} results")
for doc in r:
    print(doc.metadata)
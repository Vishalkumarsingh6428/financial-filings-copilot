from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.config import INDEX_NAME
from app.graph.nodes import extract_filters

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

q = "What is JPMorgan's business overview?"
filters = extract_filters(q)
print("Filters:", filters)
docs = vector_store.similarity_search(q, k=5, filter=filters if filters else None)
for d in docs:
    m = d.metadata
    print(f"ticker={m['ticker']} filing={m['filing_type']} item={m['item_number']} section={m['section_title'][:40]}")

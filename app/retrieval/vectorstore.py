from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from app.config import PINECONE_API_KEY, INDEX_NAME
from app.retrieval.chunking import load_all_documents

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def get_or_create_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"Created index: {INDEX_NAME} (dim={EMBEDDING_DIM})")
    else:
        print(f"Using existing index: {INDEX_NAME}")


def upsert_all_documents(batch_size: int = 200):
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)

    docs = load_all_documents()
    print(f"Upserting {len(docs)} chunks in batches of {batch_size}...")

    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        vector_store.add_documents(batch)
        print(f"  {min(i + batch_size, len(docs))}/{len(docs)} upserted")

    print("Done.")


if __name__ == "__main__":
    get_or_create_index()
    upsert_all_documents()
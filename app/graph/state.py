from typing import TypedDict, Optional
from langchain_core.documents import Document


class ChatState(TypedDict):
    question: str                          # original user question
    standalone_question: Optional[str]     # question rewritten using chat history (Phase 4b)
    retrieved_docs: list[Document]         # chunks pulled from Pinecone
    docs_relevant: Optional[bool]          # grade_docs verdict
    retry_count: int                       # bounded-loop counter, prevents infinite retries
    answer: Optional[str]                  # final generated answer
    citations: list[dict]                  # source metadata for the answer
    verification: Optional[dict]  
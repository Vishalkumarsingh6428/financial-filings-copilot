from fastapi import FastAPI
from pydantic import BaseModel
from app.graph.build import build_graph
from app.graph.state import ChatState
from app.config import TICKERS

app = FastAPI(title="Financial Filings Copilot API")
graph = build_graph()


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    verification: dict
    retries_used: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/companies")
def companies():
    return {"tickers": TICKERS}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    state: ChatState = {
        "question": request.question,
        "standalone_question": None,
        "retrieved_docs": [],
        "docs_relevant": None,
        "retry_count": 0,
        "answer": None,
        "citations": [],
        "verification": None,
    }
    result = graph.invoke(state)
    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        verification=result["verification"],
        retries_used=result["retry_count"],
    )
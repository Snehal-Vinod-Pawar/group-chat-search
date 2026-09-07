"""
FastAPI application.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Support both `python main.py` (from backend/) and
# `uvicorn backend.main:app` (from project root).
try:
    from .db import get_client, get_messages_collection, search_with_context
    from .query_parser import parse_query
except ImportError:
    from db import get_client, get_messages_collection, search_with_context
    from query_parser import parse_query

app = FastAPI(
    title="Search a Group Chat Properly",
    description=(
        "Semantic search over a group chat export. "
        "Supports semantic, attributed, and temporal queries."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    ok: bool
    message: str
    mongodb_connected: bool


class AskRequest(BaseModel):
    query: str
    top_k: int = 5


@app.get("/api/health", response_model=HealthResponse)
def health():
    """Health-check endpoint."""
    try:
        get_client().admin.command("ping")
        mongo_ok = True
    except Exception:
        mongo_ok = False

    return HealthResponse(
        ok=True,
        message="Backend is running",
        mongodb_connected=mongo_ok,
    )


@app.get("/api/stats")
def stats():
    """Basic corpus stats."""
    try:
        coll = get_messages_collection()
        count = coll.count_documents({})
        participants = sorted(coll.distinct("sender"))
        first = coll.find_one(sort=[("timestamp", 1)])
        last = coll.find_one(sort=[("timestamp", -1)])
        date_range = [first["timestamp"], last["timestamp"]] if first else None
    except Exception:
        count, participants, date_range = 0, [], None

    return {
        "total_messages": count,
        "participants": participants,
        "date_range": date_range,
    }


@app.post("/ask")
def ask(request: AskRequest):
    """Full search pipeline: parse -> filters -> vector search -> context."""
    query = (request.query or "").strip()
    if not query:
        raise HTTPException(status_code=422, detail="Query must not be empty")
    if request.top_k < 1 or request.top_k > 25:
        raise HTTPException(status_code=422, detail="top_k must be between 1 and 25")

    parsed = parse_query(query)
    try:
        results = search_with_context(query, top_k=request.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}")

    return {
        "query": query,
        "filters": {
            "sender": parsed["sender"],
            "date_range": ([parsed["date_range"][0].isoformat(),
                            parsed["date_range"][1].isoformat()]
                           if parsed["date_range"] else None),
            "clean_query": parsed["clean_query"],
        },
        "total_results": len(results),
        "results": results,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

"""
Database connection module.
Provides a singleton MongoDB client and database handle.
The embedding model is also initialised once and reused.
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from sentence_transformers import SentenceTransformer
import numpy as np

try:
    from .config import config
except ImportError:
    from config import config

_client: MongoClient | None = None
_db: Database | None = None
_model: SentenceTransformer | None = None


def get_client() -> MongoClient:
    """Return a singleton MongoClient instance."""
    global _client
    if _client is None:
        _client = MongoClient(config.MONGODB_URI)
    return _client


def get_db() -> Database:
    """Return the configured MongoDB database."""
    global _db
    if _db is None:
        _db = get_client()[config.MONGODB_DATABASE]
    return _db


def get_messages_collection() -> Collection:
    """Return the messages collection."""
    return get_db()["messages"]


def get_model() -> SentenceTransformer:
    """Return the singleton SentenceTransformer embedding model.

    Per the project guidelines the model is loaded only once and reused
    across all requests — it is never reloaded per query.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model


def encode_query(text: str) -> np.ndarray:
    """Encode a query string into a normalised embedding vector (with query: prefix)."""
    model = get_model()
    embedding = model.encode("query: " + text, normalize_embeddings=True)
    return embedding.astype(np.float32)


def vector_search(query_text: str, top_k: int = 10, sender: str | None = None,
                  date_range: tuple | None = None) -> list[dict]:
    """Run MongoDB Vector Search with pre-filters, then suppress duplicate texts.

    Over-fetches candidates so that after keeping only the best-scoring
    occurrence of each distinct text, top_k unique results remain.
    """
    coll = get_messages_collection()
    embedding = encode_query(query_text)

    pre_filter = {}
    if sender:
        pre_filter["sender"] = sender
    if date_range:
        start, end = date_range
        pre_filter["timestamp"] = {
            "$gte": start.isoformat(),
            "$lte": end.isoformat(),
        }

    fetch_limit = top_k * 10
    stage = {
        "index": "vector_index",
        "path": "embedding",
        "queryVector": embedding.tolist(),
        "numCandidates": max(fetch_limit * 2, 200),
        "limit": fetch_limit,
    }
    if pre_filter:
        stage["filter"] = pre_filter

    pipeline = [
        {"$vectorSearch": stage},
        {
            "$project": {
                "_id": 0,
                "message_id": 1,
                "sender": 1,
                "timestamp": 1,
                "text": 1,
                "month": 1,
                "thread_id": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    candidates = list(coll.aggregate(pipeline))

    seen_texts = set()
    unique = []
    for c in candidates:
        key = " ".join(c["text"].lower().split())
        if key in seen_texts:
            continue
        seen_texts.add(key)
        unique.append(c)
        if len(unique) == top_k:
            break
    return unique


def get_messages_by_ids(ids: list[int]) -> dict[int, dict]:
    coll = get_messages_collection()
    proj = {"_id": 0, "message_id": 1, "sender": 1, "timestamp": 1,
            "text": 1, "month": 1, "thread_id": 1}
    return {m["message_id"]: m for m in coll.find({"message_id": {"$in": ids}}, proj)}




def expand_context(matches: list[dict], radius: int = 3) -> list[dict]:
    """Attach up to `radius` messages before/after each match (same thread preferred).

    Context windows are deduplicated across matches: a message already used as
    context for an earlier result is not repeated for later results.
    """
    all_ids = set()
    for m in matches:
        mid = m["message_id"]
        all_ids.update(range(mid - radius, mid + radius + 1))
    fetched = get_messages_by_ids(sorted(all_ids))

    used_context_ids = {m["message_id"] for m in matches}
    results = []
    for m in matches:
        mid, thread = m["message_id"], m["thread_id"]
        same_thread, other = [], []
        for i in range(mid - radius, mid + radius + 1):
            if i == mid or i not in fetched or i in used_context_ids:
                continue
            (same_thread if fetched[i]["thread_id"] == thread else other).append(fetched[i])
        context = sorted(same_thread, key=lambda x: x["message_id"])[: 2 * radius] or \
                  sorted(other, key=lambda x: x["message_id"])[: 2 * radius]
        for c in context:
            c["is_matched"] = False
            used_context_ids.add(c["message_id"])
        result = {k: m[k] for k in ("message_id", "sender", "timestamp", "text", "thread_id")}
        result["score"] = m["score"]
        result["is_matched"] = True
        result["context"] = sorted(context + [{**m, "is_matched": True}],
                                   key=lambda x: x["message_id"])
        results.append(result)
    return results


def search_with_context(query_text: str, top_k: int = 10, radius: int = 3) -> list[dict]:
    try:
        from .query_parser import parse_query
    except ImportError:
        from query_parser import parse_query
    parsed = parse_query(query_text)
    matches = vector_search(parsed["clean_query"], top_k=top_k,
                            sender=parsed["sender"], date_range=parsed["date_range"])
    return expand_context(matches, radius=radius)


def search(query_text: str, top_k: int = 10) -> list[dict]:
    """Parse sender/temporal filters deterministically, then run filtered vector search."""
    try:
        from .query_parser import parse_query
    except ImportError:
        from query_parser import parse_query
    parsed = parse_query(query_text)
    return vector_search(parsed["clean_query"], top_k=top_k,
                         sender=parsed["sender"], date_range=parsed["date_range"])
#!/usr/bin/env python
"""
Build embeddings for all messages in MongoDB using intfloat/multilingual-e5-small.
Stores the 384-dim normalized embedding in each message document.
"""

import os
import numpy as np
from pymongo import MongoClient
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"
BATCH_SIZE = 128


def main():
    root = os.path.join(os.path.dirname(__file__), "..")
    load_dotenv(os.path.join(root, ".env"))
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DATABASE", "group_chat_search")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    messages = list(db.messages.find({}, {"_id": 1, "text": 1}).sort("message_id", 1))
    print(f"Loaded {len(messages)} messages from MongoDB")

    model = SentenceTransformer(MODEL_NAME)
    texts = ["passage: " + m["text"] for m in messages]
    print("Encoding...")
    embeddings = model.encode(texts, batch_size=BATCH_SIZE, normalize_embeddings=True,
                              show_progress_bar=True)

    from pymongo import UpdateOne
    ops = [UpdateOne({"_id": m["_id"]}, {"$set": {"embedding": emb.tolist()}})
           for m, emb in zip(messages, embeddings)]
    result = db.messages.bulk_write(ops)
    print(f"Updated {result.modified_count} documents")

    # Verification
    total = db.messages.count_documents({})
    with_emb = db.messages.count_documents({"embedding": {"$exists": True, "$ne": None}})
    sample = db.messages.find_one({"embedding": {"$exists": True}}, {"embedding": 1})
    dim = len(sample["embedding"]) if sample else 0
    norms = [np.linalg.norm(m["embedding"])
             for m in db.messages.find({"embedding": {"$exists": True}}, {"embedding": 1}).limit(100)]

    print("\n=== VERIFICATION ===")
    print(f"  total messages:           {total}")
    print(f"  messages with embedding:  {with_emb}")
    print(f"  missing embeddings:       {total - with_emb}")
    print(f"  embedding dimension:      {dim}")
    print(f"  sample norms (min/max):   {min(norms):.6f} / {max(norms):.6f}")
    ok = total == with_emb and dim == 384 and total > 0
    print(f"  => {'ALL CHECKS PASS' if ok else 'CHECKS FAILED'}")
    client.close()


if __name__ == "__main__":
    main()

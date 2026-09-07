#!/usr/bin/env python
"""Validate data/benchmark.json against the problem statement requirements."""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.db import get_messages_collection

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "am", "do", "does",
    "did", "what", "when", "where", "who", "which", "why", "how", "kya", "ka",
    "ke", "ki", "ko", "kab", "kaha", "kahan", "kaise", "hai", "hain", "tha", "thi",
    "me", "mein", "in", "on", "at", "of", "for", "to", "and", "or", "about",
    "over", "there", "here", "we", "us", "our", "i", "you", "your", "it", "its",
    "this", "that", "these", "those", "any", "some", "ne", "se", "say", "said",
    "tell", "ask", "asked", "pucha", "karo", "karna", "hoga", "rahe", "kaun",
    "kisne", "kisi", "paas", "liye", "ya", "na", "no", "yes", "2024", "month",
    "week", "year", "january", "february", "march", "april", "may", "june",
    "last", "before", "after", "between",
}

DECISION_THREADS = {"thread_manali_trip", "thread_house_party", "thread_subscription"}


def meaningful_words(text: str) -> set:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def main():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark.json")
    with open(path, encoding="utf-8") as f:
        queries = json.load(f)

    coll = get_messages_collection()
    checks = []

    # 1. exactly 40 queries
    checks.append(("Exactly 40 queries", len(queries) == 40, f"found {len(queries)}"))

    # unique ids, one correct answer per query
    ids = [q["id"] for q in queries]
    checks.append(("Unique query ids", len(ids) == len(set(ids)), ""))
    checks.append(("Every query has exactly one correct answer",
                   all(isinstance(q.get("correct_answer_message_id"), int) for q in queries), ""))

    # 2. every answer id exists in MongoDB
    missing = []
    for q in queries:
        if coll.find_one({"message_id": q["correct_answer_message_id"]}) is None:
            missing.append(q["id"])
    checks.append(("All answer message_ids exist in MongoDB", not missing, f"missing: {missing}"))

    # 3. (covered above) one marked answer per query

    # 4. zero-overlap queries
    zero_overlap = []
    for q in queries:
        msg = coll.find_one({"message_id": q["correct_answer_message_id"]}, {"text": 1})
        overlap = meaningful_words(q["query"]) & meaningful_words(msg["text"])
        if not overlap:
            zero_overlap.append(q["id"])
    checks.append(("At least 8 zero-overlap queries",
                   len(zero_overlap) >= 8,
                   f"count={len(zero_overlap)} ids={zero_overlap}"))

    # 5. all three decision threads represented
    threads = {q["expected_thread_id"] for q in queries}
    missing_threads = DECISION_THREADS - threads
    checks.append(("All 3 decision threads represented",
                   not missing_threads,
                   f"threads={sorted(threads)} missing={sorted(missing_threads)}"))

    # 6. sender / temporal filter cases
    types = {}
    for q in queries:
        types[q["query_type"]] = types.get(q["query_type"], 0) + 1
    checks.append(("Semantic queries present", types.get("semantic", 0) > 0,
                   f"semantic={types.get('semantic', 0)}"))
    checks.append(("Attributed (sender) queries present", types.get("attributed", 0) > 0,
                   f"attributed={types.get('attributed', 0)}"))
    checks.append(("Temporal queries present", types.get("temporal", 0) > 0,
                   f"temporal={types.get('temporal', 0)}"))
    checks.append(("Sender+temporal combined queries present", types.get("combined", 0) > 0,
                   f"combined={types.get('combined', 0)}"))

    ok = True
    print("=== BENCHMARK VALIDATION ===")
    for name, passed, detail in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))
        ok &= passed

    print("\nQuery type distribution:", types)
    print("\n" + ("ALL BENCHMARK CHECKS PASS" if ok else "SOME CHECKS FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

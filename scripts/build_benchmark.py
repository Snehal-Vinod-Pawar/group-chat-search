#!/usr/bin/env python
"""Build data/benchmark.json: 40 queries with verified correct answer message IDs.

Every answer ID is verified against MongoDB and every zero-overlap claim is
recomputed before the file is written.
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.db import get_messages_collection

BENCHMARK = [
    # --- semantic, no filters ---
    ("when was the destination finally confirmed?", 3573, "semantic", {"zero_overlap": True, "thread": "manali"}),
    ("what was the final itinerary for the trip?", 3529, "semantic", {"zero_overlap": True, "thread": "manali"}),
    ("where is the celebration happening and when was it locked?", 2115, "semantic", {"zero_overlap": True, "thread": "party"}),
    ("party ke liye kharcha kitna decide hua?", 2063, "semantic", {"zero_overlap": True, "hinglish": True, "thread": "party"}),
    ("which apps are we sharing and what is the per-head cost?", 2748, "semantic", {"zero_overlap": True, "thread": "subscription"}),
    ("how are we getting there? options kya hain?", 3322, "semantic", {"zero_overlap": True, "hinglish": True, "thread": "manali"}),
    ("accommodation sorted hai kya?", 3484, "semantic", {"zero_overlap": True, "hinglish": True, "thread": "manali"}),
    ("who came up with the celebration idea?", 1519, "semantic", {"zero_overlap": True, "thread": "party"}),
    ("did anyone mention the weather over there?", 2976, "semantic", {"thread": "manali"}),
    ("results kab aa rahe hain?", 46, "semantic", {"hinglish": True}),
    ("koi movie recommend karega weekend ke liye?", 13, "semantic", {"hinglish": True}),
    ("notes kisi ke paas hain kya?", 18, "semantic", {"hinglish": True}),
    ("who should get the plan money and how was it worked out?", 2397, "semantic", {"zero_overlap": True, "thread": "subscription"}),
    ("was the hall ticket rule made clear to everyone?", 162, "semantic", {"zero_overlap": True}),
    # --- attributed (sender filter) ---
    ("what did Vikram say about where to stay?", 3453, "attributed", {"zero_overlap": True, "sender": "Vikram", "thread": "manali"}),
    ("what did Vikram say about transport costs?", 3380, "attributed", {"zero_overlap": True, "sender": "Vikram", "thread": "manali"}),
    ("what did Rohan say about the trip budget?", 3120, "attributed", {"zero_overlap": True, "sender": "Rohan", "thread": "manali"}),
    ("what did Amit suggest to keep costs low?", 3099, "attributed", {"zero_overlap": True, "sender": "Amit", "thread": "manali"}),
    ("who offered their place for the party?", 1569, "attributed", {"zero_overlap": True, "sender": "Sneha", "thread": "party"}),
    ("what did Anjali offer for the party?", 1545, "attributed", {"zero_overlap": True, "sender": "Anjali", "thread": "party"}),
    ("what did Karan say about the food?", 2034, "attributed", {"zero_overlap": True, "sender": "Karan", "thread": "party"}),
    ("what did Meera think about the whole plan?", 1520, "attributed", {"zero_overlap": True, "sender": "Meera", "thread": "party"}),
    ("Amit ne sound system ke baare mein kya pucha?", 1573, "attributed", {"hinglish": True, "sender": "Amit", "thread": "party"}),

    # --- temporal ---
    ("what was shared in January 2024 about scholarships?", 25, "temporal", {}),
    ("any reminders about exam entry in February?", 795, "temporal", {}),
    ("what happened in the group in March 2024?", 1519, "temporal", {"thread": "party"}),
    ("what did we discuss last month about streaming?", 2650, "temporal", {"zero_overlap": True, "thread": "subscription"}),
    ("any pending payments this month?", 3599, "temporal", {"zero_overlap": True, "thread": "manali"}),
    ("where are we staying? share the location this month", 3670, "temporal", {"zero_overlap": True, "thread": "manali"}),
    ("what did we discuss before April about the party date?", 1668, "temporal", {"thread": "party"}),
    ("what was the mood about celebrating between March 10 and March 15?", 1539, "temporal", {"zero_overlap": True, "thread": "party"}),

    # --- sender + temporal combined ---
    ("what did Priya say about streaming choices in May 2024?", 2650, "combined", {"zero_overlap": True, "sender": "Priya", "thread": "subscription"}),
    ("what did Priya say about the money split in April 2024?", 2063, "combined", {"zero_overlap": True, "sender": "Priya", "thread": "party"}),
    ("what did Anjali favour for the journey in May 2024?", 3355, "combined", {"zero_overlap": True, "sender": "Anjali", "thread": "manali"}),
    ("what did Karan say about Netflix in April 2024?", 2439, "combined", {"sender": "Karan", "thread": "subscription"}),
    ("Sneha ne Manali ke baare mein kya kaha May 2024 mein?", 2976, "combined", {"hinglish": True, "sender": "Sneha", "thread": "manali"}),

    # --- short / typo queries ---
    ("party kab?", 2122, "semantic", {"short": True, "hinglish": True, "zero_overlap": True, "thread": "party"}),
    ("budjet ka final kya tha?", 2748, "semantic", {"typo": True, "hinglish": True, "thread": "subscription"}),
    ("airbnb walo ne otp bheja hoga, check karo", 3570, "semantic", {"hinglish": True, "thread": "manali"}),
    ("confrim ho gaya sab?", 2117, "semantic", {"typo": True, "hinglish": True, "thread": "party"}),
]

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "am", "do", "does",
    "did", "what", "when", "where", "who", "which", "why", "how", "kya", "ka",
    "ke", "ki", "ko", "kab", "kaha", "kahan", "kaise", "hai", "hain", "tha", "thi",
    "me", "mein", "in", "on", "at", "of", "for", "to", "and", "or", "about",
    "over", "there", "here", "we", "us", "our", "i", "you", "your", "it", "its",
    "this", "that", "these", "those", "any", "some", "ne", "se", "say", "said",
    "tell", "ask", "asked", "pucha", "karo", "karna", "hoga", "rahe", "kaun",
    "kisne", "kisi", "paas", "liye", "was", "ka", "ya", "na", "no", "yes",
    "2024", "month", "week", "year", "january", "february", "march", "april",
    "may", "june", "last", "before", "after", "between",
}


def meaningful_words(text: str) -> set:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def main():
    coll = get_messages_collection()
    out = []
    zero_overlap_count = 0

    for qid, (query, ans_id, qtype, flags) in enumerate(BENCHMARK, start=1):
        msg = coll.find_one({"message_id": ans_id},
                            {"_id": 0, "message_id": 1, "sender": 1, "timestamp": 1,
                             "text": 1, "thread_id": 1})
        if msg is None:
            print(f"FAIL: query {qid} answer id {ans_id} not found in MongoDB")
            sys.exit(1)

        expected_thread = flags.get("thread")
        if expected_thread:
            expected_thread = {"manali": "thread_manali_trip",
                               "party": "thread_house_party",
                               "subscription": "thread_subscription"}[expected_thread]
        if expected_thread and msg["thread_id"] != expected_thread:
            print(f"FAIL: query {qid!r} answer #{ans_id} in thread "
                  f"{msg['thread_id']}, expected {expected_thread}")
            sys.exit(1)

        overlap = meaningful_words(query) & meaningful_words(msg["text"])
        if flags.get("zero_overlap") and overlap:
            print(f"FAIL: query {qid!r} claimed zero-overlap but shares {overlap} "
                  f"with answer #{ans_id}: {msg['text'][:60]!r}")
            sys.exit(1)
        if not overlap:
            zero_overlap_count += 1

        out.append({
            "id": qid,
            "query": query,
            "query_type": qtype,
            "correct_answer_message_id": ans_id,
            "expected_thread_id": msg["thread_id"],
            "answer_text": msg["text"],
            "answer_sender": msg["sender"],
            "answer_timestamp": msg["timestamp"],
            "flags": flags,
        })

    total = len(out)
    threads, types = {}, {}
    for item in out:
        threads[item["expected_thread_id"]] = threads.get(item["expected_thread_id"], 0) + 1
        types[item["query_type"]] = types.get(item["query_type"], 0) + 1
    print(f"Queries: {total} (expected 40)")
    print(f"Zero-overlap queries: {zero_overlap_count} (minimum required: 8)")
    print("Threads:", threads)
    print("Types:", types)

    if total != 40:
        print("FAIL: benchmark must contain exactly 40 queries")
        sys.exit(1)
    if zero_overlap_count < 8:
        print("FAIL: fewer than 8 zero-overlap queries")
        sys.exit(1)

    path = os.path.join(os.path.dirname(__file__), "..", "data", "benchmark.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(out)} queries -> {os.path.abspath(path)}")


if __name__ == "__main__":
    main()

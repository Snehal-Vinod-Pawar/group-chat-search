#!/usr/bin/env python
"""Run all benchmark queries against the live /ask API and compute accuracy."""

import json
import os
import sys
import urllib.request
import urllib.error

BASE = os.path.join(os.path.dirname(__file__), "..")
API = os.environ.get("ASK_URL", "http://localhost:8000/ask")


def ask(query, top_k=10):
    data = json.dumps({"query": query, "top_k": top_k}).encode()
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()[:200]}
    except Exception as e:
        return {"error": "connection", "detail": str(e)}


def main():
    with open(os.path.join(BASE, "data", "benchmark.json"), encoding="utf-8") as f:
        queries = json.load(f)

    detail = []
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    zo_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    by_type = {}
    filter_ok = 0
    filter_total = 0
    context_ok = 0

    for q in queries:
        resp = ask(q["query"])
        results = resp.get("results", [])
        got_ids = [r["message_id"] for r in results]
        expected = q["correct_answer_message_id"]
        flags = q.get("flags", {})

        k_hits = {k: expected in got_ids[:k] for k in (1, 3, 5, 10)}
        for k in hits:
            if k_hits[k]:
                hits[k] += 1
                if flags.get("zero_overlap"):
                    zo_hits[k] += 1

        # verify filters were applied by the API
        parsed = resp.get("filters", {})
        filters_applied = True
        if flags.get("sender"):
            filter_total += 1
            if parsed.get("sender") == flags["sender"] and all(
                r["sender"] == flags["sender"] for r in results
            ):
                filter_ok += 1
            else:
                filters_applied = False
        if q["query_type"] in ("temporal", "combined") and results:
            filter_total += 1
            dr = parsed.get("date_range")
            if dr and all(dr[0] <= r["timestamp"] <= dr[1] for r in results):
                filter_ok += 1
            else:
                filters_applied = False

        # verify context expansion invariants
        ctx_valid = bool(results) and all(
            any(c.get("is_matched") for c in r["context"])
            and [c["message_id"] for c in r["context"]] == sorted(c["message_id"] for c in r["context"])
            for r in results
        )
        if ctx_valid:
            context_ok += 1

        t = q.get("query_type", "unknown")
        agg = by_type.setdefault(t, {"total": 0, "top1": 0, "top3": 0, "top5": 0, "top10": 0})
        agg["total"] += 1
        for k in (1, 3, 5, 10):
            if k_hits[k]:
                agg[f"top{k}"] += 1

        detail.append({
            "query_id": q.get("id"),
            "query": q["query"],
            "type": t,
            "zero_overlap": flags.get("zero_overlap", False),
            "expected_message_id": expected,
            "expected_rank": (got_ids.index(expected) + 1) if expected in got_ids else None,
            "top1": k_hits[1], "top3": k_hits[3], "top5": k_hits[5], "top10": k_hits[10],
            "filters_applied": filters_applied,
            "context_valid": ctx_valid,
            "api_error": resp.get("error"),
        })
        print(f"[{'TOP1' if k_hits[1] else ('TOP' + str(detail[-1]['expected_rank']) if detail[-1]['expected_rank'] else 'MISS')}] {q['query'][:70]}")

    n = len(queries)
    nzo = sum(1 for q in queries if q.get("flags", {}).get("zero_overlap"))
    summary = {
        "total_queries": n,
        "zero_overlap_queries": nzo,
        "accuracy": {f"top{k}": round(hits[k] / n, 4) for k in hits},
        "zero_overlap_accuracy": {f"top{k}": round(zo_hits[k] / nzo, 4) for k in zo_hits},
        "filters_verified": f"{filter_ok}/{filter_total}",
        "context_valid": f"{context_ok}/{n}",
        "by_type": by_type,
    }

    out = {"summary": summary, "results": detail}
    with open(os.path.join(BASE, "data", "benchmark_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("\n=== BENCHMARK SUMMARY ===")
    print(f"total queries:        {n}")
    for k in (1, 3, 5, 10):
        print(f"top-{k:<2} accuracy:      {hits[k]}/{n} = {hits[k]/n:.1%}")
    print(f"\nzero-overlap ({nzo} queries):")
    for k in (1, 3, 5, 10):
        print(f"top-{k:<2} accuracy:      {zo_hits[k]}/{nzo} = {zo_hits[k]/nzo:.1%}")
    print(f"\nfilters verified:     {filter_ok}/{filter_total}")
    print(f"context invariants:   {context_ok}/{n}")
    print("\nby type:")
    for t, a in by_type.items():
        print(f"  {t:20s} top1 {a['top1']}/{a['total']}  top3 {a['top3']}/{a['total']}  top5 {a['top5']}/{a['total']}  top10 {a['top10']}/{a['total']}")


if __name__ == "__main__":
    main()

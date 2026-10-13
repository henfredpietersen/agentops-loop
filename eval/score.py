"""FROZEN. S and the gates. The loop may not patch, copy or re-implement this file.

S = 0.30 recall + 0.20 route_accuracy + 0.20 refusal_accuracy + 0.20 span_support + 0.10 acl_compliance
Cache hits count in the denominator but never in a quality numerator.
"""
import statistics

WEIGHTS = {"recall": 0.30, "route_accuracy": 0.20, "refusal_accuracy": 0.20, "span_support": 0.20, "acl_compliance": 0.10}


def metrics(rows: list[dict]) -> dict:
    n = len(rows)
    ans = [r for r in rows if r["answerable"]]
    fresh = lambda r: not r["cache_hit"]
    m = {
        "recall": sum(fresh(r) and r["gold_chunk_id"] in r["retrieved_ids"] for r in ans) / max(1, len(ans)),
        "route_accuracy": sum(fresh(r) and r["route"] == r["gold_route"] for r in rows) / max(1, n),
        "refusal_accuracy": sum(fresh(r) and r["refused"] != r["answerable"] for r in rows) / max(1, n),
        "span_support": sum(fresh(r) and not r["refused"] and r["gold_chunk_id"] in r["cited_ids"]
                            and r["gold_span"].lower() in r["answer"].lower() for r in ans) / max(1, len(ans)),
        "acl_compliance": sum(fresh(r) and not r["leaked"] for r in rows) / max(1, n),
    }
    m["S"] = round(sum(WEIGHTS[k] * m[k] for k in WEIGHTS), 4)
    m["cache_hits"] = sum(1 for r in rows if r["cache_hit"])
    return m


def p95(xs: list[float]) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))] if xs else 0.0


def gates(rows: list[dict], cfg: dict) -> dict:
    med = statistics.median(r["dollars"] for r in rows) if rows else 0.0
    lat = p95([r["latency_ms"] for r in rows])
    g = cfg["gates"]
    return {"median_dollars": med, "p95_latency_ms": round(lat, 2),
            "cost_ok": med <= g["median_dollars_cap"], "latency_ok": lat <= g["p95_latency_ms_cap"],
            "ok": med <= g["median_dollars_cap"] and lat <= g["p95_latency_ms_cap"]}

# Perf measurement discipline: cold/warm split + per-stage breakdown before tuning params

**Symptom**: search P50 = 30ms conclusion "speed not the bottleneck"; user real-world experienced 9-40s; 38s cold query couldn't be attributed to any stage.

**Cause**: warm P50 hidden by Redis cache; no per-stage timing = blind parameter tuning.

**Fix**:
- Always measure cold query (cache miss) separately from warm
- Add per-stage timing log BEFORE parameter tuning (prefill / fetch / rerank / dedup)
- Look for fetch-excess first: e.g. fetch 800 vectors but only feed 10 to rerank → 14s→0.8s by capping earlier
- Reduce candidate COUNT not per-candidate LENGTH: cutting CPU prefill by halving token count only saves ~20%; cutting candidates 4x saves ~75%

## Sources

- `work-note:docs/work-note/2026-09-06-search-cold-query-iter3.md`
- `commit:7a16695c`

## Frequency

2

## Triggers

latency, cold query, cache miss, benchmark, qdrant, prefill, fetch excess, stage timing

## Related hard constraints

#6 (commit 前全绿 — but green requires real measurement)
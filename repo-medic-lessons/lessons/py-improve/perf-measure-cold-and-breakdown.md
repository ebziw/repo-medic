# Performance measurement: cold/warm split + per-stage breakdown before tuning parameters

**Principle**: cache hides real performance. Aggregate P50/P99 numbers without stage breakdown blind you to where time goes. Always measure cold (cache-miss) separately and add per-stage timing BEFORE attempting parameter tuning.

**Symptom (any of)**:
- "P50 = 30ms, speed not the bottleneck" but real users see 9-40s
- 38s cold query, no idea which stage it spent
- Parameter tuning sessions that don't measurably improve end-to-end latency

**Fix**:
- Measure cold query (cache miss) separately from warm; report both
- Add per-stage timing log (prefill / fetch / rerank / dedup / render) BEFORE parameter tuning
- Look for fetch-excess first: fetching 800 vectors when only 10 feed rerank is the cheap win (14s→0.8s by capping earlier)
- Reduce candidate COUNT before per-candidate LENGTH: halving tokens saves ~20%, quartering candidates saves ~75%
- Don't trust SDK/sample benchmarks — use prod-shape inputs

## Sources

- `work-note:docs/work-note/2026-09-06-search-cold-query-iter3.md`
- `commit:7a16695c`

## Frequency

High (every latency-sensitive system eventually hits this)

## Triggers

latency, cold query, cache miss, benchmark, qdrant, prefill, fetch excess, stage timing, P50 misleading

## Related hard constraints

#6 (commit 前全绿 — green requires real measurement, not synthetic)
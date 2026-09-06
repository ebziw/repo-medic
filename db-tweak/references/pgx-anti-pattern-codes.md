# PGX_* Anti-pattern Codes (borrowed from `pg-explain`)

Stable, greppable codes for every EXPLAIN-plan anti-pattern we detect. Each code is the diagnostic id + config key, used in scripts and reports. Pattern: borrow the codes wholesale from `pg-explain` so any agent familiar with that tool sees the same vocabulary.

## Rule catalogue

| Code | Flags when... | Severity |
|---|---|---|
| `PGX_CARTESIAN_PRODUCT` | Nested loop has no join condition (accidental cross join) | error |
| `PGX_SEQ_SCAN_LARGE` | Sequential scan reads a large table that an index could narrow | warn |
| `PGX_NESTED_LOOP_LARGE_OUTER` | Nested loop driven by a large outer side (re-probes inner repeatedly) | warn |
| `PGX_HIGH_FILTER_DISCARD` | Node reads many rows then discards most via filter | info |
| `PGX_LIMIT_LARGE_OFFSET` | `LIMIT` discards a large generated prefix (OFFSET pagination — use keyset) | warn |
| `PGX_SORT_SPILL_DISK` | Sort spilled to disk instead of staying in `work_mem` | warn |
| `PGX_HASH_SPILL_DISK` | Hash join's build side spilled to disk (multiple batches) | warn |
| `PGX_MEMOIZE_EVICTIONS` | Memoize cache thrashing (evictions outpace hits, or entries overflow `work_mem`) | warn |
| `PGX_CORRELATED_SUBPLAN` | Correlated subplan re-executed once per outer row | warn |
| `PGX_ROW_MISESTIMATE` | Estimated vs actual row counts diverge sharply (stale/missing stats) | warn |
| `PGX_FILTER_COULD_BE_INDEX_COND` | Residual filter could be pushed into an index condition | info |
| `PGX_COULD_BE_INDEX_ONLY` | Index scan could become index-only with a covering index | info |
| `PGX_INDEX_ONLY_HEAP_FETCHES` | Index-only scan still did many heap fetches (visibility map cold) | info |
| `PGX_BITMAP_LOSSY` | Bitmap heap scan went lossy (rechecks whole pages; `work_mem` too small) | warn |
| `PGX_WORKERS_NOT_LAUNCHED` | Parallel workers planned but not all launched | info |
| `PGX_LOW_CACHE_HIT` | Shared-buffer cache hit ratio low (heavy disk reads) | warn |
| `PGX_SIGNIFICANT_JIT` | JIT compilation consumed significant share of execution time | info |
| `PGX_TRIGGER_TIME` | Triggers consumed significant share of execution time | info |
| `PGX_STALE_STATISTICS` | Tables in plan never analyzed or churned past 20% since last ANALYZE | warn |

## Usage in repo-medic

Every EXPLAIN diagnostic (Phase 2 of `db-tweak`) emits findings with their `PGX_*` code. Reports are greppable:

```bash
grep PGX_ sweep-report.md
# PGX_SEQ_SCAN_LARGE x12 (recommend: index on predicate column)
# PGX_STALE_STATISTICS x3 (recommend: ANALYZE)
```

## Configuration

Tunable thresholds per project via `.pg-explainrc` (or `repo-medic.json`):

```jsonc
{
  "thresholds": {
    "seq_scan_large_rows": 100000,
    "cache_hit_warn_pct": 90
  },
  "rules": {
    "PGX_LOW_CACHE_HIT": { "enabled": false }
  }
}
```

## Sources

- Borrowed verbatim from `losefor/pg-explain` (https://github.com/losefor/pg-explain)
- 19 codes (we added `PGX_STALE_STATISTICS` which was a runtime check in pg-explain, not a plan code — promoted to first-class)

## Why include

- Stable codes make EXPLAIN findings machine-readable across tools
- Agents / scripts / humans all share one vocabulary
- Greppable in any report file or CI log

## Related

- Phase 2 of `db-tweak` (8-pattern sweep)
- `references/db-tuning.md` (full tuning methodology)
- Iron law 1 (evidence first — these codes are the evidence vocabulary)
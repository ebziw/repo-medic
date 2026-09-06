# Failure loop must respect connection budget: per-iter conn × high-frequency loop = pool killer

**Symptom**: feed SQL syntax error → `_read_sites_pg failed` every 5s, each iteration opened new PG connection → 2 min later PG maxed (95/100); all clients rejected "sorry, too many clients".

**Cause**: exception path didn't reuse or rate-limit connections; high-frequency loop (5s) × per-iter ≥1 conn product effect ignored.

**Fix**:
- Long-running loops: DB access via singleton/pool, not per-iter new conn
- Exception path: after N consecutive failures, sleep with backoff (don't hard-hammer every 5s)
- Monitor: `pg_stat_activity` count alert threshold (e.g. >80 = page)
- After ANY SQL change: see L4 (sql-string-concat-no-inline-comments) for EXPLAIN smoke before restart
- After daemon restart: verify actual conn count went DOWN, not just that process is up

## Sources

- `work-note:fetch-unlock.md` — SQL comment pitfall cascade

## Frequency

1 (cascade loss high)

## Triggers

too many clients, connection pool, failure loop, backoff, pg_stat_activity, conn budget, high-frequency retry

## Related hard constraints

#11 (daemon 改动独立验证 — restart 后查连接数)

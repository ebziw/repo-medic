# SQL in Python string concat: never put inline `--` comments in SQL body

**Symptom**: `-- 注释` added to SQL during whitelist fix → feed `_read_sites_pg` syntax error every 5s; each error opened a new PG connection; 2 min later 95/100 connections full; all clients rejected "too many clients".

**Cause**: Python adjacent string concat has no newline; `--` comment swallows rest of physical line including WHERE / closing paren.

**Fix**:
- Inline SQL comments must end with `\n` (or write the comment in Python layer outside the SQL string)
- Safer: zero comments inside SQL string; comment on Python side
- After any SQL change: `EXPLAIN` smoke test against PG before restarting service
- Loop exception handler: never let high-frequency loop open new conn without backoff (see db-tweak L8)

## Sources

- `work-note:fetch-unlock.md` — 二次踩坑 (自己造成, 10 分钟恢复)

## Frequency

1 (cascade impact: PG pool exhaustion)

## Triggers

SQL comment, --, string concat, syntax error loop, EXPLAIN smoke, connection pool

## Related hard constraints

#6 (commit 前全绿)

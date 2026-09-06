# PostgreSQL Tuning Reference

Generic PostgreSQL tuning reference for the `db-tweak` skill. 9 iron laws + 7 phases + 8 patterns framework + tooling stack.

---

## 9 Iron Laws (Hard Constraints)

| # | Iron law | Description |
|---|---|---|
| 1 | **Evidence first** | Before any schema change, run `EXPLAIN ANALYZE` on the current query + review `pg_stat_statements` history. See the baseline before changing anything. |
| 2 | **DDL CONCURRENTLY** | Index creation must use `CREATE INDEX CONCURRENTLY`. Otherwise the table gets locked and production returns 502. |
| 3 | **Triple check before delete** | Before DROP, check: ① still referenced? (`pg_depend` / `pg_constraint`) ② backup exists ③ a RENAME retirement window exists |
| 4 | **Naming regex trap** | Identifiers all lowercase + underscores; avoid double-quoted case sensitivity; avoid PG reserved words (`user`, `order`, `group`) |
| 5 | **statement_timeout 30s** | Set `SET statement_timeout = '30s'` on every session to keep a single query from dragging down the connection pool |
| 6 | **VACUUM FULL needs owner approval** | Default to autovacuum; `VACUUM FULL` locks the table for a duration 8x the table size, **owner approval is mandatory** |
| 7 | **Lock checks + dual clocks** | Always check lock waits over 5s; DB time != business time, cross-timezone reports must carry tz explicitly |
| 8 | **No bare DDL** | All DDL goes through a migration tool (`yoyo-migrations` / `sqlx-migrate` / in-house), never direct `psql -c` |
| 9 | **Rename before delete** | Before DROP COLUMN/TABLE, first `ALTER ... RENAME TO PLAN_DELETE_<original name>` + 1+ weeks of testing + owner review → only then the real DROP |

---

## 7 Phases (major version upgrades or full rewrites)

| Phase | Goal | Artifact |
|---|---|---|
| 1. **Major version upgrade audit** | extension compatibility + deprecated API inventory before PG 12→16 | upgrade-audit.md |
| 2. **Evidence collection** | `pg_stat_statements` top 20 slow queries + table sizes + index bloat | baseline.json |
| 3. **Pattern sweep** | checklist of the 8-pattern checks (see below) | sweep-report.md |
| 4. **Fix** | create indexes / change schema / tune parameters | migration scripts |
| 5. **Verify** | regression tests + EXPLAIN comparison + p95 latency comparison | verify-report.md |
| 6. **Distill** | write work-note to docs/work-note/ + KB sync | work-note.md |
| 7. **Retirement pipeline** | `plan-delete.sh` RENAME → 7-day review → DROP | audit-plan-delete.sh marks Ready to DROP |

---

## 8 Patterns (Anti-patterns to Detect)

| # | Pattern | Detection | Fix |
|---|---|---|---|
| 1 | **TOAST in WHERE** | EXPLAIN shows a TOAST table being fetched externally | rewrite the condition against main-table columns, or build an expression index |
| 2 | **TOAST full-table window** | `pg_stat_user_tables.seq_scan >> idx_scan` on large tables | force index scans / add a hint |
| 3 | **ORDER BY without index** | Sort node in EXPLAIN with no Index | add a btree index matching the ORDER BY order |
| 4 | **OFFSET deep pagination** | `LIMIT 20 OFFSET 100000` | switch to keyset pagination (`WHERE id > last_id`) |
| 5 | **Stale statistics** | `pg_stat_user_tables.n_mod_since_analyze > 1000` | `ANALYZE table_name` or tune autovacuum_analyze_scale_factor |
| 6 | **Implicit cast** | EXPLAIN shows a `Cast` node across types | cast explicitly or make schema types consistent |
| 7 | **SELECT *** | text columns scanned but unused | name columns explicitly; SELECT large text columns separately |
| 8 | **btree bloat** | `pgstatginindex` / `pgstatindex` bloat > 30% | `REINDEX CONCURRENTLY` (PG 12+) |

---

## Tooling Stack

| Tool | Purpose |
|---|---|
| **HypoPG** | hypothetical indexes — `CREATE INDEX ON tbl (col) WHERE ...` without actually creating it, to see whether the planner would use it |
| **pg_stat_monitor** | time-bucketed query statistics (finer-grained than pg_stat_statements) |
| **pgstattuple** | quantify table/index bloat |
| **Postgres MCP** (`crystaldba/postgres-mcp`) | LLM direct PG access, run EXPLAIN + tune indexes |
| **pgcli** | interactive CLI (syntax highlighting + autocomplete) |
| **pgFormatter** | SQL formatting (CI lint) |

---

## Retirement Pipeline (iron law 9 in practice)

```bash
# 1. RENAME (leave application code untouched for now; rename first)
./scripts/plan-delete.sh --column public.users.legacy_field
# Output:
# ALTER TABLE public.users RENAME COLUMN legacy_field TO PLAN_DELETE_legacy_field;
# (recorded to ~/.cache/db-tweak/pending-drops/users.legacy_field.json)

# 2. Monitor 7+ days for any unmigrated references
./scripts/audit-plan-delete.sh
# Lists all pending + DAYS_LEFT + STATUS

# 3. Only after DAYS_LEFT ≤ 0 run the real DROP (owner approval still required)
# Act only when the owner explicitly says "drop"; otherwise retain indefinitely
```

---

## Key Monitoring Metrics

| Metric | Threshold | Tool |
|---|---|---|
| Connection usage | < 80% | `pg_stat_activity` count / max_connections |
| Cache hit rate | > 99% | `pg_stat_database` blks_hit / (blks_hit + blks_read) |
| Replication lag | < 1s | `pg_stat_replication` replay_lag |
| Long transactions | > 5min alert | `pg_stat_activity.state = 'active' AND xact_start < now() - interval '5 min'` |
| Deadlocks | any occurrence | `pg_stat_database.deadlocks` delta > 0 |
| Table bloat | bloat > 30% | `pgstattuple` |

---

## Related

- `py-improve` — code review of the Python callers behind slow queries
- `doc-reorg` — schema doc sync (schema change → env.md / deploy.md)
- `repo-medic` (meta) — routing entry point

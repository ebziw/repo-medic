# Risk-Tier + Metadata-Only Simulation (borrowed from Valk + Azimutt)

When proposing a DB change, classify by **risk tier** and validate via **metadata-only simulation** before touching production. Combine Valk's testcontainer isolation principle with Azimutt's severity scoring.

## Risk tiers (every recommendation must declare one)

| Tier | Operations | Approval needed | Rollback window |
|---|---|---|---|
| **T1 read** | any `SELECT` from `pg_stat_*` / `pg_catalog` | none (auto) | n/a |
| **T2 reversible-write** | `create_index` (CONCURRENTLY), `update_setting`, `vacuum` | ops sign-off in PR | governed undo (see `governed-undo-protocol.md`) |
| **T3 destructive** | `drop_column`, `drop_table`, `drop_index`, `alter type` | owner sign-off + 7-day wait (per `plan-delete.sh`) | RENAME window / backup |
| **T4 irreversible** | `terminate_backend`, `cancel_query`, schema version down-migration | owner sign-off + incident declaration | no-undo; declare in PR |

Each PR that touches DB must declare all proposed changes' tier in its description.

## Metadata-only simulation (Valk principle)

> **Test your fix in an isolated instance. Don't read production row data — only metadata.**

Workflow:
1. `pg_dump --schema-only` from prod (no row data) → spin up local PG via `docker run`
2. Apply proposed change in local instance
3. `EXPLAIN (ANALYZE, BUFFERS)` the same workload
4. Compare before/after: total time, buffer hits, plan shape
5. Report stat-sig improvement (or no improvement) before merging to prod

This catches: mis-estimated index impact, plan shape changes, side-effects of `SET` changes.

## Severity scoring (Azimutt principle)

Every finding carries:
- **severity**: critical / warning / info
- **confidence**: 0-1 (e.g. "PGX_SEQ_SCAN_LARGE on 500k-row table with predicate match-rate 0.1% → confidence 0.95")
- **context**: which query / table / index is affected
- **remediation**: copy-pasteable SQL

Aggregate reports rank findings by `severity × confidence` and surface the top 5.

## Sources

- Risk tiers + no-undo declaration: `postgres-aiops` (already cited in `governed-undo-protocol.md`)
- Metadata-only simulation + testcontainer isolation: `valkdb.com`
- Severity + confidence scoring: `Azimutt Inspector`

## Why include

- "Just apply it and see" is the most common DB disaster pattern
- Risk-tier declaration forces explicit cost/benefit thought before merge
- Simulation gives evidence to commit to a change vs leave as-is
- Severity scoring helps triage which finding to act on first

## Related

- `pgx-anti-pattern-codes.md` (use `PGX_*` codes with severity tags)
- `governed-undo-protocol.md` (every T2+ write must emit undo record)
- Iron law 7 (lock checks + dual clocks — run BEFORE simulation)
- `scripts/config_drift.py` (detect prod vs committed config drift)
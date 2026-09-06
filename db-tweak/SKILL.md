---
name: db-tweak
description: "PostgreSQL database tuning — slow query optimization / index design / 9 iron laws / 7 phases / 8 patterns / retirement pipeline (PLAN_DELETE_ rename). Includes plan-delete.sh, audit-plan-delete.sh, config_drift.py. Triggers: PostgreSQL, PG, index, EXPLAIN, VACUUM, slow query, DROP, schema, tuning, plan-delete, migration, database tune, query optimization, bloat"
metadata:
  type: domain
  scope: public
---

# db-tweak — PostgreSQL Tuning

Self-contained skill. Covers PG slow query optimization, indexes, DDL safety, and the retirement pipeline for column/table deletion.

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Baseline (evidence first — iron law 1)

- [ ] **Read** `references/db-tuning.md` in full (9 iron laws + 7 phases + 8 patterns)
- [ ] **Capture top 20 slow queries**: `SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 20;`
- [ ] **Table size + index bloat snapshot**: quantify with `pgstattuple`, save as `baseline-<date>.json`
- [ ] **EXPLAIN ANALYZE** the current slow queries (with the BUFFERS option) and save a before/after comparison baseline
- [ ] 🛑 **GATE**: enter Phase 1 only after the baseline document is on disk (`baseline-<date>.json`)

### Phase 1: 9 iron laws pre-check (run through all of iron laws 1-9)

- [ ] **Iron law 1**: run `EXPLAIN (ANALYZE, BUFFERS)` on every slow query before any change
- [ ] **Iron law 2**: does the upcoming DDL use CONCURRENTLY?
- [ ] **Iron law 3**: all 3 checks done for the DROP candidate — references / backup / RENAME window?
- [ ] **Iron law 4**: identifiers all lowercase with underscores? No PG reserved words?
- [ ] **Iron law 5**: `SET statement_timeout = '30s'` set on every session?
- [ ] **Iron law 6**: about to run VACUUM FULL? owner approved?
- [ ] **Iron law 7**: lock waits currently > 5s? checked `pg_stat_activity`?
- [ ] **Iron law 8**: DDL via migration tool (no bare `psql -c`)?
- [ ] **Iron law 9**: DROP via `plan-delete.sh` instead of a direct DROP?
- [ ] 🛑 **GATE**: any of the 9 unmet = fix before entering Phase 2

### Phase 2: 8-pattern sweep

- [ ] **TOAST in WHERE**: look for external-fetch nodes in EXPLAIN
- [ ] **TOAST full-table window**: on large tables, seq_scan >> idx_scan
- [ ] **ORDER BY without index**: Sort nodes in EXPLAIN
- [ ] **OFFSET deep pagination**: look for `LIMIT N OFFSET > 10000`
- [ ] **Stale statistics**: large `pg_stat_user_tables.n_mod_since_analyze`
- [ ] **Implicit cast**: Cast nodes in EXPLAIN
- [ ] **SELECT ***: grep application code for `SELECT \*` to find candidates
- [ ] **btree bloat**: quantify with `pgstattuple`
- [ ] Emit `sweep-report.md` listing the hits + fix recommendations

### Phase 3: Fix

- [ ] **New indexes**: `CREATE INDEX CONCURRENTLY idx_xxx ON tbl (col) WHERE ...` (iron law 2)
- [ ] **Schema type changes**: via migration tool; prod during a maintenance window (iron law 7)
- [ ] **Eliminate SELECT ***: replace with explicit column names in application code
- [ ] **OFFSET → keyset**: WHERE id > last_id LIMIT N
- [ ] **REINDEX CONCURRENTLY** (PG 12+) for btree bloat > 30%
- [ ] **ANALYZE** for stale statistics
- [ ] 🛑 **GATE**: one commit per fix (hard constraint 2); after each commit, rerun `EXPLAIN ANALYZE` to confirm the improvement

### Phase 4: Verify

- [ ] **Regression tests**: application-level pytest/e2e all green
- [ ] **EXPLAIN comparison**: Phase 0 baseline vs now — p95 latency should drop
- [ ] **buffer hit rate**: Phase 0 vs now — should be ≥ 99%
- [ ] **replication lag**: `pg_stat_replication.replay_lag < 1s` (iron law 7)
- [ ] **no new locks**: 5 minutes of monitoring with no `wait_event_type = 'Lock'`
- [ ] 🛑 **GATE**: all green = safe to report the improvement magnitude. Any single regression = roll back the migration immediately

### Phase 5: Drop retirement (iron law 9)

- [ ] Skip when not applicable
- [ ] **RENAME**: `./scripts/plan-delete.sh --column public.users.legacy_field`
- [ ] **7-day observation period**: monitor the application for `column not found` errors
- [ ] **audit check**: `./scripts/audit-plan-delete.sh` lists DAYS_LEFT
- [ ] **owner explicitly authorizes** the DROP
- [ ] **actual DROP**: execute within the owner-authorized window
- [ ] 🛑 **GATE**: DROP only when both conditions hold — 7-day observation + owner authorization

### Phase 6: Document + Share

- [ ] **Write work-note**: `docs/work-note/<date>-db-tune.md` (Phase 0 baseline + Phase 4 verify comparison)
- [ ] **KB sync**: push to the KB endpoint's public-knowledge collection (skip if no KB system is configured)
- [ ] **Update schema docs**: column/table changes → env.md / deploy.md

---

## Included

| Path | Contents |
|---|---|
| `references/db-tuning.md` | 9 iron laws + 7 phases + 8 patterns + tooling stack + monitoring metrics |
| `scripts/plan-delete.sh` | RENAME → PLAN_DELETE_ pipeline before DROP |
| `scripts/audit-plan-delete.sh` | list all pending + DAYS_LEFT + STATUS |
| `scripts/config_drift.py` | live config (systemd / crontab / .env) vs git detection |

## Usage

```bash
./scripts/plan-delete.sh --column public.users.legacy_field
./scripts/plan-delete.sh --table public.old_logs
./scripts/plan-delete.sh --index public.idx_unused
./scripts/audit-plan-delete.sh
python scripts/config_drift.py --all --repo /path/to/project
```

## DB-specific iron laws

| # | Iron law |
|---|---|
| 1 | evidence first |
| 2 | DDL CONCURRENTLY |
| 3 | triple check before delete |
| 4 | naming regex trap |
| 5 | statement_timeout 30s |
| 6 | VACUUM FULL needs owner approval |
| 7 | lock checks + dual clocks |
| 8 | no bare DDL |
| 9 | rename before delete |

## 14 Hard Constraints (common across sub-workflows)

1. **Zero new dependencies (YAGNI)**: prefer built-in tools; add no dependencies beyond `pgcli` / HypoPG for hypothetical scenarios.
2. **Commit granularity**: 1 migration = 1 commit.
3. **Default rollback = RENAME window** (PLAN_DELETE_). **`git reset --hard` is absolutely forbidden**.
4. **Dead code proof**: before deleting a column/index, check `pg_depend` + grep application code + ORM migrations.
5. **TDD**: use Structural (build + test) for schema changes.
6. **All tests green before commit**: migration dry-run + application regression.
7. **prod locked**: prod DDL via migration tool + owner review. **No bare `psql -c`**.
8. **Prefer absence over fabrication**: verification relies on EXPLAIN + pg_stat_statements.
9. **Every DB deletion goes through the retirement pipeline**: PLAN_DELETE_ + 7 days + owner review.
10. **Test minimal first for batch tasks**: sample 1-10 tables before a large migration batch.
11. **4 independent steps for daemon changes**: after trigger/PL changes, verify in 4 independent steps.
12. **Buffer ownership**: the COPY FROM client buffer keeps a copy.
13. **Hash-named artifacts sync as whole directories**: switch traffic only after index rebuilds complete on all backend nodes.
14. **Verify deploys actually took effect**: after migration apply, check `pg_indexes` / `pg_attribute` to confirm the new schema.

## Related

- `/repo-medic` — meta entry point
- `/py-improve` — code review of the Python callers behind slow queries
- `/doc-reorg` — env.md / deploy.md sync after schema changes
- `/config-base` — bootstrap PG client tools (psql / pgcli / migration tool)

## Repository

github.com/ebziw/repo-medic — Apache-2.0.

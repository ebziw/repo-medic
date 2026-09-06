# Governed Undo Protocol (borrowed from `postgres-aiops`)

Every mutating DB write captures the **real before-state** and records a faithful inverse, so any change can be undone within its audit window. Irreversible ops declare no-undo upfront.

## Pair table (write op → undo)

| Write op | Capture | Undo |
|---|---|---|
| `create_index` | nothing to capture (creation) | `drop_index <name>` |
| `drop_index` | `pg_get_indexdef(index_oid)` + storage params | `create_index` with exact captured def |
| `update_setting` | prior `pg_settings` value | `update_setting` to captured prior value |
| `reset_query_stats` | prior stats snapshot (counts only) | none (declare no-undo) |
| `run_vacuum` / `run_analyze` / `reindex` | none | none (side-effect ops, no-undo) |
| `terminate_backend` / `cancel_query` | PID + query text (audit only) | none (no-undo, irreversible by design) |

## Storage

Every write emits two records to `audit/governed-writes.jsonl` (append-only):

```json
{
  "ts": "2026-09-07T03:45:12Z",
  "agent": "db-tweak@kb",
  "op": "create_index",
  "target": "public.orders.idx_user_status",
  "sql": "CREATE INDEX CONCURRENTLY ...",
  "undo_sql": "DROP INDEX CONCURRENTLY ...",
  "no_undo": false,
  "executed": true": true,
  "verified": true": "CREATE INDEX"
}
```

`undo_apply` tool reads the jsonl + runs `undo_sql` in reverse order.

## Iron law

> **No write without a captured inverse (or an explicit no-undo declaration).**

PR review must reject any DB write script that doesn't emit a governed-writes record.

## Sources

- Borrowed from `aiops-tools/postgres-aiops` undo harness (https://github.com/aiops-tools/postgres-aiops)
- Modified: appended to jsonl instead of separate DB table (works for any PG access)

## Why include

- Database writes are the highest-risk class of changes in any system
- Without an inverse, "oh shit" recovery requires manual reconstruction from git history + memory
- Audit jsonl is greppable, version-controllable, and reviewable in PR diff
- "No-undo" declaration forces you to think about irreversibility before clicking execute

## Related

- `scripts/plan-delete.sh` already implements part of this (RENAME → PLAN_DELETE_)
- `scripts/config_drift.py` (audit live config vs committed)
- Iron law 3 (triple check before delete — governed-undo is the inverse protection)
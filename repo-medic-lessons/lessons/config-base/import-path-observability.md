# When "single import OK, combined fails": print `sys.modules[X].__file__` to expose import drift

**Symptom**: feed worker `backend.*` imports all resolved to `/home/kb/prod/backend`; test changes "didn't take". Combined import `backend.core.fetch_unlock` raised ModuleNotFoundError, but each sub-module imported OK alone.

**Cause**: `feed_common` and 4 sibling files did `_sys.path.insert(0, "/home/kb/prod")` AFTER test setup → prod won index 0 → test/prod drift → worker ran hybrid code.

**Fix**:
- Diagnostic signal: "single import OK, combined ModuleNotFoundError" → immediately print `sys.modules['backend'].__file__` to see actual loaded path
- Fix: reorder so test path inserts last (test is superset of prod in safe cases); or use PYTHONPATH env instead of hardcoded `sys.path.insert`
- **Never** hardcode absolute prod paths in `sys.path.insert` — use env var or relative config
- Lint: any `_sys.path.insert(0, "/")` → block in PR review

## Sources

- `commit:a0ce201` — fix(python): feed chain sys.path prod-first → test-first

## Frequency

2 (this + systemd drift, same debug session)

## Triggers

sys.path, test-first 失效, ModuleNotFoundError combined import, hybrid code, __file__ 验证

## Related hard constraints

#14 (验证实际生效产物)

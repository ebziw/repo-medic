# `pkill -f` matches the remote bash's own command line → self-kill, exit 255

**Symptom**: remote `pkill -f 'llama-server.*18889'` returns exit 255; new service never starts; remote session may itself be killed.

**Cause**: `pkill -f` matches against the full process command line; the running bash session's own argv contains the pattern string, so it kills its own parent.

**Fix**:
- Exact name? Use `pkill -x <name>` instead of `-f`
- Pattern match? First `pgrep -af '<pattern>'` and confirm the target list does NOT include the calling shell PID
- Or pipe `pkill -f` results through grep -v $$ to exclude self

## Sources

- `work-note:docs/work-note/2026-09-06-search-cold-query-iter3.md`

## Frequency

1 (debug cost: session killed, deploy blocked)

## Triggers

pkill -f, self-match, remote exec, exit 255, process management, deploy hook

## Related hard constraints

#1 (YAGNI — don't reach for pattern match when exact works)
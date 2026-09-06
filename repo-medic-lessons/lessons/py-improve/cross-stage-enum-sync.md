# New source/status enum values must sync ALL stage whitelists

**Symptom**: after adding `super_fetch` to crawler's source enum, feed worker silently skipped it; 72 + 50 + 16 + 4 = 142 URLs status=pending for 1 month, attempts=0.

**Cause**: bidirectional claim/feed design where each side maintains its own source whitelist; adding new value to one side only = dead lock (no errors, just idle).

**Fix**:
- New enum value → grep ALL stage whitelists: `WHERE source` / `WHEN status` / case-match arms
- Schema-level fix: store whitelist in one place (DB table or shared constant) instead of duplicated in each stage
- Reconciliation query: any value present in stage-A's enum but missing from stage-B's whitelist → CI gate

## Sources

- `commit:6134baf` — fix(feed): super_fetch added to claim source whitelist

## Frequency

2 (this + handoff-receiver-pair-check, same root cause)

## Triggers

source enum, status enum, new value, whitelist, 双向死锁, silent idle, dead lock

## Related hard constraints

#8 (宁缺勿伪)

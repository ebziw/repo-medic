# Implicit contracts must be made explicit (cross-stage handoff + enum sync)

**Principle**: every "X leaves something for Y" handoff encodes a contract in the writer's head, not in code. The receiver's claim/filter conditions must explicitly cover what the writer hands off — silence ≠ handoff, missing enum value ≠ handoff.

**Symptom (any of)**:
- Work pending in stage B = 0 for N days while stage A finished it (no errors)
- New source/status enum value added to stage A, stage B silently ignores it
- "skip because 留给 X" comment with no verification that X's filter actually accepts

**Fix**:
- Any handoff comment ("留给", "skip because", "next stage handles") must be paired with verification that the receiver's claim/filter covers it
- Single source of truth for shared enums (one DB table or one constants file, not duplicated in each stage)
- Reconciliation alert: A-stage complete ∧ B-stage 0 claims ∧ time > N hours → page
- Audit greppable: "留给" / "skip because" / "next stage" must have matching whitelist reference within ±50 lines

## Sources

- `commit:6134baf` — fix(feed): super_fetch added to claim source whitelist
- `work-note:fetch-unlock.md` — 142 URLs pending 1 month silent deadlock

## Frequency

High (any multi-stage pipeline or service mesh has at least one such pair)

## Triggers

handoff, 留给, skip because, claim condition, downstream, 双向死锁, reconciliation, pending积压, enum value added

## Related hard constraints

#8 (宁缺勿伪 — implicit contracts must be made explicit)
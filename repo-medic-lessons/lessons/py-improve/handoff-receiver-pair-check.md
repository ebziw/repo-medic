# Any "skip because 留给 X" handoff must verify X can receive it

**Symptom**: crawler designed "skip if content_md exists (留给 feed)" but feed's source whitelist didn't include the new source → 142 URLs stuck status=pending for 1 month, attempts=0, no error logs.

**Cause**: handoff design assumed downstream would accept the handover based on writer's mental model, without checking the downstream's claim/filter conditions.

**Fix**:
- Any `skip because 留给 X` comment must be paired with verification that X's claim/filter actually covers the handoff
- Add periodic reconciliation: A-stage complete ∧ B-stage 0 claims ∧ time > N hours → alert
- Linter rule (manual): grep for "留给" / "skip.*because" / "next stage" comments → audit matching claim conditions

## Sources

- `commit:6134baf` — fix(feed): super_fetch added to claim source whitelist
- `work-note:fetch-unlock.md` — 2026-09-06 super_fetch 双向死锁

## Frequency

2 (cross-stage-enum + handoff-must-have-receiver 同根因)

## Triggers

handoff, 留给, skip because, claim condition, downstream, 双向死锁, reconciliation

## Related hard constraints

#8 (宁缺勿伪 — 隐式契约显式化)

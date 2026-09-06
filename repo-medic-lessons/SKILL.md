---
name: repo-medic-lessons
description: "Accumulated hard-won lessons distilled from real projects by /evolve, bucketed per sub-skill. Consult before running repo-medic sub-skills; each bucket lists pitfalls, root causes, and the 'when X happens, do Y' rule that avoids them. Triggers: repo-medic-lessons, lessons, pitfalls, past mistakes, known issues, gotchas, hard-won"
---

# repo-medic-lessons — Distilled Lessons from /evolve

This companion skill ships lessons accumulated from real projects via `/evolve`. It lives outside the main skill packages so upgrades never erase them. Consult these lessons **before** running repo-medic sub-skills to avoid pitfalls we already paid for.

## When to Use

- Before running `py-improve` / `config-base` / `db-tweak` / `doc-reorg` / `vue-improve`
- When you see a symptom described in any lesson (cross-stage deadlock, too many clients, import drift, etc.)
- When debugging a class-of-bug that recurs across sub-skills

## When NOT to Use

- Single-shot fixes → use the right sub-skill directly
- New unique bugs not matching any lesson → debug fresh, then run `/evolve` to add

## Lessons index (per bucket)

### py-improve

- [L1 handoff-receiver-pair-check](lessons/py-improve/handoff-receiver-pair-check.md) — any "skip because 留给 X" must verify X's claim/filter covers it; add periodic reconciliation alerts (#8 宁缺勿伪)
- [L2 cross-stage-enum-sync](lessons/py-improve/cross-stage-enum-sync.md) — new source/status enum values must sync all stage whitelists (双向死锁 case)
- [L3 third-party-api-params-audit](lessons/py-improve/third-party-api-params-audit.md) — every param of paid API needs official-doc audit + A/B test (#1 YAGNI)
- [L4 sql-string-concat-no-inline-comments](lessons/py-improve/sql-string-concat-no-inline-comments.md) — Python string concat kills `--` comments; either `\n` or move comment to Python layer

### config-base

- [L5 runtime-evidence-chain](lessons/config-base/runtime-evidence-chain.md) — for live behavior, trust `systemctl cat` + `ps aux` + `/proc/<pid>/cwd`, not unit main file (#14)
- [L6 import-path-observability](lessons/config-base/import-path-observability.md) — when "single import OK, combined fails", print `sys.modules[X].__file__`; ban hardcoded absolute sys.path inserts
- [L7 paid-api-cost-from-official-docs](lessons/config-base/paid-api-cost-from-official-docs.md) — credit multipliers + failure-billing + custom-feature triggers must come from official pricing, not vendor self-claims

### db-tweak

- [L8 failure-loop-conn-budget](lessons/db-tweak/failure-loop-conn-budget.md) — exception path × high-frequency loop × per-iter conn = pool killer; add backoff + `pg_stat_activity` alert (#11)

## Trigger keywords

- **py-improve**: source whitelist / status enum / deadlock / claim / handoff / wait_for / API param audit / SQL comment / string concat
- **config-base**: sys.path / import drift / systemctl cat / override / drop-in / credit multiplier / pricing / official docs
- **db-tweak**: too many clients / connection pool / failure loop / backoff / pg_stat_activity

## How lessons are written

Each lesson follows:
```
# <one-line principle>

**Symptom**: <concrete failure observed>
**Cause**: <root cause, not symptom>
**Fix**: <actionable rule, not "be careful">

## Sources
- commit:<hash> — <one-line commit subject>
- work-note:<file> — <incident summary>

## Frequency
N (notes if this recurs)

## Triggers
<keywords that should make you grep this file>

## Related hard constraints
#<N> <name>
```

## How to add a lesson

1. Run `/evolve` in a project with non-trivial work-notes
2. User reviews each candidate; bucket per sub-skill
3. Write the lesson to `lessons/<bucket>/<topic>.md` following the schema
4. Add a one-liner to SKILL.md index
5. Commit

**Never write lessons inside a skill's own directory** — upgrade would erase them.

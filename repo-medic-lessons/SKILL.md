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

- [L1 handoff-receiver-pair-check](lessons/py-improve/handoff-receiver-pair-check.md) — implicit contracts must be made explicit; any "留给 X" must verify X's claim/filter covers it (incl. enum sync case) (#8 宁缺勿伪)
- [L9 silent-fallback-grade-not-uniform](lessons/py-improve/silent-fallback-grade-not-uniform.md) — critical deps must raise, not silently fall back; grade by blast radius (#8)
- [L10 perf-measure-cold-and-breakdown](lessons/py-improve/perf-measure-cold-and-breakdown.md) — cold/warm split + per-stage breakdown before tuning parameters
- [L11 god-fn-split-requires-characterization](lessons/py-improve/god-fn-split-requires-characterization.md) — write characterization tests to lock undocumented behavior before any split (#6)
- [L12 stale-test-vs-impl-judgment](lessons/py-improve/stale-test-vs-impl-judgment.md) — find evolution evidence first; documented evolution → fix test, undocumented drift → check git history (#8)

### config-base

- [L5 runtime-evidence-chain](lessons/config-base/runtime-evidence-chain.md) — for live behavior, trust `systemctl cat` + `ps aux` + `/proc/<pid>/cwd`, not unit main file (#14)
- [L6 import-path-observability](lessons/config-base/import-path-observability.md) — when "single import OK, combined fails", print `sys.modules[X].__file__`; ban hardcoded absolute sys.path inserts
- [L7 paid-api-cost-from-official-docs](lessons/config-base/paid-api-cost-from-official-docs.md) — credit multipliers + failure-billing + custom-feature triggers must come from official pricing, not vendor self-claims
- [L14 long-lived-service-must-be-unit](lessons/config-base/long-lived-service-must-be-unit.md) — bare nohup dies silently; systemd --user unit with `Restart=on-failure` for any long-running service (#14)
- [L15 pkill-f-can-self-match](lessons/config-base/pkill-f-can-self-match.md) — `pkill -f` matches the calling bash's own argv → exit 255 self-kill; use `pkill -x` or pgrep-filter (#1)
- [L16 third-party-config-must-replicate-prod-input](lessons/config-base/third-party-config-must-replicate-prod-input.md) — sample benchmarks lie; test with prod-shape inputs (long docs, unicode) before declaring green (#14)
- [L17 shared-backend-change-verify-each-consumer](lessons/config-base/shared-backend-change-verify-each-consumer.md) — `/health` 200 ≠ contract; verify every consumer's call shape after backend switch + invalidate cache (#14)

### db-tweak

- [L8 failure-loop-conn-budget](lessons/db-tweak/failure-loop-conn-budget.md) — exception path × high-frequency loop × per-iter conn = pool killer; add backoff + `pg_stat_activity` alert (#11)

## Trigger keywords

- **py-improve**: handoff / 留给 / skip because / claim condition / enum value added / silent fallback / non-fatal except / degrade flag / cold query / per-stage timing / god function / characterization / stale test / threshold drift / evolution evidence
- **config-base**: sys.path / import drift / systemctl cat / override / drop-in / credit multiplier / pricing / official docs / nohup / systemd unit / Restart=on-failure / long-lived service / pkill -f / self-match / exit 255 / llama.cpp / n_ubatch / batch size / rerank / prod-input / schema contract / switch backend / cache invalidation
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

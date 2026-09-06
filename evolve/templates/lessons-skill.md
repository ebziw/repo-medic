---
name: repo-medic-lessons
description: "Accumulated hard-won lessons distilled from real projects by /evolve, bucketed per sub-skill. Consult before running repo-medic sub-skills; each bucket lists pitfalls, root causes, and the 'when X happens, do Y' rule that avoids them. Triggers: repo-medic-lessons, lessons, pitfalls, past mistakes, known issues, gotchas, hard-won"
metadata:
  type: ops
  scope: public
---

# repo-medic-lessons

Additive lesson store maintained by `/evolve`. Lives OUTSIDE the repo-medic skill
packages on purpose: skill directories are replaced wholesale on upgrade, so any
lesson written inside them would be lost. This directory is never touched by upgrades.

## Buckets

One folder per target sub-skill:

- `py-improve/` — Python refactoring pitfalls
- `doc-reorg/` — directory/document reorganization pitfalls
- `db-tweak/` — PostgreSQL tuning pitfalls
- `vue-improve/` — Vue 3 frontend pitfalls
- `config-base/` — toolchain bootstrap pitfalls
- `general/` — cross-cutting lessons

## Lesson format

Each lesson file: frontmatter (`title`, `date`, `target_skill`, `frequency`, `triggers`)
+ Symptom / Cause / Fix sections. Full schema: `evolve/references/lesson-schema.md`.

## Index

| Date | Bucket | Lesson | Frequency |
|---|---|---|---|
| _(empty — appended by /evolve Phase 3)_ | | | |

## Maintenance rules

1. Only `/evolve` writes here (Phase 3), one commit per lesson.
2. New lesson → append one line to the Index + add its keywords to this
   description's `Triggers:` list (keeps auto-matching accurate).
3. Never delete lessons; supersede with a new file linking the old one.

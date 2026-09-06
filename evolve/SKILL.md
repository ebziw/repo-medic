---
name: evolve
description: "repo-medic self-evolution — collect recent pitfalls and lessons from the current project, distill them into additive lessons stored in the upgrade-safe repo-medic-lessons companion skill, and stop future runs from hitting the same pitfalls. Scan git log + docs/work-note/, cluster, review with the user, then bucket per sub-skill. Triggers: pitfall, experience, lessons learned, distill, postmortem, retrospective, evolution, evolve, project retrospective, KB feedback, self-improve"
metadata:
  type: ops
  scope: public
---

# evolve — repo-medic self-evolution

Self-contained skill. Distills "pitfalls hit recently" into rules injectable into SKILL.md, so future runs stop hitting the same pitfalls.

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Collect sources

- [ ] **Read** `references/lesson-schema.md` (lesson extraction format)
- [ ] **Set the time window**: default `--since 7d` (user may change it to 1d / 30d / since-last-tag)
- [ ] **Scan git log**: extract commit message + body (using `git log --since=... --pretty=full`)
- [ ] **Scan work-notes**: read `docs/work-note/*.md` and regex-match the `**Symptom**:` / `**Cause**:` / `**Fix**:` fields
- [ ] **Optional**: scan KB public-knowledge for lesson-type content
- [ ] **Run** `python scripts/extract.py --since 7d --repo .` to extract candidates
- [ ] 🛑 **GATE**: extraction complete + candidate list presented to the user

### Phase 1: Distill (candidate → lesson)

- [ ] **Deduplicate**: merge entries with similar Symptom/Cause
- [ ] **Rank by frequency**: prioritize anything appearing ≥ 2 times (high ROI)
- [ ] **Tag by category**: give each lesson one tag (DB / deploy / config / frontend / general)
- [ ] **Filter scope**: skip anything unrelated to repo-medic (user business logic, third-party bugs, etc.)
- [ ] **Abstract into rules**: turn concrete cases into reusable "when X happens, do Y" patterns
- [ ] 🛑 **GATE**: after distillation, show the user ≤ 10 candidates (> 10 = not converged, re-extract)

### Phase 2: User review

- [ ] **Present each item**: show "Candidate N: ..." plus the matched source (commit/work-note)
- [ ] **User confirmation**: accept / reject / modify each item
- [ ] **User picks the target sub-skill**: choose per item which skill's lessons bucket the item belongs to (py-improve / doc-reorg / db-tweak / vue-improve / config-base)
- [ ] 🛑 **GATE**: user OK on every item before entering Phase 3

### Phase 3: Inject (additive only — never touch skill packages)

- [ ] **Lessons dir**: write to `~/.claude/skills/repo-medic-lessons/lessons/<target-skill>/<topic>.md` (create dirs on first run). **NEVER write inside a skill's own directory** — skill directories are replaced wholesale on upgrade, and anything written there is lost
- [ ] **Version the lessons dir**: if `~/.claude/skills/repo-medic-lessons/` is not a git repo yet, run `git init` + an initial commit — this makes the 1-lesson-1-commit gate below enforceable and gives lessons history/rollback
- [ ] **Index update**: maintain `~/.claude/skills/repo-medic-lessons/SKILL.md` — one summary line per lesson + accumulate trigger keywords per domain (skeleton in `templates/lessons-skill.md`)
- [ ] **Commit**: 1 commit = 1 lesson (iron rule 2)
- [ ] 🛑 **GATE**: show the diff to the user + user OK before committing

### Phase 4: Verify + Share

- [ ] **Tests pass**: sub-skill tests or smoke test
- [ ] **KB sync** (optional): push to the KB endpoint's public-knowledge collection (skip if no KB system is configured)
- [ ] **Work-note**: write `docs/work-note/<date>-evolve-extract.md` recording this distillation round
- [ ] **No in-package writes**: do not add anything to `evolve/` or any other skill dir — all durable output goes to `repo-medic-lessons/`

---

## Contents

| Path | Contents |
|---|---|
| `scripts/extract.py` | git log + work-notes extractor (outputs candidate lessons) |
| `templates/lesson.md` | lesson file format template |
| `templates/lessons-skill.md` | skeleton for the `repo-medic-lessons` companion skill (Phase 3 creates it from this) |
| `references/lesson-schema.md` | extraction field definitions (Symptom / Cause / Fix / Frequency) |

## Usage

```bash
# Scan the last 7 days by default
python scripts/extract.py --repo .

# Custom time window + output to a file
python scripts/extract.py --repo . --since 30d --output lessons-candidates.md

# Limit the number of commits
python scripts/extract.py --repo . --max-commits 100

# JSON for downstream scripts to consume
python scripts/extract.py --repo . --json | jq '.candidates[].tag' | sort | uniq -c
```

The output is a candidate list (including source commit/work-note links + frequency). After user review, bucket each lesson under its target sub-skill in the `repo-medic-lessons` companion skill (Phase 3).

## 14 Hard Constraints (common across sub-workflows)

1. **Zero new dependencies (YAGNI)**: extract.py uses only the stdlib (git log via subprocess, no pygit2).
2. **Commit granularity**: 1 lesson = 1 commit.
3. **Default rollback = git revert**. **`git reset --hard` is absolutely forbidden**.
4. **Dead-code proof**: N/A (extract is a throwaway script, not long-term sub-skill code).
5. **TDD**: N/A (one-shot extraction + human review).
6. **All green before commit**: run the sub-skill smoke test after injecting a lesson.
7. **prod lockdown**: never modify a prod project sub-skill's SKILL.md directly — try it in a fork or worktree first.
8. **Prefer missing over fake**: extract output carries source links (commit hash + work-note file) so the user can verify.
9. **DB deletion**: N/A.
10. **Test the smallest sample first in batches**: run `extract.py --since 1d` on a small scope + calibrate, then widen to 30d.
11. **daemon 4-step independence**: N/A.
12. **buffer ownership**: N/A.
13. **hash artifact whole-directory sync**: N/A.
14. **Deploy verified as actually effective**: after injecting a lesson, run the sub-skill smoke test + verify once with real usage.

## Related

- `/repo-medic` — meta entry point
- all other sub-skills — evolve's injection targets
- `docs/work-note/` — data source (CLAUDE.md-mandated Symptom/Cause/Fix format)

## Repository

github.com/ebziw/repo-medic — Apache-2.0.

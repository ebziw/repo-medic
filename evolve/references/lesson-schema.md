# Lesson Schema — evolve extraction field definitions

evolve distills lessons from project history; each lesson uses the following structure:

## Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | auto-generated `{short_hash}_{index}` |
| `tag` | enum | category: `db` / `deploy` / `config` / `frontend` / `general` / `python` / `doc` |
| `target_skill` | enum | suggested injection target: `py-improve` / `doc-reorg` / `db-tweak` / `vue-improve` / `config-base` / `repo-medic` (meta) |
| `symptom` | string | symptom description (≤ 80 characters) |
| `cause` | string | root-cause analysis (≤ 120 characters) |
| `fix` | string | fix / solution (≤ 120 characters) |
| `references` | enum | the 14 hard-constraint numbers (e.g. "1", "2", "11"), marking which constraint was violated/supplemented |
| `triggers` | list[str] | this lesson's match keywords (used to inject into the target_skill's `Triggers:`) |
| `frequency` | int | occurrence count (after dedup); the higher the value, the higher the ROI |
| `sources` | list[str] | sources: `commit:<hash>` or `work-note:<path>` or `kb:<url>` |
| `confidence` | enum | `low` / `med` / `high` (extract.py heuristic score) |

## Source formats

- `commit:<hash>` — a commit captured by `git log --pretty=format:%H`
- `work-note:<path>` — `docs/work-note/YYYY-MM-DD-*.md`
- `kb:<collection>/<name>` — KB public-knowledge / work-note

## Priority

| Frequency | Default action |
|---|---|
| ≥ 3 | High priority — always enters Phase 2 (user review) |
| 2 | Medium priority — enters Phase 2, but may be flagged as "low frequency" |
| 1 | Low priority — enters only when strongly related to the 14 hard constraints |

## Injection locations

All lessons go to the upgrade-safe companion skill **outside any skill package**:

- `~/.claude/skills/repo-medic-lessons/lessons/<target_skill>/<topic>.md` — the lesson file
- `~/.claude/skills/repo-medic-lessons/SKILL.md` — index + per-domain trigger keywords

**Never write into `~/.claude/skills/<target_skill>/`** (SKILL.md / references/ / scripts/): skill directories are replaced wholesale on upgrade, so in-package edits and additions are lost. The companion skill survives every upgrade because no release ever touches it.

Each lesson must be **injected into exactly one target_skill bucket** (avoids duplication + keeps a single authoritative file).

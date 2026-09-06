---
name: py-improve
description: "Python code improvement — god-fn splitting / dead code removal / duplicate method merging / dict constant dedup / silent-swallow fixes / logging observability / pre-merge CR. Includes the ruff/vulture/bandit/radon/pyright MCP toolchain. Triggers: god-fn, code review, Python, pytest, mypy, ruff, vulture, refactor, dedup, silent error, god function"
metadata:
  type: domain
  scope: public
---

# py-improve — Python code improvement

Self-contained skill. Copy the whole directory to share it with other projects.

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Reconnaissance

- [ ] **Read** `references/code-refactor.md` in full (17 phases methodology)
- [ ] **Read** `references/code-review-checklist.md` (pre-merge mechanical rules)
- [ ] **Read** `references/logging-observability.md` (silent-swallow scan commands)
- [ ] **Read** `references/dict-dedup.md` if dict/constant changes involved
- [ ] **Run** the silent-swallow scan: `python scripts/silent_swallow.py src/`
- [ ] **Run** the reference-residue scan: `python scripts/reorg_drift.py` (if renaming/moving)
- [ ] **Build** codegraph (large projects, ≥ 5 min): `codegraph build --no-incremental`
- [ ] 🛑 **GATE**: enter Phase 1 only after baseline metrics are captured (no baseline = no improvement evidence)

### Phase 1: Diagnose

- [ ] **List god-fn candidates**: cyclomatic > 15 OR > 100 lines (`radon cc -s src/`)
- [ ] **List dead-code candidates**: ruff `F401` / `F841` / pyright `reportUnused*`
- [ ] **List duplicates**: identical function signatures in ≥ 2 places (grep function def)
- [ ] **List dict/constant duplicates**: cross-check against the 4 problem categories in `references/dict-dedup.md`
- [ ] 🛑 **GATE**: start editing only after candidates are listed and the user confirms scope (avoids aimless large changes)

### Phase 2: Execute

- [ ] **1 commit = 1 logical unit** (hard rule 2) — change one class of problem at a time
- [ ] **Write tests first** (one of the 4 TDD modes: Characterization / Red-Green / Regression / Structural)
- [ ] **Run** `pytest` + `ruff check` + `mypy` immediately after each change (hard rule 6)
- [ ] **Run** `silent_swallow.py src/` on every commit (cross-cutting hard rule 13.1)
- [ ] 🛑 **GATE**: all tests must be green before the next commit (red = back to Phase 2)

### Phase 3: Verify

- [ ] **All tests green**: `pytest tests/` 0 fail
- [ ] **No new silent-swallow**: `silent_swallow.py src/` output does not grow
- [ ] **No broken imports in codegraph**: `codegraph where <moved_module>` still resolves
- [ ] **New features have tests**: `pytest --cov` shows coverage on new code
- [ ] **Clean commit history**: `git log --oneline` shows one improvement per commit at a glance
- [ ] 🛑 **GATE**: all boxes checked = report completion. Any box unchecked = "done" may not be claimed.

---

## Included

| Path | Content |
|---|---|
| `references/code-refactor.md` | god-fn splitting + dead-code 7 steps + 4 TDD modes + YAGNI |
| `references/code-review-checklist.md` | pre-merge mechanical rules + no-silent-swallow P0 |
| `references/logging-observability.md` | silent-swallow scan commands + fix templates |
| `references/dict-dedup.md` | dict/constant dedup 4 problem categories + Phases 0-5 |
| `references/dict-dedup-case-levelcfg.md` | _LEVEL_CFG CONFLICT case study |
| `scripts/silent_swallow.py` | silent-swallow scanner |
| `scripts/reorg_drift.py` | reference-residue scan (check callers after deleting a module) |
| `mcp_servers/python_refactor_server.py` | MCP server: ruff/vulture/bandit/radon/pyright |

## Usage

```bash
# silent-swallow scan
python ~/.claude/skills/py-improve/scripts/silent_swallow.py src/

# reference residue
python ~/.claude/skills/py-improve/scripts/reorg_drift.py

# MCP tools (register in ~/.claude/settings.json)
# see mcp_servers/python_refactor_server.py
```

## 14 hard constraints (universal across sub-workflows)

1. **Zero new dependencies + zero preemptive defense (YAGNI)**: use stdlib + already-installed libraries only. Do not add try/except / retry / fallback / abstraction layers ahead of hypothetical risks.
2. **Commit granularity**: 1 logical unit = 1 commit, independently revertible.
3. **Default rollback = rsync backup restore** (lossless). **`git reset --hard` is absolutely forbidden**.
4. **Dead-code proof requires the 7-step checklist**: static references + text search + framework registration + exports + dynamic calls + tests/generated code + user sign-off. 0-caller grep ≠ proof.
5. **TDD has 4 modes by scenario**: Characterization / Red-Green / Structural (7 steps + full build/test) / Regression.
6. **Full test suite green before every commit**; never break CI. **Project-level exception**: when running the suite is unsafe in this project (e.g. tests mutate prod data), the project's own rule wins — record the exception in the run report and run the safest subset that still covers the change.
7. **Prod locked**: do not touch production code; touch it only with explicit owner authorization.
8. **Prefer gaps over fabrication**: leave a TODO for uncertain facts; never invent. Verify with grep / codegraph / pyright against reality.
9. **DB deletion always goes through the retirement pipeline**: RENAME before DROP → PLAN_DELETE_<original_name> → 7 days of testing → user review.
10. **Test the minimum first for batch tasks**: for any batch operation, run a minimal sample (1-10) end to end + time it, then extrapolate full-run duration proportionally. **Never start with the largest collection**.
11. **Daemon/service code changes in 4 independent steps**: ① local Edit ② local py_compile verification ③ scp upload + clear __pycache__ ④ systemctl restart + pgrep to verify the PID changed. **Never chain `restart && smoke`**.
12. **Buffer ownership is transferred**: the caching side must keep a copy; pass bytes.slice(0) / np.array(..., copy=True) before every hand-off.
13. **Hash-named build artifacts must be synced as a whole directory**: frontend chunk names carry hashes — pushing only the changed files → index.html references new hashes → missing chunks → MIME text/html 404.
14. **After deploy/release, verify the identifier of the actually-live artifact**: a script printing "✓ done" ≠ a successful deploy.

## Related

- `/repo-medic` — meta entry point
- `/doc-reorg` — post-refactor directory archiving
- `/db-tweak` — review of DB-related callers

## Repository

github.com/ebziw/repo-medic — Apache-2.0.

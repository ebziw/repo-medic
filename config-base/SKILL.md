---
name: config-base
description: "Toolchain bootstrap required by repo-medic — detect + install + upgrade every supporting component (ruff/mypy/codegraph/node/psql etc.). Run `python scripts/tools.py check` to see the status table; `install` auto-installs missing items. Triggers: tool missing, configuration, environment bootstrap, install deps, bootstrap, setup, environment check, dependency check"
metadata:
  type: ops
  scope: public
---

# config-base — repo-medic toolchain bootstrap

Self-contained skill. Detects, installs, and upgrades every tool the repo-medic sub-skills depend on.

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Detect current state

- [ ] **Run** `python scripts/tools.py check`
- [ ] **Read** the output table; mark OK / MISSING / OUTDATED / ERROR
- [ ] **Cross-check** against the sub-skill requirements list (enumerated in Phase 1)
- [ ] 🛑 **GATE**: report to the user + get user confirmation for the next action (never install on your own initiative)

### Phase 1: Identify user needs

- [ ] Which sub-skills will actually be used? Install only what gets used (YAGNI iron rule 1)
- [ ] py-improve needs → ruff/mypy/vulture/bandit/radon/pyright/pytest + codegraph + MCP deps
- [ ] doc-reorg needs → rg + tree + git (git is usually already installed)
- [ ] db-tweak needs → psql + pg_dump
- [ ] vue-improve needs → node ≥ 18 + npm/pnpm + project-local vite/vitest
- [ ] 🛑 **GATE**: enter Phase 2 only after the requirements list is complete + user OK

### Phase 2: Install missing

- [ ] **Dry-run first**: `python scripts/tools.py install --all` (omit --yes to see what would be installed)
- [ ] **Review** the output; confirm item by item whether each needs installing
- [ ] **Actually install**: `python scripts/tools.py install --all --yes` or a single `python scripts/tools.py install <name> --yes`
- [ ] **Verify**: after install, run `python scripts/tools.py check` again to see whether it turns OK
- [ ] 🛑 **GATE**: after install, the check table should be all OK; any remaining gap needs a justified reason

### Phase 3: Configure

- [ ] **MCP server registration**: configure the `python_refactor_server` path in `~/.claude/settings.json`
- [ ] **PATH check**: tool is on PATH (the script runs `which` automatically to verify)
- [ ] **Environment variables**: check the env vars used by sub-skills (provider API tokens / DATABASE_URL etc.) — **not managed here**; each sub-skill configures its own
- [ ] **Optional**: write `~/.config/repo-medic/config.toml` recording tool paths (diff on upgrade)
- [ ] 🛑 **GATE**: say "environment ready" only after check + registration are done

### Phase 4: Document + Share

- [ ] **work-note** (if the environment changed): write docs/work-note/<date>-env-bootstrap.md
- [ ] **Do not**: auto-commit / touch the prod env / decide for the user what to install (iron rules 7 + 1)

---

## Tool manifest

| Category | Tools | Consuming sub-skill | Platform install method |
|---|---|---|---|
| python | python ≥ 3.12 | py-improve + db-tweak MCP | system |
| python | uv | package manager (handles the Debian typing_extensions conflict) | system |
| python | ruff, mypy, vulture, bandit, radon, pyright | py-improve lint/type/audit | uv pip install |
| python | pytest | py-improve testing | uv pip install |
| node | node ≥ 18, npm, pnpm | vue-improve + codegraph | system |
| system | codegraph | py-improve reference graph | npm install -g @optave/codegraph |
| system | rg (ripgrep), tree | doc-reorg + general | apt/brew |
| db | psql, pg_dump | db-tweak | apt (postgresql-client) |
| mcp | mcp + fastapi + uvicorn | MCP server for py-improve | uv pip install |

Full list (including min_version): see the `TOOLS` list in `scripts/tools.py`.

## Usage

```bash
# Detect the current environment
python scripts/tools.py check
# Output:
# TOOL          CAT     STATUS   VERSION              REQUIRED
# -----------------------------------------------------------------
# python        python  OK       Python 3.14.3        3.12
# ruff          python  MISSING  -                    0.3
# mypy          python  MISSING  -                    1.8
# ...
# Total: 17  OK=2  MISSING=8  OUTDATED=1  ERROR=6

# JSON output (for script consumption)
python scripts/tools.py check --json

# Dry-run install (see what would be installed, without installing)
python scripts/tools.py install --all
# Output:
# Will install: ruff, mypy, vulture, ...
# Use --yes to proceed

# Actually install all missing items
python scripts/tools.py install --all --yes

# Install a single tool
python scripts/tools.py install ruff --yes

# Re-check after installing
python scripts/tools.py check
```

## Cross-platform

| Platform | Detection | Package install priority |
|---|---|---|
| Linux | `which` + `subprocess --version` | `uv pip install --system` (Debian typing_extensions compatibility) → `apt-get install` |
| macOS | same as Linux | `brew install` → `uv pip install --system` |
| Windows | same as Linux | `pip install --user` → `winget install` |

Adding a tool for a new platform: edit the `TOOLS` list in `scripts/tools.py` and add an `install_cmd_<platform>` field.

## 14 hard constraints (common across sub-workflows)

1. **Zero new dependencies (YAGNI)**: do not install tools for hypothetical scenarios (do not pre-install vue-improve tools unless the user says they will be used).
2. **Commit granularity**: env changes usually stay out of git (live config iron rule); use a separate work-note.
3. **Default rollback**: **install is irreversible** — strong YAGNI + dry-run first.
4. **Dead code**: not applicable (the script itself).
5. **TDD**: not applicable.
6. **Do not break CI**: run `check` after install to verify.
7. **prod lock**: never touch the prod env; never install tools for the user without asking.
8. **Prefer absence over fabrication**: detection failure = genuinely missing; never pretend it is installed.
9. **DB**: not applicable (this skill deletes no DB).
10. **Minimal sample before batch**: run `check` once through before `install --all`.
11. **4 independent steps for daemons**: after install, verify independently with `which` + `--version` (no chained &&).
12. **Buffer ownership**: not applicable.
13. **Hashed artifact sync**: not applicable (the toolchain has no hashed builds).
14. **Deploy verification of actual liveness**: `check` printing OK = genuinely installed, not merely a script exit 0.

## Related

- `/repo-medic` — meta entry point
- `/py-improve` — primary consumer (ruff/mypy/codegraph)
- `/doc-reorg` — consumer (rg/tree)
- `/db-tweak` — consumer (psql)
- `/vue-improve` — consumer (node + vite project-local)

## Repository

github.com/ebziw/repo-medic — Apache-2.0. The manifest lives in `scripts/tools.py`; edit the `TOOLS` list to add new tools.

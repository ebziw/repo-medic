# Code Refactor Subflow (project-doctor sub-workflow)

> Trigger: the user says "code refactor" / "god-fn splitting" / "dead code cleanup" / "duplicate method merging" / "architecture optimization"
> Scope: code layer only (`.py` / `.go` / `.ts` / `.rs`); do not touch directory structure / docs
> Order: designed by the user (2026-08-04) — lock behavior first → audit → design → plan → multi-agent execution → cleanup → doc sync

## Ground rules: do not interrupt the user (2026-08-05)

Default behaviors / explicit authorization / conflict-resolution rules (performance vs readability → readability wins; YAGNI vs future extension → YAGNI wins; abstraction vs directness → directness wins; stdlib vs installed library → stdlib wins) **all live in SKILL.md §default behaviors + explicit authorization, not repeated here**.

No confirmation inside a phase, no confirmation at phase boundaries; **only the final plan before Phase 12** is output once before execution (based on the plan produced by 9-11), after which execution proceeds automatically.

> For the toolchain degradation order (`codegraph MCP → CLI → grep fallback`), see Phase 1.

## Contents

1. [Phase 0: pre-flight](#phase-0-pre-flight)
2. [Phase 1: codegraph index build](#phase-1-codegraph-index-build)
3. [Phase 2: Read the code](#phase-2-read-the-code)
4. [Phase 3: TDD safety net](#phase-3-tdd-safety-net)
5. [Phase 4: /code-review audit](#phase-4-code-review-audit)
6. [Phase 5: Decompose god functions](#phase-5-decompose-god-functions)
7. [Phase 6: Merge shared methods](#phase-6-merge-shared-methods)
8. [Phase 7: Merge dicts + resolve conflicts](#phase-7-merge-dicts--resolve-conflicts)
9. [Phase 8: improve-codebase-architecture architecture optimization](#phase-8-improve-codebase-architecture-architecture-optimization)
10. [Phase 9: writing-plans implementation plan](#phase-9-writing-plans-implementation-plan)
11. [Phase 10: /ponytail-audit plan subtraction](#phase-10-ponytail-audit-plan-subtraction)
12. [Phase 11: plan-eng-review plan review](#phase-11-plan-eng-review-plan-review)
13. [Phase 12: Multi-subagent execution](#phase-12-multi-subagent-execution)
14. [Phase 13: Remove dead code](#phase-13-remove-dead-code)
15. [Cross-cutting: silent-swallow scan (P0)](#cross-cutting-silent-swallow-scan-p0-independent-of-the-phase-system)
16. [Phase 14: Delete dead files](#phase-14-delete-dead-files)
17. [Phase 15: Update design docs + code comments](#phase-15-update-design-docs--code-comments)
18. [Phase 16: Success metrics evaluation](#phase-16-success-metrics-evaluation)

---

## Phase 0: pre-flight

> **Before invoking**, replace the placeholders: `${REPO_ROOT}` `${BACKUP_BIN}` `${BACKUP_ROOT}` `${PROJECT_NAME}` (see SKILL.md §placeholder conventions). Running without replacing them errors out. After replacement, run once to confirm no residual `${`.

```bash
# backup + tag (timestamped, prevents tag collisions on repeated same-day runs)
git tag project-doctor-code-baseline-$(date -u +%Y-%m-%d-%H%M%S)
${BACKUP_BIN} ${REPO_ROOT} ${BACKUP_ROOT}/${PROJECT_NAME}/code-$(date -u +%Y-%m-%d)/
```

**Optional**: for large-scale refactors, isolate in a git worktree (`superpowers:using-git-worktrees`) and merge after completion, keeping the main branch unpolluted.

---

## Phase 1: codegraph index build

**Toolchain degradation** (single authority; the summary at the top is not repeated):

```
[1] MCP codegraph_explore (preferred, call it in conversation; v1.5.0 installed locally)
    ↓ unavailable (not registered in mcp)
[2] codegraph CLI (shell)
    ↓ unavailable (not installed / Kylin native build fail)
[3] grep + rg manual indexing (fallback, loses the call graph)
```

A `.codegraph/` directory present = index built; prefer calling the MCP tools directly (in Claude conversation). Absent → run `codegraph init` or `codegraph build`.

**.codegraph/ existence check** (automatic, non-interrupting):

```bash
# .codegraph/ at the repo root → query directly with MCP tools
# none → run codegraph init (one-time)
[ -d .codegraph ] && echo "INDEXED" || codegraph init -i
```

**[1] MCP tools** (called in the Claude Code conversation, recommended):

```
codegraph_explore(query="how does X work", session_id="...")
codegraph_explore(query="<fn_name>")
codegraph_explore(query="<file_name>")
```

Returns: symbol source + call paths + blast radius (sub-millisecond, already Read). **This tool is Read-equivalent** — Claude can Edit directly from the result without Reading the source file again.

**[2] CLI tools** (shell):

```bash
# build/update the graph (one-time; incremental on by default)
codegraph build
# project structure overview (hottest files = candidate hotspots)
codegraph map --limit 30
# locate symbols
codegraph where <name>
codegraph context <name> -T       # source + dependencies + callers
codegraph fn-impact <name> -T     # impact scope
codegraph diff-impact --staged -T # staged change impact
```

**[3] Fallback** (codegraph not installable / Kylin native build failure / cross-machine):

```bash
# function index
rg -n '^(func|def|class) ' src/ | wc -l          # scale
rg -n '(elif|case|switch|&&|\|\|)' src/ | wc -l  # rough complexity signal
# reference count
rg -n "<name>" src/ tests/ | wc -l              # candidate references
```

**Degradation losses**:
- No automatic call-graph traversal → dead-code checks fall back to repo-wide reference counting
- No blast radius → Phase 12 multi-agent execution needs more manual dependency checks
- Function/call paths rely entirely on manual reasoning

**deliverable**: function/module index (feeds Phase 2 code reading + Phase 5 locating + the Phase 13 dead-code 7 steps).

---

## Phase 2: Read the code

Read the project structure + core files and understand:
- layering / module boundaries / data flow
- each module's responsibility (1 sentence)
- note suspicious spots as they appear (god functions / duplicates / dead code / hardcoding) for the Phase 4 roll-up

```bash
# function index (Phase 1 output) + rough complexity ranking
rg -n '^(func|def|class) ' src/ | wc -l          # scale
rg -n '(elif|case|switch|&&|\|\|)' src/ | wc -l  # rough complexity signal
```

**deliverable**: `docs/audit/<date>-code-reorg.md` code map + suspicious-spot notes.

---

## Phase 3: TDD safety net

**Purpose**: lock current behavior before refactoring so later changes have verifiable regression. **Build the net before touching anything.**

```bash
Skill: test-driven-development
```

**TDD modes** (this pipeline is refactor-centric → mostly Characterization):

| Scenario | Mode | Verification |
|---|---|---|
| Refactoring existing behavior (extract/rename) | Characterization: write passing tests for current behavior | old and new behavior byte-identical |
| New feature / bug fix (found in audit) | Red-Green: failing → implement → passing → refactor | red → green → still green |
| Pure deletion (cleanup stage) | Structural: grep 0 callers + framework registration checks | all 0 on the 7-step checklist |
| Rename / move (cross-module) | Regression: full test + lint + type-check | all green + 0 reference leaks |

**deliverable**: critical-path behavior tests all green (baseline before and after changes).

---

## Phase 4: /code-review audit

**Purpose**: find every point needing change and form the issue list (drives the design steps in 5-8).

```bash
Skill: code-review
# output: issue list sorted by severity (bugs / smells / over-engineering / dead code)
```

**deliverable**: `docs/audit/<date>-code-reorg.md` issue list, each entry with file:line + suggested action, tagged by owner:
- → Phase 5 (god functions)
- → Phase 6 (duplicate methods)
- → Phase 7 (dict conflicts)
- → Phase 8 (architecture)
- → Phase 13/14 (dead code/files)

> **Degradation when the skill is missing**: without code-review → Claude self-checks: go through boundary conditions / failure paths / duplicates / dead code / over-engineering item by item.

---

## Phase 5: Decompose god functions

Pick god-fn candidates from the Phase 4 list (high cyclomatic / many lines) and locate each split point one by one.

```bash
codegraph context "<fn_name>" -T   # source + dependencies + callers
codegraph fn-impact "<fn_name>" -T  # impact scope
```

**Order** (low risk → high risk):
| Step | Action | Risk |
|---|---|---|
| 5a | Pure function split (stateless) | Low |
| 5b | Split with mutable state (State dataclass + integration test) | High |

**1 commit per step**:
```
refactor(<module>): split <fn>
- cyclomatic: <N> → <M>
- tests: <file>:<line> guards behavior
```

> ⚠️ **This step is "identify + design"**: actual code changes go to Phase 12 multi-agent execution. For a single-agent small refactor, edit directly inside the net. **A post-split call chain deeper than 3 levels with no benefit → do not split (over-engineering signal).**

---

## Phase 6: Merge shared methods

Pick duplicate methods from the Phase 4 list (one logic, multiple implementations).

**Identify**: multiple hits for `rg -n '<pattern>' src/` + similar function bodies → candidate.

**Principles**:
- Same logic → 1 implementation, migrate all callers
- Differences only in signature/boundaries → abstract the common part + parameterize the differences
- Uncertain whether truly duplicate (similar but semantically different) → follow the "do not interrupt" decision table: lowest risk = do not merge (default); genuine ambiguity = fall back to asking

**deliverable**: duplicate-method list + merge plan (feeds the Phase 9 plan).

---

## Phase 7: Merge dicts + resolve conflicts

Pick duplicate/contradictory dict definitions from the Phase 4 list. Full method: `@references/dict-dedup.md:1`.

**4 problem categories**:
| Type | Definition | Handling |
|---|---|---|
| DUPLICATE | values/structure fully identical | auto-merge: keep 1 authoritative source, re-export elsewhere |
| CONFLICT | same-name field with differing values | **CONFLICT requires a user decision** (?)— high risk (business numbers); fall back to stopping and asking |
| STALE | outdated copy with no callers | delete + git rm |
| REVERSE-MISSING | a→b exists, b→a missing | add the reverse dict |

**detect**:
```bash
# candidates + fingerprint clustering (see dict-dedup.md steps 1-2)
grep -rnE '^\s*[A-Z][A-Z_0-9]+\s*[:=]\s*[\{\[]' src/ --include="*.py"
```

> **CONFLICT handling** (the only fall-back-and-ask scenario): ground-truth identification > auto-merge. The commit message includes `decided: A is ground truth, B is a typo`.

---

## Phase 8: improve-codebase-architecture architecture optimization

Pick architecture-level issues from the Phase 4 list (coupling / unclear layering / tangled dependencies).

```bash
Skill: improve-codebase-architecture
```

**deliverable**: architecture-optimization recommendation list (decoupling / layering / boundaries) feeding the Phase 9 plan.

---

## Phase 9: writing-plans implementation plan

Consolidate all Phase 4-8 findings into an **executable plan** — large-scale refactoring requires a plan before execution.

```bash
Skill: superpowers:writing-plans
```

**Plan requirements**:
- Each step: what changes (file:line) / verification (test names / lint) / rollback point
- Order: low risk → high risk, each step independently revertible
- Spell out which steps can run in parallel (for multi-agent execution)

**deliverable**: `<project>/plans/<date>-code-reorg.md`

---

## Phase 10: /ponytail-audit plan subtraction

Run a subtraction audit on the **plan** — cut over-engineering / needless abstraction / fake-requirement steps.

```bash
Skill: ponytail-audit
# per plan step, output: <tag> <what to cut>. <replacement>. [plan-step]
# tags: delete / stdlib / native / yagni / shrink
```

**Apply**: feed the audit results straight back into the plan (drop steps / simplify / downgrade); do not execute the original plan.

> **Degradation when the skill is missing**: Claude self-checks — for each step ask "which already-occurred problem is this step for?" No answer → delete it.

---

## Phase 11: plan-eng-review plan review

Run an engineering review of the plan; adjust it per the recommendations.

```bash
Skill: plan-eng-review
```

**Review focus**: boundary conditions / failure paths / performance impact / test coverage / rollback plan.

**Conflict resolution** (when multiple reviews disagree):
1. Performance vs readability: readability wins (measure perf later)
2. YAGNI vs future extension: YAGNI wins (add it when needed)
3. Abstraction vs directness: directness wins (1 impl = fake seam)
4. stdlib vs installed library: stdlib wins (unless the installed library is clearly better)

**deliverable**: finalized plan (basis for Phase 12 execution).

---

## Phase 12: Multi-subagent execution

**Before execution**: output the final plan (1 paragraph, from the Phase 9-11 output) — no further confirmation; run it directly.

Dispatch execution per the finalized plan; run independent steps in parallel.

```bash
Skill: superpowers:subagent-driven-development
```

**Rules**:
- Independent steps → parallel subagents (worktree isolation to avoid file conflicts)
- Dependent steps → run sequentially
- After each step, run the corresponding tests (Phase 3 net + newly added)
- 1 commit per step, independently revertible
- Conflicts (concurrent edits to the same file) → serialize, or merge then rebase once

---

## Phase 13: Remove dead code

After refactoring, remove dead code (splitting/merging can produce new dead code). **Dead-code 7-step checklist** (0-caller grep = candidate signal, not proof):

| # | Check | Command |
|---|---|---|
| 1 | codegraph static references | `codegraph fn-impact "<name>"` (or rg repo-wide) |
| 2 | text/config/manifest search | `rg -n "<name>" --glob '*.{toml,yaml,yml,json,ini,cfg}'` |
| 3 | framework registration points (CLI entry / decorator / router / signal) | `rg "@app.route|@pytest.fixture|@click.command"` |
| 4 | public API / export check | `rg "^__all__"` / `__init__.py` re-exports |
| 5 | dynamic calls (getattr / importlib / eval) | `rg "getattr|importlib|eval\("` |
| 6 | tests + generated code | search `tests/` `build/` `dist/` `*_pb2.py` |
| 7 | confirm external API exposure | list import/export sources → internal = delete; external = fall back to asking |

**Cleanup**: all 7 steps 0 → run the cross-cutting silent-swallow scan below → delete + commit.

---

## Cross-cutting: silent-swallow scan (P0, independent of the phase system)

> **Belongs to no phase** — across the whole Code Subflow (Phase 5-6 splitting / Phase 12 execution / Phase 13 cleanup / any Edit), **run it immediately after every file change**; scan and fix on the spot. Scanning only at the end of a phase = missing the swallow points introduced by splitting.
> Scan for silent-swallow hazards in **changed functions and their call chains**. Not just deleted functions — also modified functions and the upstream/downstream of split functions.

**Scan scope**: god functions and helpers split in Phase 5-6 / call chains around dead code cleaned in Phase 13 / every file touched by Edit.

**Scan command**: same as `logging-observability.md` Phase 1.1 (3 greps, single source `@references/logging-observability.md:1`); not rewritten or duplicated here. Automation: `scripts/silent_swallow.py` (Phase 13.1 + 13.2 context-aware filtering).

**Judgment criteria**: the 4-pattern verdict table + 4 pass conditions live only in `@references/code-review-checklist.md:1` (no-silent-swallow); not duplicated here.

**Fix template**:

```python
# before fix (silent swallow)
except Exception:
    pass

# after fix (observed)
except Exception as _e:
    _task_log(task_id, f'xxx failed: {_e}', level='WARN', stage='pipeline')
```

**Why**: code reorganization is the best moment to surface hidden hazards. Nobody looks at this code normally; fixing it while reorganizing = clearing technical debt to zero.

**deliverable**: `docs/audit/<date>-code-reorg.md` includes the silent-swallow fix list (file:line + before + after).

---

## Phase 14: Delete dead files

Delete whole dead files with 0 callers (dead files), distinct from the dead functions of Phase 13.

```bash
# candidates: 0 referenced definitions in the file + 0 imports
rg -l "import.*from" src/ | xargs rg -l "def |class |func " | while read f; do
  base=$(basename "$f")
  refs=$(rg -l "import.*${base%.*}|from.*${base%.*}" src/ tests/ 2>/dev/null | wc -l)
  [ "$refs" -le 1 ] && echo "CANDIDATE: $f"
done
```

**Rules**:
- 0 cross-file references + not an external API → delete + `git rm`
- External API / depended on externally → go through Phase 13 step 7 user confirmation
- Before deleting, confirm the file is not on a `build/` `dist/` reference chain

---

## Phase 15: Update design docs + code comments

Post-refactor doc/comment sync — reflect the **latest code**.

**Comments** (required for key methods):
```python
def process_payment(order_id: str, amount: Decimal) -> PaymentResult:
    """Process a payment request and return the payment result.

    Args:
        order_id: order ID (UUID-format string)
        amount: payment amount, 2-decimal precision

    Returns:
        PaymentResult: {success: bool, transaction_id: str?, error: str?}

    Side effects:
        - writes the payment_log table
        - calls the third-party payment API (retryable 3 times)

    Caller:
        _checkout, _retry_payment
    """
```

**Doc consistency checks** (env vars / systemd / ports):
```bash
# 5.1 code env vars → env.md (pick one by project language)
# Python
grep -roPh 'os\.environ\.get\(["\x27]\K[A-Z_][A-Z_0-9]+' src/ | sort -u > /tmp/code_vars.txt
# Go
grep -roPh 'os\.Getenv\(["\x27]\K[A-Z_][A-Z_0-9]+' src/ | sort -u > /tmp/code_vars.txt
# TypeScript / Node
grep -roP 'process\.env\.[A-Z_][A-Z_0-9]+' src/ | grep -oP 'env\.\K[A-Z_]+' | sort -u > /tmp/code_vars.txt
# others → manual: rg -noE '[A-Z][A-Z_0-9]{2,}' src/ then filter by hand
grep -oP '\| \`[A-Z_]+\`' env.md | tr -d '|`' | sort -u > /tmp/doc_vars.txt
diff /tmp/code_vars.txt /tmp/doc_vars.txt

# 5.2 systemd units vs env.md (Linux only)
ls ~/.config/systemd/user/*.service 2>/dev/null | awk -F/ '{print $NF}' | sort -u > /tmp/units.txt
grep -oP '[a-z]+-[a-z-]+\.service' env.md deploy.md 2>/dev/null | sort -u > /tmp/doc_units.txt
diff /tmp/units.txt /tmp/doc_units.txt

# 5.3 ports vs docs
grep -rnP '127\.0\.0\.1:\d+' src/ deploy/ 2>/dev/null | grep -oP ':\d+' | sort -u > /tmp/ports.txt
grep -oP '\|\s*\d+\s*\|' env.md | grep -oP '\d+' | sort -u > /tmp/doc_ports.txt
diff /tmp/ports.txt /tmp/doc_ports.txt

# 5.4 doc-referenced file existence
grep -rn "docs/[a-zA-Z_-]*\.md" docs/ 2>/dev/null | grep -oP 'docs/[a-zA-Z_-]+\.md' | while read f; do
  [ ! -f "$f" ] && echo "BROKEN: $f"
done
```

**Fix**: code missing an env var → add it in config.py + sync env.md; doc missing a unit/port → add it to env.md; BROKEN → fix/delete.

---

## Phase 16: Success metrics evaluation

**How to judge whether it was worth it once done** (write results into the audit report):

| Metric | Target |
|---|---|
| cyclomatic reduction | core methods < 60% of original after the god-fn split |
| dead code removed | all 0 callers on the 7-step checklist |
| duplicates merged | 1 implementation per logic |
| tests | all green before and after, no tests deleted |
| comments | key-method ratio ≥ 0.3 (heuristic) |

**Signs it is not worth it** (stop or roll back):
- post-split call chain deeper than 3 levels with no benefit
- performance regressed without a readability gain
- the deleted "dead code" was actually referenced dynamically (step 7 was missed)

---

## Phase 16.5: Pre-merge CR (runs automatically at the end of the Code Subflow, P0)

**Full rules**: `@references/code-review-checklist.md:1` (no-silent-swallow 4 pass conditions / Edit-Read pairing / routing grep / deploy verification).

**Mandatory checks** (specific to the code-refactor scenario):
- [ ] pre-merge CR script runs clean (0 bare except hits) — script template in the verification-scripts section of `code-review-checklist.md`; write it to `scripts/` when needed
- [ ] `scripts/reorg_drift.py` (mandatory after import changes / module deletion) — 0 residual references
- [ ] no new `except: pass` / `except Exception: return default` in files changed this round
- [ ] no duck-typing silent fallback in helpers (`except AttributeError` default-fallback pattern)

**Design**: integrating Code Review here instead of keeping it a standalone subflow = the user need not actively know to run it. Full Reorg (runbook) also depends on this phase (see runbook Phase 6).

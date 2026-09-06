# Code Review Subflow (project-doctor sub-workflow)

> Trigger: the user says "code review" / "pre-merge check" / "CR checklist" / "silent-swallow detection"
> Scope: the pre-merge, mechanically checkable rule set — rely on the checklist, not on feel
> **Core principle**: rules must be mechanically decidable (pass/fail), not "senior engineer intuition".

## Contents

1. [no-silent-swallow (P0)](#no-silent-swallow-p0)
2. [Edit-Read pairing (P1)](#edit-read-pairing-p1)
3. [Routing/config grep (P0)](#routingconfig-grep-p0)
4. [Deploy verification (P1)](#deploy-verification-p1)
5. [LLM hard rules (P1)](#llm-hard-rules-p1)
6. [References/data (P2)](#referencesdata-p2)
7. [Verification scripts](#verification-scripts)

---

## no-silent-swallow (P0)

**Severity**: error (blocks merge)

Every `except Exception:` / `except <specific exception>:` block must satisfy one of the following conditions, otherwise FAIL:

| # | Pass condition | How to identify |
|---|---|---|
| 1 | the except body logs at WARN/ERROR | `_task_log(..., level='WARN')` / `logger.error(...)` / `logger.exception(...)` |
| 2 | explicit re-raise | `raise` / `raise SomeException(...)` |
| 3 | nested try: inner logs, outer pass exists to keep the inner from blowing up | outer `except: pass` wrapping an inner `try: _task_log(...) except: pass` |
| 4 | the except body contains `_silent_fail(...)` or `bump_counter("fail.xxx")` | the call itself counts as observed |

**Failure patterns (any one = FAIL)**:

```python
# ❌ fully silent
except Exception:
    pass

# ❌ silent fallback, no log
except Exception as e:
    return ""

# ❌ silent assignment, no log
except Exception:
    _refs_rows = []

# ❌ comment in place of observation
except Exception:
    # failure does not block
    return None
```

**Good examples (PASS)**:

```python
# ✅ has log + fallback
except Exception as e:
    _task_log(task_id, f'refs_rows load failed: {e}', level='WARN', stage='pipeline')
    _refs_rows = []

# ✅ nested log (outer pass protects)
except Exception:
    try:
        _task_log(...)
    except Exception:
        pass

# ✅ explicit re-raise
except Exception:
    raise

# ✅ already recorded (_silent_fail)
except Exception:
    try:
        _silent_fail(task_id, 'event', 'reason')
    except Exception:
        pass
```

**Mechanical check commands**:

```bash
# find all bare except Exception: pass (the most dangerous)
grep -rnE "except\s+Exception\s*:\s*$" ${REPO_ROOT}/ --include="*.py" -A1 | grep -B1 "^\s*pass\s*$"

# find all except Exception: (regardless of what follows)
grep -rnE "except\s+Exception\s*:\s*$" ${REPO_ROOT}/ --include="*.py" -A3

# find all except: pass (broader)
grep -rnE "except\s*:\s*$" ${REPO_ROOT}/ --include="*.py" -A1 | grep -B1 "^\s*pass\s*$"
```

**Judgment**: each hit must be manually confirmed against pass conditions 1-4. Not satisfied → FAIL.

---

## Edit-Read pairing (P1)

**Rule**: the Edit tool silently fails on files that were not Read (reports success without actually changing anything).

**Checks**:
- Before every Edit call, the same file must already be Read (same session context)
- After Edit, grep immediately to verify the change really landed
- After cp-syncing across environments, verify consistency with md5sum

**Historical incidents**: `main.py` router / `_call_llm.py` / `stage_search.py` / `vite.config.js` — silent fail left the user seeing no effect.

---

## Generic patterns (apply to any project)

**Rule**: before changing routing/config, grep all copies (multi-instance hardcoding is a CONFLICT source); when docs contradict data, trust the data and fix the docs on the spot.

**Deploy verification (P1)**:
- [ ] commit first, then git pull (a dirty tree gets silently wiped by deploy)
- [ ] after deploy, verify the PID changed + deployed_at is fresh (`curl /api/build-check` or equivalent)
- [ ] after cp, restart the user service (worker/FastAPI resident processes)
- [ ] `systemctl --user is-active <svc>` confirms active

---

## Frontend (JS/TS) mechanical rules (P1)

> Trigger: the diff contains `.vue/.js/.jsx/.ts/.tsx`. The first 8 rules are grep-decidable (expanded in v0.7.9); the last 10 are manual spot checks.
> All generalized from a real-world pdf.js v3 selector-scope incident (full case study archived separately).
> Replace the path `${REPO_ROOT}/frontend/src/` with the project's frontend source directory (skip the whole section if there is none).

**grep-decidable**:

```bash
# 1. ArrayBuffer passed straight to a library with no copy (postMessage / getDocument({data: x}) transfers it → cache empty)
grep -rnE "getDocument\(\{ ?data: [a-zA-Z_]+|postMessage\([a-zA-Z_]+\)" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# pass condition: a .slice(0) copy is passed, or the original buffer is consumed once and never reused

# 2. Assigning to a ref that the watchEffect/computed body itself depends on (infinite loop → UI freeze)
#    manual check: the watchEffect body assigns srcDoc.value = ... directly (srcDoc is read by the watchEffect)
grep -rnE "watchEffect" "${REPO_ROOT}/frontend/src/" 2>/dev/null

# 3. Are the let/const referenced by immediate callbacks (immediate:true / computed getters) declared first
grep -rnE "immediate: ?true" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# manual check: a variable declared after the watch registration line but referenced by the callback → TDZ

# 4. One-shot consumption flag whose reset depends on watch/event (leak → swallows later behavior)
grep -rnE "_skip[A-Za-z]+ ?= ?true|_pending[A-Za-z]* ?= ?true" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# manual check: is the flag reset unconditionally, or waiting on a watch fire (waiting = leak)
```

**v0.7.9 additions (grep-decidable)**:

```bash
# 5. Fixed setTimeout delay as an "A before B" ordering guarantee (reverses on slow networks — replace with a completion-promise gate)
grep -rnE "setTimeout\([a-zA-Z]+, *[0-9]{2,4}\)" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# manual check: does the delay span an async ordering scenario (start after something loads)? yes → switch to a real completion signal

# 6. Writing shared state after await (.value = / setX) with no seq/token check → out-of-order late overwrite
grep -rnE "await .*\n.*\.value = " "${REPO_ROOT}/frontend/src/" 2>/dev/null  # multi-line needs -U
# manual check: before a slow async result writes a shared reference, is there an "I'm still latest" check (token/seq/old-value comparison)

# 7. Global serial lock (promise chain) with no watchdog → a fn inside the lock that never settles = permanent freeze
grep -rnE "Promise\.resolve\(\)\s*$|_withRenderLock|_renderQ|_lock = Promise" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# manual check: can a fn inside the chained lock never settle (depends on a killable resource like a worker/connection)?
#   yes → the trio: cancel before destroy + destroyed flag + Promise.race watchdog

# 8. Heavy resources (worker/connection) instantiated per operation → repeated download/handshake per operation
grep -rnE "new (PDFWorker|Worker)\(|createConnection|new Pool" "${REPO_ROOT}/frontend/src/" 2>/dev/null
# manual check: new inside a loop/per request? can a single shared instance + destroy-after-use discipline work?
```

**v0.7.9 additions (manual spot checks)**:

| # | Check | Counter-example |
|---|---|---|
| 9 | state flags (errorMsg/loading) cleared on every exit | cleared only in the failure branch; success/early-return paths leave residue → v-show hides forever = blank screen |
| 10 | batch warmup/concurrent requests capped (3-5 in flight) | forEach fires 18 fetches at once; the backend computes per request → saturates and slows every API |

**Manual spot checks (sample 5 per diff)**:

| # | Check | Counter-example |
|---|---|---|
| 5 | destructured/loop variable names do not collide with outer business variables | `const [srcDoc] = await ...` shadows the outer `srcDoc` ref |
| 6 | buffers handed to libraries are copied or single-use | after `getDocument({data: bytes})`, bytes is still reused by the cache |
| 7 | long-lived caches do not store library instances (docs/connections/workers) | `Map<pageNum, PDFDocumentProxy>` used as cache — should store bytes |
| 8 | pixel-verification detection logic self-tested first | blank check `rgb<250` ignores alpha → opaque white background misreports as empty |

**Mechanical verdicts**: #1 FAIL = passed non-copy straight through with the buffer reused; #2 FAIL = the watchEffect body writes a tracked ref; #3 FAIL = a later declaration referenced by an immediate callback; #4 FAIL = the flag has no unconditional reset point.

---

## Verification scripts

```bash
#!/bin/bash
# pre-merge mechanical checks (template: write the whole block to scripts/ when needed; naming per project)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== CR: no-silent-swallow ==="
BARE_EXCEPT=$(grep -rnE "except\s+Exception\s*:\s*$" "${REPO_ROOT}/backend/" --include="*.py" -A1 | grep -B1 "^\s*pass\s*$" | grep -c "except" || true)
if [ "$BARE_EXCEPT" -gt 0 ]; then
    echo "❌ FAIL: ${BARE_EXCEPT} bare except Exception: pass"
    grep -rnE "except\s+Exception\s*:\s*$" "${REPO_ROOT}/backend/" --include="*.py" -A1 | grep -B1 "^\s*pass\s*$"
    exit 1
fi
echo "✅ PASS: 0 bare except Exception: pass"

echo "=== CR: print in prod ==="
PRINT_PROD=$(grep -rnE "^\s*print\(" "${REPO_ROOT}/backend/" --include="*.py" | grep -v "/tests/" | grep -v "# " | wc -l || true)
if [ "$PRINT_PROD" -gt 0 ]; then
    echo "⚠️ WARNING: ${PRINT_PROD} print calls on prod paths"
    grep -rnE "^\s*print\(" "${REPO_ROOT}/backend/" --include="*.py" | grep -v "/tests/"
fi

echo "=== CR: undefined name (pyflakes) ==="
if command -v pyflakes &>/dev/null; then
    pyflakes "${REPO_ROOT}/backend/" 2>&1 | grep -E "undefined name" | head -10 || echo "✅ PASS: pyflakes 0 undefined"
fi

echo "=== CR: except candidates needing human judgment (beyond the 4 pass conditions) ==="
# find except blocks within 3 lines: no WARN/ERROR log + no raise + no _silent_fail recording candidates
grep -rnE "except\s+(Exception|[A-Za-z]+Error)\s*(as\s+\w+)?\s*:" "${REPO_ROOT}/backend/" --include="*.py" -A3 \
  | awk '/^[^:]+:[0-9]+[:-]except/{file=$0; body=""; n=0}
         /^[^:]+:[0-9]+[:-][[:space:]]*(pass|continue|return|#|\s*$)/{body=body" "$0; n++}
         n>=3 && body !~ /logger\.(error|warning|exception)|raise|_silent_fail|bump_counter/{print "🔴 CANDIDATE: " file " → check against the 4 conditions (log/raise/_silent_fail/nested protection)"}' || echo "✅ no candidates"

echo "=== CR: all checks passed ==="
```

---

## Relationship to logging-observability

> The logging-observability sub-workflow (Phases 1-5) is "fix" — detect + repair swallowed errors.
> The code review checklist is "prevent" — intercept new swallowed errors before merge.
>
> The two complement each other: logging-observability pays down historical debt, code review keeps new debt from appearing.

---

## Known pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Rules too loose | "it depends" becomes "always passes" | rules must be binary pass/fail; no "it depends" |
| Too many rules | the checklist becomes a burden nobody uses | keep ≤ 10 P0 rules; sample the rest at P1/P2 |
| Mechanical false positives | nested try has inner logging but is still judged FAIL | pass condition 3 explicitly covers the nested pattern |
| Stale rules | code evolves but the rules do not | update rules immediately after every pitfall (trigger an update event) |
| Deleting a function without cleaning `__all__` | `from ._module import *` raises AttributeError | after deleting a function, grep `__all__` and clean references in step |
| Deleting a function without cleaning the import chain | A is deleted but B does `from A import X` → ImportError | grep the whole repo to confirm 0 callers before deleting |
| **Variable/method name shadowing** | same-name family bug: one variable name assigned twice by APIs from different sources; the 2nd silently overwrites the 1st result → business decisions based on the stale value fail silently (e.g. the account-frozen check cost 3h; `import datetime` shadowed by `from datetime import datetime`, same family; case source: arbit, projects/arbit.md) | within one function **forbid re-assigning the same variable name from different-source APIs**; the 2nd call's result must go into a new variable (`balance_kc = ...`); type annotations do not save this (types too wide) |
| **shell=True command-line concatenation** | external data (user input/URLs/titles) concatenated into `subprocess.run(f"...{data}...")` triggers bandit B602, equivalent to remote code execution | always `shell=False` + array args; when the shell is truly required, go through a stdin pipe (`subprocess.run(cmd, shell=True, input="...sql...\n")`) — SQL/data via stdin, never the command line |
| **stdin pipes + nested quote escaping** | `ssh "... mysql ... '{sql}'"` stacks quote layers; in `-e "...{sql}..."` ssh and mysql each strip a layer of quotes; git-bash strips one more | three stable patterns: ① scp the SQL file → feed mysql on the remote via `<` ② `printf sql | ssh ... mysql` (verifies the ssh stdin pipe works) ③ heredoc inside ssh (`cat <<SQL \| mysql`); **never build inner double quotes into `-e` on the Windows side** |
| **MCP tool output exceeds the token limit** | ruff_check's 588KB text + 1.2K-line JSON/MD header blows straight through the 200K cap; reports "result exceeds maximum allowed tokens", output lands in tool-results | MCP server design must split the flow: short results return directly, long results (≥10K lines / 200K chars) must land on disk; the main agent does not read the full text — **use python to tally rule distribution + path frequencies**, decide, then read targeted spots |
| **MCP server's own interface drift** | `mcp__python-refactor-local__bandit_scan` fails with `-f text` (bandit 1.9 renamed it to `-f txt`); other MCP servers' tool names/params change too | before every sweep, **probe the interface with 1 minimal help/text call**; on failure switch immediately to the local CLI (`python -m bandit -r ...`) as fallback instead of repeatedly calling MCP and wasting time |
| **In-process cache + config change without restart** | three yaml loaders all define `invalidate_cache()` but it is called 0 times; after adding members/changing mappings the old values stay in use | (follow the "config drift" rule) an in-process module-level dict cache also counts as config: restart via deploy.sh after every change; or watch mtime for automatic cache misses; add to the CR checklist: always check whether cache files have an invalidator |
| **Pyright pre-existing errors vs this round's** | legacy projects often carry many pre-existing Pyright errors (unresolvable side-effect imports / types for uninstalled packages) that silently mix into new errors, making "did I introduce this" hard to tell (arbit measured 39 pre-existing; case: projects/arbit.md) | run `pyright_check <file>` once before and once after changing a file; N before vs N after, the diff = this round's additions; only a 0 delta counts as "zero impact"; a delta > 0 must be reviewed item by item |
| **Helper type contract + silent fallback** | the helper's return type contradicts the docstring/caller assumption (returns a string, the caller indexes it as a dict) → silent business error or a cast crash | helpers must not duck-type + silently fall back: enforce `isinstance` + `raise TypeError` on the failure path; or defend at the caller with `isinstance(x, dict)` against degraded input; add to the CR checklist "is the helper's return type annotated in its docstring" |
| **README/docstring states the reverse of reality** | a comment says "0 = external" when it actually means "0 = counterparty account" (account semantics written backwards); the next 3h of debugging gets misled | before writing any "semantics/enum/constant explanation" comment, **grep the true source config file** once (`*.yaml` / DB schema / official doc); add to the CR checklist "spot-check 3 code semantic comments against config files" |
| **`.get(k, default)` silent fallback** | when the data source is wrong, `.get` returns the default; the caller does not error but behaves wrongly (e.g. a wrong NAV source returns 0 → the page displays a NAV of 0) | use `.get(k, default)` only where the key is genuinely optional; **required keys** should use `result[k]` so the explicit KeyError tells upstream immediately; in CR, distinguish these two kinds of dict access |

> Global deploy pitfalls such as systemd restart with an unchanged PID → single source, the SKILL.md known-pitfalls table; not duplicated here.

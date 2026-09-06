# Dict Dedup Subflow (project-doctor sub-workflow)

> Trigger: user says "dict dedup" / "dict consolidation" / "constant conflict" / "duplicate id definitions" / "dedup dictionary" / "unify error codes" / "scattered enums" / "merge duplicate definitions"
> Scope: dict/enum/constant definitions only (id:description / status / error_code / role / permission, etc.)
> Hazard: multiple contradictory definitions of the same id -> the program takes the wrong branch -> hard-to-trace bugs (no exception raised, only behavior drift)
> **Style**: ponytail minimalism. One home per dict; elsewhere only re-exports allowed. Conflict detection > auto-merge.

## 4-Category Problem Classification (core)

> Routing entry: the Dict Dedup Subflow row of the SKILL.md routing table. **Full definition = this document itself** — 4-category problem classification (table below) + Phase 0-5 detect/fix pipeline + YAGNI + known pitfalls.

| Category | Meaning | Handling |
|------|------|------|
| **DUPLICATE** | Multiple identical definitions (same value/structure) | Auto-merge: keep 1 authoritative copy, turn the others into imports / re-exports |
| **CONFLICT** | Same-named fields with different values (contradictory definitions) | **Stop and ask a human** — which one is the truth? Never auto-overwrite |
| **STALE** | Outdated copy with no callers (deletable) | Delete + matching `git rm` |
| **REVERSE-MISSING** | a→b exists but the b→a reverse lookup is missing (lookup tables often omit it) | Add the reverse dict, or standardize on bidict |

## Table of Contents

- [Phase 0: Quick Scan (30s)](#phase-0-quick-scan-30s)
1. [Phase 1: Dict Definition Scan](#phase-1-dict-definition-scan)
2. [Phase 2: generic 4-category detection pipeline](#phase-2-same-id-multi-source-detection-with-4-category-classification)
3. [Phase 3: Contradiction Detection + Conflict Report](#phase-3-contradiction-detection--conflict-report)
4. [Phase 4: Select Authoritative Source + Merge](#phase-4-select-authoritative-source--merge)
5. [Phase 5: Caller Migration + Verification](#phase-5-caller-migration--verification)
6. [Typical case: _LEVEL_CFG CONFLICT](dict-dedup-case-levelcfg.md)

---

## Phase 0: Quick Scan (30s)

> **80% of real cases are DUPLICATE + CONFLICT**; STALE/REVERSE-MISSING are the minority.
> Full Phase 1-2 requires an AST scan + whole-repo grep, which is slow. Run this first and review the list before deciding whether to deep-scan.

```bash
# 0.1 Find all module-level dict literals (one-line grep, no Python run)
grep -rnE '^\s*_*[A-Z][A-Z_0-9]+_*\s*[:=]\s*[\{\[]' ${REPO_ROOT}/ \
  --include="*.py" | grep -v test | sort -t: -k3 > /tmp/dict-snapshot.txt

# 0.2 Count + aggregate by dict name
awk -F: '{print $3}' /tmp/dict-snapshot.txt | sort | uniq -c | sort -rn | head -30
# Output:
#   8 _LEVEL_CFG          ← defined in 8 places? Something is wrong
#   3 _PRESET_DOMAIN_MAP
#   2 STAGES
#   1 _DEPTH_WHITELIST
```

**Interpretation**:

| Count | Meaning | Next step |
|---|---|---|
| **≥3 same-named copies** | Duplicates or conflicts guaranteed | Run Phase 2 detailed fingerprinting |
| **Exactly 2 same-named copies** | Could be DUPLICATE or CONFLICT | Run Phase 2 |
| **1 copy** | Single definition, skip | (unless callers are scattered) |

**When to use**:
- Asked "does X have duplicate definitions in the code" -> run 0.1+0.2 directly
- Before a full dict dedup run, use 0.2 to size the budget — 30+ sites: go slowly; under 10: merge fast
- CI gate: 0.2 output above threshold (e.g. 5 same-named copies) fails immediately

---

## Phase 1: Dict Definition Scan

**Goal**: find all id:description-style dicts / enums / constant definitions.

```bash
# 1.1 Python: find all Dict/Enum/constant definitions
grep -rnE '^\s*[A-Z][A-Z_0-9]+\s*[:=]' ${REPO_ROOT}/ --include="*.py" | grep -v test | head -50

# 1.2 Find where ERROR_CODE / STATUS / ROLE / PERMISSION names concentrate
find ${REPO_ROOT} -type f \( -name "*error*.py" -o -name "*status*.py" -o -name "*role*.py" -o -name "*permission*.py" -o -name "*enum*.py" -o -name "*constant*.py" \) -not -path '*/.git/*' | head

# 1.3 Go: find const blocks
grep -rnE '^\s*(const|var)\s+[A-Z][A-Z_]+\s*=' ${REPO_ROOT}/ --include="*.go" | head -30

# 1.4 Node/TS: find enum / const objects
grep -rnE 'export\s+(const|enum)\s+[A-Z][A-Z_]+' ${REPO_ROOT}/ --include="*.ts" --include="*.js" | head -30

# 1.5 Find constants with similar ID names scattered across files (e.g. USER_STATUS_ACTIVE defined in both a.py and b.py)
grep -rnE 'USER_(STATUS|ROLE)_[A-Z]+|ERROR_CODE_[A-Z_]+|ORDER_STATE_[A-Z]+' ${REPO_ROOT}/ --include="*.py" | head -50
```

**deliverable**: `docs/audit/<date>-dict-snapshot.md` listing every id namespace.

---

## Phase 2: Same-id Multi-source Detection (with 4-category classification)

**Core check**: the same id string defined in multiple places (especially with inconsistent descriptions/values). Cluster by fingerprint, then classify into the 4 categories.

### 2.1 Python: cluster by fingerprint (json.dumps sorted)

```bash
# 2.1.1 Find all module-level dict/set/list literals
grep -rnE '^\s*_*[A-Z][A-Z_0-9]+_*\s*[:=]\s*[\{\[]' ${REPO_ROOT}/ --include="*.py" | grep -v test | head -100
```

```python
# 2.1.2 fingerprint clustering + 4-category classification
python3 << 'PYEOF'
import ast, pathlib, json, collections

repo = pathlib.Path("${REPO_ROOT}")
by_name = collections.defaultdict(list)  # name -> [(file, line, fp, value)]

for py in repo.rglob("*.py"):
    if "test" in str(py) or "/.venv/" in str(py):
        continue
    try:
        src = py.read_text()
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not (isinstance(tgt, ast.Name) and tgt.id.isupper()):
                continue
            try:
                val = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue  # skip values that cannot be literal-evaluated (function calls, etc.)
            # convert dict/set to sorted JSON as the fingerprint (order-insensitive)
            if isinstance(val, (dict, set)):
                fp = json.dumps(val, sort_keys=True, ensure_ascii=False)
            else:
                fp = repr(val)
            by_name[tgt.id].append((str(py), node.lineno, fp, val))

# output the categories
for name, defs in by_name.items():
    if len(defs) <= 1:
        continue
    fps = {d[2] for d in defs}
    files = {d[0] for d in defs}
    if len(fps) == 1:
        # all definitions hold the same value -> DUPLICATE
        print(f"[DUPLICATE] {name} (value={fps.pop()[:80]}) in {len(defs)} places across {len(files)} files")
        for path, line, fp, val in defs:
            print(f"   {path}:{line}")
    elif len(fps) > 1:
        # values differ -> CONFLICT (must ask a human)
        print(f"[CONFLICT] {name}")
        for path, line, fp, val in defs:
            print(f"   {path}:{line} = {fp[:80]}")
PYEOF
```

### 2.2 STALE detection (outdated copies with no callers)

```bash
# 2.2.1 Find all dict literals, then check each one for imports / references
python3 << 'PYEOF'
import ast, pathlib, sys

repo = pathlib.Path("${REPO_ROOT}")
defined = set()  # every defined dict name

# find definitions
for py in repo.rglob("*.py"):
    if "test" in str(py) or "/.venv/" in str(py):
        continue
    try:
        tree = ast.parse(py.read_text())
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isupper():
                    defined.add(tgt.id)

# find references
referenced = set()
for py in repo.rglob("*.py"):
    try:
        src = py.read_text()
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            referenced.add(node.id)
        elif isinstance(node, ast.Attribute):
            base = node
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                referenced.add(base.id)

# STALE: defined but never referenced
stale = defined - referenced
for name in sorted(stale):
    if name.startswith("_"): continue
    print(f"[STALE] {name} (defined but not referenced)")
PYEOF
```

### 2.3 REVERSE-MISSING detection (a→b exists but b→a missing)

```python
# 2.3.1 Check whether each dict has a reverse lookup
python3 << 'PYEOF'
import ast, pathlib

repo = pathlib.Path("${REPO_ROOT}")
for py in repo.rglob("*.py"):
    if "test" in str(py) or "/.venv/" in str(py):
        continue
    try:
        tree = ast.parse(py.read_text())
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not (isinstance(tgt, ast.Name) and tgt.id.isupper()):
                continue
            try:
                val = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue
            if not isinstance(val, dict):
                continue
            # heuristic: dict name contains _MAP / _TO / _INDEX -> a reverse is expected
            if any(k in tgt.id for k in ("_MAP", "_TO_", "_INDEX", "_LOOKUP")):
                reverse = tgt.id + "_REVERSE"  # common naming
                # search the whole repo for whether the reverse exists
                # simplified: flag only, do not enforce
                keys_unique = len(set(str(v) for v in val.values())) == len(val)
                if keys_unique:
                    # values unique -> a reverse is worthwhile
                    print(f"[REVERSE-MISSING?] {tgt.id} at {py}:{node.lineno} (values unique, consider {reverse})")
PYEOF
```

**deliverable**: list of candidate duplicate ids + each definition location + 4-category classification (DUPLICATE/CONFLICT/STALE/REVERSE-MISSING).

---

## Phase 3: Contradiction Detection + Conflict Report

**Core**: whether the **values or descriptions** of the same id's multiple definitions agree.

```bash
# 3.1 Extract each id's "right-hand value" at every site (Python dict literals)
python3 << 'PYEOF'
import ast, pathlib, sys, collections

repo = pathlib.Path("${REPO_ROOT}")
dup_report = collections.defaultdict(list)

for py in repo.rglob("*.py"):
    if "test" in str(py) or "/.venv/" in str(py):
        continue
    try:
        tree = ast.parse(py.read_text())
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            # from typing import Final / ClassVar
            pass
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isupper():
                    try:
                        val = ast.unparse(node.value)
                        dup_report[tgt.id].append((str(py), node.lineno, val))
                    except Exception:
                        pass

# find the ones with differing values
for name, defs in dup_report.items():
    if len(defs) > 1:
        values = {d[2] for d in defs}
        if len(values) > 1:
            print(f"⚠ CONFLICT: {name}")
            for path, line, val in defs:
                print(f"   {path}:{line} = {val}")
        elif len(values) == 1 and len({d[0] for d in defs}) > 1:
            print(f"✓ DUPLICATE-OK: {name} = {values.pop()} (in {len(defs)} files)")
PYEOF
```

**Conflict grading**:

| Category | Description | Severity |
|------|------|--------|
| **CONFLICT (values differ)** | Same id, different values | 🔴 Critical — must merge |
| **DUPLICATE-OK (values identical)** | Same id, identical value, scattered | 🟡 Warning — merging recommended (DRY) |
| **LEGACY (deprecation marker present)** | Old version carrying the `_LEGACY` suffix | 🟢 OK — keep + annotate |

**Truth identification (mandatory for CONFLICT; never guessed by an algorithm)**:

A human/evidence must decide which CONFLICT side is the truth. Any heuristic (majority vote / most recent edit / longest fields) can be wrong.

| Evidence source | Usage | Weight |
|---------|------|------|
| **Code comments** | wording like "authoritative source" / "single entry point" / "single source of truth" | 🔴 Strong |
| **git log** | `git log -p <file>` shows which one is new and which one is legacy | 🔴 Strong |
| **File mtime** | `stat -c %y <file>` — the most recent timestamp wins | 🟡 Medium |
| **Reference count** | `grep -rn "<NAME>"` — the more referenced one is likelier the designed API | 🟡 Medium |
| **Import chain** | whoever is the source module (imported by many other modules) is the authority | 🟡 Medium |
| **Test coverage** | the copy covered by tests is likelier the designed contract; the untested copy is likelier a temporary duplicate | 🟢 Weak |

**Typical decision flow** (case `_LEVEL_CFG`):

1. `git log --follow backend/core/stages/_config.py` → newer mtime, gained a "single entry point" comment → 🔴 authoritative
2. `git log --follow backend/core/research_phases.py` → older mtime, untouched for a long time → old copy
3. `grep -rn "_LEVEL_CFG" backend/` → 4 import sites, 2 old 2 new, import chain inconsistent
4. **Decision**: keep `_config.py`, delete the `research_phases.py` copy, migrate old callers to the new import

**Why algorithmic decisions fail**:

| Automatic decision | Why it is wrong |
|---------|---------|
| "Majority vote" | Both 500 vs 300 sit in a plausible range; no way to know which side is wrong |
| "Most recent edit" | An admin's edit may reflect an operations adjustment, not a bug fix |
| "The longest one" | More fields does not mean more authoritative; the extras may be noise |
| An "authoritative source" marker | If no source is marked authoritative, the algorithm cannot know |

**Truth identification > auto-merge**. This case rested on four pieces of evidence — `commit message + file mtime + code comments + import chain` — not on an algorithmic guess.

**deliverable**: `docs/audit/<date>-dict-conflicts.md` containing:
- Critical conflict list (differing values)
- Warning duplicate list (identical values, scattered)
- Contradictory-definition decision (which one is authoritative)

---

## Phase 4: Select Authoritative Source + Merge

**Decision principles** (by priority):

1. **Official/external definitions** (HTTP status codes, ISO standards, protocol constants) → never change; reference directly, never inline
2. **Business-core dicts** (USER_ROLE / ORDER_STATE / ERROR_CODE) → centralize in a top-level `constants/` or `enums/` module
3. **Local dicts** (single-module internal state) → keep in the original file, but export explicitly via `__all__`
4. **Test fixtures** → do not merge; tests stay independent

**Execution steps**:

```bash
# 4.1 Create the authoritative directory
mkdir -p ${REPO_ROOT}/src/constants  # match the project layout, e.g. src/ for Python, pkg/ for Go

# 4.2 Write the authoritative definition (example user_role.py)
cat > ${REPO_ROOT}/src/constants/user_role.py << 'EOF'
"""User role constants. Single source of truth.

All other modules MUST import from here, never redefine.
"""
from enum import Enum

class UserRole(str, Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
EOF

# 4.3 Delete/edit the duplicate definitions elsewhere
# e.g. delete USER_ROLE_DICT in a.py and the local USER_ROLES definition in b.py
# replace with: from src.constants.user_role import UserRole

# 4.4 One merge, one commit
git add src/constants/
git rm <old definition file if deleting the whole file>
git commit -m "refactor(dict): consolidate <name> to src/constants/ (<date>)"
```

**Anti-patterns (do not do)**:
- ❌ Add `from constants import *` at every old definition site while keeping the old names — two sources still risk drift
- ❌ Replace enums with dataclasses — loses exhaustiveness checking
- ❌ Stuff every dict into one mega file — bloats the file; splitting by domain is better

---

## Phase 5: Caller Migration + Verification

**Caller migration**: point every reference at the old location to the new location.

```bash
# 5.1 Find callers
grep -rn "USER_ROLE_\|<OLD_NAME>" ${REPO_ROOT}/ --include="*.py" | grep -v "src/constants/"

# 5.2 Bulk replace (codemod or sed)
# e.g. rewrite every "from a import USER_ROLE_DICT" to "from src.constants.user_role import UserRole"
# then dict[key] -> UserRole(key)

# 5.3 Verify tests + lint
${TEST_RUNNER}
ruff check ${REPO_ROOT}/
mypy ${REPO_ROOT}/
```

**Done criteria**:
- `grep -rn "<OLD_NAME>"` 0 hits (docs/comments excepted)
- `grep -rnE "^\s*[A-Z][A-Z_0-9]+\s*=\s*["\x27]" ${REPO_ROOT}/ --include="*.py" | grep -v "src/constants/" | grep -v test` 0 hits (no scattered definitions)
- `grep -rnE "if .* in USER_ROLE_DICT" ${REPO_ROOT}/` — everything uses the new import
- ${TEST_RUNNER} all green
- type checker 0 errors

**Rollback**: follow generic hard constraint #3 (rsync backup + git revert)

---

## YAGNI Notes (zero upfront defense)

- ❌ Do not write a metaclass registry up front for "may add new statuses later"
- ❌ Do not make dict definitions dynamically loaded (unless the project already uses a plugin system)
- ❌ Do not add version numbers to ids across namespaces (e.g. USER_ROLE_V1_USER) — add versioning only when truly needed
- ✅ **Current state first**: merge exactly as many sites as exist; do not abstract ahead of imaginary requirements

---

## Known Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| `str` enum vs `int` enum chosen wrongly | DB stores int, code uses str, deserialization breaks | Use `str` enums for business dicts; protocol dicts (HTTP status) follow the original standard |
| Test fixtures still use the old dict literals | Tests break after the merge | grep the test files and migrate them in the same pass (tests may be edited) |
| Third-party enum forbids subclassing | Adding business methods fails | Do not subclass the third-party enum; wrap it in a local wrapper layer |
| Enum values contain special characters (spaces/hyphens) | Deserialization fails | Use ASCII alphanumerics + underscore only |
| The dict is also used in database migration scripts | DB and code drift apart | The single source for the dict = code; the DB uses a lookup table + migration to stay in sync |

---

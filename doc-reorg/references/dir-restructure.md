# Directory Restructure Subflow (project-doctor sub-workflow)

> Trigger: user says "directory restructure" / "organize directories" / "directory cleanup" / "git mv cleanup" / "reorganize directory" / "consolidate scripts" / "merge duplicate folder"
> Scope: directory structure only (git mv + script archiving + tmp cleanup); do not touch code logic / document content

## Table of contents

1. [Phase 0: pre-flight](#phase-0-pre-flight)
2. [Phase 1: Current directory snapshot + statistics](#phase-1-current-directory-snapshot--statistics)
3. [Phase 2: Script sorting (scripts/)](#phase-2-script-sorting-scripts)
4. [Phase 3: Temporary file archiving (tmp/)](#phase-3-temporary-file-archiving-tmp)
5. [Phase 4: Debug artifact cleanup](#phase-4-debug-artifact-cleanup)
6. [Phase 5: Duplicate directory merge](#phase-5-duplicate-directory-merge)
7. [Phase 6: Verification + archiving old paths](#phase-6-verification--archiving-old-paths)

---

## 🚨 CRITICAL — Iron Law

> **Never leave a half-split state, and no rushed hotfixes during a restructure.**
>
> A half-split state = industrial-scale disaster (Knight Capital 2012). **Every phase must be closed out (commit / revert / backup) before entering the next**.
>
> Rushing a hotfix during a restructure = the same disaster (FB BGP 2021). **No touching production during the reorg / no interrupting a phase / no mixing commits**.

---

## Phase 0: pre-flight

```bash
# File backup
mkdir -p ${BACKUP_ROOT}/${PROJECT_NAME}/dir-$(date -u +%Y-%m-%d)
${BACKUP_BIN} ${REPO_ROOT} ${BACKUP_ROOT}/${PROJECT_NAME}/dir-$(date -u +%Y-%m-%d)/

# git tag baseline
git tag ${SKILL_NAME}-baseline-$(date -u +%Y-%m-%d)
```

**5 dimensions balanced**: development rhythm / findability / git friendliness / human observability / type before domain.

---

## Phase 1: Current directory snapshot + statistics

**Purpose**: establish a baseline, quantify the "before" state.

```bash
# 1.1 Overview (directory count + file count + line count)
find ${REPO_ROOT} -type d -not -path '*/.git*' -not -path '*/node_modules*' -not -path '*/__pycache__*' -not -path '*/.venv*' | wc -l
find ${REPO_ROOT} -type f -not -path '*/.git*' -not -path '*/node_modules*' | wc -l

# 1.2 Count by extension
find ${REPO_ROOT} -type f -not -path '*/.git/*' | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20

# 1.3 List of large files (>1MB)
find ${REPO_ROOT} -type f -size +1M -not -path '*/.git/*' -exec ls -lh {} \; | awk '{print $5, $NF}'

# 1.4 Empty directories
find ${REPO_ROOT} -type d -empty -not -path '*/.git*'

# 1.5 Top-level scattered scripts (not inside ${SOURCE_DIRS})
find ${REPO_ROOT} -maxdepth 2 \( -name "*.sh" -o -name "*.py" \) | grep -v "${SOURCE_DIRS}" | head
```

**deliverable**: `docs/audit/<date>-dir-snapshot.md`

---

## Phase 2: Script sorting (scripts/)

**Rules**:

| Type | Path | Naming |
|------|------|------|
| Scattered reusable scripts | `scripts/<category>/<name>.<ext>` | kebab-case |
| Categories | deploy / maintenance / cron / utils | - |
| One-off scripts | `${REPO_ROOT}/.scratch/` (not committed) | - |

**Execution**:

```bash
# 2.1 Find candidates
find ${REPO_ROOT} -maxdepth 2 \( -name "*.sh" -o -name "*.py" \) | grep -v "${SOURCE_DIRS}"

# 2.2 Evaluate + classify
#   deploy_*      → scripts/deploy/
#   cron_*        → scripts/cron/
#   cleanup_*.sh  → scripts/maintenance/
#   other reusable → scripts/utils/
#   one-off        → rm (keep locally in .scratch/)

# 2.3 git mv (preserve history)
git mv ${REPO_ROOT}/rotate-logs.sh ${REPO_ROOT}/scripts/maintenance/rotate-logs.sh

# 2.4 One commit per sorting pass
git commit -m "chore(dir): organize scripts and temp files (<date>)"
```

**Verification**:
- `find ${REPO_ROOT} -maxdepth 2 \( -name "*.sh" -o -name "*.py" \)` — everything lands in `${SOURCE_DIRS}` or `scripts/`
- `scripts/` has no strays (everything inside subdirectories)

---

## Phase 3: Temporary file archiving (tmp/)

**Rules**:

| Type | Path | .gitignore |
|------|------|------------|
| Runtime temp files | `tmp/<category>/<name>` | yes |
| Categories | logs / cache / run / debug | - |

**Execution**:

```bash
# 3.1 Create the tmp structure
mkdir -p tmp/{logs,cache,run,debug}

# 3.2 Move into tmp/ + add .gitignore
mv *.log tmp/logs/ 2>/dev/null
mv .cache tmp/cache/ 2>/dev/null
echo "tmp/" >> .gitignore

# 3.3 Temp files committed by mistake: git rm + move locally
git rm --cached *.log 2>/dev/null
mv *.log tmp/logs/

# 3.4 One commit per archiving pass
git add .gitignore
git commit -m "chore(dir): move temp files to tmp/ (<date>)"
```

**Expiry cleanup** (runs automatically at the end of Phase 4):
```bash
# tmp files not accessed for 30 days
find tmp/ -type f -atime +30 -delete
# empty directory cleanup
find tmp/ -type d -empty -delete
```

---

## Phase 4: Debug artifact cleanup

**Rules**:

| Type | Handling |
|------|------|
| Committed by mistake (*.debug / *.dump / *.core / *.trace / *.prof / nohup.out) | `git rm` + add to `.gitignore` |
| Misplaced inside the repo | move to `tmp/debug/<date>/` |
| Never enters ${SOURCE_DIRS} / `scripts/` / ${DOCS_DIR} | - |

**Execution**:

```bash
# 4.1 Find debug artifacts
find ${REPO_ROOT} -type f \( -name "*.debug" -o -name "*.dump" -o -name "*.core" -o -name "*.trace" -o -name "*.prof" -o -name "nohup.out" \) -not -path '*/.git/*'

# 4.2 git rm the ones committed by mistake
git rm --cached path/to/leaked.debug
mv path/to/leaked.debug tmp/debug/

# 4.3 Add .gitignore rules
echo -e "*.debug\n*.dump\n*.core\n*.trace\n*.prof\nnohup.out" >> .gitignore
git add .gitignore
git commit -m "chore(dir): clean debug artifacts + ignore (<date>)"
```

---

## Phase 5: Duplicate directory merge

**Scenario**: same-named/similar directory trees scattered in several places (e.g. `crawler/` + `scraper/` + `spiders/` all do crawling)

**Execution**:

```bash
# 5.1 Find similar directories (by file traits)
for dir in crawler scraper spiders; do
  find ${REPO_ROOT} -type d -name "$dir" -not -path '*/.git/*'
done

# 5.2 Evaluate: merge into the canonical directory or split into submodules

# 5.3 git mv (preserve history) — git mv only accepts 2 paths; use `git mv scraper crawler` only when renaming a whole directory,
#     here we "merge everything from scraper/ into crawler/": glob expansion (crawler/ must already exist)
git mv scraper/* crawler/  # merge everything from scraper/ into crawler/

# 5.4 Verify import paths are not broken
${TEST_RUNNER} --collect-only
```

**Principle**: do not delete ${PROD_DIR} (prod is a mirror); run the reorganization in ${REPO_ROOT} (staging).

---

## Phase 6: Verification + archiving old paths

**Verification**:

```bash
# 6.1 imports not broken
${TEST_RUNNER} 2>&1 | tee /tmp/test_after.log

# 6.2 deploy scripts still work
bash ${DEPLOY_SCRIPT_BACKEND} --dry-run 2>/dev/null || echo "no deploy script"

# 6.3 no scattered scripts left in the source tree
find ${REPO_ROOT} -maxdepth 2 \( -name "*.sh" -o -name "*.py" \) | grep -v "${SOURCE_DIRS}" | grep -v "scripts/"

# 6.4 tmp/ is .gitignored
grep -q "^tmp/$" .gitignore && echo "✓ tmp/ ignored"

# 6.5 One commit per archiving pass
git commit -m "chore(dir): verify dir-reorg result (<date>)"
```

**Rollback on failure** (runs only on explicit ${OWNER} request, pick one of three):
```bash
# 1. Backup rollback (recommended): restore the whole directory via rsync
${BACKUP_BIN} ${BACKUP_ROOT}/${PROJECT_NAME}/dir-<DATE>/ ${REPO_ROOT}/

# 2. Single commit rollback: git revert (compliance first, no history loss)
git revert <COMMIT_HASH> --no-edit

# 3. Range rollback
git revert <START>..HEAD --no-edit
```

**Rollback policy**: default is rsync backup restore. `git revert` for undoing commits already made. **`git reset --hard` is absolutely forbidden** (global CLAUDE.md iron law).

**Last resort** (always git tag a backup first):
```bash
# Recommended: rsync backup restore (lossless)
rsync -a --delete ${BACKUP_ROOT}/${PROJECT_NAME}/dir-baseline-${DATE}/ ${REPO_ROOT}/

# Alternative: git revert range undo (writes a reverse commit per commit, no history loss)
git tag dir-rollback-${DATE}-pre-revert
git revert dir-baseline-${DATE}..HEAD --no-edit
```

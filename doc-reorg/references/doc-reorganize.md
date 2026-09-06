# Document Reorganize Subflow (project-doctor sub-workflow)

> Trigger: user says "document restructure" / "organize documents" / "env.md sync" / "deploy.md sync" / "document baseline" / "document archiving" / "archive stale docs"
> Scope: documents only (env.md / deploy.md / classification / archiving); do not touch code logic / directory structure

## Table of contents

1. [Phase 1: Inventory](#phase-1-inventory)
2. [Phase 2: Document classification and archiving (MRD/PRD/ARCH/DESIGN/TEST/RESEARCH)](#phase-2-document-classification-and-archiving-mrdprdarchdesigntestresearch)
3. [Phase 3: env.md / deploy.md sync](#phase-3-envmd--deploymd-sync)
4. [Phase 4: Evergreen authoritative document templates](#phase-4-evergreen-authoritative-document-templates)
5. [Phase 5: Consistency check](#phase-5-consistency-check)

---

## Phase 1: Inventory

**Purpose**: quantify the "before" state — file count / type distribution / scattered docs / orphan references.

```bash
# 1.1 Overview
find docs/ -name "*.md" | wc -l
find docs/ -type d | sort

# 1.2 By type (if mrd/, prd/ etc. subdirectories already exist)
for d in docs/*/; do echo "$d: $(find "$d" -name '*.md' | wc -l)"; done

# 1.3 Scattered documents (not under docs/)
find ${REPO_ROOT} -maxdepth 3 -name "*.md" -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/venv/*" -not -path "*/docs/*" | head

# 1.4 Candidates for archiving (not modified for 12 months)
find docs/ -name "*.md" -not -path "*/archive/*" -mtime +365 | head -20
```

**deliverable**: `docs/audit/<date>-doc-snapshot.md` containing the file list + classification status.

---

## Phase 2: Document classification and archiving (MRD/PRD/ARCH/DESIGN/TEST/RESEARCH)

**Project-level documents** (top-level `docs/`):

| Type | Path | Trigger scenario |
|------|------|---------|
| **MRD** (Market Requirements) | `docs/mrd/` | 0 → 1 project / quarterly business alignment |
| **PRD** (Product Requirements) | `docs/prd/` | one per feature version |
| **ARCH** (Architecture) | `docs/arch/` | before a major version / architecture change |
| **DESIGN** (UI/UX Design) | `docs/design/` | visual specs, interaction drafts, design tokens |
| **TEST** (Test Plans) | `docs/test/` | test plans, cases, coverage reports |
| **RESEARCH** (Research Notes) | `docs/research/` | research notes, technology selection comparisons, spike results |

**Execution**:

```bash
# 2.1 Create the subdirectories
mkdir -p docs/{mrd,prd,arch,design,test,research}

# 2.2 Evaluate + git mv
# e.g.: move SCRATCH-2026-market.md into mrd/
git mv docs/SCRATCH-2026-market.md docs/mrd/2026-market-overview.md

# 2.3 Create INDEX.md
cat > docs/INDEX.md << 'EOF'
# Documentation Index

## MRD (Market)
- [2026-market-overview](mrd/2026-market-overview.md)

## PRD (Product)
- (empty)

## ARCH
- (empty)

## DESIGN
- (empty)

## TEST
- (empty)

## RESEARCH
- (empty)

## Archive
- (empty)
EOF

# 2.4 One commit per classification pass
git commit -m "docs(reorg): categorize into mrd/prd/arch/design/test/research (<date>)"
```

### Stale document archiving (mandatory)

**Trigger conditions** (archive when any one is met):
- Document last modified > 12 months ago and has no active references
- The feature/version the document describes has been retired
- The document has been fully superseded by a new version (when the old version still has reference value)

**Archive path**: `docs/archive/<type>/<yyyy-mm>/<DATE>-<name>.md`
(keep the original filename, add a `<DATE>-` prefix, organize by month)

**Execution**:

```bash
# 3.1 Find candidates
find docs/ -maxdepth 3 -name "*.md" -mtime +365 -not -path "*/archive/*"

# 3.2 Cross-check codegraph for remaining references
codegraph where "<doc-title>" 2>/dev/null

# 3.3 Candidate + zero references → git mv
DATE=$(date -u +%Y-%m-%d)
git mv docs/old-feature-spec.md docs/archive/prd/2026-07/${DATE}-old-feature-spec.md

# 3.4 Add a comment at the top of the archived file
sed -i '1i > Archived '"$DATE"': superseded by v2 spec\n' docs/archive/prd/2026-07/${DATE}-old-feature-spec.md

# 3.5 One commit per archiving batch
git commit -m "docs(archive): move <N> stale files to docs/archive/ (<DATE>)"
```

**Forbidden**: permanently deleting stale documents (compliance requirement). After archiving, git history stays traceable.

### Second-level archiving rules (archive bloat control)

- archive > 5 years → split into second-level directories by decade (`docs/archive/2020s/2020/prd/...`)
- archive > 1000 files → split by milestone (`docs/archive/milestone-v2/prd/...`)

---

## Phase 3: env.md / deploy.md sync

**deliverable**: bring `env.md` + `deploy.md` up to the current real state.

### env.md sync

```bash
# 3.1 Extract the env vars actually used in code
grep -roPh 'os\.environ\.get\(["\x27]\K[A-Z_][A-Z_0-9]+' ${REPO_ROOT}/ | sort -u > /tmp/code_vars.txt

# Go:    grep -rE 'os\.Getenv\("[A-Z_]+"' ${REPO_ROOT}/
# Node:  grep -roE 'process\.env\.[A-Z_]+' ${REPO_ROOT}/
# Rust:  grep -roE 'std::env::var\("[A-Z_]+"' ${REPO_ROOT}/

# 3.2 Vars listed in the existing env.md
grep -oP '\| \`[A-Z_]+\`' ${REPO_ROOT}/env.md | tr -d '|`' | sort -u > /tmp/doc_vars.txt

# 3.3 diff: present in code but missing from doc → add; present in doc but unused by code → mark deprecated
diff /tmp/code_vars.txt /tmp/doc_vars.txt
```

**env.md write rules**:
- secrets never go into env.md (project-specific env file only, mode 600)
- env.md lists only **variable name + role + default value + whether required**
- new variable added → sync it into env.md
- variable removed → mark deprecated, keep for 1 version, then delete

### deploy.md sync

```bash
# Deploy scripts / systemd units
ls ~/.config/systemd/user/*.service 2>/dev/null | awk -F/ '{print $NF}' | sort -u > /tmp/units.txt
grep -oP '[a-z]+-[a-z-]+\.service' ${REPO_ROOT}/env.md ${REPO_ROOT}/deploy.md | sort -u > /tmp/doc_units.txt
diff /tmp/units.txt /tmp/doc_units.txt

# Ports
grep -rnP '127\.0\.0\.1:\d+' ${REPO_ROOT}/ | grep -oP ':\d+' | sort -u > /tmp/ports.txt
grep -oP '\|\s*\d+\s*\|' ${REPO_ROOT}/env.md | grep -oP '\d+' | sort -u > /tmp/doc_ports.txt
diff /tmp/ports.txt /tmp/doc_ports.txt
```

**deploy.md must contain**:
- deploy script paths (e.g. `${DEPLOY_SCRIPT_BACKEND}`)
- systemd service list (Linux only)
- port mappings (staging + prod included)
- rollback steps (rsync / git revert, **never git reset --hard**)

### Doc reference integrity

```bash
# 5.4 doc reference file existence
grep -rn "docs/[a-zA-Z_-]*\.md" docs/ 2>/dev/null | grep -oP 'docs/[a-zA-Z_-]+\.md' | while read f; do
  [ ! -f "$f" ] && echo "BROKEN: $f"
done
```

**Fixes**:
- BROKEN references → fix / delete (avoid 404s)
- env var missing in code → add it in config.py + sync env.md
- unit / port missing in docs → fill it into env.md

---

## Phase 4: Evergreen authoritative document templates

**Project-level required**:

| File | Content | Update trigger |
|------|------|---------|
| `env.md` | env variable inventory (name + role + default value) | env changes |
| `deploy.md` | deploy flow + rollback steps | deploy changes |
| `pipeline.md` (as needed) | pipeline module flow diagram | pipeline changes |
| `<other-module>.md` (as needed) | project-specific module reference | changes to that module |
| `CLAUDE.md` | agent entry point + mandatory constraints | flow changes |
| `docs/INDEX.md` | document directory index | documents added/archived/deleted |

**CLAUDE.md mandate block** (suggested structure):
```markdown
# CLAUDE.md

## Mandatory constraints
1. <core constraint 1>
2. <core constraint 2>
...

## Workflows
- <scenario 1>: <steps>
- <scenario 2>: <steps>
...

## Required reading (by priority)
1. env.md (env setup)
2. deploy.md (deploy flow)
3. <other-module>.md (project-specific)
```

**Update flow**: any env/deploy/module change → **must** be synced into the corresponding document + a single commit `docs(<area>): sync <summary>`.

---

## Phase 5: Consistency check

**deliverable**: `docs/audit/<date>-consistency.md`

| Check | Command |
|--------|------|
| env var consistency | `diff /tmp/code_vars.txt /tmp/doc_vars.txt` |
| systemd unit consistency | `diff /tmp/units.txt /tmp/doc_units.txt` |
| port consistency | `diff /tmp/ports.txt /tmp/doc_ports.txt` |
| doc reference integrity | `grep -rn "docs/.*\.md" docs/ \| while read f; do [ ! -f "$f" ] && echo BROKEN; done` |
| INDEX.md matches reality | `find docs/ -name "*.md" -not -path "*/archive/*" \| sort` vs the INDEX.md list |

**Fixes**:
- inconsistency → sync the update + commit
- BROKEN → fix / delete the reference
- missing in INDEX → add it; extra in INDEX → remove it

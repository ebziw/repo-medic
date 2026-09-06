---
name: doc-reorg
description: "One-pass directory + document + file reorganization — git mv renames, tmp archiving, script sorting, debug artifact cleanup, document classification and archiving (MRD/PRD/ARCH/DESIGN/TEST/RESEARCH), env.md/deploy.md sync. Triggers: directory reorganization, file archiving, tmp cleanup, document classification, README, templates, env, deploy, git mv, file reorganization, archive"
metadata:
  type: domain
  scope: public
---

# doc-reorg — Directory + Document Reorganization

Self-contained skill. One invocation completes directory restructuring and document archiving.

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Snapshot + Reconnaissance

- [ ] **Read** `references/dir-restructure.md` in full (7 phases)
- [ ] **Read** `references/doc-reorganize.md` (5 phases + 6 categories)
- [ ] **Backup**: `rsync -a ./ "backup-pre-doc-reorg-$(date +%Y%m%d)/"` (Iron Law 3, for rollback)
- [ ] **git status clean** — commit existing uncommitted work before making changes
- [ ] 🛑 **GATE**: backup succeeds + working tree clean before entering Phase 1

### Phase 1: Inventory

- [ ] **Directory scan**: `tree -L 3 --noreport` + `find . -maxdepth 2 -type d` to list all subdirectories
- [ ] **Document inventory**: list `*.md` files, pre-classify into the 6 MRD/PRD/ARCH/DESIGN/TEST/RESEARCH categories
- [ ] **tmp/ candidates**: `find . -name "tmp*" -o -name "*.tmp" -o -name "*.bak*" -o -name "*~"` to list deletion candidates
- [ ] **debug artifact candidates**: `.log` / `nohup.out` / `*.pid` / `core.*` files
- [ ] **Broken-link candidates**: `rg "\.\./\.\./" --type md` to find possibly broken relative path references

### Phase 2: Classify

- [ ] **Script sorting**: scattered `.sh` / `.py` go into `scripts/{deploy,maintenance,cron,utils}/`
- [ ] **6 document categories**: scattered `.md` moved by type into `docs/{mrd,prd,arch,design,test,research}/`
- [ ] **Duplicate directory merge**: `diff -rq dirA dirB` to find fully equivalent ones (back up before merging)
- [ ] **Keep redirects for old paths**: for old paths users have referenced, write `_redirect.md` or a symlink
- [ ] 🛑 **GATE**: present the classification plan to the user for confirmation + user OK before entering Phase 3

### Phase 3: Execute

- [ ] **`git mv`, not `mv`** — preserve history (Iron Law 1 + YAGNI: do not bypass git)
- [ ] **1 commit = 1 category** (Iron Law 2) — touch only one category at a time (scripts / docs / tmp)
- [ ] **After every commit** run `git log --oneline` + `git status` checks
- [ ] **grep before deleting temp files** to confirm no code references them: `rg "tmp/oldname"` should return 0 hits
- [ ] 🛑 **GATE**: after every single commit run `git status` + `git diff --stat` to verify nothing unexpected

### Phase 4: Verify

- [ ] **rsync diff verification**: `diff -rq backup-pre-doc-reorg-*/ ./ | grep -v "^Only in backup"` should be empty (except .git)
- [ ] **Broken-link check**: extract all relative paths from `.md` files, run `test -e` on each
- [ ] **CI passes**: for projects with CI documented, run `pytest` to confirm code is unaffected
- [ ] **env.md / deploy.md sync**: path changes must be synced into env.md (ports, paths) + deploy.md (deploy scripts)
- [ ] 🛑 **GATE**: every box checked = reorganization complete. Any single failure = roll back + investigate

### Phase 5: Cleanup

- [ ] **Delete tmp/ debug artifacts**: `git rm -r tmp/ debug/`
- [ ] **Delete backup/**: once verification passes, `rm -rf backup-pre-doc-reorg-*`
- [ ] **Write a work-note**: record "which paths changed + why + which old paths keep redirects" in `docs/work-note/<date>-doc-reorg.md`
- [ ] **KB sync**: push to the KB endpoint's public-knowledge collection (skip if no KB system is configured)
- [ ] 🛑 **GATE**: only after all cleanup is done may "reorganization complete" be declared

---

## Contents

| Path | Content |
|---|---|
| `references/dir-restructure.md` | Phases 0-6 (snapshot → script sorting → tmp → debug → merge → archive) |
| `references/doc-reorganize.md` | 5 phases (inventory → six categories → env/deploy sync → templates → consistency) |
| `references/ai-cruft-detector.md` | AI-authored residue patterns (versioned dups / scratch docs / affirmation prose / debug residue / model-attributed TODOs) — borrowed from `alint` agent-hygiene@v1 |
| `references/safe-apply-protocol.md` | undo-script + drift-abort pattern — borrowed from `j-256/reorg` `apply --yes` semantics |

## Usage flow

Run dir-restructure.md Phase 0-6; on completion continue with doc-reorganize.md Phase 1-5. Use `ai-cruft-detector.md` as pre-commit / CI gate. Use `safe-apply-protocol.md` for any batch file operation.

## 14 hard constraints (shared across sub-workflows)

1. **Zero new dependencies + zero premature defense (YAGNI)**: stdlib + already-installed libraries only.
2. **Commit granularity**: 1 logical unit = 1 commit.
3. **Default rollback = rsync backup restore**. **`git reset --hard` is absolutely forbidden**.
4. **Dead-code proof requires a 7-step checklist**: grep for references before deleting paths.
5. **TDD**: does not apply to doc changes; if modifying doc-generator code, use Characterization.
6. **Full test suite green before commit**: path changes may affect test imports.
7. **prod locked**: do not touch production paths.
8. **Prefer missing over fake**: if an old path has user references, it must keep a redirect / symlink; do not cut it outright.
9. **DB deletion must go through the exit pipeline**: **within doc-reorg scope**: before deleting a doc file, confirm no external links reference it (grep + check README references).
10. **Test the minimum first on batch tasks**: for large mv batches, sample 1 subdirectory first.
11. **daemon / service code changes in 4 independent steps**: if a deploy script path changed → verify in 4 independent steps.
12. **Buffer ownership is transferred**: the caching side must keep a copy.
13. **Hash-named build artifacts must be synced whole-directory**: static asset path changes require a rebuild + whole-directory sync.
14. **Verify the actually effective artifact identifier after deploy/release**: a request to the new path must return curl 200.

## Related

- `/repo-medic` — meta entry point
- `/py-improve` — directory archiving after refactoring (run py-improve to improve code first, then doc-reorg to organize)
- `/db-tweak` — document sync after schema changes

## Repository

github.com/liyong-labs/repo-medic — Apache-2.0.

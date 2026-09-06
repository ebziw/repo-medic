---
name: doc-reorg
description: 目录 + 文档 + 文件一次性整理 — git mv 重命名、tmp 归档、脚本归类、debug 产物清理、文档分类归档（MRD/PRD/ARCH/DESIGN/TEST/RESEARCH）、env.md/deploy.md 同步。Triggers: 目录整理, 文件归档, tmp 清理, 文档分类, README, 模板, env, deploy, git mv, file reorganization, document classification, archive
metadata:
  type: domain
  scope: public
---

# doc-reorg — 目录 + 文档整理

self-contained skill。一次调用完成目录重构和文档归档。

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Snapshot + Reconnaissance

- [ ] **Read** `references/dir-restructure.md` in full (7 phases)
- [ ] **Read** `references/doc-reorganize.md` (5 phases + 6 分类)
- [ ] **备份**: `rsync -a ./ "backup-pre-doc-reorg-$(date +%Y%m%d)/"` (铁律 3，回滚用)
- [ ] **git status 干净** — 改前先 commit 现有未提交工作
- [ ] 🛑 **GATE**: 备份成功 + 工作区干净才能进 Phase 1

### Phase 1: Inventory

- [ ] **目录扫描**: `tree -L 3 --noreport` + `find . -maxdepth 2 -type d` 列出所有子目录
- [ ] **文档分类盘点**: 列出 `*.md` 文件，按 MRD/PRD/ARCH/DESIGN/TEST/RESEARCH 6 类预归类
- [ ] **tmp/ 候选**: `find . -name "tmp*" -o -name "*.tmp" -o -name "*.bak*" -o -name "*~"` 列出候选删除
- [ ] **debug 产物候选**: `.log` / `nohup.out` / `*.pid` / `core.*` 文件
- [ ] **断链候选**: `rg "\.\./\.\./" --type md` 找可能断的相对路径引用

### Phase 2: Classify

- [ ] **脚本归类**: 散落的 `.sh` / `.py` 归到 `scripts/{deploy,maintenance,cron,utils}/`
- [ ] **文档 6 分类**: 散落 `.md` 按类型移到 `docs/{mrd,prd,arch,design,test,research}/`
- [ ] **重复目录合并**: `diff -rq dirA dirB` 找完全等价的（合并前先备份）
- [ ] **旧路径保留 redirect**: 用户引用过的旧路径，写 `_redirect.md` 或 symlink
- [ ] 🛑 **GATE**: 分类计划列给用户确认 + 用户 OK 才能进 Phase 3

### Phase 3: Execute

- [ ] **`git mv` 不 `mv`** — 保留历史（铁律 1 + YAGNI 不绕过 git）
- [ ] **1 commit = 1 分类**（铁律 2）— 一次只动一类（脚本 / 文档 / tmp）
- [ ] **每 commit 后** `git log --oneline` + `git status` 检查
- [ ] **临时文件可删前先 grep** 确认无代码引用: `rg "tmp/oldname"` 应 0 命中
- [ ] 🛑 **GATE**: 单个 commit 后必跑 `git status` + `git diff --stat` 验证无意外

### Phase 4: Verify

- [ ] **rsync diff 验证**: `diff -rq backup-pre-doc-reorg-*/ ./ | grep -v "^Only in backup"` 应为空（除 .git）
- [ ] **断链检查**: 把所有 `.md` 里的相对路径提出来，`test -e` 每个
- [ ] **CI 通过**: 文档里有 CI 的项目跑 `pytest` 确认代码未受影响
- [ ] **env.md / deploy.md 同步**: 路径变更必同步到 env.md（端口、路径）+ deploy.md（部署脚本）
- [ ] 🛑 **GATE**: 全部勾选 = 重构完成。任何一项失败 = 回滚 + 排查

### Phase 5: Cleanup

- [ ] **删除 tmp/ debug 产物**: `git rm -r tmp/ debug/`
- [ ] **删除 backup/**: 验证通过后 `rm -rf backup-pre-doc-reorg-*`
- [ ] **写 work-note**: 把"哪些路径变了 + 为何变 + 哪些旧路径保留 redirect"写到 `docs/work-note/<date>-doc-reorg.md`
- [ ] **KB 同步**: 推到所配 KB 端点的 public-knowledge 集合（未配 KB 系统则跳过）
- [ ] 🛑 **GATE**: 全部清理完才能说"重构完成"

---

## 包含

| 路径 | 内容 |
|---|---|
| `references/dir-restructure.md` | Phase 0-6（snapshot → 脚本归类 → tmp → debug → 合并 → 归档） |
| `references/doc-reorganize.md` | 5 phases（盘点 → 六分类 → env/deploy 同步 → 模板 → 一致性） |

## 使用流程

按 dir-restructure.md Phase 0-6 执行；完成后接 doc-reorganize.md Phase 1-5。

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 + 零提前防御 (YAGNI)**: 只用 stdlib + 已装库。
2. **commit 颗粒度**: 1 逻辑单元 = 1 commit。
3. **默认回滚 = rsync 备份还原**。**绝对禁止 `git reset --hard`**。
4. **死代码证明需 7 步 checklist**: 删除路径前 grep 确认无引用。
5. **TDD**: doc 改动不适用；如改 doc generator 代码用 Characterization。
6. **commit 前全量测试全绿**: 路径变更可能影响测试 import。
7. **prod 锁定**: 不动线上 prod 路径。
8. **宁缺勿伪**: 旧路径如有用户引用，必须 redirect / symlink，不直接砍。
9. **DB 删除必走退场流水线**: **doc-reorg 范围内**：删除 doc 文件前先确认无外部链接引用（grep + 检查 README 引用）。
10. **批量任务先测最小**: 大批量 mv 先选 1 个子目录 sample。
11. **daemon / 服务代码改动 4 步独立**: 部署脚本路径改了 → 4 步独立验证。
12. **buffer 所有权被转移**: 缓存方必须保留副本。
13. **hash 化构建产物必须整目录同步**: 静态资源路径变更需重新 build + 整目录同步。
14. **部署/发布后必须验证实际生效产物标识**: 新路径请求 curl 200。

## 关联

- `/repo-medic` — meta 入口
- `/py-improve` — 重构后目录归档（先 py-improve 改善代码，再 doc-reorg 整理）
- `/db-tweak` — schema 变更后文档同步

## 仓库

github.com/ebziw/repo-medic — Apache-2.0。

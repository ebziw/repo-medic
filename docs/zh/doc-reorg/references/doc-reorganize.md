# Document Reorganize Subflow (project-doctor 子工作流)

> 触发: 用户说 "文档重构" / "整理文档" / "env.md 同步" / "deploy.md 同步" / "文档基线" / "文档归档" / "archive stale docs"
> 范围: 仅文档 (env.md / deploy.md / 分类 / 归档), 不动代码逻辑 / 目录结构

## 目录

1. [Phase 1: 现状盘点](#phase-1-现状盘点)
2. [Phase 2: 文档分类归档](#phase-2-文档分类归档-mrdprdarchdesigntestresearch)
3. [Phase 3: env.md / deploy.md 同步](#phase-3-envmd--deploymd-同步)
4. [Phase 4: 永续权威文档模板](#phase-4-永续权威文档模板)
5. [Phase 5: 一致性核对](#phase-5-一致性核对)

---

## Phase 1: 现状盘点

**目的**: 量化"整理前" — 文件数 / 类型分布 / 散落文档 / 孤儿引用.

```bash
# 1.1 总览
find docs/ -name "*.md" | wc -l
find docs/ -type d | sort

# 1.2 按类型分 (如已有 mrd/ prd/ 等子目录)
for d in docs/*/; do echo "$d: $(find "$d" -name '*.md' | wc -l)"; done

# 1.3 散落文档 (不在 docs/ 下)
find ${REPO_ROOT} -maxdepth 3 -name "*.md" -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/venv/*" -not -path "*/docs/*" | head

# 1.4 12 月未改的候选归档
find docs/ -name "*.md" -not -path "*/archive/*" -mtime +365 | head -20
```

**deliverable**: `docs/audit/<date>-doc-snapshot.md` 含文件清单 + 分类现状.

---

## Phase 2: 文档分类归档 (MRD/PRD/ARCH/DESIGN/TEST/RESEARCH)

**项目级文档** (顶层 `docs/`):

| 类型 | 路径 | 触发场景 |
|------|------|---------|
| **MRD** (Market Requirements) | `docs/mrd/` | 0 → 1 项目 / 季度业务对齐 |
| **PRD** (Product Requirements) | `docs/prd/` | 每个功能版本一个 |
| **ARCH** (Architecture) | `docs/arch/` | 大版本前 / 架构变更 |
| **DESIGN** (UI/UX Design) | `docs/design/` | 视觉规范, 交互稿, 设计 token |
| **TEST** (Test Plans) | `docs/test/` | 测试计划, 用例, 覆盖率报告 |
| **RESEARCH** (Research Notes) | `docs/research/` | 调研笔记, 选型对比, spike 结果 |

**执行**:

```bash
# 2.1 创建子目录
mkdir -p docs/{mrd,prd,arch,design,test,research}

# 2.2 评估 + git mv
# 例: 把 SCRATCH-2026-market.md 移到 mrd/
git mv docs/SCRATCH-2026-market.md docs/mrd/2026-market-overview.md

# 2.3 创建 INDEX.md
cat > docs/INDEX.md << 'EOF'
# Documentation Index

## MRD (Market)
- [2026-market-overview](mrd/2026-market-overview.md)

## PRD (Product)
- (空)

## ARCH
- (空)

## DESIGN
- (空)

## TEST
- (空)

## RESEARCH
- (空)

## Archive
- (空)
EOF

# 2.4 一次分类 1 commit
git commit -m "docs(reorg): categorize into mrd/prd/arch/design/test/research (<date>)"
```

### 过时文档归档 (强制执行)

**触发条件** (满足任一即归档):
- 文档最后一次修改 > 12 个月, 且无 active 引用
- 文档描述的功能/版本已下线
- 文档被新版本完全取代 (旧版有参考价值时)

**归档路径**: `docs/archive/<type>/<yyyy-mm>/<DATE>-<name>.md`
(保留原文件名, 加 `<DATE>-` 前缀, 按月份组织)

**执行**:

```bash
# 3.1 找候选
find docs/ -maxdepth 3 -name "*.md" -mtime +365 -not -path "*/archive/*"

# 3.2 交叉检查 codegraph 是否还被引用
codegraph where "<doc-title>" 2>/dev/null

# 3.3 候选 + 零引用 → git mv
DATE=$(date -u +%Y-%m-%d)
git mv docs/old-feature-spec.md docs/archive/prd/2026-07/${DATE}-old-feature-spec.md

# 3.4 在归档文件头部加注释
sed -i '1i > Archived '"$DATE"': superseded by v2 spec\n' docs/archive/prd/2026-07/${DATE}-old-feature-spec.md

# 3.5 单批归档 1 commit
git commit -m "docs(archive): move <N> stale files to docs/archive/ (<DATE>)"
```

**禁止**: 永久删除过时文档 (合规要求). 归档后保留 git 历史可追溯.

### 二级归档规则 (archive 膨胀控制)

- archive > 5 年 → 按 decade 拆二级目录 (`docs/archive/2020s/2020/prd/...`)
- archive > 1000 文件 → 按 milestone 拆 (`docs/archive/milestone-v2/prd/...`)

---

## Phase 3: env.md / deploy.md 同步

**deliverable**: 更新 `env.md` + `deploy.md` 到当前真实状态.

### env.md 同步

```bash
# 3.1 提取代码中实际使用的 env var
grep -roPh 'os\.environ\.get\(["\x27]\K[A-Z_][A-Z_0-9]+' ${REPO_ROOT}/ | sort -u > /tmp/code_vars.txt

# Go:    grep -rE 'os\.Getenv\("[A-Z_]+"' ${REPO_ROOT}/
# Node:  grep -roE 'process\.env\.[A-Z_]+' ${REPO_ROOT}/
# Rust:  grep -roE 'std::env::var\("[A-Z_]+"' ${REPO_ROOT}/

# 3.2 现有 env.md 列出的 var
grep -oP '\| \`[A-Z_]+\`' ${REPO_ROOT}/env.md | tr -d '|`' | sort -u > /tmp/doc_vars.txt

# 3.3 diff: code 有 doc 缺 → 加; doc 有 code 不用 → 标 deprecated
diff /tmp/code_vars.txt /tmp/doc_vars.txt
```

**env.md 写入规则**:
- secret 永远不进 env.md (只写项目专属 env 文件, mode 600)
- env.md 只列**变量名 + 角色 + 默认值 + 是否必填**
- 新增变量 → 同步加到 env.md
- 删除变量 → 标 deprecated 保留 1 个版本再删

### deploy.md 同步

```bash
# 部署脚本 / systemd unit
ls ~/.config/systemd/user/*.service 2>/dev/null | awk -F/ '{print $NF}' | sort -u > /tmp/units.txt
grep -oP '[a-z]+-[a-z-]+\.service' ${REPO_ROOT}/env.md ${REPO_ROOT}/deploy.md | sort -u > /tmp/doc_units.txt
diff /tmp/units.txt /tmp/doc_units.txt

# 端口
grep -rnP '127\.0\.0\.1:\d+' ${REPO_ROOT}/ | grep -oP ':\d+' | sort -u > /tmp/ports.txt
grep -oP '\|\s*\d+\s*\|' ${REPO_ROOT}/env.md | grep -oP '\d+' | sort -u > /tmp/doc_ports.txt
diff /tmp/ports.txt /tmp/doc_ports.txt
```

**deploy.md 必含**:
- 部署脚本路径 (例: `${DEPLOY_SCRIPT_BACKEND}`)
- systemd service 列表 (Linux only)
- 端口映射 (含 staging + prod)
- 回滚步骤 (rsync / git revert, **不用 git reset --hard**)

### doc 引用完整性

```bash
# 5.4 doc 引用文件存在性
grep -rn "docs/[a-zA-Z_-]*\.md" docs/ 2>/dev/null | grep -oP 'docs/[a-zA-Z_-]+\.md' | while read f; do
  [ ! -f "$f" ] && echo "BROKEN: $f"
done
```

**修复**:
- BROKEN 引用 → 改 / 删 (避免 404)
- code 缺 env var → config.py 加 + env.md 同步
- doc 缺 unit / port → env.md 补

---

## Phase 4: 永续权威文档模板

**项目级必备**:

| 文件 | 内容 | 更新触发 |
|------|------|---------|
| `env.md` | env 变量清单 (名+角色+默认值) | env 改动 |
| `deploy.md` | 部署流程 + 回滚步骤 | 部署改动 |
| `pipeline.md` (按需) | pipeline 模块流程图 | pipeline 改动 |
| `<其他模块>.md` (按需) | 项目特有模块参考 | 该模块改动 |
| `CLAUDE.md` | agent 入口 + 强制约束 | 流程改动 |
| `docs/INDEX.md` | 文档目录索引 | 新增/归档/删除文档 |

**CLAUDE.md mandate block** (建议结构):
```markdown
# CLAUDE.md

## 强制约束
1. <核心约束 1>
2. <核心约束 2>
...

## 工作流
- <场景 1>: <步骤>
- <场景 2>: <步骤>
...

## 必读文档 (按优先级)
1. env.md (env 设置)
2. deploy.md (部署流程)
3. <其他模块>.md (项目特有)
```

**更新流程**: 任何 env/deploy/模块改动 → **必须** 同步到对应文档 + 单 commit `docs(<area>): sync <summary>`.

---

## Phase 5: 一致性核对

**deliverable**: `docs/audit/<date>-consistency.md`

| 检查项 | 命令 |
|--------|------|
| env var 一致性 | `diff /tmp/code_vars.txt /tmp/doc_vars.txt` |
| systemd unit 一致性 | `diff /tmp/units.txt /tmp/doc_units.txt` |
| 端口一致性 | `diff /tmp/ports.txt /tmp/doc_ports.txt` |
| doc 引用完整性 | `grep -rn "docs/.*\.md" docs/ \| while read f; do [ ! -f "$f" ] && echo BROKEN; done` |
| INDEX.md 与实际一致 | `find docs/ -name "*.md" -not -path "*/archive/*" \| sort` vs INDEX.md 列表 |

**修复**:
- 不一致 → 同步更新 + commit
- BROKEN → 改 / 删引用
- INDEX 漏 → 补; INDEX 多 → 删
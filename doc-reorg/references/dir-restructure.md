# Directory Restructure Subflow (project-doctor 子工作流)

> 触发: 用户说 "目录重构" / "整理目录" / "目录清理" / "git mv 重整" / "reorganize directory" / "consolidate scripts" / "merge duplicate folder"
> 范围: 仅目录结构 (git mv + 脚本归档 + tmp 整理), 不动代码逻辑 / 文档内容

## 目录

1. [Phase 0: pre-flight](#phase-0-pre-flight)
2. [Phase 1: 当前目录快照](#phase-1-当前目录快照--统计)
3. [Phase 2: 脚本归类](#phase-2-脚本归类scripts)
4. [Phase 3: 临时文件归档](#phase-3-临时文件归档tmp)
5. [Phase 4: debug 产物清理](#phase-4-debug-产物清理)
6. [Phase 5: 重复目录合并](#phase-5-重复目录合并)
7. [Phase 6: 验证 + 归档旧路径](#phase-6-验证--归档旧路径)

---

## 🚨 CRITICAL — Iron Law

> **严禁拆一半状态 + 重构期间不可 rush hotfix.**
>
> 拆一半状态 = 工业级灾难 (Knight Capital 2012). **任何 phase 必须闭环 (commit / revert / backup) 才能进下一个**.
>
> 重构期间 rush hotfix = 同样灾难 (FB BGP 2021). **不在 reorg 期间动生产 / 不打断 phase / 不混 commit**.

---

## Phase 0: pre-flight

```bash
# 文件备份
mkdir -p ${BACKUP_ROOT}/${PROJECT_NAME}/dir-$(date -u +%Y-%m-%d)
${BACKUP_BIN} ${REPO_ROOT} ${BACKUP_ROOT}/${PROJECT_NAME}/dir-$(date -u +%Y-%m-%d)/

# git tag baseline
git tag ${SKILL_NAME}-baseline-$(date -u +%Y-%m-%d)
```

**5 维兼顾**: 开发节奏 / 方便查找 / git 友好 / 人类观测 / 类型优先于域.

---

## Phase 1: 当前目录快照 + 统计

**目的**: 建立 baseline, 量化"整理前".

```bash
# 1.1 总览 (目录数 + 文件数 + 行数)
find ${REPO_ROOT} -type d -not -path '*/.git*' -not -path '*/node_modules*' -not -path '*/__pycache__*' -not -path '*/.venv*' | wc -l
find ${REPO_ROOT} -type f -not -path '*/.git*' -not -path '*/node_modules*' | wc -l

# 1.2 按扩展名统计
find ${REPO_ROOT} -type f -not -path '*/.git/*' | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20

# 1.3 大文件 (>1MB) 列表
find ${REPO_ROOT} -type f -size +1M -not -path '*/.git/*' -exec ls -lh {} \; | awk '{print $5, $NF}'

# 1.4 空目录
find ${REPO_ROOT} -type d -empty -not -path '*/.git*'

# 1.5 顶层散落脚本 (不在 ${SOURCE_DIRS} 内)
find ${REPO_ROOT} -maxdepth 2 \( -name "*.sh" -o -name "*.py" \) | grep -v "${SOURCE_DIRS}" | head
```

**deliverable**: `docs/audit/<date>-dir-snapshot.md`

---

## Phase 2: 脚本归类 (scripts/)

**规则**:

| 类型 | 路径 | 命名 |
|------|------|------|
| 散落的可复用脚本 | `scripts/<category>/<name>.<ext>` | kebab-case |
| 类别 | deploy / maintenance / cron / utils | - |
| 一次性脚本 | `${REPO_ROOT}/.scratch/` (不入库) | - |

**执行**:

```bash
# 2.1 找候选
find ${REPO_ROOT} -maxdepth 2 \( -name "*.sh" -o -name "*.py" \) | grep -v "${SOURCE_DIRS}"

# 2.2 评估 + 分类
#   deploy_*      → scripts/deploy/
#   cron_*        → scripts/cron/
#   cleanup_*.sh  → scripts/maintenance/
#   其他可复用    → scripts/utils/
#   一次性        → rm (本地留 .scratch/)

# 2.3 git mv (保留 history)
git mv ${REPO_ROOT}/rotate-logs.sh ${REPO_ROOT}/scripts/maintenance/rotate-logs.sh

# 2.4 一次归类 1 commit
git commit -m "chore(dir): organize scripts and temp files (<date>)"
```

**验证**:
- `find ${REPO_ROOT} -maxdepth 2 \( -name "*.sh" -o -name "*.py" \)` 全部在 `${SOURCE_DIRS}` 或 `scripts/`
- `scripts/` 无散落 (全在子目录)

---

## Phase 3: 临时文件归档 (tmp/)

**规则**:

| 类型 | 路径 | .gitignore |
|------|------|------------|
| 运行时临时文件 | `tmp/<category>/<name>` | 是 |
| 类别 | logs / cache / run / debug | - |

**执行**:

```bash
# 3.1 创建 tmp 结构
mkdir -p tmp/{logs,cache,run,debug}

# 3.2 移到 tmp/ + 加 .gitignore
mv *.log tmp/logs/ 2>/dev/null
mv .cache tmp/cache/ 2>/dev/null
echo "tmp/" >> .gitignore

# 3.3 误提交的临时文件: git rm + 移到本地
git rm --cached *.log 2>/dev/null
mv *.log tmp/logs/

# 3.4 一次归档 1 commit
git add .gitignore
git commit -m "chore(dir): move temp files to tmp/ (<date>)"
```

**过期清理** (Phase 4 末自动跑):
```bash
# 30 天未访问的 tmp 文件
find tmp/ -type f -atime +30 -delete
# 空目录清理
find tmp/ -type d -empty -delete
```

---

## Phase 4: debug 产物清理

**规则**:

| 类型 | 处理 |
|------|------|
| 误提交 (*.debug / *.dump / *.core / *.trace / *.prof / nohup.out) | `git rm` + 加 `.gitignore` |
| 误放在仓库内 | 移到 `tmp/debug/<date>/` |
| 永远不入 `${SOURCE_DIRS}` / `scripts/` / `${DOCS_DIR}` | - |

**执行**:

```bash
# 4.1 找 debug 产物
find ${REPO_ROOT} -type f \( -name "*.debug" -o -name "*.dump" -o -name "*.core" -o -name "*.trace" -o -name "*.prof" -o -name "nohup.out" \) -not -path '*/.git/*'

# 4.2 git rm 误提交
git rm --cached path/to/leaked.debug
mv path/to/leaked.debug tmp/debug/

# 4.3 .gitignore 加规则
echo -e "*.debug\n*.dump\n*.core\n*.trace\n*.prof\nnohup.out" >> .gitignore
git add .gitignore
git commit -m "chore(dir): clean debug artifacts + ignore (<date>)"
```

---

## Phase 5: 重复目录合并

**场景**: 同名/相似目录树散落多处 (例: `crawler/` + `scraper/` + `spiders/` 都做爬虫)

**执行**:

```bash
# 5.1 找相似目录 (按文件特征)
for dir in crawler scraper spiders; do
  find ${REPO_ROOT} -type d -name "$dir" -not -path '*/.git/*'
done

# 5.2 评估: 合并到 canonical 目录 or 拆分为子模块

# 5.3 git mv (保留 history) — git mv 只收 2 路径; 整目录更名才用 `git mv scraper crawler`,
#     此处为"合并 scraper/ 全部进 crawler/": glob 展开 (crawler/ 须已存在)
git mv scraper/* crawler/  # 合并 scraper/ 全部到 crawler/

# 5.4 验证 import path 没破
${TEST_RUNNER} --collect-only
```

**原则**: 不删 ${PROD_DIR} (prod 是 mirror), 重整在 ${REPO_ROOT} (staging) 做.

---

## Phase 6: 验证 + 归档旧路径

**验证**:

```bash
# 6.1 import 不破
${TEST_RUNNER} 2>&1 | tee /tmp/test_after.log

# 6.2 部署脚本仍 work
bash ${DEPLOY_SCRIPT_BACKEND} --dry-run 2>/dev/null || echo "no deploy script"

# 6.3 源码树无散落脚本
find ${REPO_ROOT} -maxdepth 2 \( -name "*.sh" -o -name "*.py" \) | grep -v "${SOURCE_DIRS}" | grep -v "scripts/"

# 6.4 tmp/ 已 .gitignore
grep -q "^tmp/$" .gitignore && echo "✓ tmp/ ignored"

# 6.5 单次归档 1 commit
git commit -m "chore(dir): verify dir-reorg result (<date>)"
```

**出错时回滚** (${OWNER} explicit 才跑, 三选一):
```bash
# 1. 备份回滚 (推荐): 整目录 rsync 还原
${BACKUP_BIN} ${BACKUP_ROOT}/${PROJECT_NAME}/dir-<DATE>/ ${REPO_ROOT}/

# 2. 单 commit 回滚: git revert (合规优先, 不丢历史)
git revert <COMMIT_HASH> --no-edit

# 3. 范围回滚
git revert <START>..HEAD --no-edit
```

**回滚策略**: 默认 rsync 备份还原. `git revert` 用于已 commit 撤回. **绝对禁止 `git reset --hard`** (全局 CLAUDE.md 铁律).

**最后手段** (必先 git tag 备份):
```bash
# 推荐: rsync 备份还原 (无损)
rsync -a --delete ${BACKUP_ROOT}/${PROJECT_NAME}/dir-baseline-${DATE}/ ${REPO_ROOT}/

# 备选: git revert 范围撤销 (逐 commit 写反向 commit, 不丢历史)
git tag dir-rollback-${DATE}-pre-revert
git revert dir-baseline-${DATE}..HEAD --no-edit
```
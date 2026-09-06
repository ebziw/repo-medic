# Lesson Schema — evolve 提取字段定义

evolve 从项目历史中蒸馏 lesson，每条 lesson 用以下结构：

## 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 自动生成 `{short_hash}_{index}` |
| `tag` | enum | 分类：`db` / `deploy` / `config` / `frontend` / `general` / `python` / `doc` |
| `target_skill` | enum | 建议注入到：`py-improve` / `doc-reorg` / `db-tweak` / `vue-improve` / `config-base` / `repo-medic` (meta) |
| `symptom` | string | 现象描述（≤ 80 字） |
| `cause` | string | 根因分析（≤ 120 字） |
| `fix` | string | 解决方案（≤ 120 字） |
| `references` | enum | 14 硬约束编号（如 "1", "2", "11"），标哪条约束被违反/补充 |
| `triggers` | list[str] | 该 lesson 的命中关键词（用于注入到 target_skill 的 Triggers:） |
| `frequency` | int | 出现次数（去重后），值越高 ROI 越大 |
| `sources` | list[str] | 来源：`commit:<hash>` 或 `work-note:<path>` 或 `kb:<url>` |
| `confidence` | enum | `low` / `med` / `high`（extract.py 启发式打分） |

## 来源格式

- `commit:<hash>` — `git log --pretty=format:%H` 抓到的 commit
- `work-note:<path>` — `docs/work-note/YYYY-MM-DD-*.md`
- `kb:<collection>/<name>` — KB public-knowledge / work-note

## 优先级

| Frequency | 默认 action |
|---|---|
| ≥ 3 | 高优先级 — 必进 Phase 2（user review） |
| 2 | 中优先级 — 进 Phase 2，但可标记「低频」 |
| 1 | 低优先级 — 仅当与 14 硬约束强相关才进 |

## 注入位置

所有 lesson 只进升级安全的 companion skill（**任何 skill 包之外**）：

- `~/.claude/skills/repo-medic-lessons/lessons/<target_skill>/<topic>.md` — lesson 文件
- `~/.claude/skills/repo-medic-lessons/SKILL.md` — 索引 + 按域 trigger 关键词

**绝不写 `~/.claude/skills/<target_skill>/` 内部**（SKILL.md / references/ / scripts/）：skill 目录升级时整体替换，包内改动和新增都会丢。companion skill 不随任何版本发布，升级永远碰不到。

每条 lesson 必须**只归入一个 target_skill 桶**（避免重复 + 单文件权威源）。

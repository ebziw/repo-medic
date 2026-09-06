---
name: evolve
description: repo-medic 自进化 — 收集当前项目最近的坑 + 经验，蒸馏成可注入 SKILL.md 的规则，避免未来踩同样坑。扫描 git log + docs/work-note/，聚类后用户审核，写入 sub-skill。Triggers: 踩坑, 经验, 教训, 蒸馏, 蒸馏, postmortem, retrospective, 进化, lessons learned, pitfall, evolve, 项目回顾, KB 反哺, self-improve
metadata:
  type: ops
  scope: public
---

# evolve — repo-medic 自进化

self-contained skill。把"最近踩的坑"蒸馏成 SKILL.md 可注入的规则，让未来使用不再踩同样坑。

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Collect sources

- [ ] **Read** `references/lesson-schema.md` (lesson 提取格式)
- [ ] **设时间窗**: 默认 `--since 7d`（用户可改 1d / 30d / since-last-tag）
- [ ] **scan git log**: 提取 commit message + body（用 `git log --since=... --pretty=full`）
- [ ] **scan work-notes**: 读 `docs/work-note/*.md` 正则匹配 `**Symptom**:` / `**Cause**:` / `**Fix**:` 字段
- [ ] **可选**：scan KB public-knowledge 命中"教训"类内容
- [ ] **Run** `python scripts/extract.py --since 7d --repo .` 提取候选
- [ ] 🛑 **GATE**: 提取完成 + 输出候选列表给用户

### Phase 1: Distill (candidate → lesson)

- [ ] **去重**: 相似 Symptom/Cause 合并
- [ ] **频率排序**: 出现 ≥ 2 次的优先（高 ROI）
- [ ] **分类打标**: 每条 lesson 标一个 tag（DB / deploy / config / frontend / general）
- [ ] **filter 范围**: 跳过与 repo-medic 无关的（用户业务逻辑、第三方 bug 等）
- [ ] **抽象成规则**: 把具体 case 抽成可复用的「如遇 X，做 Y」模式
- [ ] 🛑 **GATE**: 蒸馏后 ≤ 10 条候选给用户看（> 10 = 没收敛，重抽）

### Phase 2: User review

- [ ] **逐条给用户**: 显示「候选 N: ...」+ 命中 source (commit/work-note)
- [ ] **用户确认**: 接受 / 拒绝 / 修改每条
- [ ] **用户指定 target sub-skill**: 每条选归入哪个 skill 的 lessons 桶（py-improve / doc-reorg / db-tweak / vue-improve / config-base）
- [ ] 🛑 **GATE**: 用户逐条 OK 才能进 Phase 3

### Phase 3: Inject（只做加法 — 永不改 skill 包内文件）

- [ ] **lessons 目录**: 写到 `~/.claude/skills/repo-medic-lessons/lessons/<target-skill>/<topic>.md`（首次运行先建目录）。**绝不写进任何 skill 自己的目录** — skill 目录升级时整体替换，写进去的迟早丢失
- [ ] **索引更新**: 维护 `~/.claude/skills/repo-medic-lessons/SKILL.md` — 每条 lesson 一行摘要 + 按域积累 trigger 关键词（骨架见 `templates/lessons-skill.md`）
- [ ] **commit**: 1 commit = 1 lesson（铁律 2）
- [ ] 🛑 **GATE**: diff 给用户看 + 用户 OK 才能 commit

### Phase 4: Verify + Share

- [ ] **tests pass**: sub-skill 测试或 smoke test
- [ ] **KB 同步**（可选）: 推到所配 KB 端点的 public-knowledge 集合（未配 KB 系统则跳过）
- [ ] **work-note**: 写 `docs/work-note/<date>-evolve-extract.md` 记录本轮蒸馏
- [ ] **零包内写入**: 不往 `evolve/` 或任何其他 skill 目录添加内容 — 持久产出只进 `repo-medic-lessons/`

---

## 包含

| 路径 | 内容 |
|---|---|
| `scripts/extract.py` | git log + work-notes 提取器（输出候选 lesson） |
| `templates/lesson.md` | lesson 注入格式模板 |
| `references/lesson-schema.md` | 提取字段定义（Symptom / Cause / Fix / Frequency） |

## 使用

```bash
# 默认扫描最近 7 天
python scripts/extract.py --repo .

# 自定义时间窗 + 输出到文件
python scripts/extract.py --repo . --since 30d --output lessons-candidates.md

# 限 commit 数
python scripts/extract.py --repo . --max-commits 100

# JSON 给后续脚本消费
python scripts/extract.py --repo . --json | jq '.candidates[].tag' | sort | uniq -c
```

输出是候选列表（含来源 commit/work-note 链接 + 频率）。用户审核后再 inject 到目标 sub-skill。

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 (YAGNI)**: extract.py 只用 stdlib（git log 是 subprocess，no pygit2）。
2. **commit 颗粒度**: 1 lesson = 1 commit。
3. **默认回滚 = git revert**。**绝对禁止 `git reset --hard`**。
4. **死代码证明**: 不适用（extract 是临时脚本，不入 sub-skill 长期代码）。
5. **TDD**: 不适用（一次性提取 + 人工审核）。
6. **commit 前全绿**: 注入 lesson 后跑 sub-skill smoke test。
7. **prod 锁定**: 不直接动 prod 项目 sub-skill 的 SKILL.md — 先在 fork 或 worktree 试。
8. **宁缺勿伪**: extract 输出含 source 链接（commit hash + work-note 文件），用户可验证。
9. **DB 删除**: 不适用。
10. **批量先测最小**: `extract.py --since 1d` 先小范围跑 + 校准，再扩到 30d。
11. **daemon 4 步独立**: 不适用。
12. **buffer 所有权**: 不适用。
13. **hash 产物整目录同步**: 不适用。
14. **部署验证实际生效**: lesson 注入后跑 sub-skill smoke test + 用户实际使用验证 1 次。

## 关联

- `/repo-medic` — meta 入口
- 所有其他 sub-skill — evolve 的 inject target
- `docs/work-note/` — 数据源（CLAUDE.md 强制格式 Symptom/Cause/Fix）

## 仓库

github.com/ebziw/repo-medic — Apache-2.0。

# {lesson.symptom}

**Symptom**: {具体错误/现象, 含数字+版本+环境, 例 "Claude Sonnet 4.5 在 50K token 后 tone drift 中文回复出现 '在当今时代' 套话"}

**Cause**: {根因分析, 例 "Lost-in-the-middle 衰减 + 中文语料风格化训练偏差"}

**Fix**: {解决方案 + 引用, 例 "section-by-section 而非 whole-piece (参考 SuperWriter ACL 2026)"}

## 来源

- `commit:<hash>` — `{commit_message}`
- `work-note:<path>` — `{date}-{slug}.md`

## 频率

{frequency} 次（去重后）

## 触发词

{comma-separated 关键词列表 — 用于注入 target_skill 的 frontmatter description Triggers:}

## 关联硬约束

参考 14 硬约束 #{references}

---
name: doc-reorg
description: 目录 + 文档 + 文件一次性整理 — git mv 重命名、tmp 归档、脚本归类、debug 产物清理、文档分类归档（MRD/PRD/ARCH/DESIGN/TEST/RESEARCH）、env.md/deploy.md 同步。Triggers: 目录整理, 文件归档, tmp 清理, 文档分类, README, 模板, env, deploy, git mv, file reorganization, document classification, archive
metadata:
  type: domain
  scope: public
---

# doc-reorg — 目录 + 文档整理

self-contained skill。一次调用完成目录重构和文档归档。

## 包含

| 路径 | 内容 |
|---|---|
| `references/dir-restructure.md` | 7 phases（snapshot → 脚本归类 → tmp → debug → 合并 → 归档） |
| `references/doc-reorganize.md` | 5 phases（盘点 → 六分类 → env/deploy 同步 → 模板 → 一致性） |

## 使用流程

按 dir-restructure.md Phase 0-6 执行；完成后接 doc-reorganize.md Phase 1-5。

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 + 零提前防御 (YAGNI)**: 只用 stdlib + 已装库。不为假设风险提前加 try/except / retry / fallback / 抽象层。
2. **commit 颗粒度**: 1 逻辑单元 = 1 commit，独立可回滚。
3. **默认回滚 = rsync 备份还原** (无损)。**绝对禁止 `git reset --hard`**。
4. **死代码证明需 7 步 checklist**: 静态引用 + 文本搜索 + 框架注册 + export + 动态调用 + 测试/生成 + 用户签字。0 caller grep ≠ 证明。
5. **TDD 按场景分 4 模式**: Characterization / Red-Green / Structural / Regression。
6. **commit 前全量测试全绿**，不破 CI。
7. **prod 锁定**: 不动线上代码，owner 显式授权才动。
8. **宁缺勿伪**: 不确定的事实留 TODO，不编。校验靠 grep / codegraph / pyright 实测。
9. **DB 删除必走退场流水线**: DROP 前 RENAME → PLAN_DELETE_<原名>。**doc-reorg 范围内**：删除 doc 文件前先确认无外部引用。
10. **批量任务先测最小**: 任何批量操作先选最小样本 (1-10) 跑通 + 计时，按比例推全量耗时。**禁止直接开最大集合**。
11. **daemon / 服务代码改动 4 步独立**: ①本地 Edit ②本地 py_compile 验证 ③scp 上传 + 清 __pycache__ ④systemctl restart + pgrep 验证 PID 变了。
12. **buffer 所有权被转移**: 缓存方必须保留副本，每次传递前拷贝。
13. **hash 化构建产物必须整目录同步**: 前端 chunk 名带 hash — 只推改的文件 → index.html 引用新 hash → 缺 chunk → MIME text/html 404。
14. **部署/发布后必须验证实际生效产物标识**: 脚本输出 "✓ done" ≠ 部署成功。

## 关联

- `/repo-medic` — meta 入口
- `/py-improve` — 重构后目录归档（先 py-improve 改善代码，再 doc-reorg 整理）
- `/db-tweak` — schema 变更后文档同步

## 仓库

github.com/ebziw/repo-medic — Apache-2.0。

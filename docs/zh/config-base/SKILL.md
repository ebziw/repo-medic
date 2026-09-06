---
name: config-base
description: repo-medic 依赖的工具链 bootstrap — 检测 + 安装 + 升级所有支撑组件（ruff/mypy/codegraph/node/psql 等）。运行 `python scripts/tools.py check` 看到状态表，`install` 自动安装缺失项。Triggers: tool missing, 配置, 环境 bootstrap, 安装依赖, install deps, bootstrap, setup, 环境检查, dependency check
metadata:
  type: ops
  scope: public
---

# config-base — repo-medic 工具链 bootstrap

self-contained skill。检测、安装、升级 repo-medic 所有 sub-skill 依赖的工具。

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Detect current state

- [ ] **Run** `python scripts/tools.py check`
- [ ] **Read** 输出表格，标 OK / MISSING / OUTDATED / ERROR
- [ ] **Cross-check** 与 sub-skill 需求清单（Phase 1 列出）
- [ ] 🛑 **GATE**: 报告给用户 + 用户确认下一步动作（不要擅自 install）

### Phase 1: Identify user needs

- [ ] 哪几个 sub-skill 实际会用到？只装用得上的（YAGNI 铁律 1）
- [ ] py-improve 用 → ruff/mypy/vulture/bandit/radon/pyright/pytest + codegraph + MCP deps
- [ ] doc-reorg 用 → rg + tree + git（git 通常已装）
- [ ] db-tweak 用 → psql + pg_dump
- [ ] vue-improve 用 → node ≥ 18 + npm/pnpm + 项目本地 vite/vitest
- [ ] 🛑 **GATE**: 列完需求 + 用户 OK 才能进 Phase 2

### Phase 2: Install missing

- [ ] **Dry-run first**: `python scripts/tools.py install --all` （不传 --yes 看会装什么）
- [ ] **Review** 输出，逐项确认是否需要装
- [ ] **实际安装**: `python scripts/tools.py install --all --yes` 或单个 `python scripts/tools.py install <name> --yes`
- [ ] **Verify**: install 后再跑 `python scripts/tools.py check` 看是否变 OK
- [ ] 🛑 **GATE**: install 完 check 表应全 OK，缺项必须有合理理由

### Phase 3: Configure

- [ ] **MCP server 注册**: `~/.claude/settings.json` 配 `python_refactor_server` 路径
- [ ] **PATH 检查**: tool 在 PATH 中（脚本自动跑 `which` 验证）
- [ ] **环境变量**: 检查 sub-skill 用的 env var（各家 provider 的 API token / DATABASE_URL 等）— **不在这管**，各 sub-skill 自己配
- [ ] **Optional**: 写 `~/.config/repo-medic/config.toml` 记录工具路径（升级时 diff）
- [ ] 🛑 **GATE**: 检查 + 注册 完才能说"环境 ready"

### Phase 4: Document + Share

- [ ] **work-note**（如改环境）: 写 docs/work-note/<date>-env-bootstrap.md
- [ ] **不做**: 不自动 commit / 不动 prod env / 不替用户决定装什么（铁律 7 + 1）

---

## 工具清单（manifest）

| 类别 | 工具 | 用途 sub-skill | 平台安装方式 |
|---|---|---|---|
| python | python ≥ 3.12 | py-improve + db-tweak MCP | system |
| python | uv | 包管理器（处理 Debian typing_extensions 冲突） | system |
| python | ruff, mypy, vulture, bandit, radon, pyright | py-improve lint/type/audit | uv pip install |
| python | pytest | py-improve 测试 | uv pip install |
| node | node ≥ 18, npm, pnpm | vue-improve + codegraph | system |
| system | codegraph | py-improve 引用图 | npm install -g @optave/codegraph |
| system | rg (ripgrep), tree | doc-reorg + 通用 | apt/brew |
| db | psql, pg_dump | db-tweak | apt (postgresql-client) |
| mcp | mcp + fastapi + uvicorn | py-improve 的 MCP server | uv pip install |

完整清单（含 min_version）：见 `scripts/tools.py` 的 `TOOLS` list。

## 使用

```bash
# 检测当前环境
python scripts/tools.py check
# 输出:
# TOOL          CAT     STATUS   VERSION              REQUIRED
# -----------------------------------------------------------------
# python        python  OK       Python 3.14.3        3.12
# ruff          python  MISSING  -                    0.3
# mypy          python  MISSING  -                    1.8
# ...
# Total: 17  OK=2  MISSING=8  OUTDATED=1  ERROR=6

# JSON 输出（脚本消费）
python scripts/tools.py check --json

# Dry-run install（看会装什么，不真装）
python scripts/tools.py install --all
# 输出:
# Will install: ruff, mypy, vulture, ...
# Use --yes to proceed

# 实际装全部缺失项
python scripts/tools.py install --all --yes

# 装单个
python scripts/tools.py install ruff --yes

# 装完后重新检测
python scripts/tools.py check
```

## 跨平台

| 平台 | 检测方式 | 包安装优先级 |
|---|---|---|
| Linux | `which` + `subprocess --version` | `uv pip install --system` (Debian typing_extensions 兼容) → `apt-get install` |
| macOS | 同 Linux | `brew install` → `uv pip install --system` |
| Windows | 同 Linux | `pip install --user` → `winget install` |

添加新平台工具：编辑 `scripts/tools.py` 的 `TOOLS` list，加 `install_cmd_<platform>` 字段。

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 (YAGNI)**: 不为假设场景装工具（不预先装 vue-improve 工具除非用户说要用）。
2. **commit 颗粒度**: env 变更通常不进 git（live config 铁律），单独 work-note。
3. **默认回滚**: **install 不可逆** — 强 YAGNI + 先 dry-run。
4. **死代码**: 不适用（脚本本身）。
5. **TDD**: 不适用。
6. **不破 CI**: install 后跑 `check` 验证。
7. **prod 锁定**: 不改 prod env，不替 user 装无询问工具。
8. **宁缺勿伪**: 检测失败 = 真实缺失，不假装已装。
9. **DB**: 不适用（本 skill 不删 DB）。
10. **批量先测最小**: `check` 先跑一遍再 `install --all`。
11. **daemon 4 步独立**: install 后用 `which` + `--version` 独立验证（不链式 &&）。
12. **buffer 所有权**: 不适用。
13. **hash 产物同步**: 不适用（工具链无 hash build）。
14. **部署验证实际生效**: `check` 输出 OK = 真的装好了，不是脚本退出 0。

## 关联

- `/repo-medic` — meta 入口
- `/py-improve` — 主要消费者（ruff/mypy/codegraph）
- `/doc-reorg` — 消费者（rg/tree）
- `/db-tweak` — 消费者（psql）
- `/vue-improve` — 消费者（node + vite 项目本地）

## 仓库

github.com/ebziw/repo-medic — Apache-2.0。manifest 在 `scripts/tools.py`，编辑 `TOOLS` list 加新工具。

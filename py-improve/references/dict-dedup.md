# Dict Dedup Subflow (project-doctor 子工作流)

> 触发: 用户说 "字典去重" / "字典整合" / "常量冲突" / "id 定义重复" / "dedup dictionary" / "统一错误码" / "enum 分散" / "合并重复定义"
> 范围: 仅字典/枚举/常量定义 (id:描述 / status / error_code / role / permission 等)
> 危害: 同 id 多个定义矛盾 → 程序分支走错路径 → 难查的 bug (不抛异常, 只行为漂移)
> **风格**: ponytail 极简. dict 只一个家, 别处只允许 re-export. 冲突检测 > 自动合并.

## 4 类问题分类 (核心)

> 路由入口: SKILL.md 路由表 Dict Dedup Subflow 行. **完整定义 = 本文档自身** — 4 类问题分类 (下表) + Phase 0-5 检测/处理 pipeline + YAGNI + 已知坑.

| 类型 | 含义 | 处理 |
|------|------|------|
| **DUPLICATE** | 完全相同的多份定义 (值/结构一致) | 自动合并: 留 1 处权威, 别处改 import / re-export |
| **CONFLICT** | 同名字段值不一致 (矛盾定义) | **停下问人** — 哪个是真值? 不自动覆盖 |
| **STALE** | 无 caller 的过时副本 (可删) | 删 + 同步 git rm |
| **REVERSE-MISSING** | 有 a→b 但缺 b→a 反查 (lookup 表常漏) | 补反向 dict, 或统一用 bidict |

## 目录

- [Phase 0: 快速扫描 (30s)](#phase-0-快速扫描-30s)
1. [Phase 1: 字典定义扫描](#phase-1-字典定义扫描)
2. [Phase 2: 4 类通用检测 pipeline](#phase-2-4-类通用检测-pipeline)
3. [Phase 3: 矛盾检测 + 冲突报告](#phase-3-矛盾检测--冲突报告)
4. [Phase 4: 选定权威源 + 合并](#phase-4-选定权威源--合并)
5. [Phase 5: caller 迁移 + 验证](#phase-5-caller-迁移--验证)
6. [典型案例: _LEVEL_CFG CONFLICT](dict-dedup-case-levelcfg.md)

---

## Phase 0: 快速扫描 (30s)

> **真实场景 80% 是 DUPLICATE + CONFLICT**, STALE/REVERSE-MISSING 是少数.
> 完整 Phase 1-2 要扫 AST + 全文 grep, 慢. 先跑这个, 看清单再决定要不要深扫.

```bash
# 0.1 找所有 module-level dict 字面量 (一行 grep, 不跑 Python)
grep -rnE '^\s*_*[A-Z][A-Z_0-9]+_*\s*[:=]\s*[\{\[]' ${REPO_ROOT}/ \
  --include="*.py" | grep -v test | sort -t: -k3 > /tmp/dict-snapshot.txt

# 0.2 计数 + 按 dict 名字聚合
awk -F: '{print $3}' /tmp/dict-snapshot.txt | sort | uniq -c | sort -rn | head -30
# 输出:
#   8 _LEVEL_CFG          ← 定义了 8 处? 必有问题
#   3 _PRESET_DOMAIN_MAP
#   2 STAGES
#   1 _DEPTH_WHITELIST
```

**判断**:

| 计数 | 含义 | 下一步 |
|---|---|---|
| **≥3 处同名** | 必有重复或矛盾 | 跑 Phase 2 详细 fingerprint |
| **恰好 2 处同名** | 可能是 DUPLICATE 也可能是 CONFLICT | 跑 Phase 2 |
| **1 处** | 单一定义, 跳过 | (除非 caller 散落) |

**适用场景**:
- 用户问"代码里 X 有没有重复定义" → 直接跑 0.1+0.2
- 完整 dict dedup 跑前先用 0.2 看预算 — 30 处以上慢慢做, 10 处以下快速合并
- CI gate: 0.2 输出 > 阈值 (e.g. 5 处同名) 直接 fail

---

## Phase 1: 字典定义扫描

**目的**: 找出所有 id:描述 风格的字典 / 枚举 / 常量定义.

```bash
# 1.1 Python: 找所有 Dict/Enum/常量定义
grep -rnE '^\s*[A-Z][A-Z_0-9]+\s*[:=]' ${REPO_ROOT}/ --include="*.py" | grep -v test | head -50

# 1.2 找 ERROR_CODE / STATUS / ROLE / PERMISSION 命名集中地
find ${REPO_ROOT} -type f \( -name "*error*.py" -o -name "*status*.py" -o -name "*role*.py" -o -name "*permission*.py" -o -name "*enum*.py" -o -name "*constant*.py" \) -not -path '*/.git/*' | head

# 1.3 Go: 找 const 块
grep -rnE '^\s*(const|var)\s+[A-Z][A-Z_]+\s*=' ${REPO_ROOT}/ --include="*.go" | head -30

# 1.4 Node/TS: 找 enum / const 对象
grep -rnE 'export\s+(const|enum)\s+[A-Z][A-Z_]+' ${REPO_ROOT}/ --include="*.ts" --include="*.js" | head -30

# 1.5 找 ID 命名相似但散落多处的常量 (例: USER_STATUS_ACTIVE 在 a.py 和 b.py 各定义)
grep -rnE 'USER_(STATUS|ROLE)_[A-Z]+|ERROR_CODE_[A-Z_]+|ORDER_STATE_[A-Z]+' ${REPO_ROOT}/ --include="*.py" | head -50
```

**deliverable**: `docs/audit/<date>-dict-snapshot.md` 含所有 id 命名空间清单.

---

## Phase 2: 同 id 多源检测 (含 4 类分类)

**核心检测**: 同一个 id 字符串在多处定义 (尤其描述/数值不一致). 按 fingerprint 聚类后分 4 类.

### 2.1 Python: 按 fingerprint (json.dumps sorted) 聚类

```bash
# 2.1.1 找所有 module-level dict/set/list 字面量
grep -rnE '^\s*_*[A-Z][A-Z_0-9]+_*\s*[:=]\s*[\{\[]' ${REPO_ROOT}/ --include="*.py" | grep -v test | head -100
```

```python
# 2.1.2 fingerprint 聚类 + 4 类分类
python3 << 'PYEOF'
import ast, pathlib, json, collections

repo = pathlib.Path("${REPO_ROOT}")
by_name = collections.defaultdict(list)  # name -> [(file, line, fp, value)]

for py in repo.rglob("*.py"):
    if "test" in str(py) or "/.venv/" in str(py):
        continue
    try:
        src = py.read_text()
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not (isinstance(tgt, ast.Name) and tgt.id.isupper()):
                continue
            try:
                val = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue  # 跳过不可字面量求值的 (含函数调用等)
            # dict/set 转 sorted JSON 当 fingerprint (顺序无关)
            if isinstance(val, (dict, set)):
                fp = json.dumps(val, sort_keys=True, ensure_ascii=False)
            else:
                fp = repr(val)
            by_name[tgt.id].append((str(py), node.lineno, fp, val))

# 输出 4 类
for name, defs in by_name.items():
    if len(defs) <= 1:
        continue
    fps = {d[2] for d in defs}
    files = {d[0] for d in defs}
    if len(fps) == 1:
        # 所有定义值一致 → DUPLICATE
        print(f"[DUPLICATE] {name} (value={fps.pop()[:80]}) in {len(defs)} places across {len(files)} files")
        for path, line, fp, val in defs:
            print(f"   {path}:{line}")
    elif len(fps) > 1:
        # 值不一致 → CONFLICT (必须问人)
        print(f"[CONFLICT] {name}")
        for path, line, fp, val in defs:
            print(f"   {path}:{line} = {fp[:80]}")
PYEOF
```

### 2.2 STALE 检测 (无 caller 的过时副本)

```bash
# 2.2.1 找所有 dict 字面量, 然后逐个检查是否被 import / 引用
python3 << 'PYEOF'
import ast, pathlib, sys

repo = pathlib.Path("${REPO_ROOT}")
defined = set()  # 所有被定义的 dict 名字

# 找定义
for py in repo.rglob("*.py"):
    if "test" in str(py) or "/.venv/" in str(py):
        continue
    try:
        tree = ast.parse(py.read_text())
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isupper():
                    defined.add(tgt.id)

# 找引用
referenced = set()
for py in repo.rglob("*.py"):
    try:
        src = py.read_text()
        tree = ast.parse(src)
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            referenced.add(node.id)
        elif isinstance(node, ast.Attribute):
            base = node
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                referenced.add(base.id)

# STALE: 定义了但没引用
stale = defined - referenced
for name in sorted(stale):
    if name.startswith("_"): continue
    print(f"[STALE] {name} (defined but not referenced)")
PYEOF
```

### 2.3 REVERSE-MISSING 检测 (有 a→b 但缺 b→a)

```python
# 2.3.1 检查每个 dict 是否有反向 lookup
python3 << 'PYEOF'
import ast, pathlib

repo = pathlib.Path("${REPO_ROOT}")
for py in repo.rglob("*.py"):
    if "test" in str(py) or "/.venv/" in str(py):
        continue
    try:
        tree = ast.parse(py.read_text())
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not (isinstance(tgt, ast.Name) and tgt.id.isupper()):
                continue
            try:
                val = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                continue
            if not isinstance(val, dict):
                continue
            # 启发式: dict 名字含 _MAP / _TO / _INDEX → 期望有反向
            if any(k in tgt.id for k in ("_MAP", "_TO_", "_INDEX", "_LOOKUP")):
                reverse = tgt.id + "_REVERSE"  # 常见命名
                # 全文搜反向是否存在
                # 简化: 只标记, 不强求
                keys_unique = len(set(str(v) for v in val.values())) == len(val)
                if keys_unique:
                    # value 唯一 → 反向有价值
                    print(f"[REVERSE-MISSING?] {tgt.id} at {py}:{node.lineno} (values unique, consider {reverse})")
PYEOF
```

**deliverable**: 候选重复 id 清单 + 每处定义位置 + 4 类分类 (DUPLICATE/CONFLICT/STALE/REVERSE-MISSING).

---

## Phase 3: 矛盾检测 + 冲突报告

**核心**: 同 id 多处定义的**值或描述是否一致**.

```bash
# 3.1 提取每个 id 在每处的"右侧值" (Python Dict 字面量)
python3 << 'PYEOF'
import ast, pathlib, sys, collections

repo = pathlib.Path("${REPO_ROOT}")
dup_report = collections.defaultdict(list)

for py in repo.rglob("*.py"):
    if "test" in str(py) or "/.venv/" in str(py):
        continue
    try:
        tree = ast.parse(py.read_text())
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            # from typing import Final / ClassVar
            pass
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id.isupper():
                    try:
                        val = ast.unparse(node.value)
                        dup_report[tgt.id].append((str(py), node.lineno, val))
                    except Exception:
                        pass

# 找出值不一致的
for name, defs in dup_report.items():
    if len(defs) > 1:
        values = {d[2] for d in defs}
        if len(values) > 1:
            print(f"⚠ CONFLICT: {name}")
            for path, line, val in defs:
                print(f"   {path}:{line} = {val}")
        elif len(values) == 1 and len({d[0] for d in defs}) > 1:
            print(f"✓ DUPLICATE-OK: {name} = {values.pop()} (in {len(defs)} files)")
PYEOF
```

**冲突分级**:

| 类型 | 描述 | 严重度 |
|------|------|--------|
| **CONFLICT (值不同)** | 同 id 不同值 | 🔴 Critical — 必须合并 |
| **DUPLICATE-OK (值同)** | 同 id 相同值散落 | 🟡 Warning — 建议合并 (DRY) |
| **LEGACY (有 deprecation 标记)** | 旧版带 `_LEGACY` 后缀 | 🟢 OK — 保留 + 加注释 |

**真值识别 (CONFLICT 必做, 不靠算法猜)**:

CONFLICT 必须由人/证据决定哪个是真值. 任何启发式 (多数票/最近改/最长字段) 都可能错.

| 证据来源 | 用法 | 权重 |
|---------|------|------|
| **代码注释** | "权威源"/"统一入口"/"single source of truth" 等字样 | 🔴 强 |
| **git log** | `git log -p <file>` 看哪个是新增哪个是历史遗留 | 🔴 强 |
| **文件 mtime** | `stat -c %y <file>` 时间戳最近的优先 | 🟡 中 |
| **调用频次** | `grep -rn "<NAME>"` 谁被引用多, 谁更可能是设计 API | 🟡 中 |
| **import 链** | 谁是源头 module (被多个其他模块 import), 谁就是权威 | 🟡 中 |
| **测试覆盖** | 有 test 覆盖那份更可能是设计 (contract), 没测试那份更可能是临时副本 | 🟢 弱 |

**典型判断流程** (案例 `_LEVEL_CFG`):

1. `git log --follow backend/core/stages/_config.py` → 新版 mtime 后, 加了"统一入口"注释 → 🔴 权威
2. `git log --follow backend/core/research_phases.py` → 旧版 mtime 早, 长期没动 → 旧副本
3. `grep -rn "_LEVEL_CFG" backend/` → 4 处 import, 2 旧 2 新, import 链不统一
4. **决策**: 留 `_config.py`, 删 `research_phases.py` 那份, 旧 caller 改 import

**为什么不能算法决策**:

| 自动决策 | 为什么错 |
|---------|---------|
| 按"多数票" | 数值 500 vs 300 都是合理范围, 哪边写错不知道 |
| 按"最近修改" | admin 改了可能是因为运营调整, 不是 bug 修复 |
| 按"最长那个" | 字段多不代表更权威, 可能多出的是 noise |
| 按"权威源"标记 | 如果没标记权威源, 算法不知道 |

**真值识别 > 自动合并**. 本案靠 `commit message + 文件 mtime + 代码注释 + import 链` 四条证据, 不是算法猜的.

**deliverable**: `docs/audit/<date>-dict-conflicts.md` 含:
- Critical 冲突清单 (值不同)
- Warning 重复清单 (值同, 散落)
- 矛盾定义决策 (谁权威)

---

## Phase 4: 选定权威源 + 合并

**决策原则** (按优先级):

1. **官方/外部定义** (HTTP status code, ISO 标准, 协议常量) → 永不变, 直接引用, 不内联
2. **业务核心字典** (USER_ROLE / ORDER_STATE / ERROR_CODE) → 集中到 `constants/` 或 `enums/` 顶层模块
3. **局部字典** (单模块内部状态) → 留在原文件, 但加 `__all__` 显式 export
4. **测试 fixture** → 不合并, 测试独立

**执行步骤**:

```bash
# 4.1 建权威目录
mkdir -p ${REPO_ROOT}/src/constants  # 按项目结构, 例 Python 是 src/, Go 是 pkg/

# 4.2 写权威定义 (例 user_role.py)
cat > ${REPO_ROOT}/src/constants/user_role.py << 'EOF'
"""User role constants. Single source of truth.

All other modules MUST import from here, never redefine.
"""
from enum import Enum

class UserRole(str, Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
EOF

# 4.3 删/改其他位置的重复定义
# 例: 删除 a.py 里的 USER_ROLE_DICT, b.py 里的 USER_ROLES 局部定义
# 改: from src.constants.user_role import UserRole

# 4.4 单次合并 1 commit
git add src/constants/
git rm <旧定义文件 if 整文件删除>
git commit -m "refactor(dict): consolidate <name> to src/constants/ (<date>)"
```

**反模式 (不要做)**:
- ❌ 在每个旧定义处都加 `from constants import *` 然后保留旧名 — 双源仍同步风险
- ❌ 用 dataclass 替代 enum — 失去穷尽性检查
- ❌ 把所有字典塞一个 mega 文件 — 文件臃肿, 不如按域分多个

---

## Phase 5: caller 迁移 + 验证

**caller 迁移**: 把所有旧位置的引用改成新位置.

```bash
# 5.1 找 caller
grep -rn "USER_ROLE_\|<OLD_NAME>" ${REPO_ROOT}/ --include="*.py" | grep -v "src/constants/"

# 5.2 批量替换 (用 codemod 或 sed)
# 例: 把所有 "from a import USER_ROLE_DICT" 改成 "from src.constants.user_role import UserRole"
# 然后 dict[key] → UserRole(key)

# 5.3 验证测试 + lint
${TEST_RUNNER}
ruff check ${REPO_ROOT}/
mypy ${REPO_ROOT}/
```

**结束标准**:
- `grep -rn "<OLD_NAME>"` 0 命中 (除文档/注释)
- `grep -rnE "^\s*[A-Z][A-Z_0-9]+\s*=\s*["\x27]" ${REPO_ROOT}/ --include="*.py" | grep -v "src/constants/" | grep -v test` 0 命中 (无散落定义)
- `grep -rnE "if .* in USER_ROLE_DICT" ${REPO_ROOT}/` 全用新 import
- ${TEST_RUNNER} 全绿
- type checker 0 错误

**回滚**: 走通用硬约束 #3 (rsync 备份 + git revert)

---

## YAGNI 注意 (零提前防御)

- ❌ 不要为"将来可能加新 status"提前写 metaclass 注册表
- ❌ 不要把字典定义做动态加载 (除非项目已经用插件系统)
- ❌ 不要为不同 namespace 的 id 加版本号 (例: USER_ROLE_V1_USER) — 真需要时再加
- ✅ **现状优先**: 出现几处就合并几处, 不为假想需求提前抽象

---

## 已知坑

| 坑 | 现象 | 解决 |
|---|---|---|
| `str` enum vs `int` enum 选错 | DB 存 int, 代码用 str, 反序列化错 | 业务字典用 `str` enum, 协议字典 (HTTP status) 跟随原标准 |
| 测试 fixture 用了旧 dict 字面量 | 合并后测试 broken | grep 测试文件, 同步迁移 (测试可改) |
| 第三方库 enum 不让继承 | 想加业务方法失败 | 不要继承第三方 enum, 自己 wrap 一层 |
| enum 值含特殊字符 (空格/连字符) | 反序列化失败 | 只用 ASCII alphanumeric + underscore |
| 字典在数据库迁移脚本里也用了 | DB 和 代码不同步 | 字典唯一源 = 代码, DB 用 lookup table + migration 同步 |

---

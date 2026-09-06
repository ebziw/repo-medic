# Dict Dedup — 典型案例: _LEVEL_CFG CONFLICT

> 90 行 case study: 自 [dict-dedup.md](dict-dedup.md) §Phase 3 真值识别 的"典型判断流程"拆出展开 (原全档 L434+ 位置, 重组后以链接章节为准)
> 主文档见 [dict-dedup.md](dict-dedup.md): Phase 0-5 (含 4 类问题分类 + CONFLICT 真值识别证据表) + YAGNI + 已知坑

## 典型案例: `_LEVEL_CFG` CONFLICT

> **真实 bug 教学案例**. 这是为什么字典整合 skill 必须存在的核心原因 — 不是 dedup, 是发现潜在 silent bug.

### 业务背景

`_LEVEL_CFG` 定义 4 种研究深度的写作参数 (学术研究 / 专业讨论 / 严肃媒体 / 社交媒体):

```python
# 学术研究配置示例
"学术研究": {
    "max_tokens": 384000,      # LLM 输出上限
    "max_chars": 35000,         # 合成阶段字符上限
    "thinking": True/False,     # 是否启用思考链
    "search_web": 20,           # 外网搜索次数
    "search_academic": 6,       # 学术引擎搜索次数
    "compress": "full",         # 压缩模式
    "mimo_eval": True,          # 是否启用 mimo 模型评估
    "glm_review": True,         # 是否启用 glm 复审
    # ... 其他参数
}
```

### 这次碰到的 bug

代码里有**两份完全独立**的 `_LEVEL_CFG`, 两份只差 1 行 (`thinking` 字段 True vs False):

```python
# 位置 1: stages/_config.py:34 (新版, 应该是真值)
"学术研究": { ..., "thinking": False, ... }
"专业讨论": { ..., "thinking": False, ... }

# 位置 2: research_phases.py:952 (旧版, 未删)
"学术研究": { ..., "thinking": True, ... }    # ← 矛盾!
"专业讨论": { ..., "thinking": True, ... }    # ← 矛盾!
```

**实际生效取决于 import 链**:

| caller | 从哪 import | 用哪份 | thinking 值 |
|--------|-----------|--------|------------|
| `stage_compose.py` | `stages._config` | **新版** | False |
| `research_phases.py:968` `_tokens_for_length` | 本地副本 | **旧版** | True |
| `research_pipeline.py` | `research_phases` | **旧版** | True |

### 后果

1. **同一深度在不同阶段行为不一致** — compose 阶段认为"学术研究不开 thinking", 但 token 计算认为"要开", LLM 实际请求 token 上限不同, **可能爆 token / 截断**
2. **用户看不出来** — 没有 WARN, 调用方以为拿到了 `_LEVEL_CFG`, 实际拿到了过期副本
3. **测试无法发现** — 测试只测函数返回值, 不验证"两份 dict 是否一致"

### DUPLICATE vs CONFLICT 对比 (本案教学)

| 维度 | DUPLICATE (无害) | **CONFLICT (本案)** |
|------|----------------|-------------------|
| 表现 | 两份 dict **完全相同** | 字段值**不一致** |
| 风险 | 仅维护负担 (改一处忘另一处) | 行为不一致, **silent bug** |
| 检测 | grep + 指纹匹配即发现 | **必须逐字段 diff** |
| 修复 | 删一份 + 改 re-export | **必须先判断哪个是真值才能动** |

### 真值识别 (本案关键)

> 真值识别 4 条证据表见 Phase 3. 本案具体应用:

1. **`stages/_config.py` 文件 mtime 更新** — commit `2b4a9b4` 简化后改的
2. **`research_phases.py:952` 长期没动** — 在 commit `70d102596` 前就在了
3. **代码注释明示** — `_config.py` 标 "统一入口"
4. **→ 删 `research_phases.py` 那份**, 所有 caller 改 import 自 `_config`

### 处理流程 (本案教学)

1. AST 对比两处 fingerprint → 标 CONFLICT
2. 输出两处逐字段 diff (`thinking: False vs True`)
3. **停** — 让人/查 git history 决策真值
4. 找到真值后:
   - 权威源移到 `constants/level_cfg.py`
   - `stages/_config.py` 改 `from constants.level_cfg import LEVEL_CFG` (re-export 兼容老 import)
   - `research_phases.py:952` **整段删除** (不 re-export — 旧 API 已误用)
   - 所有 caller 改 import
   - commit msg: `fix(dict): resolve _LEVEL_CFG CONFLICT, decided _config.py is truth (thinking=False)`
5. 跑回归, baseline 行为不变 (新版本下所有阶段 thinking 统一 False, LLM 请求 token 上限一致)

### 核心教训

- **字典整合 skill 的核心价值不是 dedup, 是发现 silent bug**.
- CONFLICT 比 DUPLICATE 危险 100 倍: DUPLICATE 只增加维护负担, CONFLICT 直接让程序行为漂移.
- 真值识别必须靠证据 (git log / mtime / 注释), 不是启发式算法.
- 自动化工具永远不能替你做"哪个是真值"这个决策.
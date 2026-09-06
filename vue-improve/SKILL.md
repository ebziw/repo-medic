---
name: vue-improve
description: Vue 3 + TypeScript + Vite + Pinia 前端代码改进。包含组件设计、setup TDZ 坑、watchEffect 陷阱、Pinia store 模式、Vite build 优化、chunk hash 部署。用于触发：Vue 组件审查、Pinia store、setup 函数、watch / watchEffect、Vite 打包优化、前端 bundle 分析。
metadata:
  type: domain
  scope: public
---

# vue-improve — Vue 3 前端代码改进

self-contained skill。第一版骨架，references 待补充。可用部分：

## 包含

| 路径 | 内容 |
|---|---|
| `references/vue-best-practices.md` | 占位（首版空，下个版本填） |
| `references/vue-anti-patterns.md` | 占位（首版空） |
| `references/frontend-deploy.md` | 占位（首版空） |

## 已知坑（首版内置，v0.1）

### setup TDZ 立即回调引用后置绑定

```js
// BAD: watch 立即同步执行 cb，cb 引用后声明的变量 → ReferenceError
const user = ref(null)
watch(user, (val) => console.log(user.name))  // setup 期执行
const fetched = ref(null)  // 后声明

// GOOD: 后置绑定，或用 watchEffect 延迟
const fetched = ref(null)
const user = ref(null)
watch(user, (val) => console.log(user.value?.name, fetched.value))
```

### watchEffect 回调内写自身订阅源 = 无限循环

```js
// BAD
watchEffect(() => {
  if (data.value.length === 0) data.value = [1]  // 写回自身
})

// GOOD: 用 watch 或加 guard
let initialized = false
watchEffect(() => {
  if (!initialized && data.value.length === 0) {
    initialized = true
    data.value = [1]
  }
})
```

### 一次性消费 flag 泄漏

```js
// BAD: 状态已等于目标值时 watch 不触发
let pending = true
watch(loading, (val) => {
  if (val === false && pending) {
    pending = false
    doStuff()
  }
})

// GOOD: 快照比较
let prev = loading.value
watch(loading, (val) => {
  if (val !== prev) { prev = val; if (val === false) doStuff() }
})
```

### 解构遮蔽外层 ref

```js
// BAD
const [srcDoc, tgtDoc] = await Promise.all([fetchA(), fetchB()])
// srcDoc 遮蔽外层 ref → 后续访问错对象

// GOOD: 不同名前缀
const [firstDoc, secondDoc] = await Promise.all([...])
```

### Pinia store 解构丢失响应性

```js
// BAD
const { count } = useStore()  // 普通变量，count 变更不触发渲染

// GOOD
const store = useStore()  // 整个 store 引用保持响应
// 或用 storeToRefs
const { count } = storeToRefs(useStore())
```

## Vite 部署：chunk hash 同步

前端 build 产物 chunk 名带内容 hash（如 `index-abc123.js`）。只推改的文件 → index.html 引用新 hash → 缺 chunk → MIME `text/html` 404。

**部署后必做**：curl 验证新 index.html 引用的**每一个** entry/chunk URL 都返回 200。

```bash
# 部署后
curl -s https://example.com/ | grep -oE 'src="[^"]+"' | sed 's/src="//;s/"//' | \
  while read f; do
    code=$(curl -sI "https://example.com/$f" | head -1 | awk '{print $2}')
    [ "$code" = "200" ] || echo "MISSING: $f"
  done
```

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 + 零提前防御 (YAGNI)**: 只用 Vue 生态已装库 + Vite 默认配置，不为假设场景加 lodash / rxjs。
2. **commit 颗粒度**: 1 逻辑单元 = 1 commit（组件 + store + 测试同 commit）。
3. **默认回滚 = git revert**（前端无 rsync）。**绝对禁止 `git reset --hard`**。
4. **死代码证明需 7 步 checklist**: 组件删除前确认无 router / 动态 import 引用。
5. **TDD**: Vue 组件用 Vitest + @vue/test-utils，Pinia store 单测。
6. **commit 前全量测试全绿**: `vitest run` + `vue-tsc --noEmit`。
7. **prod 锁定**: 部署前 staging 验证。
8. **宁缺勿伪**: 不编组件 prop 类型，TypeScript 严格模式打开。
9. **DB 删除**: 不适用（前端无 DB）。
10. **批量任务先测最小**: 大批量组件迁移先选 1 个目录 sample。
11. **daemon / 服务代码改动 4 步独立**: dev server 重启验证：`pgrep -af "vite"` 对比 PID。
12. **buffer 所有权被转移**: `postMessage` / `getDocument({data})` / buffer transfer — 缓存方保留副本，每次传递前拷贝。
13. **hash 化构建产物必须整目录同步**: 见上「Vite 部署」节。
14. **部署/发布后必须验证实际生效产物标识**: curl 验证新 hash 实际生效，不看脚本退出码。

## 关联

- `/repo-medic` — meta 入口
- `/py-improve` — 后端 API 配套审查（前端调的后端）
- `/doc-reorg` — 组件文档（README / storybook）整理

## 仓库

github.com/ebziw/repo-medic — Apache-2.0。vue-improve 当前为骨架，欢迎贡献完整 references。

---
name: vue-improve
description: Vue 3 + TypeScript + Vite + Pinia 前端代码改进。包含组件设计、setup TDZ 坑、watchEffect 陷阱、Pinia store 模式、Vite build 优化、chunk hash 部署。Triggers: Vue, 组件, Pinia, Vite, setup, watch, watchEffect, ref, 路由, bundle, chunk, TypeScript, TS, 前端, frontend, SPA, reactivity
metadata:
  type: domain
  scope: public
---

# vue-improve — Vue 3 前端代码改进

self-contained skill。第一版骨架，references 待补（欢迎贡献）。

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Reconnaissance

- [ ] **读现有 Vue 项目结构**: `package.json` + `vite.config.*` + `tsconfig.json` + `src/` 布局
- [ ] **列组件**: `find src -name "*.vue" | head -50` 摸规模
- [ ] **列 stores** (Pinia): `find src/stores -name "*.ts" 2>/dev/null`
- [ ] **列路由**: `find src/router -name "*.ts" 2>/dev/null`
- [ ] **bundle 当前大小**: `pnpm build && du -sh dist/` 或 `npm run build`
- [ ] 🛑 **GATE**: 摸清规模才能进 Phase 1（小项目 < 50 组件跳过重型优化）

### Phase 1: Anti-pattern scan

- [ ] **setup TDZ 引用后置绑定**: `rg "watch\(.*\)" src/ | head -20` 找可能 TDZ 风险
- [ ] **watchEffect 写自身订阅源**: `rg "watchEffect" src/`，人工 review 每个 callback
- [ ] **一次性消费 flag 泄漏**: `rg "let .* = true" src/ | rg -v "test"` 找 watch flag
- [ ] **解构遮蔽外层 ref**: `rg "const \[.*\] = .*await Promise.all" src/`
- [ ] **Pinia store 解构丢响应性**: `rg "const \{.*\} = use\w+Store\(\)" src/`（应为 `storeToRefs`）
- [ ] **选择器根 scope 漏判**: 第三方库（pdf.js / ECharts）的 worker / 实例共享（参考代码清单）
- [ ] 输出 `anti-pattern-report.md` 列命中项 + 文件:行 + 修复建议

### Phase 2: Fix

- [ ] **TDZ 后置绑定**: 把 const 声明移到 watch 之前
- [ ] **watchEffect 改 watch**: 或加 `let initialized = false` guard
- [ ] **flag 泄漏改 prev 比较**: `let prev = val; watch(val, v => { if (v !== prev) { prev = v; ... } })`
- [ ] **解构改前缀**: `const [firstDoc, secondDoc] = ...`
- [ ] **Pinia storeToRefs**: `import { storeToRefs } from 'pinia'; const { count } = storeToRefs(useStore())`
- [ ] **第三方库实例化谨慎**: 用 `import.meta.glob` 或 `new MyClass()` 单例 + destroy
- [ ] 🛑 **GATE**: 每个 fix 单独 commit（铁律 2）+ 跑 vitest 验证

### Phase 3: Test + Type

- [ ] **vitest 全绿**: `npx vitest run` 0 fail
- [ ] **vue-tsc 无类型错误**: `npx vue-tsc --noEmit`
- [ ] **ESLint**: `npx eslint src/`
- [ ] **组件 prop 类型显式**: 不能用 `any`
- [ ] 🛑 **GATE**: 上面 4 项全绿才能 build

### Phase 4: Build + Deploy verify

- [ ] **build 成功**: `pnpm build` 0 error
- [ ] **bundle 大小对比**: Phase 0 baseline vs 现在
- [ ] **chunk hash 列表**: `ls dist/assets/` 列出所有 `*.js` / `*.css`
- [ ] **部署后 curl 验证**:
  ```bash
  curl -s https://example.com/ | grep -oE 'src="[^"]+"' | sed 's/src="//;s/"//' | \
    while read f; do
      code=$(curl -sI "https://example.com/$f" | head -1 | awk '{print $2}')
      [ "$code" = "200" ] || echo "MISSING: $f"
    done
  ```
- [ ] **新 hash 实际生效**: 浏览器 DevTools Network 看实际加载的 chunk hash
- [ ] 🛑 **GATE**: 部署验证全部 200 + 新 hash 可见才能说"上线完成"

---

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
// BAD
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

### Vite 部署：chunk hash 同步

前端 build 产物 chunk 名带内容 hash（如 `index-abc123.js`）。只推改的文件 → index.html 引用新 hash → 缺 chunk → MIME `text/html` 404。

**部署后必做**：curl 验证新 index.html 引用的**每一个** entry/chunk URL 都返回 200。

## 14 硬约束（跨子工作流通用）

1. **零新增依赖 + 零提前防御 (YAGNI)**: 只用 Vue 生态已装库 + Vite 默认配置。
2. **commit 颗粒度**: 1 逻辑单元 = 1 commit（组件 + store + 测试同 commit）。
3. **默认回滚 = git revert**。**绝对禁止 `git reset --hard`**。
4. **死代码证明需 7 步 checklist**: 组件删除前确认无 router / 动态 import 引用。
5. **TDD**: Vue 组件用 Vitest + @vue/test-utils，Pinia store 单测。
6. **commit 前全量测试全绿**: `vitest run` + `vue-tsc --noEmit`。
7. **prod 锁定**: 部署前 staging 验证。
8. **宁缺勿伪**: 不编组件 prop 类型，TypeScript 严格模式打开。
9. **DB 删除**: 不适用（前端无 DB）。
10. **批量任务先测最小**: 大批量组件迁移先选 1 个目录 sample。
11. **daemon 改动 4 步独立**: dev server 重启验证 `pgrep -af "vite"`。
12. **buffer 所有权被转移**: `postMessage` / `getDocument({data})` / buffer transfer — 缓存方保留副本，每次传递前拷贝。
13. **hash 化构建产物必须整目录同步**: 见上「Vite 部署」节。
14. **部署验证实际生效标识**: curl 验证新 hash 实际生效，不看脚本退出码。

## 关联

- `/repo-medic` — meta 入口
- `/py-improve` — 后端 API 配套审查（前端调的后端）
- `/doc-reorg` — 组件文档（README / storybook）整理
- `/config-base` — bootstrap Node + Vite + Vue 工具链

## 仓库

github.com/liyong-labs/repo-medic — Apache-2.0。vue-improve 当前为骨架，欢迎贡献完整 references（best-practices / anti-patterns / deploy）。

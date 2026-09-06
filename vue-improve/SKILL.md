---
name: vue-improve
description: "Vue 3 + TypeScript + Vite + Pinia frontend code improvement. Covers component design, setup TDZ pitfalls, watchEffect traps, Pinia store patterns, Vite build optimization, chunk hash deployment. Triggers: Vue, component, Pinia, Vite, setup, watch, watchEffect, ref, routing, bundle, chunk, TypeScript, TS, frontend, SPA, reactivity"
metadata:
  type: domain
  scope: public
---

# vue-improve — Vue 3 Frontend Code Improvement

Self-contained skill. First-version skeleton; references pending (contributions welcome).

## 🛑 MANDATORY WORKFLOW — check all before declaring done

### Phase 0: Reconnaissance

- [ ] **Read the existing Vue project structure**: `package.json` + `vite.config.*` + `tsconfig.json` + `src/` layout
- [ ] **List components**: `find src -name "*.vue" | head -50` to gauge scale
- [ ] **List stores** (Pinia): `find src/stores -name "*.ts" 2>/dev/null`
- [ ] **List routes**: `find src/router -name "*.ts" 2>/dev/null`
- [ ] **Current bundle size**: `pnpm build && du -sh dist/` or `npm run build`
- [ ] 🛑 **GATE**: enter Phase 1 only once the scale is known (skip heavy optimization for small projects with < 50 components)

### Phase 1: Anti-pattern scan

- [ ] **setup TDZ late-declared binding references**: `rg "watch\(.*\)" src/ | head -20` to find potential TDZ risks
- [ ] **watchEffect writing its own dependency source**: `rg "watchEffect" src/`; manually review each callback
- [ ] **One-shot consume flag leaks**: `rg "let .* = true" src/ | rg -v "test"` to find watch flags
- [ ] **Destructuring shadowing an outer ref**: `rg "const \[.*\] = .*await Promise.all" src/`
- [ ] **Pinia store destructure losing reactivity**: `rg "const \{.*\} = use\w+Store\(\)" src/` (should be `storeToRefs`)
- [ ] **Missed selector-root scope checks**: worker / instance sharing in third-party libraries (pdf.js / ECharts) (see the Known pitfalls section below)
- [ ] Write `anti-pattern-report.md` listing hits + file:line + fix suggestions

### Phase 2: Fix

- [ ] **TDZ late-declared bindings**: move the const declaration before the watch
- [ ] **watchEffect → watch**: or add a `let initialized = false` guard
- [ ] **Flag leaks → prev comparison**: `let prev = val; watch(val, v => { if (v !== prev) { prev = v; ... } })`
- [ ] **Destructuring → distinct prefixes**: `const [firstDoc, secondDoc] = ...`
- [ ] **Pinia storeToRefs**: `import { storeToRefs } from 'pinia'; const { count } = storeToRefs(useStore())`
- [ ] **Careful third-party library instantiation**: use `import.meta.glob` or a `new MyClass()` singleton + destroy
- [ ] 🛑 **GATE**: commit each fix separately (iron rule 2) + run vitest to verify

### Phase 3: Test + Type

- [ ] **vitest all green**: `npx vitest run` with 0 fail
- [ ] **vue-tsc no type errors**: `npx vue-tsc --noEmit`
- [ ] **ESLint**: `npx eslint src/`
- [ ] **Explicit component prop types**: `any` is not allowed
- [ ] 🛑 **GATE**: build only after all 4 items above are green

### Phase 4: Build + Deploy verify

- [ ] **Build succeeds**: `pnpm build` with 0 error
- [ ] **Bundle size comparison**: Phase 0 baseline vs now
- [ ] **Chunk hash list**: `ls dist/assets/` listing all `*.js` / `*.css`
- [ ] **Post-deploy curl verification**:
  ```bash
  curl -s https://example.com/ | grep -oE 'src="[^"]+"' | sed 's/src="//;s/"//' | \
    while read f; do
      code=$(curl -sI "https://example.com/$f" | head -1 | awk '{print $2}')
      [ "$code" = "200" ] || echo "MISSING: $f"
    done
  ```
- [ ] **New hashes actually live**: check the chunk hashes actually loaded in browser DevTools Network
- [ ] 🛑 **GATE**: say "deploy complete" only after deploy verification is all 200 + new hashes visible

---

## Known pitfalls (built into the first version, v0.1)

### setup TDZ: immediate callback referencing a late-declared binding

```js
// BAD: watch runs cb synchronously; cb references a variable declared later → ReferenceError
const user = ref(null)
watch(user, (val) => console.log(user.name))  // runs during setup
const fetched = ref(null)  // declared later

// GOOD: declare the binding first, or defer with watchEffect
const fetched = ref(null)
const user = ref(null)
watch(user, (val) => console.log(user.value?.name, fetched.value))
```

### Writing to its own dependency source inside a watchEffect callback = infinite loop

```js
// BAD
watchEffect(() => {
  if (data.value.length === 0) data.value = [1]  // writes back to itself
})

// GOOD: use watch or add a guard
let initialized = false
watchEffect(() => {
  if (!initialized && data.value.length === 0) {
    initialized = true
    data.value = [1]
  }
})
```

### One-shot consume flag leak

```js
// BAD
let pending = true
watch(loading, (val) => {
  if (val === false && pending) {
    pending = false
    doStuff()
  }
})

// GOOD: snapshot comparison
let prev = loading.value
watch(loading, (val) => {
  if (val !== prev) { prev = val; if (val === false) doStuff() }
})
```

### Destructuring shadowing an outer ref

```js
// BAD
const [srcDoc, tgtDoc] = await Promise.all([fetchA(), fetchB()])
// srcDoc shadows the outer ref → later accesses hit the wrong object

// GOOD: distinct names/prefixes
const [firstDoc, secondDoc] = await Promise.all([...])
```

### Pinia store destructure losing reactivity

```js
// BAD
const { count } = useStore()  // plain variable; count changes never trigger renders

// GOOD
const store = useStore()  // keeping the whole store reference preserves reactivity
// or use storeToRefs
const { count } = storeToRefs(useStore())
```

### Vite deploy: chunk hash sync

Frontend build artifacts carry a content hash in chunk names (e.g. `index-abc123.js`). Pushing only the changed files → index.html references the new hash → missing chunk → MIME `text/html` 404.

**Mandatory after deploy**: curl-verify that **every** entry/chunk URL referenced by the new index.html returns 200.

## 14 hard constraints (common across sub-workflows, adapted per domain)

1. **Zero new dependencies + zero up-front defensive code (YAGNI)**: use only libraries already installed in the Vue ecosystem + Vite default config.
2. **Commit granularity**: 1 logical unit = 1 commit (component + store + tests in the same commit).
3. **Default rollback = git revert**. **`git reset --hard` is absolutely forbidden**.
4. **Dead-code proof requires a 7-step checklist**: before deleting a component, confirm there are no router / dynamic import references.
5. **TDD**: Vue components with Vitest + @vue/test-utils, unit tests for Pinia stores.
6. **Full test suite green before commit**: `vitest run` + `vue-tsc --noEmit`.
7. **prod lock**: staging verification before deploy.
8. **Prefer absence over fabrication**: never invent component prop types; TypeScript strict mode on.
9. **DB deletion**: not applicable (no DB in the frontend).
10. **Test a minimal sample before batch tasks**: for large component migrations, pick 1 directory as a sample first.
11. **4 independent steps for daemon changes**: verify the dev server restart with `pgrep -af "vite"`.
12. **Buffer ownership is transferred**: `postMessage` / `getDocument({data})` / buffer transfer — the caching side keeps a copy; copy before every handoff.
13. **Hashed build artifacts must be synced as a whole directory**: see the "Vite deploy" section above.
14. **Deploy verification checks the actually-live marker**: curl-verify that the new hash is actually live; ignore script exit codes.

## Related

- `/repo-medic` — meta entry point
- `/py-improve` — companion review for the backend API (the backend called by the frontend)
- `/doc-reorg` — component docs (README / storybook) organization
- `/config-base` — bootstrap the Node + Vite + Vue toolchain

## Repository

github.com/liyong-labs/repo-medic — Apache-2.0. vue-improve is currently a skeleton; contributions of complete references (best-practices / anti-patterns / deploy) are welcome.

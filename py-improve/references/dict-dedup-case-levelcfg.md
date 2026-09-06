# Dict Dedup — Typical Case: _LEVEL_CFG CONFLICT

> 90-line case study: split out and expanded from the "Typical decision flow" of [dict-dedup.md](dict-dedup.md) §Phase 3 truth identification (originally at L434+ of the single-file doc; after reorganization the linked section is authoritative)
> Main document: [dict-dedup.md](dict-dedup.md) — Phase 0-5 (incl. 4-category problem classification + the CONFLICT truth-identification evidence table) + YAGNI + known pitfalls

## Typical Case: `_LEVEL_CFG` CONFLICT

> **Real-bug teaching case**. This is the core reason a dict-consolidation skill must exist — not dedup, but uncovering latent silent bugs.

### Business Context

`_LEVEL_CFG` defines writing parameters for 4 research depths (academic research / professional discussion / serious media / social media):

```python
# Academic research config example
"Academic Research": {
    "max_tokens": 384000,      # LLM output cap
    "max_chars": 35000,         # character cap for the synthesis stage
    "thinking": True/False,     # whether the thinking chain is enabled
    "search_web": 20,           # web search count
    "search_academic": 6,       # academic engine search count
    "compress": "full",         # compression mode
    "mimo_eval": True,          # whether mimo model evaluation is enabled
    "glm_review": True,         # whether glm re-review is enabled
    # ... other parameters
}
```

### The Bug Hit This Time

The code contains **two fully independent** `_LEVEL_CFG` copies, differing in exactly 1 line (the `thinking` field, True vs False):

```python
# Location 1: stages/_config.py:34 (newer copy, presumed truth)
"Academic Research": { ..., "thinking": False, ... }
"Professional Discussion": { ..., "thinking": False, ... }

# Location 2: research_phases.py:952 (older copy, never deleted)
"Academic Research": { ..., "thinking": True, ... }    # ← contradiction!
"Professional Discussion": { ..., "thinking": True, ... }    # ← contradiction!
```

**Which one takes effect depends on the import chain**:

| caller | imports from | uses which copy | thinking value |
|--------|-----------|--------|------------|
| `stage_compose.py` | `stages._config` | **newer** | False |
| `research_phases.py:968` `_tokens_for_length` | local copy | **older** | True |
| `research_pipeline.py` | `research_phases` | **older** | True |

### Consequences

1. **The same depth behaves inconsistently across stages** — the compose stage believes "academic research disables thinking" while token calculation believes "enable it"; the LLM's actual requested token cap differs, **possibly blowing the token limit / truncating**
2. **Invisible to users** — no WARN is raised; callers believe they received `_LEVEL_CFG` but actually got a stale copy
3. **Tests cannot catch it** — tests only assert function return values and never verify "the two dicts agree"

### DUPLICATE vs CONFLICT Comparison (teaching case)

| Dimension | DUPLICATE (harmless) | **CONFLICT (this case)** |
|------|----------------|-------------------|
| Presentation | The two dicts are **identical** | Field values **differ** |
| Risk | Maintenance burden only (edit one, forget the other) | Inconsistent behavior, **silent bug** |
| Detection | grep + fingerprint matching finds it | **Requires a field-by-field diff** |
| Fix | Delete one copy + switch to a re-export | **Must first decide which copy is the truth before touching anything** |

### Truth Identification (key to this case)

> The 4-row evidence table for truth identification is in Phase 3. Applied to this case:

1. **`stages/_config.py` has the newer file mtime** — edited during the simplification in commit `2b4a9b4`
2. **`research_phases.py:952` untouched for a long time** — already present before commit `70d102596`
3. **Code comments state it explicitly** — `_config.py` is marked "single entry point"
4. **→ delete the `research_phases.py` copy**, and migrate every caller to import from `_config`

### Handling Flow (teaching case)

1. Compare the two fingerprints via AST → flag CONFLICT
2. Emit a field-by-field diff of the two sites (`thinking: False vs True`)
3. **Stop** — let a human / git history decide the truth
4. Once the truth is found:
   - Move the authoritative source to `constants/level_cfg.py`
   - Switch `stages/_config.py` to `from constants.level_cfg import LEVEL_CFG` (re-export keeps old imports working)
   - **Delete the entire `research_phases.py:952` block** (no re-export — the old API was already misused)
   - Migrate all callers to the new import
   - commit msg: `fix(dict): resolve _LEVEL_CFG CONFLICT, decided _config.py is truth (thinking=False)`
5. Run regression; baseline behavior unchanged (under the new version every stage uses thinking=False uniformly and the LLM request token cap is consistent)

### Core Lessons

- **The core value of a dict-consolidation skill is not dedup, it is uncovering silent bugs.**
- CONFLICT is 100x more dangerous than DUPLICATE: DUPLICATE only adds maintenance burden, CONFLICT makes program behavior drift outright.
- Truth identification must rest on evidence (git log / mtime / comments), not on heuristic algorithms.
- Automated tooling must never be allowed to make the "which one is the truth" decision.

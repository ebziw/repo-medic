# python-pptx can open ≠ PowerPoint can open — manual OOXML edits must check reference integrity

**Symptom**: generated PPTs opened fine in python-pptx and zip validators for months; PowerPoint exits immediately on open. 3 prehistoric files even python-pptx couldn't open.

**Cause**: PowerPoint strict mode walks the full rel chain — dangling rels, `Content_Types` Override pointing at missing parts, slide→notesSlide chain that needs presentation.xml to register notesMaster. Each "fix it again" iteration left dangling references.

**Fix**:
- After any manual OOXML edit, assert:
  (a) every part referenced exists (`zipfile` + walk `*.xml.rels`)
  (b) every `Target` resolves to a real file
  (c) every part has a `Content_Types` Override
- If notes are not actually used: delete the ENTIRE chain (slide→notesSlide→notesMaster) rather than partially fix
- Run final test against the real consumer (PowerPoint), not just the parser SDK

## Sources

- `commit:a7c56fd7`
- `work-note:docs/work-note/2026-09-06-ppt-notes-chain-powerpoint-fix.md`

## Frequency

2 (this + llama.cpp batch-size — same root: tool SDK pass ≠ consumer pass)

## Triggers

pptx, OOXML, PowerPoint strict, python-pptx, notesMaster, rels, Content_Types Override, dangling reference

## Related hard constraints

#14 (verify actually-running product against real consumer)
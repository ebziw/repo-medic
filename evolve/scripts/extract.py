"""evolve extract — 扫描 git log + work-notes 提取 lesson 候选。

Stdlib only（no pygit2 / no PyYAML）。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path


WORK_NOTE_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
WORK_NOTE_SYMPTOM = re.compile(r"\*\*Symptom\*\*:\s*(.+)")
WORK_NOTE_CAUSE = re.compile(r"\*\*Cause\*\*:\s*(.+)")
WORK_NOTE_FIX = re.compile(r"\*\*Fix\*\*:\s*(.+)")
COMMIT_PITFALL_KEYWORDS = (
    "踩坑", "bug", "fix", "BUG", "FIX", "教训", "注意", "warn", "error",
    "wrong", "broken", "revert", "rollback", "lesson",
)


@dataclass
class Lesson:
    id: str
    tag: str  # db / deploy / config / frontend / python / doc / general
    target_skill: str  # py-improve / doc-reorg / db-tweak / vue-improve / config-base
    symptom: str
    cause: str
    fix: str
    frequency: int = 1
    sources: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    references: list[int] = field(default_factory=list)  # 14 hard constraints
    confidence: str = "low"

    def to_markdown(self) -> str:
        src = "\n".join(f"- `{s}`" for s in self.sources) or "- (none)"
        trig = ", ".join(self.triggers) if self.triggers else "-"
        refs = ", ".join(f"#{r}" for r in self.references) or "-"
        return (
            f"### Candidate: {self.symptom[:80]}\n\n"
            f"- **tag**: `{self.tag}` → `{self.target_skill}`\n"
            f"- **frequency**: {self.frequency}\n"
            f"- **confidence**: {self.confidence}\n"
            f"- **Symptom**: {self.symptom}\n"
            f"- **Cause**: {self.cause}\n"
            f"- **Fix**: {self.fix}\n"
            f"- **Triggers**: {trig}\n"
            f"- **References**: {refs}\n"
            f"- **Sources**:\n{src}\n"
        )


def _git_log(repo: Path, since: str, max_commits: int) -> list[dict]:
    """Return list of commits: {hash, subject, body, date}."""
    fmt = "%H%n%s%n%b%n--END--"
    cmd = [
        "git", "-C", str(repo), "log",
        f"--since={since}",
        f"--max-count={max_commits}",
        f"--pretty=format:{fmt}",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"git log failed: {e}", file=sys.stderr)
        return []
    if out.returncode != 0:
        return []
    commits = []
    for block in out.stdout.split("--END--"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n", 2)
        if len(lines) < 2:
            continue
        h = lines[0].strip()
        subject = lines[1].strip()
        body = lines[2].strip() if len(lines) > 2 else ""
        commits.append({"hash": h[:10], "subject": subject, "body": body})
    return commits


def _commit_pitfall_score(c: dict) -> int:
    """Heuristic: how likely is this commit to be a pitfall/lesson?"""
    text = (c["subject"] + " " + c["body"]).lower()
    return sum(1 for kw in COMMIT_PITFALL_KEYWORDS if kw.lower() in text)


def _scan_work_notes(repo: Path) -> list[Lesson]:
    """Scan docs/work-note/*.md for Symptom/Cause/Fix pattern."""
    notes_dir = repo / "docs" / "work-note"
    if not notes_dir.exists():
        return []
    lessons = []
    for fp in sorted(notes_dir.glob("*.md")):
        text = fp.read_text(encoding="utf-8", errors="replace")
        sym = WORK_NOTE_SYMPTOM.search(text)
        cau = WORK_NOTE_CAUSE.search(text)
        fix = WORK_NOTE_FIX.search(text)
        if not (sym and cau and fix):
            continue
        # crude tag inference from filename + content
        tag = _infer_tag(text, fp.stem)
        target = _infer_target_skill(tag)
        lessons.append(Lesson(
            id=f"wn_{fp.stem[:30]}_{len(lessons)}",
            tag=tag,
            target_skill=target,
            symptom=sym.group(1).strip()[:200],
            cause=cau.group(1).strip()[:200],
            fix=fix.group(1).strip()[:200],
            frequency=1,
            sources=[f"work-note:{fp.relative_to(repo)}"],
            confidence="med",
        ))
    return lessons


_TAG_RULES = [
    ("db", ("postgres", "pg", "sql", "database", "schema", "migration", "drop", "vacuum", "索引", "数据库")),
    ("deploy", ("deploy", "release", "k8s", "docker", "ci", "cd", "部署", "发布", "ssh")),
    ("config", ("config", "env", "yaml", "toml", "json", ".env", "配置", "环境变量")),
    ("frontend", ("vue", "react", "vite", "css", "ts", "前端", "component", "store")),
    ("python", ("python", "pytest", "ruff", "mypy", "pyright", "import", "类", "函数")),
    ("doc", ("doc", "readme", "markdown", "文档", "work-note")),
    ("general", ()),
]

_TARGET_BY_TAG = {
    "db": "db-tweak",
    "deploy": "config-base",
    "config": "config-base",
    "frontend": "vue-improve",
    "python": "py-improve",
    "doc": "doc-reorg",
    "general": "py-improve",
}


def _infer_tag(text: str, name: str) -> str:
    blob = (text + " " + name).lower()
    for tag, kws in _TAG_RULES:
        if any(kw in blob for kw in kws):
            return tag
    return "general"


def _infer_target_skill(tag: str) -> str:
    return _TARGET_BY_TAG.get(tag, "py-improve")


def _merge(lessons: list[Lesson]) -> list[Lesson]:
    """Dedupe by (symptom[:60], cause[:60]). Merge sources + frequency."""
    grouped: dict[tuple, Lesson] = {}
    for ls in lessons:
        key = (ls.symptom[:60].lower(), ls.cause[:60].lower())
        if key in grouped:
            ex = grouped[key]
            ex.frequency += 1
            ex.sources = list(set(ex.sources + ls.sources))
            if ls.confidence == "high" or ex.confidence == "high":
                ex.confidence = "high"
            elif ls.confidence == "med" or ex.confidence == "med":
                ex.confidence = "med"
        else:
            grouped[key] = ls
    return sorted(grouped.values(), key=lambda x: -x.frequency)


def cmd_extract(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"not a git repo: {repo}", file=sys.stderr)
        return 1

    lessons: list[Lesson] = []

    # work-notes (high signal — explicit Symptom/Cause/Fix)
    wn_lessons = _scan_work_notes(repo)
    lessons.extend(wn_lessons)

    # git commits with pitfall keyword (lower signal — heuristic)
    commits = _git_log(repo, args.since, args.max_commits)
    scored = [(c, _commit_pitfall_score(c)) for c in commits]
    for c, score in scored:
        if score == 0:
            continue
        # commit-level lesson (low confidence)
        tag = _infer_tag(c["subject"] + " " + c["body"], c["hash"])
        target = _infer_target_skill(tag)
        lessons.append(Lesson(
            id=f"co_{c['hash']}_{len(lessons)}",
            tag=tag,
            target_skill=target,
            symptom=c["subject"][:200],
            cause="(inferred from commit context; user verify)",
            fix="(commit body — user extract action)",
            frequency=1,
            sources=[f"commit:{c['hash']}"],
            confidence="low",
        ))

    merged = _merge(lessons)

    # frequency gate: only keep >= 2 OR explicit work-note
    kept = [ls for ls in merged if ls.frequency >= 2 or ls.sources[0].startswith("work-note:")]

    if args.json:
        print(json.dumps([asdict(ls) for ls in kept], indent=2, ensure_ascii=False))
        return 0

    # Markdown output
    lines = [
        f"# evolve extract — {len(kept)} candidates",
        f"",
        f"- repo: `{repo}`",
        f"- since: {args.since}",
        f"- max commits: {args.max_commits}",
        f"- work-notes found: {len(wn_lessons)}",
        f"- total commits scanned: {len(commits)}",
        f"- candidates after dedup: {len(merged)}",
        f"- candidates after gate (freq>=2 OR work-note): {len(kept)}",
        f"",
        "---",
        "",
    ]
    by_skill = defaultdict(list)
    for ls in kept:
        by_skill[ls.target_skill].append(ls)

    for skill, items in sorted(by_skill.items()):
        lines.append(f"## → {skill} ({len(items)} candidates)")
        lines.append("")
        for ls in items:
            lines.append(ls.to_markdown())
            lines.append("---")
            lines.append("")

    out = "\n".join(lines)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"[write] {args.output}  ({len(kept)} candidates)")
    else:
        print(out)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="evolve: extract lesson candidates from project history")
    p.add_argument("--repo", default=".", help="project root (default: cwd)")
    p.add_argument("--since", default="7d", help="git log --since (default 7d)")
    p.add_argument("--max-commits", type=int, default=200, help="max commits to scan (default 200)")
    p.add_argument("--output", default=None, help="write markdown to file (default: stdout)")
    p.add_argument("--json", action="store_true", help="output JSON instead of markdown")
    args = p.parse_args()
    return cmd_extract(args)


if __name__ == "__main__":
    sys.exit(main())

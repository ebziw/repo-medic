# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v0.x    | :white_check_mark: (latest minor) |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of these channels:

1. **GitHub Security Advisories** (preferred): <https://github.com/liyong-labs/repo-medic/security/advisories/new>
2. **Private issue with `security` label**: <https://github.com/liyong-labs/repo-medic/issues/new> (mark as private when possible)

Please include:

- Type of vulnerability
- Steps to reproduce
- Affected versions
- Potential impact
- Suggested fix (if any)

## What to expect

- **Initial response**: within 72 hours
- **Triage decision**: within 7 days (accept / won't-fix / need-more-info)
- **Fix timeline**: depends on severity
  - Critical (RCE, arbitrary code execution): ASAP, within days
  - High (privilege escalation, data exfiltration): within 2 weeks
  - Medium (information disclosure): within 1 month
  - Low: best-effort, may be deferred to next release

## Scope

This is a skill toolkit that runs user-supplied code (via `python_refactor_server`
MCP tools, audit scripts, etc.). Security concerns include:

- **Arbitrary code execution** in audit scripts (e.g. `subprocess.run` without shell=False)
- **Path traversal** in file scanners
- **MCP server input validation**
- **Skill discovery** — malicious SKILL.md frontmatter could trick LLM into unexpected behavior

## Out of scope

- Vulnerabilities in dependencies (report upstream)
- Issues requiring physical access to user machine
- Social engineering attacks

## Recognition

We follow a "thanks but no bounty" policy. Reporters will be credited in
CHANGELOG (with permission) but no monetary reward.

## Past advisories

None yet.

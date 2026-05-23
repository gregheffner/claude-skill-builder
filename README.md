<div align="center">

# ⚡ Skill Builder

**Turn one line of English into a real Claude skill.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Built with Claude Agent SDK](https://img.shields.io/badge/built%20with-Claude%20Agent%20SDK-D97757.svg)](https://code.claude.com/docs/en/agent-sdk/overview)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*by [Greg Heffner](https://greg.heffner.live) · Nerdsense*

</div>

---

A tiny CLI that turns this:

```bash
skill-builder "fetch youtube transcripts from a URL or search query"
```

into a working Claude skill at `.claude/skills/<name>/SKILL.md` — frontmatter, allowed tools, hard-stop rule, the whole convention. No copy-pasting templates, no "wait, what was the YAML key called again." Claude figures out the steps; you confirm or edit before use.

## Why

Skills are the unit of repetition for Claude agents. The format is simple — one folder, one `SKILL.md` — but every time I started a new one I'd open an old one, copy the frontmatter, forget which tool names were valid, and miss the `## Hard stop` for destructive ops. This is the script I should have written the first time.

More background on Claude agents and the building blocks → [my blog post](https://greg.heffner.live/image/pages/2026/May/ClaudeSkills.html).

## Quick start

```bash
git clone https://github.com/gregheffner/claude-skill-builder
cd claude-skill-builder

python3 -m venv .venv
source .venv/bin/activate
pip install claude-agent-sdk

npm install -g @anthropic-ai/claude-code   # one-time, SDK uses the CLI under the hood
export ANTHROPIC_API_KEY=sk-ant-...

python3 skill-builder-agent.py "weekly cron job that lints my homelab manifests"
```

You'll get back a complete `.claude/skills/cron-lint-manifests/SKILL.md` (or whatever name Claude picks) with:

- A `description` packed with trigger phrases so it auto-fires
- Least-privilege `allowed-tools` (read-only by default)
- Numbered, concrete steps — no hand-waves
- A `## Hard stop` block if it needs `Write`, `Edit`, or `Bash`

## Flags

| flag | what it does |
|---|---|
| `-v` | verbose — show every message, tool call, and result block |
| `--no-banner` | suppress the launch banner (also respects `NO_COLOR`) |

## What's inside

- `skill-builder-agent.py` — the Claude Agent SDK app. ~120 lines, one file, no magic.
- `skill-builder.py` — a non-agent scaffolder for when you already know exactly what you want and just need the boilerplate written.

## Philosophy

Build in public. Automate the boring stuff. Share what works (and what doesn't).

If you ship a skill with this, drop me a line — would love to see what people are building.

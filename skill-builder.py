#!/usr/bin/env python3
"""
skill-builder — scaffold a Claude Skill from a few prompts.

Follows the conventions from greg.heffner.live/.../ClaudeSkills.html:
  - one folder under .claude/skills/<name>/
  - SKILL.md with YAML frontmatter (name + description)
  - locked-down allowed_tools list
  - inputs → steps → hard stop pattern
  - keep it small
"""

import re
import sys
from pathlib import Path

DEFAULT_TOOLS = ["Read", "Glob", "Grep"]   # read-only by default; expand if needed
DESTRUCTIVE   = {"Write", "Edit", "Bash"}


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or (default or "")


def slug(name):
    return re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")


def build_skill_md(name, description, when, steps, tools, stop_rule):
    tool_list = ", ".join(tools)
    steps_md = "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
    has_destructive = any(t in DESTRUCTIVE for t in tools)
    stop_block = ""
    if has_destructive and stop_rule:
        stop_block = f"\n## Hard stop\n{stop_rule}\n"

    return (
        f"---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"allowed-tools: [{tool_list}]\n"
        f"---\n\n"
        f"# {name}\n\n"
        f"## When to use\n{when}\n\n"
        f"## Steps\n{steps_md}\n"
        f"{stop_block}"
    )


def main():
    print("Claude Skill Builder — minimal scaffolder\n")

    name        = slug(ask("Skill name (kebab-case)", "my-skill"))
    description = ask("When should Claude trigger this skill?",
                      "Use when ...")
    when        = ask("One-line trigger phrase",
                      "Trigger with '...'")
    print("\nSteps — enter one per line, blank line to finish:")
    steps = []
    while True:
        s = input(f"  step {len(steps)+1}: ").strip()
        if not s:
            break
        steps.append(s)
    if not steps:
        steps = ["Read inputs.", "Do the work.", "Report results."]

    print(f"\nAllowed tools (comma-separated). Default = {DEFAULT_TOOLS}")
    raw = ask("tools", ",".join(DEFAULT_TOOLS))
    tools = [t.strip() for t in raw.split(",") if t.strip()]

    stop_rule = ""
    if any(t in DESTRUCTIVE for t in tools):
        stop_rule = ask("Hard-stop rule before destructive action",
                        "Stop and ask the user before writing/committing/sending anything.")

    # default to current dir / .claude/skills/<name>
    default_root = Path.cwd() / ".claude" / "skills" / name
    out = Path(ask("Output dir", str(default_root))).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    skill_md = build_skill_md(name, description, when, steps, tools, stop_rule)
    (out / "SKILL.md").write_text(skill_md)

    print(f"\nWrote {out/'SKILL.md'} ({len(skill_md)} bytes)")
    print("\nPreview:")
    print("-" * 40)
    print(skill_md)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\naborted.")
        sys.exit(1)

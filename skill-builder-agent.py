#!/usr/bin/env python3
"""
skill-builder-agent — Claude Agent SDK app that turns a plain-English
request into a real Claude skill.

User runs:   python3 skill-builder-agent.py "I want a skill that
                                              transcribes youtube videos"
Agent will:  ask clarifying questions, pick the right tools, draft the
             SKILL.md, write it to ./.claude/skills/<name>/SKILL.md,
             and stop for human review before doing anything else.

Requires:    pip install claude-agent-sdk
             export ANTHROPIC_API_KEY=...
"""

import anyio
import os
import sys
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions

VERBOSE   = "-v" in sys.argv or os.getenv("SKILL_BUILDER_VERBOSE")
NO_BANNER = "--no-banner" in sys.argv or os.getenv("NO_COLOR")
sys.argv  = [a for a in sys.argv if a not in ("-v", "--no-banner")]

# ── Brand ──────────────────────────────────────────────────────
VERSION   = "0.1.0"
AUTHOR    = "Greg Heffner"
BLOG_NAME = "Nerdsense"
BLOG_URL  = "https://greg.heffner.live"
REPO_URL  = "https://github.com/gregheffner/claude-skill-builder"

# ── ANSI ───────────────────────────────────────────────────────
_TTY = sys.stdout.isatty()
def c(code, s):  return f"\033[{code}m{s}\033[0m" if _TTY else s
def cyan(s):     return c("96", s)
def dim(s):      return c("2",  s)
def bold(s):     return c("1",  s)
def yellow(s):   return c("93", s)


def print_banner():
    if NO_BANNER or not _TTY:
        return
    rule = cyan("━" * 60)
    print(rule)
    print(f" {yellow('⚡')}  {bold(cyan('SKILL BUILDER'))}  {dim('· v' + VERSION)}")
    print(f" {dim('Turn plain English into a Claude skill.')}")
    print()
    print(f" {AUTHOR}  {dim('·')}  {BLOG_NAME}  {dim(BLOG_URL)}")
    print(f" {dim(REPO_URL)}")
    print(rule)
    print()

SYSTEM_PROMPT = """\
You are a Claude Skill Builder. The user will describe a workflow they want
to automate, and you will produce a single SKILL.md file that follows
Anthropic's skill convention.

RULES — follow exactly:

1. A skill is one folder under .claude/skills/<kebab-name>/ containing a
   SKILL.md file with YAML frontmatter:

       ---
       name: <kebab-name>
       description: <when Claude should trigger this skill — pack it with
                    natural trigger phrases>
       allowed-tools: [<comma-separated tools>]
       ---

       # <name>
       ## When to use
       ## Inputs
       ## Steps
       ## Hard stop          (only if destructive tools are allowed)
       ## Requires           (only if external deps like yt-dlp, jq, etc.)

2. Valid tool names ONLY (case-sensitive):
   Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch,
   AskUserQuestion, Agent.
   wget/curl/jq/yt-dlp are NOT tools — they are shell commands run via Bash.

3. Default to LEAST privilege. Start with [Read, Glob, Grep]. Only add
   Write/Edit/Bash if the workflow actually requires them. If you add any
   of those, include a "## Hard stop" section that tells Claude to confirm
   with the user before the destructive action.

4. The `description` field is what makes the skill auto-trigger. Pack it
   with the actual phrases a user would say. Bad: "Get transcripts."
   Good: "Fetch transcripts/captions/subtitles from YouTube videos. Use
         when the user shares a YouTube URL or asks 'what did the video
         say', 'transcribe this', 'get captions'."

5. Steps are numbered, imperative, and concrete. Name the exact command
   or tool call. No "do the thing" hand-waves.

6. Ask the user clarifying questions via AskUserQuestion if anything is
   genuinely ambiguous — but make reasonable assumptions first. Don't
   interrogate them.

7. When the skill is drafted, write it with the Write tool to
   ./.claude/skills/<name>/SKILL.md (relative to the user's cwd).
   Do NOT run the skill, do NOT modify anything else.

8. AFTER the Write call, print a short plain-text summary in this exact
   shape (no markdown headers, no fences):

       BUILT: <skill-name>
       FILE:  ./.claude/skills/<skill-name>/SKILL.md
       WHAT:  <one sentence describing what the skill does>
       USE:   <one sentence on how the user invokes it in Claude>
       NEEDS: <comma-list of external CLIs/deps the skill calls, or "none">

   Keep each line to one line. No extra commentary after the block.
"""


async def main():
    print_banner()

    if len(sys.argv) < 2:
        print("usage: skill-builder-agent.py [-v] [--no-banner] "
              "\"<what the skill should do>\"")
        sys.exit(1)

    user_request = " ".join(sys.argv[1:])

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Write"],
        cwd=str(Path.cwd()),
        permission_mode="bypassPermissions",  # acceptEdits still prompts; bypass for headless
        max_turns=15,
    )

    written_path = None
    thinking_shown = False

    print("Thinking...", flush=True)

    async for msg in query(prompt=user_request, options=options):
        kind = type(msg).__name__

        if VERBOSE:
            print(f"\n--[{kind}]-- {msg!r}\n")

        # Skip the noisy end-of-run telemetry message entirely.
        if kind == "ResultMessage":
            continue

        content = getattr(msg, "content", None)
        if content is None:
            continue

        for block in content:
            btype = type(block).__name__

            if btype == "ThinkingBlock":
                if not thinking_shown:
                    thinking_shown = True   # already printed "Thinking..."
                continue

            if btype == "ToolUseBlock":
                name = getattr(block, "name", "?")
                inp = getattr(block, "input", {}) or {}
                path = inp.get("file_path", "")
                if name == "Write" and path.endswith("SKILL.md"):
                    rel = Path(path).name if not path else path
                    print(f"Writing {Path(path).relative_to(Path.cwd()) if Path(path).is_absolute() else path}...")
                    written_path = path
                continue

            if btype == "ToolResultBlock":
                if getattr(block, "is_error", False):
                    err = getattr(block, "content", "")
                    print(f"  ⚠ tool error: {err}")
                continue

            # Plain text — this is the BUILT/FILE/WHAT/USE/NEEDS block.
            if hasattr(block, "text") and block.text.strip():
                print()
                print(block.text.rstrip())

    # Deterministic footer — doesn't depend on the model.
    print("\n" + "─" * 60)
    if not written_path:
        print("⚠️  no SKILL.md was written. Rerun with a more specific "
              "prompt, or check the messages above for errors.")
        return

    rel = Path(written_path).resolve().relative_to(Path.cwd()) \
        if Path(written_path).is_absolute() else Path(written_path)
    print(f"✅  Wrote {rel}")
    print()
    print("To tweak this skill:")
    print(f"    $EDITOR {rel}")
    print()
    print("To rebuild it from scratch (overwrites the file):")
    script = Path(sys.argv[0]).name
    print(f"    python3 scripts/{script} \"<new description>\"")
    print()
    print("To use it: open Claude in this directory — the skill will")
    print("auto-trigger when your prompt matches its `description` field.")


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\naborted.")

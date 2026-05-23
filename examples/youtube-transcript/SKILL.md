---
name: youtube-transcript
description: Fetch transcripts, captions, or subtitles from YouTube videos given either a direct URL or a search query. Use when the user shares a YouTube URL, asks "what did the video say", "transcribe this video", "get the captions for X", "find the transcript of Y", "summarize this YouTube video", or otherwise wants the spoken/captioned text of a YouTube video pulled into the chat.
allowed-tools: [Read, Write, Bash, AskUserQuestion]
---

# youtube-transcript

## When to use
- User pastes a YouTube URL (youtube.com/watch, youtu.be/, youtube.com/shorts/) and wants its contents read, summarized, quoted, or transcribed.
- User asks for the transcript/captions/subtitles of a video by title or topic ("get the transcript of the latest Fireship video on Bun").
- User says "what did they say in this video", "pull the captions", "give me the text of this YouTube clip".

Do NOT use for:
- Non-YouTube video platforms (Vimeo, X, TikTok) — bail out and tell the user.
- Live streams currently in progress (captions may not be finalized).

## Inputs
- **Primary input**: either
  - a YouTube URL, or
  - a free-text search query describing the video.
- **Optional**: preferred language (default: `en`, fall back to auto-generated).

If the user gave a search query but no URL, use `AskUserQuestion` to confirm the top candidate before downloading — don't pull the wrong video.

## Steps

1. **Detect input type.**
   - If the input matches `youtube\.com/(watch|shorts)` or `youtu\.be/`, treat it as a URL → go to step 3.
   - Otherwise, treat it as a search query → step 2.

2. **Resolve search query → URL.**
   - Run:
     ```
     yt-dlp "ytsearch5:<query>" --print "%(id)s | %(title)s | %(uploader)s | %(duration_string)s" --skip-download
     ```
   - Show the top 5 candidates to the user via `AskUserQuestion` and have them pick one. Build the canonical URL as `https://www.youtube.com/watch?v=<id>`.

3. **Pull captions only (no video, no audio).**
   - Create a working dir: `mkdir -p /tmp/yt-transcript && cd /tmp/yt-transcript`
   - Run:
     ```
     yt-dlp --write-subs --write-auto-subs --sub-langs "en.*,en" --sub-format "vtt" --skip-download --output "%(id)s.%(ext)s" "<URL>"
     ```
   - Prefer human-uploaded subs; fall back to auto-generated if those are the only ones present.

4. **Convert VTT → clean text.**
   - Use Bash to strip VTT timestamps, cue settings, and dedupe rolling-caption repeats:
     ```
     awk '/-->/{next} /^WEBVTT/{next} /^NOTE/{next} /^$/{next} /^[0-9]+$/{next} {print}' /tmp/yt-transcript/<id>.en*.vtt \
       | awk '!seen[$0]++' \
       > /tmp/yt-transcript/<id>.txt
     ```
   - If multiple `en*.vtt` files exist (e.g. `en.vtt` plus `en-orig.vtt`), prefer the non-`auto` one.

5. **Present the transcript.**
   - Read the cleaned `.txt` file with the `Read` tool.
   - Output the transcript inline, prefixed with the video title and URL.
   - If the user asked for a summary, quote, or specific question — answer from the transcript content, don't just dump it.

6. **Cleanup.**
   - Leave files in `/tmp/yt-transcript/` (auto-cleaned by OS). Do not write to the user's repo or home dir.

## Requires
- `yt-dlp` (install: `brew install yt-dlp`) — must be on `$PATH`.
- `awk` (standard on macOS/Linux).

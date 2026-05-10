#!/usr/bin/env bash
# PostToolUse hook — appends one line to .scrapekit/session.log
# Env: CLAUDE_TOOL_NAME, CLAUDE_TOOL_INPUT (JSON)

TOOL="${CLAUDE_TOOL_NAME:-unknown}"
INPUT="${CLAUDE_TOOL_INPUT:-{}}"
LOG=".scrapekit/session.log"

mkdir -p .scrapekit

# Extract URL or path depending on tool
case "$TOOL" in
  WebFetch)
    TARGET=$(echo "$INPUT" | jq -r '.url // empty' 2>/dev/null) ;;
  Bash)
    # Pull first URL-looking token or the raw command (truncated)
    CMD=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)
    TARGET=$(echo "$CMD" | grep -oE 'https?://[^ "]+' | head -1)
    [[ -z "$TARGET" ]] && TARGET=$(echo "$CMD" | cut -c1-80) ;;
  *)
    TARGET=$(echo "$INPUT" | jq -r '.url // .path // .command // empty' 2>/dev/null | head -1 | cut -c1-80) ;;
esac

[[ -z "$TARGET" ]] && exit 0

printf '%s\t%s\t%s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$TOOL" "$TARGET" >> "$LOG"

#!/usr/bin/env bash
# PostToolUse hook — appends one line to .scrapekit/session.log
# Env: CLAUDE_TOOL_NAME, CLAUDE_TOOL_INPUT, CLAUDE_TOOL_OUTPUT (JSON)

TOOL="${CLAUDE_TOOL_NAME:-unknown}"
INPUT="${CLAUDE_TOOL_INPUT:-{}}"
OUTPUT="${CLAUDE_TOOL_OUTPUT:-}"
LOG=".scrapekit/session.log"

# Extract a real http(s) URL — only URL-bearing activity is logged.
# A bare Bash command with no URL is not scrapekit-related, so skip it
# (this is what prevented the ghost .scrapekit/ folders).
case "$TOOL" in
  WebFetch)
    TARGET=$(echo "$INPUT" | jq -r '.url // empty' 2>/dev/null) ;;
  Bash)
    CMD=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)
    TARGET=$(echo "$CMD" | grep -oE 'https?://[^ "]+' | head -1) ;;
  *)
    TARGET=$(echo "$INPUT" | jq -r '.url // empty' 2>/dev/null) ;;
esac

# No URL → not a scrapekit-relevant call. Exit before any folder is created.
[[ "$TARGET" =~ ^https?:// ]] || exit 0

# Only log into a .scrapekit/ that already exists — never create one.
# The directory is the opt-in: scrapekit's skill creates it when invoked.
[[ -d .scrapekit ]] || exit 0

# Determine status from output
OUTPUT_TEXT=$(echo "$OUTPUT" | jq -r '.content // .output // .' 2>/dev/null || echo "$OUTPUT")
OUTPUT_LEN=${#OUTPUT_TEXT}

if [[ -z "$OUTPUT_TEXT" ]]; then
  STATUS="err"
elif echo "$OUTPUT_TEXT" | grep -qiE '(error|failed|forbidden|not found|403|404|blocked|cloudflare|access denied)'; then
  STATUS="err"
elif [[ "$OUTPUT_LEN" -lt 200 ]]; then
  STATUS="thin"
else
  STATUS="ok"
fi

printf '%s\t%s\t%s\t%s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$STATUS" "$TOOL" "$TARGET" >> "$LOG"

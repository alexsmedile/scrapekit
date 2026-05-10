#!/usr/bin/env bash
# PostToolUse hook — appends one line to .scrapekit/session.log
# Env: CLAUDE_TOOL_NAME, CLAUDE_TOOL_INPUT, CLAUDE_TOOL_OUTPUT (JSON)

TOOL="${CLAUDE_TOOL_NAME:-unknown}"
INPUT="${CLAUDE_TOOL_INPUT:-{}}"
OUTPUT="${CLAUDE_TOOL_OUTPUT:-}"
LOG=".scrapekit/session.log"

mkdir -p .scrapekit

# Extract URL or path depending on tool
case "$TOOL" in
  WebFetch)
    TARGET=$(echo "$INPUT" | jq -r '.url // empty' 2>/dev/null) ;;
  Bash)
    CMD=$(echo "$INPUT" | jq -r '.command // empty' 2>/dev/null)
    TARGET=$(echo "$CMD" | grep -oE 'https?://[^ "]+' | head -1)
    [[ -z "$TARGET" ]] && TARGET=$(echo "$CMD" | cut -c1-80) ;;
  *)
    TARGET=$(echo "$INPUT" | jq -r '.url // .path // .command // empty' 2>/dev/null | head -1 | cut -c1-80) ;;
esac

[[ -z "$TARGET" ]] && exit 0

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

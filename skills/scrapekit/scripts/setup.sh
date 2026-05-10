#!/usr/bin/env bash
# scrapekit setup — health check + guided onboarding
# Usage: bash setup.sh [--recheck]
#
# Checks every scrapekit tool: binary presence, Python imports, API keys.
# Saves results to .scrapekit/setup.json so subsequent runs skip the check
# (unless --recheck is passed).

set -uo pipefail

SETUP_FILE=".scrapekit/setup.json"
RECHECK=false
[[ "${1:-}" == "--recheck" ]] && RECHECK=true

mkdir -p .scrapekit

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}✓${RESET}  $*"; }
warn() { echo -e "  ${YELLOW}!${RESET}  $*"; }
fail() { echo -e "  ${RED}✗${RESET}  $*"; }

# ── Skip if already verified ──────────────────────────────────────────────────
if [[ "$RECHECK" == false && -f "$SETUP_FILE" ]]; then
  echo ""
  echo "scrapekit already set up ($(cat "$SETUP_FILE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('date','unknown'))" 2>/dev/null || echo "unknown date"))."
  echo "Run with --recheck to re-run the health check."
  echo ""
  exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  scrapekit setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ISSUES=()
STATUS="{}"

# ── Helper ────────────────────────────────────────────────────────────────────
check_binary() {
  local name="$1"
  if command -v "$name" &>/dev/null; then
    ok "$name — $(command -v "$name")"
    return 0
  else
    return 1
  fi
}

check_python_import() {
  python3 -c "import $1" 2>/dev/null
}

# ── 1. trafilatura ────────────────────────────────────────────────────────────
echo "[ trafilatura ]"
if check_binary trafilatura; then
  :
elif check_python_import trafilatura; then
  ok "trafilatura (python module)"
else
  fail "trafilatura not found"
  warn "Install: pip install trafilatura"
  ISSUES+=("trafilatura: pip install trafilatura")
fi
echo ""

# ── 2. webclaw ────────────────────────────────────────────────────────────────
echo "[ webclaw ]"
if check_binary webclaw; then
  :
else
  fail "webclaw not found"
  warn "Install: cargo install --git https://github.com/0xMassi/webclaw.git webclaw-cli"
  ISSUES+=("webclaw: cargo install --git https://github.com/0xMassi/webclaw.git webclaw-cli")
fi
echo ""

# ── 3. playwright ─────────────────────────────────────────────────────────────
echo "[ playwright ]"
if check_python_import playwright; then
  ok "playwright (python module)"
  if python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); b.close()
" 2>/dev/null; then
    ok "chromium browser — ready"
  else
    warn "chromium not installed"
    warn "Run: playwright install chromium"
    ISSUES+=("playwright: playwright install chromium")
  fi
else
  fail "playwright not found"
  warn "Install: pip install playwright && playwright install chromium"
  ISSUES+=("playwright: pip install playwright && playwright install chromium")
fi
echo ""

# ── 4. docling ────────────────────────────────────────────────────────────────
echo "[ docling ]"
if check_python_import docling; then
  ok "docling (python module)"
elif check_binary docling; then
  :
else
  fail "docling not found"
  warn "Install: pip install docling"
  ISSUES+=("docling: pip install docling")
fi
echo ""

# ── 5. browser-harness ────────────────────────────────────────────────────────
echo "[ browser-harness ]"
if check_binary browser-harness; then
  :
else
  fail "browser-harness not found"
  warn "See: references/browser-harness.md for install instructions"
  ISSUES+=("browser-harness: see references/browser-harness.md")
fi
echo ""

# ── 6. searxng (Docker) ───────────────────────────────────────────────────────
echo "[ searxng ]"
if command -v docker &>/dev/null; then
  ok "docker — $(docker --version 2>/dev/null | head -1)"
  if curl -sf --max-time 3 "http://localhost:8080/search?q=test&format=json" &>/dev/null; then
    ok "searxng — running at http://localhost:8080"
  else
    warn "searxng not running"
    warn "Start: docker run -d -p 8080:8080 searxng/searxng"
    ISSUES+=("searxng: docker run -d -p 8080:8080 searxng/searxng")
  fi
else
  warn "docker not found — searxng unavailable"
  warn "Install Docker Desktop or run searxng another way"
  ISSUES+=("searxng: docker not found — install Docker Desktop")
fi
echo ""

# ── 7. jina ───────────────────────────────────────────────────────────────────
echo "[ jina ]"
if [[ -n "${JINA_API_KEY:-}" ]]; then
  ok "JINA_API_KEY set"
  # Validate key with a minimal request
  STATUS_CODE=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 5 \
    "https://r.jina.ai/https://example.com" \
    -H "Authorization: Bearer $JINA_API_KEY" 2>/dev/null || echo "000")
  if [[ "$STATUS_CODE" == "200" ]]; then
    ok "API key valid"
  else
    warn "API key check returned HTTP $STATUS_CODE"
    warn "Verify at: https://jina.ai"
    ISSUES+=("jina: API key may be invalid (HTTP $STATUS_CODE)")
  fi
else
  warn "JINA_API_KEY not set — using anonymous (20 RPM limit)"
  warn "Get a free key (500 RPM + 10M tokens): https://jina.ai"
  warn "Set: export JINA_API_KEY=your_key"
fi
echo ""

# ── 8. apify ──────────────────────────────────────────────────────────────────
echo "[ apify ]"
if check_binary apify; then
  if [[ -n "${APIFY_TOKEN:-}" ]]; then
    ok "APIFY_TOKEN set"
  else
    warn "APIFY_TOKEN not set — social/e-commerce scraping unavailable"
    warn "Sign up (free tier): https://apify.com/sign-up"
    warn "Set: export APIFY_TOKEN=your_token"
    ISSUES+=("apify: export APIFY_TOKEN=your_token  # https://apify.com/sign-up")
  fi
else
  fail "apify CLI not found"
  warn "Install: npm install -g apify-cli"
  ISSUES+=("apify: npm install -g apify-cli")
  if [[ -z "${APIFY_TOKEN:-}" ]]; then
    warn "Also set: export APIFY_TOKEN=your_token  # https://apify.com/sign-up"
    ISSUES+=("apify: export APIFY_TOKEN=your_token  # https://apify.com/sign-up")
  fi
fi
echo ""

# ── 9. tavily ─────────────────────────────────────────────────────────────────
echo "[ tavily ]"
if [[ -n "${TAVILY_API_KEY:-}" ]]; then
  ok "TAVILY_API_KEY set"
  if check_python_import tavily; then
    ok "tavily python package"
  else
    warn "tavily python package not found"
    warn "Install: pip install tavily-python"
    ISSUES+=("tavily: pip install tavily-python")
  fi
else
  warn "TAVILY_API_KEY not set — 1k credits/month extraction unavailable"
  warn "Get a free key: https://app.tavily.com"
  warn "Set: export TAVILY_API_KEY=your_key"
  ISSUES+=("tavily: export TAVILY_API_KEY=your_key  # https://app.tavily.com")
fi
echo ""

# ── 10. firecrawl ─────────────────────────────────────────────────────────────
echo "[ firecrawl ]"
if check_binary firecrawl; then
  if [[ -n "${FIRECRAWL_API_KEY:-}" ]]; then
    ok "FIRECRAWL_API_KEY set"
  else
    warn "FIRECRAWL_API_KEY not set — firecrawl will fail"
    warn "Get a key: https://firecrawl.dev"
    warn "Set: export FIRECRAWL_API_KEY=your_key"
    ISSUES+=("firecrawl: export FIRECRAWL_API_KEY=your_key  # https://firecrawl.dev")
  fi
else
  fail "firecrawl CLI not found"
  warn "Install: npm install -g @mendable/firecrawl-js  OR  pip install firecrawl-py"
  ISSUES+=("firecrawl: npm install -g @mendable/firecrawl-js")
fi
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ ${#ISSUES[@]} -eq 0 ]]; then
  echo -e "  ${GREEN}All tools ready.${RESET}"
else
  echo -e "  ${YELLOW}${#ISSUES[@]} item(s) need attention:${RESET}"
  echo ""
  for issue in "${ISSUES[@]}"; do
    echo -e "  ${YELLOW}→${RESET}  $issue"
  done
fi
echo ""

# ── Save setup.json ───────────────────────────────────────────────────────────
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
ISSUES_JSON=$(printf '%s\n' "${ISSUES[@]:-}" | python3 -c "
import sys, json
lines = [l for l in sys.stdin.read().splitlines() if l]
print(json.dumps(lines))
")

python3 -c "
import json
data = {
  'date': '$DATE',
  'issues': $ISSUES_JSON
}
print(json.dumps(data, indent=2))
" > "$SETUP_FILE"

echo "  Setup state saved to $SETUP_FILE"
echo "  Run with --recheck to re-run at any time."
echo ""

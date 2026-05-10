#!/usr/bin/env bash
# Usage: compare.sh <url>
# Runs all scrapekit tools against the URL, generates a tabbed HTML viewer.
# Shows timing, word count, token count, and cost per tool.
# Tools: webfetch, trafilatura, jina, playwright, firecrawl, crawl4ai, webclaw, tavily

set -euo pipefail

URL="${1:?Usage: compare.sh <url>}"
SLUG=$(echo "$URL" | sed 's|https\?://||;s|[^a-zA-Z0-9]|-|g;s|-\+|-|g;s|^-||;s|-$||' | cut -c1-60)
OUT_DIR=".scrapekit/compare/${SLUG}"
HTML="$OUT_DIR/compare.html"

mkdir -p "$OUT_DIR"

echo "==> URL: $URL"
echo ""

# --- Timing helper (macOS-compatible milliseconds via python3) ---
now_ms() { python3 -c "import time; print(int(time.time() * 1000))"; }

timed_run() {
  local label="$1"; shift
  local start end elapsed
  start=$(now_ms)
  "$@"
  end=$(now_ms)
  elapsed=$(( end - start ))
  echo "$elapsed" > "$OUT_DIR/${label}.time"
}

read_time() { cat "$OUT_DIR/$1.time" 2>/dev/null || echo "0"; }

# --- Tool runners ---

run_webfetch() {
  echo "[1/8] webfetch (curl + markdownify)..."
  timed_run webfetch bash -c "
    curl -sL --max-time 15 \
      -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' \
      '$URL' | python3 -c \"
import sys
from markdownify import markdownify
print(markdownify(sys.stdin.read()))
\" > '$OUT_DIR/webfetch.md' 2>/dev/null || echo '(failed)' > '$OUT_DIR/webfetch.md'
  "
}

run_trafilatura() {
  echo "[2/8] trafilatura..."
  timed_run trafilatura bash -c "
    trafilatura -u '$URL' --output-format markdown \
      > '$OUT_DIR/trafilatura.md' 2>/dev/null || echo '(failed or empty)' > '$OUT_DIR/trafilatura.md'
    [ -s '$OUT_DIR/trafilatura.md' ] || echo '(empty output)' > '$OUT_DIR/trafilatura.md'
  "
}

run_jina() {
  echo "[3/8] jina reader..."
  timed_run jina bash -c "
    if [ -n '${JINA_API_KEY:-}' ]; then
      curl -s --max-time 30 'https://r.jina.ai/$URL' \
        -H 'Authorization: Bearer ${JINA_API_KEY:-}' \
        > '$OUT_DIR/jina.md' 2>/dev/null || echo '(failed)' > '$OUT_DIR/jina.md'
    else
      curl -s --max-time 30 'https://r.jina.ai/$URL' \
        > '$OUT_DIR/jina.md' 2>/dev/null || echo '(failed)' > '$OUT_DIR/jina.md'
    fi
    [ -s '$OUT_DIR/jina.md' ] || echo '(empty output)' > '$OUT_DIR/jina.md'
  "
}

run_playwright() {
  echo "[4/8] playwright + markdownify..."
  timed_run playwright python3 - <<EOF
from playwright.sync_api import sync_playwright
from markdownify import markdownify
import sys
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("$URL", wait_until="networkidle", timeout=30000)
        md = markdownify(page.content())
        browser.close()
    with open("$OUT_DIR/playwright.md", "w") as f:
        f.write(md)
except Exception as e:
    with open("$OUT_DIR/playwright.md", "w") as f:
        f.write(f"(failed: {e})")
EOF
  [ -s "$OUT_DIR/playwright.md" ] || echo "(empty output)" > "$OUT_DIR/playwright.md"
}

run_firecrawl() {
  echo "[5/8] firecrawl..."
  if command -v firecrawl &>/dev/null; then
    timed_run firecrawl bash -c "
      firecrawl scrape '$URL' --only-main-content -o '$OUT_DIR/firecrawl.md' 2>/dev/null \
        || echo '(failed)' > '$OUT_DIR/firecrawl.md'
      [ -s '$OUT_DIR/firecrawl.md' ] || echo '(empty output — check credits)' > '$OUT_DIR/firecrawl.md'
    "
  else
    echo "0" > "$OUT_DIR/firecrawl.time"
    echo "(firecrawl not installed)" > "$OUT_DIR/firecrawl.md"
  fi
}

run_crawl4ai() {
  echo "[6/8] crawl4ai..."
  timed_run crawl4ai python3 - <<EOF
import asyncio, warnings
warnings.filterwarnings("ignore")
try:
    from crawl4ai import AsyncWebCrawler
    async def main():
        async with AsyncWebCrawler(verbose=False) as c:
            r = await c.arun("$URL")
            md = r.markdown or "(empty output)"
            open("$OUT_DIR/crawl4ai.md", "w").write(md)
    asyncio.run(main())
except Exception as e:
    open("$OUT_DIR/crawl4ai.md", "w").write(f"(failed: {e})")
EOF
  [ -s "$OUT_DIR/crawl4ai.md" ] || echo "(empty output)" > "$OUT_DIR/crawl4ai.md"
}

run_webclaw() {
  echo "[7/8] webclaw..."
  if command -v webclaw &>/dev/null; then
    timed_run webclaw bash -c "
      webclaw '$URL' -f llm > '$OUT_DIR/webclaw.md' 2>/dev/null \
        || echo '(failed)' > '$OUT_DIR/webclaw.md'
      [ -s '$OUT_DIR/webclaw.md' ] || echo '(empty output)' > '$OUT_DIR/webclaw.md'
    "
  else
    echo "0" > "$OUT_DIR/webclaw.time"
    echo "(webclaw not installed — cargo install --git https://github.com/0xMassi/webclaw.git webclaw-cli)" > "$OUT_DIR/webclaw.md"
  fi
}

run_tavily() {
  echo "[8/8] tavily..."
  if [ -n "${TAVILY_API_KEY:-}" ]; then
    timed_run tavily python3 - <<EOF
try:
    from tavily import TavilyClient
    client = TavilyClient(api_key="${TAVILY_API_KEY:-}")
    r = client.extract("$URL")
    results = r.get("results", [])
    if results:
        md = results[0].get("raw_content", "(empty)")
    else:
        md = "(no results returned)"
    open("$OUT_DIR/tavily.md", "w").write(md)
except Exception as e:
    open("$OUT_DIR/tavily.md", "w").write(f"(failed: {e})")
EOF
  else
    echo "0" > "$OUT_DIR/tavily.time"
    echo "(TAVILY_API_KEY not set — get free key at app.tavily.com, 1000 credits/month)" > "$OUT_DIR/tavily.md"
  fi
  [ -s "$OUT_DIR/tavily.md" ] || echo "(empty output)" > "$OUT_DIR/tavily.md"
}

run_webfetch
run_trafilatura
run_jina
run_playwright
run_firecrawl
run_crawl4ai
run_webclaw
run_tavily

echo ""
echo "==> Generating compare.html..."

# --- Helpers ---
read_file() { cat "$OUT_DIR/$1.md" 2>/dev/null || echo "(missing)"; }

escape_html() {
  python3 -c "import sys, html; print(html.escape(sys.stdin.read()))"
}

count_tokens() {
  python3 - "$OUT_DIR/$1.md" <<'PYEOF' 2>/dev/null || echo "0"
import sys, pathlib
try:
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    text = pathlib.Path(sys.argv[1]).read_text(errors="replace")
    print(len(enc.encode(text)))
except Exception:
    text = pathlib.Path(sys.argv[1]).read_text(errors="replace")
    print(len(text) // 4)
PYEOF
}

wc_words() { wc -w < "$OUT_DIR/$1.md" 2>/dev/null | tr -d ' '; }

# Read all outputs
WF=$(read_file webfetch | escape_html)
TR=$(read_file trafilatura | escape_html)
JN=$(read_file jina | escape_html)
PW=$(read_file playwright | escape_html)
FC=$(read_file firecrawl | escape_html)
C4=$(read_file crawl4ai | escape_html)
WC=$(read_file webclaw | escape_html)
TV=$(read_file tavily | escape_html)

# Words
W1=$(wc_words webfetch);    W2=$(wc_words trafilatura); W3=$(wc_words jina)
W4=$(wc_words playwright);  W5=$(wc_words firecrawl);   W6=$(wc_words crawl4ai)
W7=$(wc_words webclaw);     W8=$(wc_words tavily)

# Tokens
TK1=$(count_tokens webfetch);    TK2=$(count_tokens trafilatura); TK3=$(count_tokens jina)
TK4=$(count_tokens playwright);  TK5=$(count_tokens firecrawl);   TK6=$(count_tokens crawl4ai)
TK7=$(count_tokens webclaw);     TK8=$(count_tokens tavily)

# Times
T1=$(read_time webfetch);    T2=$(read_time trafilatura); T3=$(read_time jina)
T4=$(read_time playwright);  T5=$(read_time firecrawl);   T6=$(read_time crawl4ai)
T7=$(read_time webclaw);     T8=$(read_time tavily)

# Cost labels
C1="free"; C2="free"; C3="tokens(jina)"; C4L="free(heavy)"; C5="1 credit"
C6="free"; C7="free"; C8="1 credit(tavily)"

cat > "$HTML" <<HTMLEOF
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>scrapekit compare — ${URL}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f0f0f; color: #e0e0e0; }
  header { padding: 16px 24px; background: #1a1a1a; border-bottom: 1px solid #333; }
  header h1 { font-size: 14px; font-weight: 600; color: #aaa; }
  header .url { font-size: 12px; color: #666; margin-top: 4px; word-break: break-all; }
  .tabs { display: flex; gap: 2px; padding: 12px 24px 0; background: #1a1a1a; flex-wrap: wrap; }
  .tab { padding: 8px 14px; font-size: 13px; cursor: pointer; border-radius: 6px 6px 0 0;
         background: #252525; color: #888; border: 1px solid #333; border-bottom: none;
         user-select: none; }
  .tab:hover { color: #ccc; background: #2a2a2a; }
  .tab.active { background: #0f0f0f; color: #fff; border-color: #444; }
  .tab .meta { font-size: 10px; color: #555; display: flex; gap: 8px; margin-top: 3px; }
  .tab.active .meta { color: #777; }
  .tab .cost { color: #4a8; }
  .tab.active .cost { color: #6da; }
  .tab .tokens { color: #88f; }
  .tab.active .tokens { color: #aaf; }
  .pane { display: none; padding: 24px; height: calc(100vh - 140px); overflow-y: auto; }
  .pane.active { display: block; }
  pre { white-space: pre-wrap; word-break: break-word; font-family: "SF Mono", "Fira Code", monospace;
        font-size: 13px; line-height: 1.6; color: #d4d4d4; background: #141414;
        padding: 20px; border-radius: 8px; border: 1px solid #2a2a2a; }
</style>
</head>
<body>
<header>
  <h1>scrapekit compare</h1>
  <div class="url">${URL}</div>
</header>
<div class="tabs">
  <div class="tab active" onclick="show(0)">
    webfetch
    <div class="meta"><span>${W1}w</span><span class="tokens">${TK1}tok</span><span>${T1}ms</span><span class="cost">${C1}</span></div>
  </div>
  <div class="tab" onclick="show(1)">
    trafilatura
    <div class="meta"><span>${W2}w</span><span class="tokens">${TK2}tok</span><span>${T2}ms</span><span class="cost">${C2}</span></div>
  </div>
  <div class="tab" onclick="show(2)">
    jina
    <div class="meta"><span>${W3}w</span><span class="tokens">${TK3}tok</span><span>${T3}ms</span><span class="cost">${C3}</span></div>
  </div>
  <div class="tab" onclick="show(3)">
    playwright
    <div class="meta"><span>${W4}w</span><span class="tokens">${TK4}tok</span><span>${T4}ms</span><span class="cost">${C4L}</span></div>
  </div>
  <div class="tab" onclick="show(4)">
    firecrawl
    <div class="meta"><span>${W5}w</span><span class="tokens">${TK5}tok</span><span>${T5}ms</span><span class="cost">${C5}</span></div>
  </div>
  <div class="tab" onclick="show(5)">
    crawl4ai
    <div class="meta"><span>${W6}w</span><span class="tokens">${TK6}tok</span><span>${T6}ms</span><span class="cost">${C6}</span></div>
  </div>
  <div class="tab" onclick="show(6)">
    webclaw
    <div class="meta"><span>${W7}w</span><span class="tokens">${TK7}tok</span><span>${T7}ms</span><span class="cost">${C7}</span></div>
  </div>
  <div class="tab" onclick="show(7)">
    tavily
    <div class="meta"><span>${W8}w</span><span class="tokens">${TK8}tok</span><span>${T8}ms</span><span class="cost">${C8}</span></div>
  </div>
</div>
<div class="pane active"><pre>${WF}</pre></div>
<div class="pane"><pre>${TR}</pre></div>
<div class="pane"><pre>${JN}</pre></div>
<div class="pane"><pre>${PW}</pre></div>
<div class="pane"><pre>${FC}</pre></div>
<div class="pane"><pre>${C4}</pre></div>
<div class="pane"><pre>${WC}</pre></div>
<div class="pane"><pre>${TV}</pre></div>
<script>
  const tabs = document.querySelectorAll('.tab');
  const panes = document.querySelectorAll('.pane');
  function show(i) {
    tabs.forEach((t,j) => t.classList.toggle('active', i===j));
    panes.forEach((p,j) => p.classList.toggle('active', i===j));
  }
</script>
</body>
</html>
HTMLEOF

echo "==> Done: $HTML"
echo ""
printf "%-14s %8s %8s %8s  %s\n" "tool" "words" "tokens" "time" "cost"
printf "%-14s %8s %8s %8s  %s\n" "webfetch"    "$W1" "$TK1" "${T1}ms"  "$C1"
printf "%-14s %8s %8s %8s  %s\n" "trafilatura" "$W2" "$TK2" "${T2}ms"  "$C2"
printf "%-14s %8s %8s %8s  %s\n" "jina"        "$W3" "$TK3" "${T3}ms"  "$C3"
printf "%-14s %8s %8s %8s  %s\n" "playwright"  "$W4" "$TK4" "${T4}ms"  "$C4L"
printf "%-14s %8s %8s %8s  %s\n" "firecrawl"   "$W5" "$TK5" "${T5}ms"  "$C5"
printf "%-14s %8s %8s %8s  %s\n" "crawl4ai"    "$W6" "$TK6" "${T6}ms"  "$C6"
printf "%-14s %8s %8s %8s  %s\n" "webclaw"     "$W7" "$TK7" "${T7}ms"  "$C7"
printf "%-14s %8s %8s %8s  %s\n" "tavily"      "$W8" "$TK8" "${T8}ms"  "$C8"
echo ""
open "$HTML" 2>/dev/null || xdg-open "$HTML" 2>/dev/null || echo "Open manually: $HTML"

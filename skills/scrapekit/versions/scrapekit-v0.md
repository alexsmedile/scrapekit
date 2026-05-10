---
name: scrapekit
description: |
  Proactive web scraping and document extraction router. Routes fetch/scrape tasks across webclaw, trafilatura, jina, playwright, tavily, apify, browser-harness, docling, searxng, and firecrawl based on source type, cost, and complexity. Use when user wants to fetch a URL, scrape a page, extract content from HTML/PDF/DOCX, convert to markdown or JSON, crawl a site, search the web, scrape social media (Instagram, TikTok, YouTube, LinkedIn, Twitter/X, Facebook, Reddit, Google Maps), scrape e-commerce (Amazon, Google Shopping), or needs full browser rendering. Triggers on: "fetch", "scrape", "get the page", "extract from", "convert to markdown", "crawl", "search the web", "parse PDF", "render page", "scrape instagram/tiktok/youtube/linkedin/twitter/facebook/reddit/amazon". Proactively picks the cheapest/fastest tool that can handle the job.
allowed-tools:
  - WebFetch
  - Bash(trafilatura*)
  - Bash(docling*)
  - Bash(playwright*)
  - Bash(markdownify*)
  - Bash(python3*)
  - Bash(firecrawl*)
  - Bash(mkdir*)
  - Bash(head*)
  - Bash(grep*)
  - Bash(jq*)
  - Bash(curl*)
  - Bash(docker*)
  - Bash(browser-harness*)
  - Bash(webclaw*)
  - Bash(apify*)
---

# scrapekit — routing guide

**Default rule: local tools first. Use external APIs (jina, firecrawl) only when:**
- user explicitly requests them, OR
- local tools clearly won't work (login-gated, heavy JS SPA, bot-blocked), OR
- speed/simplicity is more important than avoiding an API call

## Routing decision tree

```
Need to find URLs first (no URL yet)?
  ├─ searxng (local Docker, free, snippets)         ← default
  ├─ need full page content in results?  → jina search (s.jina.ai, external)
  └─ user requests it / searxng unavailable? → firecrawl search (credits)

Have a URL?
  ├─ Local file or structured doc (PDF, DOCX, PPTX, tables)?
  │    └─ docling (local)
  │
  ├─ Quick lookup / tokens don't matter?
  │    └─ webclaw (fastest of all: 35-850ms, free, local)
  │         └─ no webclaw? → webfetch
  │
  ├─ Article / Wikipedia / static docs / pricing page?
  │    └─ trafilatura   ← best token efficiency (3-5x less than others)
  │         └─ output < 200 tokens? → it's a SPA → webclaw → playwright
  │
  ├─ GitHub repo / SPA / React app?
  │    └─ webclaw first (fast, often complete)
  │         └─ thin output? → playwright → jina
  │
  ├─ YouTube / bot-protected?
  │    └─ jina reader   ← only tool with real content (17k tok vs webclaw 967)
  │
  ├─ Need clean LLM-ready extraction with credits budget?
  │    └─ tavily (1k free credits/month, 500-2000ms, good quality)
  │         └─ fails on YouTube, auth-gated, bot-blocked
  │
  ├─ Platform-specific scraping (social, e-commerce, maps, reviews)?
  │    └─ apify — purpose-built actors, generous free tier
  │         ├─ Instagram, TikTok, YouTube, LinkedIn, X/Twitter, Facebook
  │         ├─ Reddit, Google Maps, Amazon, Airbnb, TripAdvisor
  │         └─ see actor catalog below
  │
  ├─ Login-gated / need real cookies / multi-step interaction?
  │    └─ browser-harness   ← connects to user's running Chrome with real session
  │         └─ can click, fill forms, scroll, screenshot, handle iframes/shadow DOM
  │
  └─ All tools failed?
       └─ firecrawl (credits, last resort)
```

**Tool tiers:**
- **Local (free, no external call):** webclaw, webfetch, trafilatura, playwright+markdownify, crawl4ai, docling, searxng, browser-harness
- **External API (free tier / monthly credits):** jina reader (10M free tokens), tavily (1k/month), apify (generous free tier per actor)
- **Credits (last resort):** firecrawl

---

## Benchmark results — 10 real sites, 8 tools

Tokens = cl100k_base (same as Claude context cost). Firecrawl excluded (0 credits). Tavily = 1 credit/page from 1k/month free.

| Site | Type | webfetch | trafilatura | jina | playwright | crawl4ai | webclaw | tavily |
|---|---|---|---|---|---|---|---|---|
| Wikipedia/LLM | Long article | 72k/384ms | **24k**/509ms | 83k/1785ms | 73k/1664ms | 86k/2150ms | 47k/**207ms** | 85k/1159ms |
| docs.firecrawl.dev | JS docs SPA | 3.2k/256ms | **0.7k**/487ms | 3.7k/921ms | 37/30548ms | 3.9k/1883ms | **1.9k/189ms** | 1.5k/527ms |
| jina.ai/reader | Marketing SPA | 12.6k/198ms | **3.1k**/423ms | 10.7k/807ms | 15.9k/2346ms | 29.8k/2202ms | 6.2k/**157ms** | 8k/711ms |
| obsidian.md/pricing | Pricing SSR | 1.8k/143ms | **418**/368ms | 2.4k/1058ms | 1.8k/1091ms | 2.2k/1994ms | 980/**104ms** | 2.4k/715ms |
| github.com SDK | GitHub repo | 4.4k/720ms | 158/1509ms | 8.9k/**378ms** | **7.9k**/2683ms | 9k/2043ms | 1.8k/154ms | 2.2k/1948ms |
| notion.so/product | Full SPA | 5.4k/907ms | 91/1249ms | **7.9k/377ms** | 6.1k/3802ms | 6.8k/3092ms | **13k**/1017ms | 753/545ms |
| docs.searxng.org | Static docs | 21.6k/239ms | **5.2k**/406ms | 24.6k/1978ms | 21.6k/1366ms | 26.9k/2585ms | 14.2k/**122ms** | 17.9k/857ms |
| youtube.com/watch | Bot wall | 247/1071ms | 57/1275ms | **17k/624ms** | 13.8k/4501ms | 640/2725ms | 967/965ms | 4/1194ms |
| playwright.dev/api | API reference | 62k/522ms | **28k**/746ms | 64k/1038ms | 62k/2008ms | 71k/2776ms | **28k/228ms** | 62k/1043ms |
| docs.claude.ai | Auth-gated | 1/136ms | 5/229ms | **59/207ms** | 64/438ms | 3/1121ms | 3/**35ms** | 4/1294ms |

Format: `tokens/ms`. **Bold** = best for that site on that dimension.

### Tool verdicts

**webclaw** — biggest winner overall. Fastest tool across the board (35–1017ms, no Chromium). Token-efficient: beats webfetch on every page. Got **13k on Notion** (best of all tools). Tied trafilatura on Playwright API docs (28k vs 28k). Fails on YouTube (967 vs jina 17k) and thin on GitHub (1.8k vs playwright 7.9k). Free, local, Rust-based TLS fingerprinting — no bot detection.

**trafilatura** — still best token efficiency on SSR/static pages. Wikipedia: 24k vs everyone else at 72-86k. Pricing pages, docs, articles — 3-5x cleaner than all others. Hard fails on SPAs (GitHub: 158 tok, Notion: 91 tok).

**tavily** — solid mid-tier. Consistent 500-2000ms. Good quality on static/SSR pages. Fails completely on YouTube (4 tok) and auth-gated. Costs 1 credit/page from 1k/month free budget. No advantage over free tools on static pages — save credits for pages where webclaw/trafilatura also struggle.

**jina** — still the only tool for YouTube (17k tok). Fast on SPAs when not rate-limited (377ms on Notion). Over-fetches on Wikipedia (83k = highest of all). Variable latency: 207ms to 1978ms.

**playwright** — reliable SPA fallback (GitHub: 7.9k). But 30s+ timeout on bot-blocked JS SPAs (firecrawl.dev: 30,548ms for 37 tokens). Always 1.3-4.5s minimum overhead. Use only when webclaw comes up thin on SPAs.

**crawl4ai** — underperforms. Slower than playwright (2-3s always), noisier output (jina.ai: 29.8k vs trafilatura 3.1k). Marginal GitHub edge (9k vs playwright 7.9k). Hard to justify over playwright+markdownify.

**webfetch** — still useful for pure speed when token count doesn't matter (143ms on pricing page). Includes full page chrome. Replaced by webclaw as default quick tool.

### By content type — best tool

| Content type | Best | Why |
|---|---|---|
| Wikipedia / long articles | trafilatura | 24k vs 47-86k for everything else |
| Static docs (Sphinx, ReadTheDocs) | trafilatura | 5.2k vs 14-27k |
| API reference (large) | trafilatura or webclaw | Both 28k, webclaw 3x faster |
| Pricing / marketing SSR | trafilatura | 418 tok vs 980-2400 |
| Quick lookup, speed matters | webclaw | Fastest: 35-850ms, free, local |
| GitHub repo page | playwright | webclaw thin (1.8k), playwright complete (7.9k) |
| React / Notion SPA | webclaw | Got 13k vs playwright 6.1k |
| JS docs SPA | webclaw or jina | webclaw 1.9k, playwright dead (30s) |
| YouTube / bot-protected | jina | Only one with real content (17k) |
| Need credits, quality matters | tavily | 500-2000ms, clean output, 1k/month free |
| Auth-gated / login-gated | browser-harness | Real Chrome session |
| Multi-step interaction | browser-harness | Click, scroll, fill, screenshot |
| PDF / DOCX / PPTX | docling | Purpose-built |

### Speed ranking (fastest → slowest)
1. **webclaw** — 35–1,017ms ← fastest overall
2. **webfetch** — 130–1,071ms
3. **jina** — 207–1,978ms avg (spikes on rate-limited IPs)
4. **trafilatura** — 229–1,509ms
5. **tavily** — 527–1,948ms
6. **crawl4ai** — 1,121–3,092ms
7. **playwright** — 438–30,548ms (30s+ on bot-blocked)

### Token efficiency ranking (least → most tokens)
1. **trafilatura** — best on SSR/static, 3-5x cleaner than others
2. **webclaw** — close second, better on SPAs than trafilatura
3. **tavily** — mid-range, consistent quality
4. **webfetch / playwright** — include full page chrome
5. **jina** — over-fetches (Wikipedia: 83k, highest)
6. **crawl4ai** — noisiest (jina.ai: 29.8k vs trafilatura 3.1k)

---

## WebFetch — built-in, free, fastest

Use for: simple articles, docs pages, quick lookups.

```python
# Via Claude tool — no shell command needed
# Just call WebFetch(url, prompt) directly
```

Signs output is incomplete: < 1000 chars, truncated mid-sentence, missing known sections.

---

## trafilatura — free, URL or local HTML

Use for: web articles, blogs, news, docs — when WebFetch is incomplete.

```bash
# URL → markdown (stdout)
trafilatura -u "https://example.com" --output-format markdown

# URL → JSON with metadata
trafilatura -u "https://example.com" --output-format json

# Local HTML file → markdown
trafilatura -f --output-format markdown < page.html

# Batch: list of URLs from file
trafilatura --input-file urls.txt --output-dir .scrapekit/ --output-format markdown

# Crawl a site (follow links from seed URL)
trafilatura --crawl "https://example.com" --output-dir .scrapekit/ --output-format markdown

# Sitemap crawl
trafilatura --sitemap "https://example.com" --output-dir .scrapekit/ --output-format markdown

# With metadata, preserve formatting and links
trafilatura -u "https://example.com" --output-format markdown --formatting --links --with-metadata

# Precision mode (fewer results, higher quality)
trafilatura -u "https://example.com" --output-format markdown --precision

# Recall mode (more content, lower precision)
trafilatura -u "https://example.com" --output-format markdown --recall
```

---

## docling — free, local-first, structured output

Use for: PDFs, DOCX, PPTX, images, local files, any format needing structured JSON.
Slower than trafilatura — good for documents, not fast web scraping.

```bash
# PDF → markdown (default output: current dir)
docling file.pdf

# PDF → markdown, specific output dir
docling file.pdf --output .scrapekit/

# PDF → JSON
docling file.pdf --to json --output .scrapekit/

# URL → markdown
docling "https://example.com/doc.pdf" --output .scrapekit/

# HTML → markdown
docling page.html --from html --to md --output .scrapekit/

# DOCX / PPTX
docling file.docx --output .scrapekit/
docling file.pptx --output .scrapekit/

# Batch: entire folder
docling ./docs/ --output .scrapekit/

# Multiple output formats at once
docling file.pdf --to md --to json --output .scrapekit/

# With OCR (for scanned PDFs or images)
docling scan.pdf --ocr --output .scrapekit/

# Tables only, fast mode
docling file.pdf --table-mode fast --output .scrapekit/

# Structured JSON with table extraction (best for data)
docling file.pdf --to json --tables --output .scrapekit/
```

---

## jina reader — free tier, JS rendering, zero setup

Use for: JS-heavy pages, PDFs, any URL when trafilatura is incomplete. No install, no browser.
Free tier: 20 RPM (no key), 500 RPM (free API key). 10M tokens on signup.

**Setup (optional, raises rate limit):**
```bash
export JINA_API_KEY="your_key_here"   # get free at jina.ai
```

**Fetch URL → markdown:**
```bash
# No API key (20 RPM)
curl -s "https://r.jina.ai/https://example.com" -o .scrapekit/page.md
head -80 .scrapekit/page.md

# With API key (500 RPM)
curl -s "https://r.jina.ai/https://example.com" \
  -H "Authorization: Bearer $JINA_API_KEY" \
  -o .scrapekit/page.md
```

**Search with full content (s.jina.ai):**
```bash
# Returns search results WITH extracted content — no follow-up scrape needed
curl -s "https://s.jina.ai/?q=YOUR+QUERY" \
  -H "Authorization: Bearer $JINA_API_KEY" \
  -H "Accept: application/json" \
  -o .scrapekit/search.json

# Without key (lower rate limit)
curl -s "https://s.jina.ai/?q=YOUR+QUERY" -o .scrapekit/search.md
```

**Options via headers:**
```bash
# Target specific CSS selector (cuts noise)
-H "X-Target-Selector: main article"

# Return links in output
-H "X-Return-Format: markdown"

# With images captioned
-H "X-With-Images-Summary: true"
```

---

## playwright + markdownify — free, full browser rendering

Use for: JS-heavy SPAs, React/Vue/Angular, SPA dashboards, lazy-loaded pages, infinite scroll.

**The tell:** trafilatura returns empty output or just `<div id="root"></div>` — content is rendered client-side. That's the signal to switch to playwright.

**Not worth it for:**
- Normal articles/blogs — trafilatura handles these
- Login-gated pages — use browser-harness for interactive auth instead
- Bot-blocked sites — headless Chromium is detectable, use jina/firecrawl instead

**Why it works:** Playwright launches real Chromium, executes JS, then `markdownify` converts the
fully-rendered HTML to markdown in-process. No temp files, no piping.

**Downsides:** Heavy — launches Chromium, slower, memory hungry. Bar is "trafilatura returned garbage", not "might be JS".

**Canonical pattern (use this):**
```python
from playwright.sync_api import sync_playwright
from markdownify import markdownify

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    html = page.content()
    md = markdownify(html)
    browser.close()
```

**In practice via bash:**
```bash
mkdir -p .scrapekit

# Fetch JS page → markdown in one python3 call
python3 - <<'EOF'
from playwright.sync_api import sync_playwright
from markdownify import markdownify

url = "https://example.com"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    md = markdownify(page.content())
    browser.close()

with open(".scrapekit/page.md", "w") as f:
    f.write(md)
EOF
head -80 .scrapekit/page.md

# Wait for specific element, grab only main content area
python3 - <<'EOF'
from playwright.sync_api import sync_playwright
from markdownify import markdownify

url = "https://example.com"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    page.wait_for_selector("main", timeout=10000)
    md = markdownify(page.inner_html("main"))
    browser.close()

with open(".scrapekit/page.md", "w") as f:
    f.write(md)
EOF
```

**One-time setup if chromium not installed:**
```bash
playwright install chromium
```

---

## searxng — free, self-hosted web search

Use for: web search when you have no URL. Free, unlimited, no tracking, no credits.
Requires: local Docker instance running on port 8080.

**One-time setup:**
```bash
mkdir searxng && cd searxng
curl -fsSL -O https://raw.githubusercontent.com/searxng/searxng/master/container/docker-compose.yml \
    -O https://raw.githubusercontent.com/searxng/searxng/master/container/.env.example
cp .env.example .env
docker compose up -d
# Opens at http://localhost:8080
```

**Always start → search → stop. Never leave running.**

```bash
# Start
docker compose -f ~/searxng/docker-compose.yml up -d

# Wait for ready (polls until responsive)
until curl -sf "http://localhost:8080/search?q=test&format=json" > /dev/null; do sleep 1; done

# Search → save results
curl -s "http://localhost:8080/search?q=YOUR+QUERY&format=json" -o .scrapekit/search.json

# Stop immediately after
docker compose -f ~/searxng/docker-compose.yml down
```

**Extract from results:**
```bash
jq -r '.results[].url' .scrapekit/search.json
jq -r '.results[] | "\(.title)\n\(.url)"' .scrapekit/search.json | head -30
jq '.results[:5]' .scrapekit/search.json
```

**Multiple queries — parallel (fastest):**
```bash
docker compose -f ~/searxng/docker-compose.yml up -d
until curl -sf "http://localhost:8080/search?q=test&format=json" > /dev/null; do sleep 1; done

# Fire all queries in parallel, wait for all to finish
curl -s "http://localhost:8080/search?q=QUERY+ONE&format=json" -o .scrapekit/search-one.json &
curl -s "http://localhost:8080/search?q=QUERY+TWO&format=json" -o .scrapekit/search-two.json &
curl -s "http://localhost:8080/search?q=QUERY+THREE&format=json" -o .scrapekit/search-three.json &
wait

docker compose -f ~/searxng/docker-compose.yml down
```

---

## webclaw — fastest local tool

Use for: quick lookups, SPAs, any page where speed matters. Rust-based, TLS fingerprinting, no browser.
Free, local, no API key.

```bash
# URL → LLM-optimized markdown (fastest)
webclaw "https://example.com" -f llm > .scrapekit/page.md
head -80 .scrapekit/page.md

# Default format
webclaw "https://example.com" > .scrapekit/page.md
```

**Install:** `cargo install --git https://github.com/0xMassi/webclaw.git webclaw-cli`

---

## crawl4ai — local async crawler

Use for: when you specifically need async Python crawler with LLM-extraction hooks. In practice slower and noisier than playwright+markdownify — prefer playwright unless you need crawl4ai's extraction strategies.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as c:
        r = await c.arun("https://example.com")
        open(".scrapekit/page.md", "w").write(r.markdown)

asyncio.run(main())
```

---

## tavily — 1k free credits/month, clean extraction

Use for: pages where free tools struggle and you want LLM-ready output without spinning up playwright.
1,000 free credits/month at app.tavily.com. Requires `TAVILY_API_KEY` env var.
**Avoid on:** YouTube, auth-gated pages (returns near-zero content).

```python
from tavily import TavilyClient
client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Extract page content
r = client.extract("https://example.com")
content = r["results"][0]["raw_content"]
open(".scrapekit/page.md", "w").write(content)

# Search
results = client.search("query", max_results=5)
```

**Check remaining credits:** monitor at app.tavily.com dashboard.

---

## browser-harness — real Chrome, real session

Use for: login-gated pages, multi-step interactions, sites that block headless Chromium, anything requiring real cookies.

**Key difference from playwright:** connects to the user's **already-running Chrome** via CDP — real browser, real auth state, real cookies. Playwright launches a clean headless Chromium with no session.

**When to use over playwright:**
- Page requires login and you're already logged in on Chrome
- Site detects and blocks headless Chromium (playwright gets 37 tokens, browser-harness gets full content)
- Need to click, scroll, fill forms, handle dialogs before extracting
- Iframe / shadow DOM / cross-origin content that needs compositor-level clicks

**Extraction pattern:**
```bash
browser-harness -c '
new_tab("https://example.com/dashboard")
wait_for_load()
# get full page markdown
from markdownify import markdownify
md = markdownify(js("document.documentElement.outerHTML"))
open(".scrapekit/page.md", "w").write(md)
print(f"Extracted {len(md)} chars")
'
```

**With screenshot to verify before extracting:**
```bash
browser-harness -c '
new_tab("https://example.com")
wait_for_load()
capture_screenshot()   # view current state
md = markdownify(js("document.body.innerHTML"))
open(".scrapekit/page.md", "w").write(md)
'
```

**Bulk HTTP (fast, no browser overhead):**
```bash
browser-harness -c '
from concurrent.futures import ThreadPoolExecutor
urls = ["https://example.com/page1", "https://example.com/page2"]
results = list(ThreadPoolExecutor().map(http_get, urls))
'
```

**Not for:** pages you are not logged into, headless server use without remote daemon, parallel scraping (use remote daemon with BU_NAME for that).

See full docs: `~/code/tools/browser-harness/SKILL.md`

---

## apify — platform-specific scraping, generous free tier

Use for: social media, e-commerce, maps, reviews — any platform that blocks generic scrapers.
Apify provides purpose-built actors with anti-bot bypass for each platform.
Free tier is generous per actor (varies by actor, check before running).

**Install CLI:**
```bash
npm install -g apify-cli
apify login   # opens browser OAuth — or: export APIFY_TOKEN=your_token
```
Get token: https://console.apify.com/settings/integrations

**Workflow:**
```bash
# 1. Find the right actor (or use catalog below)
apify actors search "instagram scraper" --json 2>/dev/null | jq '.items[:3] | .[] | {id: .username, title, users: .stats.totalUsers30Days}'

# 2. Check actor input schema
apify actors info "apify/instagram-scraper" --input --json 2>/dev/null

# 3. Run (blocking, waits for result)
apify actors call "apify/instagram-scraper" \
  -i '{"directUrls":["https://www.instagram.com/natgeo/"],"resultsType":"posts","resultsLimit":20}' \
  --json 2>/dev/null | tee .scrapekit/run.json

# 4. Fetch dataset results
DATASET_ID=$(jq -r '.defaultDatasetId' .scrapekit/run.json)
apify datasets get-items "$DATASET_ID" --format json > .scrapekit/results.json
head -c 2000 .scrapekit/results.json

# Long-running: start async, poll
apify actors start "ACTOR_ID" -i 'JSON_INPUT' --json 2>/dev/null | tee .scrapekit/run.json
RUN_ID=$(jq -r '.id' .scrapekit/run.json)
apify runs info "$RUN_ID" --json 2>/dev/null | jq '.status'
```

**Always add `--json 2>/dev/null`** — stderr has progress noise that breaks JSON parsers.

### Actor catalog — platform reference

| Platform | What | Actor ID |
|---|---|---|
| **Google** | Maps reviews | `compass/google-maps-reviews-scraper` |
| **Google** | Places | `compass/crawler-google-places` |
| **Google** | Ads | `silva95gustavo/google-ads-scraper` |
| **YouTube** | Videos / channel | `streamers/youtube-scraper` |
| **YouTube** | Comments | `streamers/youtube-comments-scraper` |
| **YouTube** | Shorts | `streamers/youtube-shorts-scraper` |
| **YouTube** | Transcripts | `pintostudio/youtube-transcript-scraper` |
| **YouTube** | Business emails | `dataovercoffee/youtube-channel-business-email-scraper` |
| **Instagram** | Posts | `apify/instagram-scraper` |
| **Instagram** | Post detail | `apify/instagram-post-scraper` |
| **Instagram** | Profile | `apify/instagram-profile-scraper` |
| **Instagram** | Reels | `apify/instagram-reel-scraper` |
| **Instagram** | Comments | `apify/instagram-comment-scraper` |
| **Instagram** | Hashtags | `apify/instagram-hashtag-scraper` |
| **TikTok** | Videos | `clockworks/tiktok-scraper` |
| **TikTok** | Profile | `clockworks/tiktok-profile-scraper` |
| **TikTok** | Comments | `clockworks/tiktok-comments-scraper` |
| **TikTok** | Hashtags | `clockworks/tiktok-hashtag-scraper` |
| **Facebook** | Posts | `apify/facebook-posts-scraper` |
| **Facebook** | Pages | `apify/facebook-pages-scraper` |
| **Facebook** | Groups | `apify/facebook-groups-scraper` |
| **Facebook** | Comments | `apify/facebook-comments-scraper` |
| **Facebook** | Reviews | `apify/facebook-reviews-scraper` |
| **Facebook** | Marketplace | `apify/facebook-marketplace-scraper` |
| **Facebook** | Ads Library | `curious_coder/facebook-ads-library-scraper` |
| **LinkedIn** | Profile | `dev_fusion/linkedin-profile-scraper` |
| **LinkedIn** | Profile search | `harvestapi/linkedin-profile-search` |
| **LinkedIn** | Profile posts | `harvestapi/linkedin-profile-posts` |
| **LinkedIn** | Jobs | `bebity/linkedin-jobs-scraper` |
| **X / Twitter** | Tweets | `apidojo/tweet-scraper` |
| **Reddit** | Posts / comments | `trudax/reddit-scraper-lite` |
| **Amazon** | Products | `junglee/amazon-crawler` |
| **E-commerce** | Generic | `apify/e-commerce-scraping-tool` |
| **Airbnb** | Listings | `tri_angle/airbnb-scraper` |
| **TripAdvisor** | Reviews | `maxcopell/tripadvisor-reviews` |

Check credits before heavy runs: https://console.apify.com/billing

---

## firecrawl — credits, JS rendering, search

Use when: free tools fail, JS-heavy SPA, need web search, or need browser interaction.
Check credits first: `firecrawl credit-usage`

**Why not self-hosted:** firecrawl self-hosted requires Redis + Postgres + Playwright microservice + API build — too heavy to maintain for occasional scraping. Playwright+markdownify already covers local JS rendering. Firecrawl's real edge (bot-bypass, login-gated) doesn't fully replicate locally anyway. Use cloud credits for the rare hard case; use browser-harness for interactive login sessions.

```bash
# Check credits before using
firecrawl credit-usage

# Search (no URL yet)
firecrawl search "query" --limit 5 -o .scrapekit/search.json --json
firecrawl search "query" --scrape -o .scrapekit/search.json --json   # include full content

# Scrape JS-heavy page
firecrawl scrape "<url>" -o .scrapekit/page.md
firecrawl scrape "<url>" --only-main-content -o .scrapekit/page.md
firecrawl scrape "<url>" --wait-for 3000 -o .scrapekit/page.md       # wait for JS

# Structured extraction
firecrawl scrape "<url>" --format json --schema '{"price":"string"}' -o .scrapekit/data.json

# Map site URLs
firecrawl map "<url>" --limit 200 --json -o .scrapekit/urls.json
```

---

## Compare tool — visual side-by-side

Run all tools against a URL, generate a tabbed HTML viewer with timing, word count, and cost per tool:

```bash
bash ~/.claude/skills/scrapekit/scripts/compare.sh "https://example.com"
# Opens .scrapekit/compare/compare.html in browser
```

Each tab shows: tool name / word count / token count / time (ms) / cost label. Use to decide which tool fits a given site. Token count uses cl100k_base (tiktoken), approximating Claude context cost.

---

## Output rules

- Always write to `.scrapekit/` to avoid context bloat
- Add `.scrapekit/` to `.gitignore`
- Never read entire output — use `head -80 file.md` or `grep "keyword" file.md`
- Naming: `.scrapekit/{site}-{slug}.md`, `.scrapekit/search-{query}.json`
- Always quote URLs in shell (avoid `?` and `&` issues)

```bash
mkdir -p .scrapekit
```

---

## Escalation pattern

```
article / docs / Wikipedia:   trafilatura → webclaw → jina → tavily → firecrawl
GitHub repo:                  playwright → jina → tavily → firecrawl
SPA / React / Notion:         webclaw → playwright → jina → firecrawl
YouTube / bot-protected:      apify (youtube-scraper) → jina → firecrawl
social media platform:        apify (platform actor) — always, generic scrapers blocked
e-commerce / Amazon:          apify (amazon-crawler / e-commerce-tool)
quick lookup, speed first:    webclaw → webfetch
login-gated / needs auth:     browser-harness (real Chrome session)
doc/PDF/DOCX:                 docling
search (no URL):              searxng → jina search → firecrawl search
```

Stop as soon as output > 200 tokens and looks complete. Don't over-engineer.

**Token check rule:** if any tool returns < 200 tokens on a page that should have content, it failed — escalate.

## When to use which

| Situation | Tool |
|---|---|
| Wikipedia / long article | trafilatura — 24k tok vs 47-86k for others |
| Static docs (Sphinx, ReadTheDocs) | trafilatura — 5k vs 14-27k |
| API reference docs | trafilatura or webclaw — both 28k, webclaw 3x faster |
| Pricing / marketing page (SSR) | trafilatura — 418 tok vs 980-2400 |
| Quick lookup, speed matters | webclaw — 35-850ms, fastest of all tools |
| Full site crawl | trafilatura --crawl or --sitemap |
| GitHub repo page | playwright — webclaw thin (1.8k), playwright complete (7.9k) |
| React / Vue / Notion SPA | webclaw — got 13k on Notion vs playwright 6.1k |
| JS docs SPA, bot-protected | webclaw or jina — playwright may timeout at 30s |
| YouTube videos / channel | apify `streamers/youtube-scraper` — structured data, no bot issues |
| YouTube comments / transcripts | apify `streamers/youtube-comments-scraper` / `pintostudio/youtube-transcript-scraper` |
| YouTube page (quick, no apify) | jina — 17k tok, only generic tool that works |
| Instagram posts / profile / reels | apify `apify/instagram-scraper` or specific actor |
| TikTok videos / profile / comments | apify `clockworks/tiktok-scraper` or specific actor |
| Facebook posts / pages / groups | apify `apify/facebook-posts-scraper` or specific actor |
| LinkedIn profile / jobs / posts | apify `dev_fusion/linkedin-profile-scraper` or specific actor |
| X / Twitter tweets | apify `apidojo/tweet-scraper` |
| Reddit posts / comments | apify `trudax/reddit-scraper-lite` |
| Google Maps / Places / reviews | apify `compass/google-maps-reviews-scraper` |
| Amazon products | apify `junglee/amazon-crawler` |
| Airbnb / TripAdvisor | apify specific actors |
| Credits budget, clean output | tavily — 500-2000ms, 1k credits/month free |
| Auth-gated / login-gated | browser-harness — real Chrome, real cookies |
| Multi-step: click → wait → extract | browser-harness |
| Site blocks headless Chromium | browser-harness — real Chrome bypasses detection |
| PDF / DOCX / PPTX | docling |
| Scanned PDF (image-based) | docling --ocr |
| Structured JSON from doc | docling --to json |
| Web search (no URL, snippets ok) | searxng — free, local Docker |
| Web search (need full content) | jina search (s.jina.ai) |
| Web search (fallback) | firecrawl search |
| Batch HTML files | trafilatura --input-dir |
| Convert saved HTML → markdown | markdownify file.html |
| All local tools failed | firecrawl (credits, last resort) |

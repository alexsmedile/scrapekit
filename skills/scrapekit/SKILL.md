---
name: scrapekit
version: 1.0.0
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

**Default rule: local free tools first. External APIs only when local tools fail.**

## Routing

```
No URL yet (need to search)?
  └─ searxng (local Docker, free)  →  jina search (s.jina.ai)  →  firecrawl search

Have a URL:
  PDF / DOCX / PPTX / structured doc  →  docling
  Login-gated / needs real cookies     →  browser-harness
  Social media / e-commerce / maps     →  apify (platform actor — generic scrapers blocked)
  YouTube                              →  apify youtube-scraper  →  jina (17k tok, only generic option)
  gumroad.com                          →  jina directly (trafilatura errors, webclaw bot-blocked)
  Article / Wikipedia / static docs    →  trafilatura (3-5x fewer tokens than others)
  Quick lookup / SPA / React / Notion  →  webclaw (fastest: 35-850ms)
  GitHub repo                          →  playwright (webclaw thin on GitHub)
  All above failed / JS SPA stuck      →  jina  →  tavily (1k credits/month)  →  firecrawl (last resort)
```

**Failure signal:** < 200 tokens on a page that should have content → escalate.

## Tool tiers

| Tier | Tools |
|---|---|
| Local free | webclaw, webfetch, trafilatura, playwright+markdownify, crawl4ai, docling, searxng, browser-harness |
| External free tier | jina (10M tokens/signup), tavily (1k/month), apify (generous per actor) |
| Credits last resort | firecrawl |

**Credit awareness:** alert the user when credits are low or exhausted — jina, tavily, apify, and firecrawl all have limits. Check API error responses for quota signals and report them explicitly rather than failing silently.

## Escalation chains

```
article / docs / Wikipedia:   trafilatura → webclaw → jina → tavily → firecrawl
GitHub repo:                  playwright → jina → tavily → firecrawl
SPA / React / Notion:         webclaw → playwright → jina → firecrawl
YouTube / bot wall:           apify (streamers/youtube-scraper) → jina → firecrawl
social media:                 apify (platform actor) — always
e-commerce / Amazon:          apify (junglee/amazon-crawler)
quick / speed first:          webclaw → webfetch
login-gated:                  browser-harness
doc/PDF/DOCX:                 docling
search (no URL):              searxng → jina search → firecrawl search
```

## Quick reference — best tool by content type

| Content | Tool | Why |
|---|---|---|
| Wikipedia / long article | trafilatura | 24k tok vs 47-86k for others |
| Static docs, blogs | trafilatura | 3-5x token efficiency |
| Pricing / marketing (SSR) | trafilatura | 418 tok vs 980-2400 |
| Quick lookup / SPA | webclaw | 35-850ms, fastest overall |
| Notion / React SPA | webclaw | 13k on Notion vs playwright 6.1k |
| GitHub repo | playwright | webclaw thin (1.8k), playwright complete (7.9k) |
| YouTube | apify `streamers/youtube-scraper` | structured, no bot issues |
| YouTube (no apify) | jina | 17k tok, only generic tool that works |
| Instagram / TikTok / Facebook / LinkedIn / X | apify (platform actor) | — |
| Reddit / Google Maps / Amazon | apify (platform actor) | — |
| Gumroad product pages | jina | trafilatura errors, webclaw bot-blocked |
| Credits budget, clean output | tavily | 500-2000ms, consistent |
| Login-gated / bot-blocks headless | browser-harness | real Chrome session |
| PDF / DOCX / PPTX | docling | — |
| Scanned PDF | docling --ocr | — |
| Web search | searxng | local Docker, free |

## Output rules

- Always write to `.scrapekit/` — never read raw output into context
- `head -80 file.md` or `grep "keyword" file.md` — never cat entire file
- Always quote URLs in shell
- Add `.scrapekit/` to `.gitignore`

```bash
mkdir -p .scrapekit
```

## Setup / onboarding

First time using scrapekit, or a tool is failing unexpectedly? Run the health check:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh"
```

This checks every tool for binary presence, Python imports, and API keys, then prints exactly what's missing and how to fix it. Results are saved to `.scrapekit/setup.json` so subsequent runs skip the check.

```bash
# Force re-check even if already run
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh" --recheck
```

When the user says "setup scrapekit", "check my tools", or "onboard", run this script and report the output.

## Compare tool

Run all tools against a URL, see tokens/timing/cost side-by-side:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/compare.sh" "https://example.com"
```

## References

Detailed usage, commands, and install instructions:

- `references/webclaw.md` — fastest local tool
- `references/trafilatura.md` — best token efficiency on SSR
- `references/jina.md` — free tier, JS rendering, YouTube
- `references/playwright.md` — full browser, SPA fallback
- `references/browser-harness.md` — real Chrome, real session
- `references/apify.md` — social/e-commerce actors + full catalog
- `references/tavily.md` — 1k credits/month extraction
- `references/firecrawl.md` — credits last resort
- `references/searxng.md` — local Docker web search
- `references/docling.md` — PDF/DOCX/PPTX
- `references/crawl4ai.md` — async Python crawler (underperforms in practice)
- `references/benchmark.md` — 10-site benchmark results

---
name: scrapekit
version: 1.5.5
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
  - Bash(gallery-dl*)
  - Bash(yt-dlp*)
  - Bash(ffmpeg*)
  - Bash(ffprobe*)
---

# scrapekit — routing guide

**Default rule: harness native or local free tools first. External APIs only when local tools fail.**

## 1. Harness Native Tools Baseline

| Harness | Native Fetch Tool | Native Search Tool | Native Browser Integration |
|:---|:---|:---|:---|
| **Claude Code** | `WebFetch` | `WebSearch` | `claude --chrome`, Playwright MCP |
| **Antigravity / Gemini** | `read_url_content`, `read_browser_page` | `search_web` | Native `/browser`, CDP bridge |
| **OpenClaw** | `web_fetch`, `fetch_url` | `web_search` | `webclaw` browser runner |
| **Hermes** | `web_scrape`, curl | `web_search` | `browser_tool` |
| **Codex** | CLI curl / python | MCP search | Sandboxed Playwright |
| **Cursor** | `@docs`, `@web` | `@web` | Built-in web search |

---

## 2. Routing

```
No URL yet (need to search)?
  └─ Harness Search (WebSearch / search_web)  →  searxng (local Docker)  →  jina search (s.jina.ai)  →  firecrawl search

Have a URL:
  PDF / DOCX / PPTX / structured doc  →  docling
  Instagram post / reel / gallery     →  gallery-dl / yt-dlp → diagnose → conditional media fallbacks
  Login-gated / needs real cookies     →  browser-harness
  Other social / e-commerce / maps     →  apify (platform actor — generic scrapers blocked)
  YouTube media / transcript            →  yt-dlp / native captions → independent captions or local ASR
  YouTube page / channel metadata       →  platform actor / page reader; not proof of transcript
  gumroad.com                          →  jina directly (trafilatura errors, webclaw bot-blocked)
  Article / Wikipedia / static docs    →  Harness Native (WebFetch)  →  trafilatura (3-5x fewer tokens)
  Medium / paywalled Medium domain     →  Freedium via WebFetch  →  freedium-mirror.cfd  →  generic paywall bypass
  Paywalled article (non-Medium)       →  12ft.io via WebFetch  →  archive.today (playwright)  →  removepaywalls.com (playwright)
  Quick lookup / SPA / React / Notion  →  curl https://r.jina.ai/<url>  →  webclaw (fast: 35-850ms)
  GitHub repo                          →  playwright (webclaw thin on GitHub)
  All above failed / JS SPA stuck      →  jina  →  tavily (1k credits/month)  →  firecrawl (last resort)

Multi-source synthesis / research across scraped pages:
  └─ notebooklm-cli / nlm (synthesize answers from long sources)
```

**Failure signal:** unexpectedly thin content requires inspection before escalation.
HTTP 403/login redirects, challenges, HTTP 429, TLS errors and timeouts are distinct.
On rate limits (including `RequestBlocked`/`IpBlocked`) or challenges, stop automatic
network fallbacks; do not rotate tools/accounts/proxies to repeat the blocked request.

For video/audio requests, read [media and transcript recovery](references/media-transcripts.md).
Download, platform captions, local ASR and visual OCR are separate evidence routes.
Select a fallback by failure type and prerequisites, not a fixed retry-all chain.
Keep raw evidence, hashes, source identity, language, coverage and attempt history;
report fixture-tested, live-verified and dependency-missing routes separately.

### Instagram acquisition and diagnosis

- Use the owner's selected existing browser/profile for the first bounded CLI
  attempt when that session is available and its use is authorized. Pass
  `--cookies-from-browser <browser>` explicitly; a visible browser login does not
  authenticate a downloader. Ignore global config (`gallery-dl --config-ignore`,
  `yt-dlp --ignore-config`) to prevent inherited paths and hooks from running.
- For ordered or mixed galleries, inspect `gallery-dl --dump-json` privately to
  determine page membership, then download with an archive and verify readable
  originals in page order. JSON mode can exit 0 while containing an error row;
  success requires actual media rows and complete expected membership.
- A login redirect does not establish that browser-cookie access failed. A large
  extracted-cookie count can come from a logged-out profile: distinguish cookie
  access/decryption, presence/expiry of the site's login cookie (Instagram uses
  `sessionid`), and an outdated extractor before browser fallback. Inspect only
  names/expiry/status, never credential values. Select the owner's exact profile
  (`gallery-dl --cookies-from-browser 'chrome/.instagram.com:<profile>'`;
  `yt-dlp --cookies-from-browser 'chrome:<profile>'`). gallery-dl's domain filter
  is not yt-dlp syntax. Request normal sign-in only when needed; do not export
  cookies or silently switch accounts. Check the installed version against an
  official release; do not pin a stale version as a permanent universal minimum.
  Preserve separate private attempt logs and verify media after the repair.
- A selected session can route Instagram through a different API endpoint.
  If the exact source is already verified publicly readable and the authenticated
  attempt fails with JSON/API parsing or a login redirect, allow one config-free
  attempt without cookies before requiring sign-in. Preserve both results; this
  does not prove cookies expired. Do not use this retry after a rate limit,
  challenge, cookie-decryption, network or TLS failure.
- A connection timeout does
  not establish a cookie failure: check DNS and a bounded HTTPS control request.
  For certificate errors, check the active Python executable and trusted CA
  configuration; use a verified system/configured CA bundle, never disable TLS
  verification. A browser loading screen is not inspected post content.
- Keep cookies, signed URLs and raw logs private. Never print cookie values or
  unfiltered response headers. Media can live in an explicitly configured external
  corpus; sanitize public metadata before creating Source/study artifacts.
- For carousel video inspection, keep video bytes only as temporary acquisition
  inputs; retain sampled frames, source URL, original hash and duration. Verify
  saved evidence before removing temporary video files. Allocate samples adaptively
  by clip duration across all video pages together, with at most 30 extracted
  frames for the entire carousel inspection. Prefer an available source-workflow
  sampler; reserve page coverage before distributing remaining slots to longer
  clips. Never apply the ceiling independently per page or accumulate runs above
  it. Record actual frame timestamps and positive durations; sampled frames do
  not establish continuous animation, audio or all displayed text.
- After resolving access, resume authorized pending URLs from their cached state.
  Preserve failures as history; verify downloads before marking the queue complete
  and distinguish captured media from completed study or approved library writes.

## 3. Tool tiers

| Tier | Tools |
|---|---|
| Harness native & local free | native WebFetch/read_url_content, webclaw, trafilatura, playwright+markdownify, crawl4ai, docling, searxng, browser-harness |
| Zero-config proxy & free API | jina proxy (r.jina.ai), jina API (10M tokens/signup), tavily (1k/month), apify (generous per actor) |
| Multi-source research synthesis | notebooklm-cli / nlm query |
| Credits last resort | firecrawl |

**Credit awareness:** alert the user when credits are low or exhausted — jina, tavily, apify, and firecrawl all have limits. Check API error responses for quota signals and report them explicitly rather than failing silently.

## Escalation chains

```
article / docs / Wikipedia:   trafilatura → webclaw → jina → tavily → firecrawl
Medium / paywalled Medium:    Freedium (WebFetch) → freedium-mirror.cfd → generic paywall bypass
paywalled article (non-Medium): 12ft.io (WebFetch) → archive.today (playwright) → removepaywalls.com (playwright)
GitHub repo:                  playwright → jina → tavily → firecrawl
SPA / React / Notion:         webclaw → playwright → jina → firecrawl
YouTube media / captions:     yt-dlp / native captions → youtube-transcript-api / existing local ASR
YouTube page metadata:        platform actor / page reader; inspect actual returned fields
Instagram:                   gallery-dl / yt-dlp → diagnose → conditional public retry / independent extractor / browser
other social media:          apify (platform actor)
e-commerce / Amazon:          apify (junglee/amazon-crawler)
quick / speed first:          webclaw → webfetch
login-gated:                  browser-harness
doc/PDF/DOCX:                 docling
search (no URL):              searxng → jina search → firecrawl search
```

## Quick reference — best tool by content type

| Content | Tool | Why |
|---|---|---|
| Medium / paywalled Medium domain | Freedium via WebFetch → freedium-mirror.cfd → remove-paywall fallback | free mirror, no auth needed |
| Paywalled article (NYT, WSJ, etc.) | 12ft.io (WebFetch) → archive.today (playwright) | see remove-paywall.md |
| Wikipedia / long article | trafilatura | 24k tok vs 47-86k for others |
| Static docs, blogs | trafilatura | 3-5x token efficiency |
| Pricing / marketing (SSR) | trafilatura | 418 tok vs 980-2400 |
| Quick lookup / SPA | webclaw | 35-850ms, fastest overall |
| Notion / React SPA | webclaw | 13k on Notion vs playwright 6.1k |
| GitHub repo | playwright | webclaw thin (1.8k), playwright complete (7.9k) |
| YouTube video / transcript | yt-dlp / platform captions; youtube-transcript-api or configured local ASR | validate actual media or nonempty timed cues |
| YouTube page / channel metadata | platform actor or jina | page text/description is not a spoken transcript; no guaranteed bot immunity |
| Instagram posts / reels / mixed galleries | gallery-dl / yt-dlp; selected browser session when available | diagnose before conditional public retry; see media recovery protocol |
| TikTok / Facebook / LinkedIn / X | apify (platform actor) | — |
| Reddit / Google Maps / Amazon | apify (platform actor) | — |
| Gumroad product pages | jina | trafilatura errors, webclaw bot-blocked |
| Credits budget, clean output | tavily | 500-2000ms, consistent |
| Login-gated / bot-blocks headless | browser-harness | real Chrome session |
| PDF / DOCX / PPTX | docling | — |
| Scanned PDF | docling --ocr | — |
| Web search | searxng | local Docker, free |

## Output rules

- Write to the explicitly configured external capture corpus when present; otherwise `.scrapekit/`. Keep raw logs and signed URLs private; inspect bounded, sanitized extracts rather than dumping raw output into context.
- `head -80 file.md` or `grep "keyword" file.md` — never cat entire file
- Always quote URLs in shell
- Add `.scrapekit/` to `.gitignore`

```bash
mkdir -p .scrapekit
```

## Setup / troubleshooting

If a tool fails unexpectedly or a subagent reports missing permissions, run the health check in quiet mode:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh" --quiet
```

Output is either `OK` (all tools ready) or `ISSUES: n` followed by a fix list. Only run this when something breaks — not proactively on every session.

When the user says "setup scrapekit", "check my tools", or "onboard", run the script and report the output. For full install instructions and permissions setup, read `references/setup.md`.

## Smart review

When the user says "smart review", "review failures", "what went wrong", or "review my scraping session", read `references/smart-review.md` and follow the process there.

## Compare tool

Run all tools against a URL, see tokens/timing/cost side-by-side:

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/compare.sh" "https://example.com"
```

## References

- [Media and transcript recovery](references/media-transcripts.md) — failure routing, independent fallbacks, provenance and qualification

- `references/setup.md` — install instructions, subagent permissions, API keys
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
- `references/medium.md` — Medium paywall bypass (Freedium, archive.today, service priority)
- `references/remove-paywall.md` — generic paywall bypass for any publisher (12ft.io, archive.today, RemovePaywalls, publisher notes)
- `references/smart-review.md` — failure analysis: reads session.log + chat history, produces structured report, files GitHub issue or saves locally

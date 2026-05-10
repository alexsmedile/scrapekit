# scrapekit

![License](https://img.shields.io/badge/license-MIT-blue)
![Version](https://img.shields.io/badge/version-1.2.0-green)
![Claude Code](https://img.shields.io/badge/Claude%20Code-skill%20%2B%20plugin-blueviolet)

The web scraping router for Claude Code. Picks the right tool automatically — trafilatura for articles, webclaw for SPAs, apify for social media — based on content type, not guesswork. **3–5× fewer tokens** than one-tool approaches. Local tools always run first; API credits are a last resort.

Includes three subagents that handle scraping tasks without triggering permission prompts.

---

## Performance

Real benchmark across 10 sites — same content, different tools:

| Tool | Tokens (Wikipedia) | Tokens (pricing page) | Speed |
|---|---|---|---|
| trafilatura | 24k | 418 | ~1s |
| webclaw | — | 980 | 35–850ms |
| playwright | 47k | 2,400 | ~3s |
| jina | 86k | — | ~2s |

trafilatura uses 3–5× fewer tokens than alternatives on SSR content. For SPAs, webclaw is fastest. The router picks automatically.

---

## What it routes

| Content type | Tool | Why |
|---|---|---|
| Articles, Wikipedia, static docs | trafilatura | 3–5× token efficiency |
| SPAs, React, Notion, quick lookups | webclaw | 35–850ms, fastest overall |
| GitHub repos | playwright | webclaw too thin (1.8k vs 7.9k tokens) |
| PDFs, DOCX, PPTX | docling | structured extraction |
| Scanned PDFs | docling --ocr | |
| YouTube | apify `streamers/youtube-scraper` | structured, no bot issues |
| Instagram, TikTok, LinkedIn, Twitter/X, Facebook | apify platform actor | generic tools bot-blocked |
| Reddit, Google Maps, Amazon | apify platform actor | |
| Gumroad product pages | jina | trafilatura errors, webclaw bot-blocked |
| Medium / Medium-hosted domains | Freedium → freedium-mirror.cfd → remove-paywall fallback | free mirror, no auth needed |
| Paywalled articles (NYT, WSJ, etc.) | 12ft.io → archive.today → RemovePaywalls | see remove-paywall.md |
| Login-gated / real session needed | browser-harness | real Chrome |
| Web search (no URL) | searxng → jina → firecrawl | local Docker first |
| Everything else failed | jina → tavily → firecrawl | escalation order |

**Failure signal:** < 200 tokens on a page that should have content → escalate automatically.

---

## Agents

Three specialized subagents are included. Install via plugin to get them automatically — each has pre-approved tool permissions so scraping tasks run without interrupting you for confirmations.

| Agent | Purpose | Key tools |
|---|---|---|
| `web-researcher` | General web fetch and scraping | trafilatura, webclaw, jina, playwright |
| `doc-fetcher` | PDF, DOCX, PPTX extraction | docling |
| `social-scraper` | Social media and e-commerce | apify platform actors |

Delegate a research task:

```
Use the web-researcher agent to fetch https://example.com and summarize it
Use doc-fetcher to extract text from this PDF: /path/to/file.pdf
Use social-scraper to get the last 10 posts from this Instagram profile
```

---

## Quick start

**1. Check your tools are ready:**

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh"
```

This verifies all 10 tools, checks API keys, and prints exactly what's missing with the fix command. Results are saved to `.scrapekit/setup.json` — subsequent runs skip the check. Run with `--recheck` to force a new scan.

Or just ask Claude: `"setup scrapekit"` / `"check my scrapekit tools"`.

**2. Use it:**

```
Fetch https://example.com and extract the main content
Scrape the Instagram profile at this URL
Search the web for recent news about X
Parse this PDF: /path/to/file.pdf
```

scrapekit triggers automatically on: `fetch`, `scrape`, `get the page`, `extract from`, `convert to markdown`, `crawl`, `search the web`, `parse PDF`, `render page`.

**3. Compare tools (optional):**

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/compare.sh" "https://example.com"
```

Runs all tools against a URL and opens a tabbed HTML viewer with tokens, timing, and cost side-by-side.

---

## Install

### Claude Code plugin (skill + agents)

```bash
/plugin marketplace add alexsmedile/scrapekit
/plugin install scrapekit@scrapekit
```

Installs the skill and all three agents automatically.

> **Permissions required for subagents**
> The three agents (web-researcher, doc-fetcher, social-scraper) need pre-approved tool permissions to run without interrupting you. Add this block to your settings file after installing:
>
> ```json
> "permissions": {
>   "allow": [
>     "WebFetch(*)",
>     "Bash(trafilatura*)", "Bash(webclaw*)", "Bash(playwright*)",
>     "Bash(markdownify*)", "Bash(python3*)", "Bash(firecrawl*)",
>     "Bash(curl*)", "Bash(jq*)", "Bash(grep*)", "Bash(head*)",
>     "Bash(mkdir*)", "Bash(browser-harness*)", "Bash(apify*)",
>     "Bash(docling*)", "Bash(docker*)"
>   ]
> }
> ```
>
> **Where to add it depends on how you installed:**
> - Plugin or global skill → `~/.claude/settings.json` (must be global — the agents are active across all projects)
> - Project-scoped skill (`--project` or `.claude/skills/`) → `.claude/settings.json` in that project is fine
>
> If a `permissions` key already exists, merge the `allow` array.

### npx skills

```bash
# Global
npx skills add alexsmedile/scrapekit

# Project-scoped
npx skills add alexsmedile/scrapekit --project
```

### Codex

```bash
codex plugin marketplace add alexsmedile/scrapekit
# then: codex /plugins → browse and install
```

### Manual

```bash
# Plugin (skill + agents)
git clone https://github.com/alexsmedile/scrapekit
claude --plugin-dir ./scrapekit

# Skill only (no agents)
git clone https://github.com/alexsmedile/scrapekit ~/.claude/skills/scrapekit
```

---

## How it works

**Default rule: local free tools first. External APIs only when local tools fail.**

Tool tiers:

| Tier | Tools |
|---|---|
| Local free | webclaw, trafilatura, playwright, docling, searxng, browser-harness |
| External free tier | jina (10M tokens/signup), tavily (1k req/month), apify (generous per actor) |
| Credits — last resort | firecrawl |

Escalation chains:

```
article / docs:       trafilatura → webclaw → jina → tavily → firecrawl
GitHub repo:          playwright → jina → tavily → firecrawl
SPA / React / Notion: webclaw → playwright → jina → firecrawl
YouTube:              apify → jina → firecrawl
social / e-commerce:  apify (always — generic tools blocked)
login-gated:          browser-harness
doc / PDF:            docling
search (no URL):      searxng → jina search → firecrawl search
```

All output writes to `.scrapekit/` — never read raw into context. Add `.scrapekit/` to `.gitignore`.

**Credit awareness:** jina, tavily, apify, and firecrawl all have usage limits. scrapekit alerts you when a call returns a quota error rather than failing silently.

---

## Who it's for

- Developers using Claude Code to automate research, data extraction, or content pipelines
- Anyone delegating web fetch tasks to Claude subagents
- Projects that scrape a mix of content types (articles, social, PDFs) and need the right tool per source

## Who it's not for

- One-off scraping with a tool you already know — just use that tool directly
- Scraping at scale without API keys — the free tiers have limits; scrapekit respects them

---

## License

MIT

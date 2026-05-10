# scrapekit TODO

## ~~First-run onboarding: tool setup + API keys~~ ✓ Done 2026-05-10

When scrapekit is invoked for the first time (or a tool fails due to missing auth), it should detect which tools are not installed or not authenticated and walk the user through setup interactively.

**Tools requiring setup:**

| Tool | What's needed |
|---|---|
| trafilatura | `pip install trafilatura` (usually pre-installed) |
| webclaw | Check if available via `which webclaw`; install via npm/brew if missing |
| jina | No key needed for basic use; optional `JINA_API_KEY` for higher rate limits |
| apify | `APIFY_TOKEN` env var — get from apify.com/sign-up |
| tavily | `TAVILY_API_KEY` env var — get from tavily.com |
| firecrawl | `FIRECRAWL_API_KEY` env var — get from firecrawl.dev |
| searxng | Local Docker instance — `docker run -d -p 8080:8080 searxng/searxng` |
| docling | `pip install docling` |
| playwright | `pip install playwright && playwright install chromium` |
| browser-harness | Separate install — check `references/browser-harness.md` |

**Onboarding flow to build:**
1. On first invoke, run a health-check script that tests each tool
2. Report which tools are ready, which are missing, which need API keys
3. For missing keys: show the signup URL and the exact env var name to set
4. For missing binaries: show the install command
5. Save a `.scrapekit/setup.json` in the project dir marking which tools were verified
6. Skip the health check on subsequent runs unless `--recheck` flag is passed

**Why:** Users installing scrapekit for the first time have no way to know which tools are pre-installed vs need setup. Silent failures (< 200 tokens returned) are confusing. A first-run wizard removes all guesswork.

## ~~Upgrade to plugin repo~~ ✓ Done 2026-05-10

- [x] Add `.claude-plugin/plugin.json` + `marketplace.json`
- [x] Add `.codex-plugin/plugin.json` with interface block
- [x] Add `.agents/plugins/marketplace.json`
- [x] Move `SKILL.md` into `skills/scrapekit/SKILL.md` (bundle structure)
- [x] Add `agents/web-researcher.md` — general web fetch + scraping
- [x] Add `agents/doc-fetcher.md` — PDF/DOCX/PPTX via docling
- [x] Add `agents/social-scraper.md` — social/e-commerce via apify
- [x] Integrate Gumroad feedback into web-researcher routing
- [x] Remove manual `~/.claude/agents/web-researcher.md` (now distributed by plugin)
- [x] Update README with agents table and all install methods
- [x] Update `.gitignore` to include `.scrapekit/`

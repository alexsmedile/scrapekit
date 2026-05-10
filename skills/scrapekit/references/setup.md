# scrapekit — setup & onboarding

## Health check

Run to verify all tools and API keys:

```bash
# Verbose (human-readable)
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh"

# Quiet (machine-readable — use this when Claude runs the check)
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh" --quiet

# Force re-check even if already run
bash "${CLAUDE_SKILL_DIR}/scripts/setup.sh" --recheck
```

Quiet output: `OK` if everything is ready, or `ISSUES: n` followed by a fix list. Results are cached to `.scrapekit/setup.json` — subsequent runs skip the check unless `--recheck` is passed.

## Subagent permissions

The three agents (web-researcher, doc-fetcher, social-scraper) need pre-approved tool permissions or they will fail when spawned as subagents.

Add this block to the correct settings file:

```json
"permissions": {
  "allow": [
    "WebFetch(*)",
    "Bash(trafilatura*)",
    "Bash(webclaw*)",
    "Bash(playwright*)",
    "Bash(markdownify*)",
    "Bash(python3*)",
    "Bash(firecrawl*)",
    "Bash(curl*)",
    "Bash(jq*)",
    "Bash(grep*)",
    "Bash(head*)",
    "Bash(mkdir*)",
    "Bash(browser-harness*)",
    "Bash(apify*)",
    "Bash(docling*)",
    "Bash(docker*)"
  ]
}
```

**Where to add it:**
- Plugin or global skill (`~/.claude/skills/`) → `~/.claude/settings.json` — must be global because the agents are active in every project
- Project-scoped skill (`.claude/skills/` in a repo) → `.claude/settings.json` in that project is sufficient

If a `permissions` key already exists, merge the `allow` array rather than replacing it.

## API keys

| Tool | Env var | Where to get it |
|---|---|---|
| jina | `JINA_API_KEY` | https://jina.ai — free 10M tokens |
| tavily | `TAVILY_API_KEY` | https://app.tavily.com — free 1k req/month |
| apify | `APIFY_TOKEN` | https://apify.com/sign-up — generous free tier |
| firecrawl | `FIRECRAWL_API_KEY` | https://firecrawl.dev |

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export JINA_API_KEY=your_key
export TAVILY_API_KEY=your_key
export APIFY_TOKEN=your_token
export FIRECRAWL_API_KEY=your_key
```

## Tool install commands

```bash
# trafilatura
pip install trafilatura

# webclaw
cargo install --git https://github.com/0xMassi/webclaw.git webclaw-cli

# playwright
pip install playwright && playwright install chromium

# docling
pip install docling

# apify CLI
npm install -g apify-cli

# firecrawl
npm install -g @mendable/firecrawl-js
# or: pip install firecrawl-py

# tavily
pip install tavily-python

# searxng (local Docker)
docker run -d -p 8080:8080 searxng/searxng
```

browser-harness requires a real Chrome session — see `references/browser-harness.md`.

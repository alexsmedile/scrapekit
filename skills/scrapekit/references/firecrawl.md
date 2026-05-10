# firecrawl — credits, last resort

Check credits first: `firecrawl credit-usage`

Self-hosted not worth it — requires Redis + Postgres + Playwright microservice. Use browser-harness for interactive login, playwright for local JS rendering. Firecrawl cloud credits for the rare hard case.

```bash
firecrawl credit-usage

# Search (no URL)
firecrawl search "query" --limit 5 -o .scrapekit/search.json --json
firecrawl search "query" --scrape -o .scrapekit/search.json --json

# Scrape
firecrawl scrape "<url>" -o .scrapekit/page.md
firecrawl scrape "<url>" --only-main-content -o .scrapekit/page.md
firecrawl scrape "<url>" --wait-for 3000 -o .scrapekit/page.md

# Structured extraction
firecrawl scrape "<url>" --format json --schema '{"price":"string"}' -o .scrapekit/data.json

# Map site URLs
firecrawl map "<url>" --limit 200 --json -o .scrapekit/urls.json
```

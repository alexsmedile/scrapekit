# jina reader — free tier, JS rendering

Only tool with real YouTube content (17k tok). Free: 20 RPM (no key), 500 RPM (free key). 10M tokens on signup.

```bash
# Fetch
curl -s "https://r.jina.ai/https://example.com" \
  -H "Authorization: Bearer $JINA_API_KEY" \
  -o .scrapekit/page.md

# Search with full content
curl -s "https://s.jina.ai/?q=YOUR+QUERY" \
  -H "Authorization: Bearer $JINA_API_KEY" \
  -H "Accept: application/json" \
  -o .scrapekit/search.json

# Options (via headers)
-H "X-Target-Selector: main article"   # target CSS selector
-H "X-With-Images-Summary: true"       # caption images
```

Get key: https://jina.ai

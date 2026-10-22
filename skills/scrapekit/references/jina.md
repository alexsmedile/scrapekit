# jina reader — free tier, JS rendering

A page-reader alternative for YouTube page text and metadata. A historical
benchmark returned 17k tokens; volume does not establish a complete transcript.
Descriptions, comments and generated summaries are not spoken-content evidence.
For captions/media use [media and transcript recovery](media-transcripts.md).
Check current provider quotas before relying on historical free-tier limits.

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

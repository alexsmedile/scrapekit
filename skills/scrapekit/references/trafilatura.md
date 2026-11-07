# trafilatura — free, URL or local HTML

Use this when: extracting clean text from static HTML or a bounded direct HTML fetch.

Best token efficiency on SSR/static pages (3-5x cleaner than others). Hard fails on SPAs.

## Google Docs and local HTML fallback

Google Docs `/mobilebasic` may contain the complete document even when a native
web reader returns an internal error. Fetch the supplied URL with a bounded
timeout, preserve the HTML privately, and inspect status/final destination for
login or denial before treating it as document content. Rate limits and challenges
still stop automatic network fallback.

Use an installed extractor on the saved HTML. Check imports in the actual Python
interpreter before relying on `bs4`; if unavailable, use the standard library
`html.parser.HTMLParser` with explicit suppression of `script`, `style` and
`noscript` content, preferably scoped to the observed document-content container.
A bare `handle_data` printer includes JavaScript and CSS and can exhaust the
output budget before reaching the document. Preserve paragraph boundaries and
reference link targets, save cleaned text, then print a bounded excerpt. Verify
the title and substantive body; HTTP 200 and nonempty HTML alone are insufficient.

## Commands

```bash
trafilatura -u "https://example.com" --output-format markdown
trafilatura -u "https://example.com" --output-format json
trafilatura -f --output-format markdown < page.html
trafilatura --input-file urls.txt --output-dir .scrapekit/ --output-format markdown
trafilatura --crawl "https://example.com" --output-dir .scrapekit/ --output-format markdown
trafilatura --sitemap "https://example.com" --output-dir .scrapekit/ --output-format markdown
trafilatura -u "https://example.com" --output-format markdown --formatting --links --with-metadata
trafilatura -u "https://example.com" --output-format markdown --precision
trafilatura -u "https://example.com" --output-format markdown --recall
```

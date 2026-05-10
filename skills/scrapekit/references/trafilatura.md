# trafilatura — free, URL or local HTML

Best token efficiency on SSR/static pages (3-5x cleaner than others). Hard fails on SPAs.

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

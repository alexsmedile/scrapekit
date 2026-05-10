# playwright + markdownify — full browser rendering

Use when trafilatura returns empty / `<div id="root"></div>`. Slower (1.3–4.5s min), heavy, detectable by bots.

```bash
python3 - <<'EOF'
from playwright.sync_api import sync_playwright
from markdownify import markdownify

url = "https://example.com"
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    md = markdownify(page.content())
    browser.close()

with open(".scrapekit/page.md", "w") as f:
    f.write(md)
EOF
head -80 .scrapekit/page.md
```

**Wait for element / extract section:**
```bash
page.wait_for_selector("main", timeout=10000)
md = markdownify(page.inner_html("main"))
```

**One-time setup:** `playwright install chromium`

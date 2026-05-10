# browser-harness — real Chrome, real session

Connects to user's running Chrome via CDP. Real cookies, real auth. Use for login-gated pages, bot-blocked sites, multi-step interactions.

Full docs: `~/code/tools/browser-harness/SKILL.md`

**Extract page:**
```bash
browser-harness -c '
new_tab("https://example.com/dashboard")
wait_for_load()
from markdownify import markdownify
md = markdownify(js("document.documentElement.outerHTML"))
open(".scrapekit/page.md", "w").write(md)
print(f"Extracted {len(md)} chars")
'
```

**Screenshot before extracting:**
```bash
browser-harness -c '
new_tab("https://example.com")
wait_for_load()
capture_screenshot()
md = markdownify(js("document.body.innerHTML"))
open(".scrapekit/page.md", "w").write(md)
'
```

**Bulk HTTP (no browser overhead):**
```bash
browser-harness -c '
from concurrent.futures import ThreadPoolExecutor
urls = ["https://example.com/1", "https://example.com/2"]
results = list(ThreadPoolExecutor().map(http_get, urls))
'
```

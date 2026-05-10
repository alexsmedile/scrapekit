# crawl4ai — async Python crawler

Slower and noisier than playwright+markdownify in benchmarks. Use only if you need crawl4ai's LLM-extraction hooks specifically.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as c:
        r = await c.arun("https://example.com")
        open(".scrapekit/page.md", "w").write(r.markdown)

asyncio.run(main())
```

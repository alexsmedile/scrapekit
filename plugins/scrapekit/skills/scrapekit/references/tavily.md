# tavily — 1k free credits/month

Clean LLM-ready extraction. 500–2000ms. Fails on YouTube and auth-gated pages.
Requires `TAVILY_API_KEY` env var. Monitor at: https://app.tavily.com

```python
import os
from tavily import TavilyClient
client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Extract page content
r = client.extract("https://example.com")
content = r["results"][0]["raw_content"]
open(".scrapekit/page.md", "w").write(content)

# Search
results = client.search("query", max_results=5)
```

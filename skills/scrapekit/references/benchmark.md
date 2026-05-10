# Benchmark — 10 real sites, 8 tools

Tokens = cl100k_base (same as Claude context cost).

| Site | Type | webfetch | trafilatura | jina | playwright | crawl4ai | webclaw | tavily |
|---|---|---|---|---|---|---|---|---|
| Wikipedia/LLM | Long article | 72k/384ms | **24k**/509ms | 83k/1785ms | 73k/1664ms | 86k/2150ms | 47k/**207ms** | 85k/1159ms |
| docs.firecrawl.dev | JS docs SPA | 3.2k/256ms | **0.7k**/487ms | 3.7k/921ms | 37/30548ms | 3.9k/1883ms | **1.9k/189ms** | 1.5k/527ms |
| jina.ai/reader | Marketing SPA | 12.6k/198ms | **3.1k**/423ms | 10.7k/807ms | 15.9k/2346ms | 29.8k/2202ms | 6.2k/**157ms** | 8k/711ms |
| obsidian.md/pricing | Pricing SSR | 1.8k/143ms | **418**/368ms | 2.4k/1058ms | 1.8k/1091ms | 2.2k/1994ms | 980/**104ms** | 2.4k/715ms |
| github.com SDK | GitHub repo | 4.4k/720ms | 158/1509ms | 8.9k/**378ms** | **7.9k**/2683ms | 9k/2043ms | 1.8k/154ms | 2.2k/1948ms |
| notion.so/product | Full SPA | 5.4k/907ms | 91/1249ms | **7.9k/377ms** | 6.1k/3802ms | 6.8k/3092ms | **13k**/1017ms | 753/545ms |
| docs.searxng.org | Static docs | 21.6k/239ms | **5.2k**/406ms | 24.6k/1978ms | 21.6k/1366ms | 26.9k/2585ms | 14.2k/**122ms** | 17.9k/857ms |
| youtube.com/watch | Bot wall | 247/1071ms | 57/1275ms | **17k/624ms** | 13.8k/4501ms | 640/2725ms | 967/965ms | 4/1194ms |
| playwright.dev/api | API reference | 62k/522ms | **28k**/746ms | 64k/1038ms | 62k/2008ms | 71k/2776ms | **28k/228ms** | 62k/1043ms |
| docs.claude.ai | Auth-gated | 1/136ms | 5/229ms | **59/207ms** | 64/438ms | 3/1121ms | 3/**35ms** | 4/1294ms |

Format: `tokens/ms`. **Bold** = best for that site on that dimension.

## Speed ranking
1. webclaw — 35–1,017ms
2. webfetch — 130–1,071ms
3. jina — 207–1,978ms
4. trafilatura — 229–1,509ms
5. tavily — 527–1,948ms
6. crawl4ai — 1,121–3,092ms
7. playwright — 438–30,548ms (30s+ on bot-blocked)

## Token efficiency (least → most)
1. trafilatura — 3-5x cleaner on SSR/static
2. webclaw — close second, better on SPAs
3. tavily — consistent quality
4. webfetch / playwright — full page chrome
5. jina — over-fetches (Wikipedia 83k, highest)
6. crawl4ai — noisiest

## Tool verdicts
- **webclaw** — fastest overall, wins on SPAs (Notion 13k), fails on YouTube
- **trafilatura** — best token efficiency on SSR/static, hard fails on SPAs
- **jina** — only tool for YouTube (17k), variable latency
- **playwright** — reliable SPA fallback but slow, 30s+ on bot-blocked
- **tavily** — solid mid-tier, fails on YouTube/auth-gated
- **crawl4ai** — underperforms, marginal vs playwright+markdownify

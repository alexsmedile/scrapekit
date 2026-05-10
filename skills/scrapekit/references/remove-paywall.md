# Remove Paywall — Generic Bypass

Generic strategies for fetching paywalled content from any publisher (NYT, WSJ, The Atlantic, Medium, Substack, etc.).

## Service Overview

| Service | Works via | URL pattern | Best for |
|---|---|---|---|
| Archive.today | playwright / browser-harness | `https://archive.today/latest/{raw_url}` | Any paywalled page; often has cached copy |
| Freedium | WebFetch, curl | `https://freedium.cfd/{encoded_url}` | Medium and Medium-hosted domains only |
| Freedium mirror | WebFetch, curl | `https://freedium-mirror.cfd/{encoded_url}` | Freedium primary down |
| RemovePaywalls | playwright / browser-harness | `https://removepaywalls.com/{raw_url}` | General paywalls; redirect page needs browser |
| ReadMedium | browser only | `https://readmedium.com/en/{encoded_url}` | Medium only; 403 programmatically |
| 12ft.io | WebFetch, curl | `https://12ft.io/proxy?q={raw_url}` | General paywalls; lightweight proxy |
| Outline.com | WebFetch | `https://outline.com/{raw_url}` | Article reader view; intermittent |

`{encoded_url}` = URL-encoded (`/` → `%2F`, `@` → `%40`)  
`{raw_url}` = original URL unmodified

## Escalation Chain (generic)

```
1. trafilatura / webclaw  →  (fails: paywalled / thin content)
2. 12ft.io via WebFetch   →  (fails: blocked or empty)
3. Outline.com via WebFetch  →  (fails: down or thin)
4. Archive.today via playwright / browser-harness  →  (captcha: try next)
5. RemovePaywalls via playwright / browser-harness  →  (fails: last resort)
6. Manual: ask user to paste article text
```

For **Medium-specific** content: start from `references/medium.md` — Freedium is more reliable than the generic chain.

## Service Details

### Archive.today
- Caches a snapshot of most public pages; often has pre-paywall copies
- URL: `https://archive.today/latest/{raw_url}` — redirects to newest snapshot
- Requires real browser (playwright or browser-harness) — WebFetch returns near-empty
- May serve captcha: use browser-harness with a real Chrome session if playwright fails
- Alternative domains (same service): `archive.ph`, `archive.is`, `archive.li`, `archive.fo`

```bash
# playwright snapshot check
playwright open "https://archive.today/latest/https://www.nytimes.com/2024/01/01/example"
```

### 12ft.io
- Lightweight proxy that strips paywall JS; works on many news sites
- WebFetch-friendly — returns article HTML directly
- URL: `https://12ft.io/proxy?q={raw_url}`
- Blocked by some publishers (NYT, WaPo detect and refuse); try archive.today if empty

```
WebFetch url: https://12ft.io/proxy?q=https://www.wsj.com/articles/example
prompt: Extract the article text and format as markdown
```

### Outline.com
- Reader-mode proxy; intermittent uptime
- URL: `https://outline.com/{raw_url}` (no encoding needed)
- WebFetch works when service is up; returns clean article HTML
- Not reliable enough to use as first attempt — use as 12ft.io fallback

### RemovePaywalls
- General-purpose bypass aggregator
- Returns a redirect/landing page — needs browser to follow
- Use playwright navigate → wait for content → extract text

### ReadMedium
- Medium-specific only
- Returns 403 on programmatic access; browser-only
- Prefer Freedium over ReadMedium in all cases

### Freedium / Freedium mirror
- Medium-specific only — see `references/medium.md` for full details

## Publisher-Specific Notes

| Publisher | Best approach |
|---|---|
| NYT / New York Times | Archive.today (large cache), 12ft.io sometimes works |
| WSJ / Wall Street Journal | Archive.today; 12ft.io often blocked |
| The Atlantic | 12ft.io → archive.today |
| Washington Post | Archive.today; 12ft.io blocked |
| Bloomberg | Archive.today; most proxies blocked |
| Medium / medium-hosted | Use `references/medium.md` (Freedium first) |
| Substack (paid posts) | Archive.today if cached; otherwise browser-harness |
| Financial Times | Archive.today; most proxies blocked |
| Wired | 12ft.io → archive.today |
| The Economist | Archive.today; most proxies blocked |

## URL Encoding

```python
from urllib.parse import quote
encoded = quote(url, safe='')
```

```bash
python3 -c "from urllib.parse import quote; print(quote('$URL', safe=''))"
```

## Common Issues

| Problem | Solution |
|---|---|
| 12ft.io returns thin/blocked page | Publisher detects proxy — try archive.today |
| Archive.today captcha | Switch to browser-harness (real Chrome session) |
| Archive.today has no snapshot | Page not cached — try 12ft.io or RemovePaywalls |
| Outline.com down | Skip to archive.today |
| All services blocked | Ask user to paste article text directly |
| < 200 tokens returned | Escalate to next service in chain |

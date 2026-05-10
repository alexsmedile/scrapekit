# Medium Paywall Bypass

Fetch paywalled Medium articles using free mirror services. Try services in order until one works.

## Service Priority

| Priority | Service | URL Pattern | WebFetch | curl | Notes |
|---|---|---|---|---|---|
| 1 | Freedium | `https://freedium.cfd/{encoded_url}` | Yes | Yes | Best option, returns full content directly |
| 1b | Freedium mirror | `https://freedium-mirror.cfd/{encoded_url}` | Yes | Yes | Fallback when primary Freedium is down |
| 2 | Archive.today | `https://archive.today/latest/{raw_url}` | No | Maybe | Often requires captcha — browser only |
| 3 | RemovePaywalls | `https://removepaywalls.com/{raw_url}` | No | No | Redirect page — needs browser rendering |
| 4 | ReadMedium | `https://readmedium.com/en/{encoded_url}` | No | No | Returns 403 programmatically |

`{encoded_url}` = URL-encoded (slashes → `%2F`, `@` → `%40`, etc.)
`{raw_url}` = original URL as-is (no encoding)

**For Claude Code: use Freedium via WebFetch. Other services require browser interaction.**

## Workflow

```
1. User provides a Medium URL
2. Try Freedium via WebFetch
3. If 4xx/5xx, bot-block, or < 200 tokens → try freedium-mirror.cfd
4. If still blocked → use playwright / browser-harness for archive.today or removepaywalls.com
5. Extract and present article content
```

## URL Encoding

```python
from urllib.parse import quote

medium_url  = "https://medium.com/@user/some-article-abc123"
encoded_url = quote(medium_url, safe='')
freedium    = f"https://freedium.cfd/{encoded_url}"
```

Or with bash:
```bash
python3 -c "from urllib.parse import quote; print(quote('$URL', safe=''))"
```

## Example

Given: `https://medium.com/@user/some-article-abc123`

```
Freedium URL:
  https://freedium.cfd/https%3A%2F%2Fmedium.com%2F%40user%2Fsome-article-abc123

curl fallback:
  curl -sL "https://freedium.cfd/https%3A%2F%2Fmedium.com%2F%40user%2Fsome-article-abc123"
```

## WebFetch call

```
url:    https://freedium.cfd/{encoded_url}
prompt: Extract the full article content and format as markdown
```

## Medium-Hosted Domains

These domains use Medium's paywall system and need the same bypass:

| Domain | Notes |
|---|---|
| `medium.com` | Primary domain |
| `*.medium.com` | Subdomains (publications) |
| `towardsdatascience.com` | Data science publication |
| `betterprogramming.pub` | Programming publication |
| `levelup.gitconnected.com` | Dev publication |
| `javascript.plainenglish.io` | JS publication |
| `uxdesign.cc` | UX/design publication |
| `hackernoon.com` | Tech publication |
| `codeburst.io` | Programming publication |
| `itnext.io` | Tech publication |
| `proandroiddev.com` | Android publication |
| `infosecwriteups.com` | Infosec publication |

## Escalation Chain

```
trafilatura (fails on paywalled content)
  → Freedium via WebFetch
    → freedium-mirror.cfd via WebFetch
      → curl -sL freedium (dangerouslyDisableSandbox if needed)
        → generic paywall bypass (see references/remove-paywall.md)
            → 12ft.io via WebFetch
            → archive.today via playwright / browser-harness
            → removepaywalls.com via playwright / browser-harness
```

## Common Issues

| Problem | Solution |
|---|---|
| Freedium down | Try `freedium-mirror.cfd` — same URL pattern |
| Article not found | Article may be too new to be cached yet |
| Garbled HTML / sparse content | Add prompt: "Extract the article text and format as markdown" |
| 403 / bot-blocked on WebFetch | Use `curl -sL` with `dangerouslyDisableSandbox: true` |
| captcha on archive.today | Use playwright or browser-harness with real Chrome |
| < 200 tokens returned | Escalate to next service in chain |

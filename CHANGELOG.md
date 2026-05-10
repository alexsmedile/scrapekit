# Changelog

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [1.4.0] — 2026-05-10

### Added
- `references/smart-review.md` — failure analysis workflow: reads `.scrapekit/session.log` for `err`/`thin` entries, cross-references current chat history, produces a structured per-failure report (target, tool, hypothesis, suggested fix, confidence level), then asks user to save locally or open a GitHub issue upstream
- Trigger added to `SKILL.md`: "smart review", "review failures", "what went wrong"

---

## [1.3.0] — 2026-05-10

### Added
- `hooks/hooks.json` + `hooks/hooks-codex.json` — PostToolUse hook logs every WebFetch and Bash call to `.scrapekit/session.log` (async, zero token cost)
- `scripts/log-tool-use.sh` — session logger: records timestamp, status (`ok` / `thin` / `err`), tool name, and URL or command; `thin` catches bot-blocks that return HTTP 200 with near-empty content
- `references/setup.md` — full onboarding detail (permissions JSON, API keys, install commands) moved out of `SKILL.md` to keep the main skill file lean
- `setup.sh --quiet` mode — machine-readable single-line output (`OK` or `ISSUES: n`) for Claude consumption; verbose mode unchanged for terminal use

### Changed
- Repo layout flattened: `agents/`, `skills/`, `.codex-plugin/`, `README.md` moved from `plugins/scrapekit/` to repo root as real directories — symlinks removed; layout is now GitHub-publishable without symlink resolution
- `SKILL.md` setup section trimmed to 5 lines pointing to `references/setup.md`; setup script runs only when something breaks, not proactively on every session

---

## [1.2.0] — 2026-05-10

### Added
- `references/medium.md` — Medium paywall bypass guide: Freedium, freedium-mirror.cfd, archive.today, RemovePaywalls, ReadMedium; service priority table, URL encoding, Medium-hosted domain list, escalation chain
- `references/remove-paywall.md` — generic paywall bypass for any publisher (NYT, WSJ, Bloomberg, etc.); covers 12ft.io, archive.today, Outline.com, RemovePaywalls with per-service details, publisher-specific notes, and escalation chain

### Changed
- Routing table: Medium and generic paywalled-article entries added with dedicated escalation paths
- `references/medium.md` escalation chain now falls through to `remove-paywall.md` when all Freedium options fail
- `SKILL.md` version bumped to 1.1.0

---

## [1.1.0] — 2026-05-10

### Added
- Plugin scaffold: `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/` manifests — scrapekit is now installable as a Claude Code / Codex plugin
- `agents/web-researcher.md` — general-purpose scraping subagent with pre-approved tool permissions and full scrapekit routing
- `agents/doc-fetcher.md` — document extraction subagent for PDF, DOCX, PPTX via docling
- `agents/social-scraper.md` — social media and e-commerce subagent via apify platform actors
- `scripts/setup.sh` — health check and guided onboarding; verifies all 10 tools, checks API keys, saves state to `.scrapekit/setup.json`

### Changed
- Restructured to plugin bundle layout: `SKILL.md` now lives in `skills/scrapekit/SKILL.md`; `references/`, `scripts/`, `versions/` moved inside the skill folder
- apm symlink updated to point to `skills/scrapekit/` directly (was plugin root)
- Gumroad routing added: skip trafilatura and webclaw entirely, go directly to jina
- Credit awareness rule added to routing guide and `web-researcher` agent: alert user on quota errors, never fail silently

### Fixed
- `compare.sh` path now uses `${CLAUDE_SKILL_DIR}` instead of hardcoded `~/.claude/skills/scrapekit`

### Removed
- `~/.claude/agents/web-researcher.md` global agent — now distributed by the plugin; install via plugin to get agents automatically

---

## [1.0.0] — 2026-05-06

Initial release — standalone skill with routing guide, tool references, benchmark data, and `compare.sh`.

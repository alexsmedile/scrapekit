# Changelog

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

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

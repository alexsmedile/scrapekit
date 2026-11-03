# webclaw — fastest local tool

Use this when: the selected route uses Webclaw rendering.

Rust-based, TLS fingerprinting, no browser. 35–1017ms. Free, local, no API key.
Best on SPAs — got 13k on Notion vs playwright 6.1k.

```bash
webclaw "https://example.com" -f llm > .scrapekit/page.md
head -80 .scrapekit/page.md
```

**Install:** `cargo install --git https://github.com/0xMassi/webclaw.git webclaw-cli`

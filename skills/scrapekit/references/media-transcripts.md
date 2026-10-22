# Media and transcript recovery

This is a portable routing protocol, not a bundled downloader implementation.
Prefer the active project's acquisition adapters when present; inspect their
CLI/config contract instead of assuming another project's scripts are installed.
Keep each attempt in fresh private staging and reuse verified cached evidence.

## Choose the evidence required

| Need | First route | Conditional fallback |
|---|---|---|
| Video picture and sound | yt-dlp with global config disabled | One no-cookie attempt after authenticated API/login failure on an observed public source; independent extractor or observed browser media |
| Ordered/mixed Instagram gallery | gallery-dl, metadata-derived membership and archive | Platform actor or browser capture; reconcile missing pages explicitly |
| Platform transcript | Exact-language published subtitle track, then explicitly selected automatic track | YouTube Transcript API on YouTube; local ASR when audio exists |
| Speech from local media | Existing configured Whisper Python/model | Existing whisper.cpp runtime and compatible model; an alternate runtime is not independent accuracy evidence |
| Visible text when audio is unavailable | OCR of timestamped frames | Visual inspection/correction; never label OCR as spoken transcript |

An Instagram caption/description is post copy, not necessarily a timed speech
transcript. Page readers and platform actors count as transcript providers only
when their actual returned evidence contains the requested transcript, with
provenance and coverage checked. Exit zero without media/nonempty cues is failure
or unavailable, not acquisition success. Empty ASR does not establish silence.

## Independent recovery layers

1. **Observed direct media → FFmpeg.** Under the active browser skill, obtain the
   actual accessible MP4/HLS/DASH resource. A blob URL is not a downloadable remote
   file. Use a bounded transfer, necessary session headers only, and a restricted
   input protocol set; remote manifests must not gain arbitrary local-file access.
   Keep signed URLs/headers out of chat and public receipts. Refresh an expired URL
   from observed playback rather than retrying it indefinitely. Label container
   remuxing accurately, probe and decode output, and verify source coverage.
2. **Instaloader.** A conditional independent Instagram extractor for one supplied
   post/reel shortcode, not a profile crawl. Use an existing installation, bounded
   connection attempts and stop on service denial/rate limit/challenge. It may fail
   on the same platform restrictions as yt-dlp; availability is not qualification.
3. **Playback recording → ASR.** When actual playback works but export does not,
   use an available recording capability with the intended window and system-audio
   source selected. Verify start/end, audible source content, interruptions and
   coverage. Import as `playback-recording`, preserve its hash and partial/full
   coverage assertion. An import adapter does not itself record the screen or
   certify audible content; do not assume a microphone captures system audio.
4. **YouTube Transcript API.** YouTube-only independent caption extraction. Select
   language and generated/published track explicitly; preserve raw timing and
   provenance. Missing/disabled captions remain unavailable. RequestBlocked,
   IpBlocked or rate limits stop automatic network fallbacks; no proxy rotation.
5. **whisper.cpp.** A local runtime fallback when existing Python/PyTorch execution
   fails. Requires an existing compatible model and executable; a PyTorch `.pt`
   file is not interchangeable with the runtime's model format. Preserve model,
   media and runtime identity, raw cues and normalized text. Do not silently install,
   convert/download models or upload audio to cloud ASR.
6. **Frame OCR.** Use existing OCR tooling/language data on inspected frames.
   Preserve image hashes and actual sample timestamps. Sparse samples cannot
   establish cue durations or continuous coverage. Nonempty output can be noise;
   review against the image before using it. Save visual text separately from ASR.

## Diagnose before choosing another route

- A browser session can select a broken authenticated API endpoint. On an exact
  source already observed publicly readable, one config-free no-cookie attempt
  after JSON/API parsing or login redirect can succeed. This does not prove an
  expired session, nor authorize accessing private content without its session.
- Cookie-access/decryption failures, login redirects, API response errors, network
  timeouts, TLS failures, rate limits and challenges need separate diagnoses.
  Do not repeat a rate-limited/challenged request via another extractor/account.
  Check trust configuration for TLS failures; never disable verification.
- Browser playback success does not guarantee browser export succeeds. Record the
  observed fetch/export failure; do not infer CORS or another root cause without
  evidence. A tool update is a hypothesis to test, not proof of repair.
- Network routes need short explicit budgets, limited retries and separate attempt
  logs. Local ASR can have a larger bounded budget. Stop once verified cached media
  satisfies the request instead of exercising every fallback against the source.

## Acceptance and reporting

Keep source identity, capture method (original/remuxed/recorded), hashes, language,
track type, raw versus normalized artifacts, timestamps and coverage explicit.
A successful decode proves file readability, not complete source capture or
perceptual A/V sync. ASR requires an audio stream and review of uncertain words;
OCR establishes only visible text. Preserve repetitions/overlaps in raw cues.
Never overwrite an approved capture or silently promote derived media to original.

Report qualification separately: documented candidate, installed prerequisite,
fixture-tested adapter, live execution, and reviewed evidence are different states.
A native-caption success on YouTube does not qualify Instagram captions. A successful
local ASR run does not prove the downloader works. Do not report several successful
methods for one source when only one download and its downstream transcription ran.
Canonical study/library saving belongs to the selected content workflow; scraping
success alone does not imply saved knowledge or publishing approval.

## Primary references

- [yt-dlp subtitle options](https://github.com/yt-dlp/yt-dlp#subtitle-options)
- [Instaloader single-post usage](https://instaloader.github.io/basic-usage.html)
- [FFmpeg protocols](https://ffmpeg.org/ffmpeg-protocols.html)
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api)
- [whisper.cpp CLI](https://github.com/ggml-org/whisper.cpp/tree/master/examples/cli)
- [Tesseract CLI](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html)

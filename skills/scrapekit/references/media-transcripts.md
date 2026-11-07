# Media and transcript recovery

Use this when: acquiring video/audio, extracting picture/speech evidence, or
recovering a media source after a diagnosed failure.

Prefer the active project's acquisition adapters when present; inspect their
CLI/config contract instead of assuming another project's scripts are installed.
Keep each attempt in fresh private staging and reuse verified cached evidence.
The standalone helper below is bundled with scrapekit and has no dependency on
Creator Studio. It captures evidence, not a canonical Study or editorial approval.

## Standalone capture and extraction

Resolve the installed skill directory from the skill catalog, then run its
`scripts/media_capture.py`. Use Python 3.11+ and installed ffmpeg/ffprobe; network
video acquisition additionally requires yt-dlp. No setup, model download or cloud
upload is implicit. Examples use `$SKILL_DIR` for that resolved package directory
and `/external/run-01` for a fresh configured capture destination.

1. Resolve the project owner, source identity, configured corpus and matching cached
   capture. Reuse valid originals instead of fetching again. A Creator Studio
   reference study stays on its Content Library route, including its native
   acquisition, sampler and reviewed Knowledge writer.
2. Choose a single acquisition route. Preview the bundled standalone helper by
   omitting `--execute`; previews write nothing and make no network request:

   ```sh
   python3 "$SKILL_DIR/scripts/media_capture.py" \
     --source-url 'https://www.instagram.com/reel/SHORTCODE/' \
     --download --audio --cookies-from-browser 'chrome:SELECTED_PROFILE' \
     --output /external/run-01 --execute
   ```

   Replace the illustrative browser/profile with the owner's configured existing
   session. Both yt-dlp and gallery-dl require explicit cookies, including metadata
   and native-caption requests. Missing/failed cookie access is a prerequisite to
   diagnose, not permission to start anonymously. Only an explicit user request
   permits a cookie-free attempt under the failure conditions below. This invokes
   one config-free yt-dlp video attempt
   with a 60-second process budget, zero retries, metadata and archive. There is
   no automatic public retry, alternate extractor or account change. Read the
   failure category and apply the conditional recovery rules below. A video
   downloader is not a complete mixed-gallery membership extractor.

   For an image/mixed gallery, first acquire ordered originals with gallery-dl
   under the Instagram membership protocol in SKILL.md. Reconcile expected versus
   returned pages, then pass **every** local file in that observed order:

   ```sh
   python3 "$SKILL_DIR/scripts/media_capture.py" \
     --source-url 'https://www.instagram.com/p/SHORTCODE/' \
     --media /external/originals/001.jpg --media /external/originals/002.mp4 \
     --audio --max-frames 30 --output /external/run-02 --execute
   ```

   Local mode also accepts one video or audio file and makes no network request.
   Animated GIFs require an explicit animation route; they are not treated as stills.
   The helper trusts the supplied ordered set, so its success alone does not prove
   platform membership or full source coverage. Keep that acquisition evidence.
3. Inspect `receipt.json` and `samples.json`. Each input is probed, fully decoded
   and hashed. Video samples share one budget of at most 30 across the entire set,
   reserve page coverage and bind each image to a decoded frame index, source PTS,
   hash and duration when available. Missing frame duration remains null, not a
   fabricated measurement. Static pages remain originals; they consume no video
   slots. Optional mono 16 kHz WAVs are derived audio with source hashes.
4. Recover speech separately: published captions when available, then explicitly
   selected automatic captions or an existing configured local ASR runtime. Keep
   model/runtime identity and raw cues, and review uncertain words. The helper
   can run configured local Whisper, but does not download platform captions itself.
   For an existing Python with `openai-whisper`/torch and an existing compatible
   model, add `--asr-python /configured/python --asr-model /configured/model.pt
   --language en`. This uses the bundled isolated worker on derived WAV, with
   a 600-second budget per audio page, no model downloads and no cloud upload.
   It preserves raw segments, word estimates, a plain-text reading aid, runtime/model/worker identity and
   source/audio hashes. Results remain `automatic-unreviewed`; empty ASR is
   `no-text`, not a claim of silence. A worker/dependency failure is a failed stage.
   To include existing evidence in a fresh extraction run instead,
   supply `--transcript /external/transcript.vtt --transcript-kind published
   --language en` (kinds: published, automatic, local-asr, supplied). It preserves
   nonempty `.vtt`, `.json` or `.txt` bytes and provenance; status is
   `captured-unvalidated`, never validated timing or verified transcription.
   Prefer the owning project's normalizer; otherwise inspect/validate cues using
   the declared format before claiming timed coverage. Description/caption copy
   is not speech evidence. For visual text, add `--ocr-language eng` (or installed
   language combination such as `ita+eng`). Existing Tesseract runs on retained
   samples and static pages only. `visual-text.json` binds text to image hashes,
   pages and point timestamps; it is never a spoken transcript or continuous cue
   map. No language-data setup is implicit; empty output stays `no-text`.
5. Inspect the actual picture and listen/play back before asserting motion, sound,
   sync or editing quality. Keep observations separate from proposed reuse.
   Return the receipt, source URL, paths/hashes, coverage, extracted material,
   uncertainty and failed stages to the requesting workflow.

**Output contract:** the explicitly selected fresh directory contains a receipt,
human-readable `capture.md`, sample manifest, frames, optional audio/transcript/OCR
and `private/` logs, archive
and native downloader sidecars. The directory is created with owner-only access;
raw logs and sidecars can contain credentials/signed URLs and stay private.
Receipts remove tracking queries (retaining YouTube watch identity); they are
local evidence and can contain local paths and transcript text. Sanitize before
external sharing. Do not publish raw downloader metadata. Do not run against
signed media URLs as source permalinks.

`complete` means the requested extraction succeeded; nonzero `partial`/`failed`
preserves the files and stage error. Transcript capture remains unvalidated even
when extraction completes. Missing audio is visible in the stream inventory, not
proof of a silent source. Missing ASR/OCR is a scoped gap, not an invented result.
Fix the failed dependency and use a fresh output, reusing valid local originals;
never overwrite an accepted capture or reset a sampling budget through retries.
For a transcript-only correction, preserve the existing sampled evidence and
store the corrected transcript as a separate derived revision through its owner;
do not rerun frame extraction just to attach text.

Originals are retained by default. A project may require frames-only archival:
verify retained hashes/transcripts and coverage, preserve original URL/hash/duration,
then let that owner record pruning. The helper never deletes source media. A
contact sheet can be built from the retained frames with an available image tool;
retain page/time mapping and reuse those frames without new extraction.

**Qualification (2026-11-02):** 19 offline tests passed, including real FFmpeg multi-stream/mixed-media fixtures and mocked downloader/ASR/OCR handoffs. One live Instagram reel download, full decode, three timestamp-bound frames, WAV extraction and local Whisper run completed with matching artifact hashes. Live OCR and platform captions were not exercised; picture, listening and transcript accuracy remain unreviewed. Run `python3 "$SKILL_DIR/scripts/test_media_capture.py"` for local
fixtures. Fixture success proves the tested helper paths, not live platform access,
ASR/OCR accuracy, full playback inspection or transfer to another video's style.

## Choose the evidence required

| Need | First route | Conditional fallback |
|---|---|---|
| Video picture and sound | yt-dlp with selected browser cookies and global config disabled | Diagnose cookie route; independent extractor with the same selected session or observed browser media. No-cookie retry only on explicit user request and observed public access. |
| Ordered/mixed Instagram gallery | gallery-dl with selected cookies for metadata and media, metadata-derived membership and archive | Platform actor or browser capture; reconcile missing pages explicitly |
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

- A browser session can select a broken authenticated API endpoint. Diagnose the
  selected cookies/profile; do not automatically remove cookies after JSON/API
  parsing errors or a login redirect. Only an explicit user request for a
  cookie-free attempt, on an exact source observed publicly readable, permits one
  config-free no-cookie attempt after that failure. This does not prove an expired
  session or authorize accessing private content without its session.
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

#!/usr/bin/env python3
"""Portable video acquisition and local evidence extraction. No installs or library writes."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit


class CaptureError(Exception):
    pass


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def write_summary(output, receipt):
    lines = ['# Media capture', '', 'Source: ' + receipt['source_url'],
             '', 'State: ' + receipt['state'], '', '| Stage | Result |', '|---|---|']
    for name, stage in receipt['stages'].items():
        lines.append(f'| {name} | {stage["state"]} |')
    if receipt.get('error'):
        lines += ['', 'Failure: ' + receipt['error']]
    lines += ['', '## Retained evidence', '']
    for artifact in receipt['artifacts']:
        path = Path(artifact['path'])
        # Labels are fixed roles; avoid interpolating source text as instructions.
        lines.append(f'- {artifact["role"]}: {path.name} (SHA-256 {artifact["sha256"]})')
    lines += ['', '## Inspection limits', '',
              'Picture, sound, transcript accuracy and source coverage remain unreviewed.',
              'Sampled frames do not establish continuous motion, sound or synchronization.',
              'ASR/OCR are automatic evidence; review uncertain text before reuse.',
              'Private logs and native metadata are local-only. No canonical study or library save was performed.', '']
    (output / 'capture.md').write_text('\n'.join(lines))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def source_url(value):
    u = urlsplit(value)
    if u.scheme != 'https' or not u.hostname or u.username or u.password:
        raise CaptureError('Supply an HTTPS public source permalink without credentials.')
    # Receipts identify the source, never persist tracking or signed query values.
    query = ''
    if u.hostname.lower() in ('youtube.com', 'www.youtube.com', 'm.youtube.com') and u.path == '/watch':
        video_id = parse_qs(u.query).get('v', [''])[0]
        if not re.fullmatch(r'[A-Za-z0-9_-]+', video_id):
            raise CaptureError('YouTube watch permalink requires a video ID.')
        query = urlencode({'v': video_id})
    return urlunsplit((u.scheme, u.netloc, u.path, query, ''))


def diagnose(log):
    text = log.lower()
    for category, needles in [
        ('rate-limit', ['429', 'too many requests', 'rate limit', 'requestblocked', 'ipblocked']),
        ('challenge', ['challenge_required', 'checkpoint_required', 'challenge page']),
        ('cookie-access', ['decrypt', 'could not find chrome cookies', 'permission denied']),
        ('tls', ['certificate verify failed', 'certificate_verify_failed']),
        ('authentication', ['login required', 'login page', 'authentication required']),
        ('api-response', ['jsondecodeerror', 'failed to parse json']),
    ]:
        if any(n in text for n in needles):
            return category
    return 'tool-failure'


def run(command, output, label, timeout):
    executable = shutil.which(command[0])
    if not executable:
        raise CaptureError('missing-dependency: ' + command[0])
    log = output / 'private' / (label + '.log')
    with log.open('wb') as stream:
        try:
            result = subprocess.run([executable, *command[1:]], stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            raise CaptureError('timeout: ' + label) from None
    if result.returncode:
        raise CaptureError(diagnose(log.read_text(errors='replace')) + ': ' + label)
    return log


def probe(path, output, index, frames=False):
    args = ['ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-of', 'json']
    args += (['-select_streams', 'v:0', '-show_frames', '-show_entries',
              'frame=best_effort_timestamp_time,duration_time,pkt_duration_time'] if frames else
             ['-show_entries', 'format=duration:stream=codec_type,width,height,sample_rate'])
    log = run(args + [str(path)], output, f'probe-{index}' + ('-frames' if frames else ''), 120)
    try:
        return json.loads(log.read_text())
    except ValueError:
        raise CaptureError('invalid-probe-output') from None


def allocate(durations, budget):
    """Reserve page coverage, then allocate proportional to duration under one ceiling."""
    if len(durations) > budget:
        raise CaptureError('frame-budget: fewer slots than video pages; choose an explicit subset.')
    desired = [max(1, math.ceil(d / 4) + 1) for d in durations]
    counts = [1] * len(durations)
    while sum(counts) < budget:
        eligible = [i for i in range(len(counts)) if counts[i] < desired[i]]
        if not eligible:
            break
        i = max(eligible, key=lambda i: math.sqrt(durations[i]) / counts[i])
        counts[i] += 1
    return counts


def choose_frames(frames, count):
    values = []
    for index, frame in enumerate(frames):
        try:
            pts = float(frame['best_effort_timestamp_time'])
        except (KeyError, ValueError, TypeError):
            continue
        if math.isfinite(pts) and pts >= 0:
            values.append((index, pts, frame))
    if not values:
        raise CaptureError('frame-timestamps-unavailable')
    selected = []
    for n in range(count):
        target = values[0][1] + (values[-1][1] - values[0][1]) * n / max(1, count - 1)
        item = min(values, key=lambda x: abs(x[1] - target))
        if item[0] not in [x[0] for x in selected]:
            selected.append(item)
    return selected


def extract(media, output, budget, audio, artifacts, stage):
    inspected = []
    for i, path in enumerate(media):
        data = probe(path, output, i)
        streams = data.get('streams', [])
        if not streams:
            raise CaptureError('no-readable-media-streams')
        # Full decode checks all streams, independently of the selected evidence.
        run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-protocol_whitelist', 'file,pipe',
             '-i', str(path), '-map', '0:v?', '-map', '0:a?', '-f', 'null', '-'], output, f'decode-{i}', 300)
        item = {'page': i + 1, 'source_path': str(path), 'sha256': sha(path), 'streams': streams}
        video = any(s.get('codec_type') == 'video' for s in streams)
        still = path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')
        if still and path.suffix.lower() == '.gif':
            raise CaptureError('animated-image: convert through an explicit animation workflow.')
        duration = float(data.get('format', {}).get('duration', 0))
        if video and not still and (not math.isfinite(duration) or duration <= 0):
            raise CaptureError('invalid-video-duration')
        item.update(duration_seconds=duration if duration > 0 else None, still_image=still)
        inspected.append(item)
        artifacts.append({'role': 'original-media', 'page': i + 1, 'path': str(path), 'sha256': item['sha256']})
        stage['media'] = inspected
    videos = [x for x in inspected if not x['still_image'] and
              any(s.get('codec_type') == 'video' for s in x['streams'])]
    counts = allocate([x['duration_seconds'] for x in videos], budget)
    samples = []
    for item, count in zip(videos, counts):
        i = item['page']
        frames = probe(Path(item['source_path']), output, i, frames=True)['frames']
        chosen = choose_frames(frames, count)
        for number, (index, pts, frame) in enumerate(chosen):
            destination = output / 'frames' / f'page-{i:03}-frame-{number:03}.png'
            destination.parent.mkdir(exist_ok=True)
            run(['ffmpeg', '-nostdin', '-v', 'error', '-protocol_whitelist', 'file,pipe',
                 '-i', item['source_path'], '-map', '0:v:0', '-vf', f'select=eq(n\\,{index})', '-vsync', '0',
                 '-frames:v', '1', str(destination)], output, f'frame-{i}-{number}', 120)
            if not destination.is_file() or not destination.stat().st_size:
                raise CaptureError('frame-extraction-empty')
            duration = frame.get('duration_time', frame.get('pkt_duration_time'))
            duration = float(duration) if duration is not None else None
            if duration is None and index + 1 < len(frames):
                duration = float(frames[index + 1]['best_effort_timestamp_time']) - pts
            samples.append({'page': i, 'stream': 'v:0', 'frame_index': index, 'timestamp_seconds': pts,
                            'duration_seconds': duration if duration and duration > 0 else None,
                            'path': str(destination), 'sha256': sha(destination)})
            stage['samples'] = samples
            artifacts.append({'role': 'sampled-frame', **samples[-1]})
    write_json(output / 'samples.json', {'frame_budget': budget, 'samples': samples,
                                        'scope': 'frames-only; not continuous playback'})
    if audio:
        for item in inspected:
            if not any(s.get('codec_type') == 'audio' for s in item['streams']):
                continue
            destination = output / f'audio-page-{item["page"]:03}.wav'
            run(['ffmpeg', '-nostdin', '-v', 'error', '-protocol_whitelist', 'file,pipe',
                 '-i', item['source_path'], '-map', '0:a:0', '-vn', '-ac', '1', '-ar', '16000', str(destination)],
                output, f'audio-{item["page"]}', 120)
            artifacts.append({'role': 'derived-audio', 'path': str(destination),
                              'sha256': sha(destination), 'source_sha256': item['sha256'],
                              'page': item['page'], 'stream': 'a:0'})
    return inspected


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-url', required=True, help='Public source permalink, not a signed media URL')
    p.add_argument('--media', type=Path, action='append', help='Existing local originals in source order')
    p.add_argument('--download', action='store_true', help='One bounded yt-dlp video acquisition')
    p.add_argument('--cookies-from-browser', help='Explicit selected yt-dlp browser[:profile]')
    p.add_argument('--output', required=True, type=Path, help='Fresh directory outside the skill package')
    p.add_argument('--max-frames', type=int, default=30)
    p.add_argument('--audio', action='store_true', help='Extract 16 kHz mono WAV when audio exists')
    p.add_argument('--transcript', type=Path, help='Existing nonempty .txt/.json/.vtt, retained without rewriting')
    p.add_argument('--transcript-kind', choices=['published', 'automatic', 'local-asr', 'supplied'])
    p.add_argument('--language', help='Transcript language; required with --transcript')
    p.add_argument('--asr-python', type=Path, help='Existing Python with openai-whisper and torch')
    p.add_argument('--asr-model', type=Path, help='Existing local Whisper model; never downloaded')
    p.add_argument('--ocr-language', help='Extract visual text using existing Tesseract language data')
    p.add_argument('--execute', action='store_true', help='Omit for a no-write, no-network preview')
    a = p.parse_args(argv)
    try:
        url = source_url(a.source_url)
        if bool(a.download) == bool(a.media):
            raise CaptureError('Choose exactly one: --download or one/more --media.')
        if not 1 <= a.max_frames <= 30:
            raise CaptureError('max-frames must be 1..30 across the complete input set.')
        if a.cookies_from_browser and not a.download:
            raise CaptureError('Browser cookies apply only to --download.')
        if bool(a.transcript) != bool(a.transcript_kind) or (a.transcript and not a.language):
            raise CaptureError('Transcript requires --transcript-kind and --language.')
        if bool(a.asr_python) != bool(a.asr_model) or (a.asr_python and not a.language):
            raise CaptureError('Local ASR requires --asr-python, --asr-model and --language.')
        if a.asr_python and a.transcript:
            raise CaptureError('Choose local ASR or an existing transcript, not both.')
        if a.asr_python and (not a.asr_python.is_file() or not a.asr_model.is_file()):
            raise CaptureError('Configured ASR Python/model must already exist.')
        media = [x.resolve(strict=True) for x in (a.media or [])]
        if any(not x.is_file() for x in media):
            raise CaptureError('Local media inputs must be files.')
        transcript = a.transcript.resolve(strict=True) if a.transcript else None
        if transcript and (transcript.suffix.lower() not in ('.txt', '.json', '.vtt') or
                           not transcript.read_text().strip()):
            raise CaptureError('Transcript must be nonempty .txt, .json or .vtt.')
        output = a.output.resolve()
        package = Path(__file__).resolve().parents[1]
        if output == package or package in output.parents or output.exists():
            raise CaptureError('Output must be fresh and outside the skill package; existing evidence is preserved.')
        if not a.execute:
            print(json.dumps({'state': 'preview', 'source_url': url, 'output': str(output),
                              'route': 'yt-dlp-video' if a.download else 'local-media',
                              'media_count': len(media), 'max_frames': a.max_frames,
                              'audio': a.audio or bool(a.asr_python), 'transcript_kind': a.transcript_kind,
                              'asr': bool(a.asr_python), 'ocr_language': a.ocr_language}))
            return 0
        output.mkdir(parents=True, mode=0o700)
        (output / 'private').mkdir(mode=0o700)
        receipt = {'schema': 'scrapekit/media-capture/1', 'source_url': url,
                   'state': 'failed', 'stages': {}, 'artifacts': [],
                   'inspection': {'picture': 'unreviewed', 'sound': 'unreviewed',
                                  'transcript_accuracy': 'unreviewed'},
                   'retention': 'Originals are preserved; project owner decides later pruning.'}
        try:
            if a.download:
                receipt['stages']['download'] = {'state': 'running', 'tool': 'yt-dlp'}
                destination = output / 'originals'
                destination.mkdir()
                command = ['yt-dlp', '--ignore-config', '--no-playlist', '--write-info-json',
                           '--download-archive', str(output / 'private' / 'archive.txt'),
                           '--retries', '0', '--fragment-retries', '0', '--extractor-retries', '0',
                           '--socket-timeout', '10', '-o', str(destination / '%(id)s.%(ext)s')]
                if a.cookies_from_browser:
                    command += ['--cookies-from-browser', a.cookies_from_browser]
                run(command + [url], output, 'download', 60)
                media = [x for x in sorted(destination.iterdir()) if x.suffix.lower() in
                         ('.mp4', '.mkv', '.webm', '.mov', '.m4a', '.mp3', '.ogg')]
                # Sidecars may include signed URLs; retain them only in private storage.
                for sidecar in destination.glob('*.json'):
                    target = sidecar.rename(output / 'private' / sidecar.name)
                    receipt['artifacts'].append({'role': 'private-native-metadata',
                                                 'path': str(target), 'sha256': sha(target)})
                if not media:
                    raise CaptureError('download-produced-no-media')
                receipt['stages']['download'] = {'state': 'complete', 'tool': 'yt-dlp'}
            else:
                receipt['stages']['download'] = {'state': 'not-requested', 'method': 'existing-local-media'}
            extraction = receipt['stages']['extraction'] = {'state': 'running'}
            extract(media, output, a.max_frames, a.audio or bool(a.asr_python), receipt['artifacts'], extraction)
            extraction['state'] = 'complete'
            if a.asr_python:
                receipt['stages']['transcript'] = {'state': 'running', 'method': 'local-asr'}
                audios = [x for x in receipt['artifacts'] if x['role'] == 'derived-audio']
                if not audios:
                    raise CaptureError('ASR requires an audio stream; source silence is unverified.')
                has_text = False
                for i, audio in enumerate(audios):
                    target = output / f'transcript-page-{audio["page"]:03}.raw.json'
                    worker = Path(__file__).with_name('whisper_transcribe.py')
                    run([str(a.asr_python.resolve()), str(worker), '--audio', audio['path'],
                         '--model', str(a.asr_model.resolve()), '--language', a.language,
                         '--output', str(target)], output, f'asr-{i}', 600)
                    decoded = json.loads(target.read_text())
                    has_text = has_text or bool(decoded.get('text', '').strip())
                    receipt['artifacts'].append({'role': 'raw-transcript', 'path': str(target),
                        'sha256': sha(target), 'source_sha256': audio['source_sha256'],
                        'audio_sha256': audio['sha256'], 'kind': 'local-asr',
                        'page': audio['page'], 'stream': audio['stream'],
                        'language': decoded.get('language'), 'worker_sha256': sha(worker)})
                    reading_aid = output / f'transcript-page-{audio["page"]:03}.txt'
                    reading_aid.write_text(decoded.get('text', '').strip() + '\n')
                    receipt['artifacts'].append({'role': 'transcript-reading-aid',
                        'path': str(reading_aid), 'sha256': sha(reading_aid),
                        'derived_from_sha256': sha(target), 'page': audio['page'],
                        'timing': 'none; refer to raw ASR estimates'})
                receipt['stages']['transcript']['state'] = 'automatic-unreviewed' if has_text else 'no-text'
            elif transcript:
                target = output / ('transcript.raw' + transcript.suffix.lower())
                shutil.copyfile(transcript, target)
                receipt['artifacts'].append({'role': 'raw-transcript', 'path': str(target),
                                             'sha256': sha(target), 'kind': a.transcript_kind,
                                             'language': a.language})
                receipt['stages']['transcript'] = {'state': 'captured-unvalidated',
                                                   'timing': 'not inferred or normalized'}
            else:
                receipt['stages']['transcript'] = {'state': 'not-requested'}
            if a.ocr_language:
                receipt['stages']['ocr'] = {'state': 'running'}
                images = [x for x in receipt['artifacts'] if x['role'] == 'sampled-frame' or
                          (x['role'] == 'original-media' and Path(x['path']).suffix.lower() in
                           ('.jpg', '.jpeg', '.png', '.webp', '.bmp'))]
                visual_text = []
                for i, image in enumerate(images):
                    base = output / f'ocr-{i:03}'
                    run(['tesseract', image['path'], str(base), '-l', a.ocr_language],
                        output, f'ocr-{i}', 60)
                    text_path = base.with_suffix('.txt')
                    visual_text.append({'image_sha256': image['sha256'],
                        'timestamp_seconds': image.get('timestamp_seconds'),
                        'page': image.get('page'), 'text': text_path.read_text(),
                        'path': str(text_path), 'sha256': sha(text_path)})
                target = output / 'visual-text.json'
                write_json(target, {'kind': 'visual-text-not-speech', 'language': a.ocr_language,
                                    'scope': 'sparse samples; timing is a point, not cue duration',
                                    'items': visual_text})
                receipt['artifacts'].append({'role': 'visual-text', 'path': str(target), 'sha256': sha(target)})
                receipt['stages']['ocr']['state'] = ('automatic-unreviewed' if any(
                    x['text'].strip() for x in visual_text) else 'no-text')
            else:
                receipt['stages']['ocr'] = {'state': 'not-requested'}
            receipt['state'] = 'complete'
        except (CaptureError, OSError, ValueError, KeyError, TypeError) as error:
            receipt['state'] = 'partial' if receipt['artifacts'] else 'failed'
            receipt['error'] = str(error) if isinstance(error, CaptureError) else type(error).__name__
            for stage in receipt['stages'].values():
                if stage.get('state') == 'running':
                    stage['state'] = 'failed'
        write_json(output / 'receipt.json', receipt)
        write_summary(output, receipt)
        print(json.dumps({'state': receipt['state'], 'receipt': str(output / 'receipt.json'),
                          'error': receipt.get('error')}))
        return 0 if receipt['state'] == 'complete' else 1
    except (CaptureError, OSError, ValueError) as error:
        print(json.dumps({'state': 'failed', 'error': str(error) if isinstance(error, CaptureError)
                          else type(error).__name__}))
        return 1


if __name__ == '__main__':
    sys.exit(main())

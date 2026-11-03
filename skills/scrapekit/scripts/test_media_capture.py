#!/usr/bin/env python3
"""Offline regression fixtures for the bundled media evidence route."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import media_capture as capture


class ContractTests(unittest.TestCase):
    def test_youtube_identity_and_tracking(self):
        self.assertEqual(capture.source_url('https://www.youtube.com/watch?v=abc_123&t=2&token=SECRET'),
                         'https://www.youtube.com/watch?v=abc_123')
        self.assertEqual(capture.source_url('https://www.instagram.com/reel/abc/?token=SECRET'),
                         'https://www.instagram.com/reel/abc/')

    def test_reject_credentials(self):
        with self.assertRaises(capture.CaptureError):
            capture.source_url('https://user:secret@example.org/video')

    def test_budget_and_page_coverage(self):
        counts = capture.allocate([1, 100, 50], 12)
        self.assertEqual(sum(counts), 12)
        self.assertTrue(all(x >= 1 for x in counts))
        with self.assertRaises(capture.CaptureError):
            capture.allocate([1] * 31, 30)

    def test_variable_frame_timestamps_and_deduplication(self):
        frames = [{'best_effort_timestamp_time': str(t)} for t in [0, .1, .8, 1.9]]
        self.assertEqual([x[:2] for x in capture.choose_frames(frames, 3)], [(0, 0), (2, .8), (3, 1.9)])
        self.assertEqual(len(capture.choose_frames(frames, 30)), 4)

    def test_rate_limit_challenge_and_cookie_diagnosis(self):
        self.assertEqual(capture.diagnose('HTTP Error 429: token=SECRET'), 'rate-limit')
        self.assertEqual(capture.diagnose('challenge_required'), 'challenge')
        self.assertEqual(capture.diagnose('failed to decrypt cookies'), 'cookie-access')

    def test_preview_has_no_writes_or_network(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(capture, 'run') as run:
            output = Path(directory) / 'new'
            with contextlib.redirect_stdout(io.StringIO()):
                status = capture.main(['--source-url', 'https://example.org/video', '--download',
                                       '--output', str(output)])
            self.assertEqual(status, 0)
            self.assertFalse(output.exists())
            run.assert_not_called()

    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'accepted.txt'
            marker.write_text('keep')
            with contextlib.redirect_stdout(io.StringIO()):
                status = capture.main(['--source-url', 'https://example.org/video', '--download',
                                       '--output', directory, '--execute'])
            self.assertEqual(status, 1)
            self.assertEqual(marker.read_text(), 'keep')

    def test_failure_receipt_does_not_print_raw_log(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'capture'
            stdout = io.StringIO()
            with patch.object(capture, 'run', side_effect=capture.CaptureError('rate-limit: download')), \
                    contextlib.redirect_stdout(stdout):
                status = capture.main(['--source-url', 'https://example.org/video?token=SECRET',
                                       '--download', '--output', str(output), '--execute'])
            self.assertEqual(status, 1)
            self.assertNotIn('SECRET', stdout.getvalue())
            receipt = json.loads((output / 'receipt.json').read_text())
            self.assertEqual(receipt['state'], 'failed')
            self.assertEqual(receipt['error'], 'rate-limit: download')
            self.assertNotIn('SECRET', json.dumps(receipt))


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg/ffprobe not installed')
class LocalMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.video = cls.root / 'source.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
                        'testsrc2=size=160x240:rate=10:duration=1.2', '-f', 'lavfi', '-i',
                        'sine=frequency=440:duration=1.2', '-c:v', 'mpeg4', '-c:a', 'aac',
                        '-shortest', str(cls.video)], check=True)
        cls.still = cls.root / 'still.png'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(cls.video),
                        '-frames:v', '1', str(cls.still)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def execute(self, name, extra):
        output = self.root / name
        with contextlib.redirect_stdout(io.StringIO()):
            status = capture.main(['--source-url', 'https://example.org/reference',
                                   '--output', str(output), '--execute', *extra])
        return status, json.loads((output / 'receipt.json').read_text()), output

    def test_mixed_media_frame_binding_audio_and_hashes(self):
        status, receipt, output = self.execute('mixed', ['--media', str(self.still), '--media',
                                                       str(self.video), '--audio'])
        self.assertEqual(status, 0)
        self.assertEqual(receipt['state'], 'complete')
        samples = json.loads((output / 'samples.json').read_text())['samples']
        self.assertEqual([s['frame_index'] for s in samples], [0, 11])
        self.assertEqual([s['timestamp_seconds'] for s in samples], [0, 1.1])
        self.assertTrue(all(s['page'] == 2 and s['duration_seconds'] > 0 for s in samples))
        for artifact in receipt['artifacts']:
            self.assertEqual(capture.sha(Path(artifact['path'])), artifact['sha256'])
        self.assertTrue((output / 'audio-page-002.wav').is_file())
        self.assertEqual(receipt['inspection']['sound'], 'unreviewed')

    def test_raw_transcript_remains_explicitly_unvalidated(self):
        transcript = self.root / 'source.vtt'
        transcript.write_text('WEBVTT\n\n00:00.000 --> 00:00.500\nHello\n')
        status, receipt, output = self.execute('transcript', ['--media', str(self.video),
            '--transcript', str(transcript), '--transcript-kind', 'supplied', '--language', 'en'])
        self.assertEqual(status, 0)
        self.assertEqual((output / 'transcript.raw.vtt').read_bytes(), transcript.read_bytes())
        self.assertEqual(receipt['stages']['transcript']['state'], 'captured-unvalidated')

    def test_corrupt_media_preserves_failure_receipt(self):
        broken = self.root / 'broken.mp4'
        broken.write_text('not a video')
        status, receipt, _ = self.execute('broken', ['--media', str(broken)])
        self.assertEqual(status, 1)
        self.assertEqual(receipt['state'], 'failed')
        self.assertEqual(receipt['stages']['extraction']['state'], 'failed')

    def test_multistream_frames_are_extracted_from_recorded_stream(self):
        source = self.root / 'multi.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-f', 'lavfi', '-i',
            'color=red:size=160x120:rate=5:duration=1', '-f', 'lavfi', '-i',
            'color=blue:size=320x240:rate=10:duration=1', '-map', '0:v', '-map', '1:v',
            '-c:v', 'mpeg4', str(source)], check=True)
        status, receipt, _ = self.execute('multi', ['--media', str(source)])
        self.assertEqual(status, 0)
        samples = [a for a in receipt['artifacts'] if a['role'] == 'sampled-frame']
        self.assertTrue(all(a['stream'] == 'v:0' for a in samples))
        for sample in samples:
            data = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
                '-show_entries', 'stream=width,height', '-of', 'json', sample['path']]))
            self.assertEqual(data['streams'][0], {'width': 160, 'height': 120})

    def test_asr_requires_audio_and_preserves_partial_evidence(self):
        import sys
        model = self.root / 'model.pt'
        model.write_text('fixture; must not be loaded without audio')
        status, receipt, _ = self.execute('no-audio', ['--media', str(self.still),
            '--asr-python', sys.executable, '--asr-model', str(model), '--language', 'en'])
        self.assertEqual(status, 1)
        self.assertEqual(receipt['state'], 'partial')
        self.assertEqual(receipt['stages']['transcript']['state'], 'failed')

    def test_download_command_and_private_sidecars(self):
        output = self.root / 'download'
        actual_run = capture.run
        calls = []
        def run(command, out, label, timeout):
            if label != 'download':
                return actual_run(command, out, label, timeout)
            calls.append(command)
            shutil.copyfile(self.video, out / 'originals' / 'fixture.mp4')
            (out / 'originals' / 'fixture.info.json').write_text('{"url":"signed-secret"}')
            return out / 'private' / 'download.log'
        with patch.object(capture, 'run', side_effect=run), contextlib.redirect_stdout(io.StringIO()):
            status = capture.main(['--source-url', 'https://example.org/video', '--download',
                '--cookies-from-browser', 'chrome:Selected', '--output', str(output), '--execute'])
        self.assertEqual(status, 0)
        self.assertIn('--ignore-config', calls[0])
        self.assertIn('--write-info-json', calls[0])
        self.assertIn('--download-archive', calls[0])
        self.assertIn('chrome:Selected', calls[0])
        self.assertTrue((output / 'private' / 'fixture.info.json').is_file())
        self.assertNotIn('signed-secret', (output / 'receipt.json').read_text())

    def test_optional_asr_and_ocr_handoffs_keep_page_identity(self):
        import sys
        model = self.root / 'existing-model.pt'
        model.write_text('fixture model; worker is mocked')
        actual_run = capture.run
        def run(command, out, label, timeout):
            if label.startswith('asr-'):
                target = Path(command[command.index('--output') + 1])
                target.write_text(json.dumps({'text': 'Hello', 'language': 'en',
                    'segments': [{'start': 0, 'end': .5, 'text': 'Hello'}],
                    'provenance': {'model_sha256': capture.sha(model), 'runtime': 'fixture'}}))
                return target
            if label.startswith('ocr-'):
                target = Path(command[2]).with_suffix('.txt')
                target.write_text('VISUAL TEXT')
                return target
            return actual_run(command, out, label, timeout)
        with patch.object(capture, 'run', side_effect=run):
            status, receipt, output = self.execute('asr-ocr', ['--media', str(self.still),
                '--media', str(self.video), '--asr-python', sys.executable, '--asr-model',
                str(model), '--language', 'en', '--ocr-language', 'eng'])
        self.assertEqual(status, 0)
        self.assertTrue((output / 'transcript-page-002.raw.json').is_file())
        transcript = next(x for x in receipt['artifacts'] if x['role'] == 'raw-transcript')
        self.assertEqual(transcript['page'], 2)
        self.assertEqual(transcript['stream'], 'a:0')
        text = json.loads((output / 'visual-text.json').read_text())
        self.assertEqual(text['kind'], 'visual-text-not-speech')
        self.assertEqual(text['items'][0]['page'], 1)
        self.assertEqual(receipt['stages']['transcript']['state'], 'automatic-unreviewed')


class LegacySafetyTests(unittest.TestCase):
    def test_all_child_shell_programs_are_fixed_source(self):
        source = Path(__file__).with_name('compare.sh').read_text()
        self.assertNotIn('bash -c "', source)
        self.assertNotIn('<<EOF', source)

    def test_compare_stops_on_empty_http_429(self):
        import os
        scripts = Path(__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            curl = bin_dir / 'curl'
            curl.write_text('#!/bin/sh\nwhile [ "$#" -gt 0 ]; do\n'
                            '  if [ "$1" = "-D" ]; then shift; printf "HTTP/2 429\\n" > "$1"; fi\n'
                            '  shift\ndone\nexit 22\n')
            curl.chmod(0o700)
            (root / 'markdownify.py').write_text('def markdownify(s): return s\n')
            env = {**os.environ, 'PATH': str(bin_dir) + os.pathsep + os.environ['PATH'],
                   'PYTHONPATH': str(root)}
            result = subprocess.run(['bash', str(scripts / 'compare.sh'), 'https://example.org/video'],
                                    cwd=root, env=env, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 1, result.stderr.decode())
            self.assertIn(b'Stopped: rate limit or challenge', result.stdout)
            self.assertNotIn(b'[2/8]', result.stdout)

    def test_compare_url_is_data_and_stops_on_challenge(self):
        import os
        scripts = Path(__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            curl = bin_dir / 'curl'
            curl.write_text('#!/bin/sh\nprintf "captcha challenge_required"\n')
            curl.chmod(0o700)
            (root / 'markdownify.py').write_text('def markdownify(s): return s\n')
            marker = root / 'injected'
            url = "https://example.org/'; touch " + str(marker) + "; echo '"
            env = {**os.environ, 'PATH': str(bin_dir) + os.pathsep + os.environ['PATH'],
                   'PYTHONPATH': str(root)}
            result = subprocess.run(['bash', str(scripts / 'compare.sh'), url], cwd=root,
                                    env=env, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 1, result.stderr.decode())
            self.assertIn(b'Stopped: rate limit or challenge', result.stdout)
            self.assertNotIn(b'[2/8]', result.stdout)
            self.assertFalse(marker.exists())

    @unittest.skipUnless(shutil.which('jq'), 'hook requires jq')
    def test_hook_sanitizes_url_and_private_log(self):
        import os
        scripts = Path(__file__).parent
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.scrapekit').mkdir()
            env = {**os.environ, 'CLAUDE_TOOL_NAME': 'WebFetch',
                   'CLAUDE_TOOL_INPUT': json.dumps({'url': 'https://user:SECRET@example.org/post?token=SECRET#SECRET'}),
                   'CLAUDE_TOOL_OUTPUT': json.dumps({'output': 'x' * 300})}
            subprocess.run(['bash', str(scripts / 'log-tool-use.sh')], env=env, cwd=root, check=True)
            log = root / '.scrapekit/session.log'
            self.assertIn('https://example.org/post', log.read_text())
            self.assertNotIn('SECRET', log.read_text())
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()

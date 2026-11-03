#!/usr/bin/env python3
"""Isolated worker for an explicitly selected existing Python/Whisper/model."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audio', required=True, type=Path)
    p.add_argument('--model', required=True, type=Path)
    p.add_argument('--language', required=True)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    if not a.audio.is_file() or not a.model.is_file() or a.output.exists():
        raise ValueError('Existing audio/model and fresh output required; no downloads.')
    import torch
    import whisper
    torch.set_num_threads(4)
    model = whisper.load_model(str(a.model.resolve()), device='cpu')
    result = model.transcribe(str(a.audio.resolve()), language=None if a.language == 'auto'
                              else a.language, fp16=False, word_timestamps=True, verbose=None)
    with a.model.open('rb') as stream:
        model_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    result['provenance'] = {'kind': 'local-asr', 'model_sha256': model_hash,
                            'runtime': importlib.metadata.version('openai-whisper'),
                            'accuracy': 'automatic, unreviewed', 'timing': 'ASR estimates'}
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()

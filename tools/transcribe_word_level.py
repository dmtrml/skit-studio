from __future__ import annotations

for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import argparse
import json
from pathlib import Path

from faster_whisper import WhisperModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe a recording with word-level timestamps.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default="large-v3")
    args = parser.parse_args()

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(
        str(args.input),
        language="ru",
        beam_size=5,
        temperature=0,
        word_timestamps=True,
        vad_filter=False,
        condition_on_previous_text=False,
    )

    segments = []
    texts = []
    for segment in segments_iter:
        text = segment.text.strip()
        texts.append(text)
        segments.append(
            {
                "start": segment.start,
                "end": segment.end,
                "text": text,
                "words": [
                    {
                        "start": word.start,
                        "end": word.end,
                        "word": word.word,
                        "probability": word.probability,
                    }
                    for word in (segment.words or [])
                ],
            }
        )

    payload = {
        "source": args.input.as_posix(),
        "model": args.model,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "text": " ".join(texts).strip(),
        "segments": segments,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    print(payload["text"])


if __name__ == "__main__":
    main()

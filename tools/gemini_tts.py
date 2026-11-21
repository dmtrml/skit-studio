"""Gemini TTS through the API (the same models as AI Studio "Generate speech"). Key: env GEMINI_API_KEY or ~/.skit-studio/gemini-key.txt, never printed.

    python <plugin>/tools/gemini_tts.py <out.wav> --text "..." [--style "..."] [--model gemini-2.5-flash-preview-tts] [--voice Charon]
    python <plugin>/tools/gemini_tts.py <out.wav> --text-file dialog.txt --speakers "Guy=Puck,Ko=Charon" [--style "..."]

The style goes in front of the text as a director's note, as in AI Studio. --speakers (2.5 models, max 2 speakers) reads a
dialogue in one request: every line of the text starts with "Name:" and the names match the --speakers list. Writes 24 kHz mono 16-bit WAV, prints the speech
span (-45 dB), the token usage and the HTTP error text if any (429 = rate / free-tier limit).
"""

from __future__ import annotations

for _s in (__import__("sys").stdout, __import__("sys").stderr):  # UTF-8 console output on Windows
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

import numpy as np

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def key_from_file() -> str:
    """The key from ~/.skit-studio/gemini-key.txt: the first line that is not empty and not a # comment."""
    try:
        for ln in (Path.home() / ".skit-studio" / "gemini-key.txt").read_text(encoding="utf-8-sig", errors="replace").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                return ln
    except OSError:
        pass
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--text", default="")
    ap.add_argument("--text-file", type=Path)
    ap.add_argument("--style", default="")
    ap.add_argument("--model", default="gemini-2.5-flash-preview-tts")
    ap.add_argument("--voice", default="Charon")
    ap.add_argument("--speakers", default="", help='multi-speaker: "Name1=Voice1,Name2=Voice2"')
    a = ap.parse_args()
    if a.text_file:
        a.text = a.text_file.read_text(encoding="utf-8").strip()
    if not a.text:
        sys.exit("give --text or --text-file")
    key = os.environ.get("GEMINI_API_KEY") or key_from_file()
    if not key:
        sys.exit("no Gemini key: set GEMINI_API_KEY or run scripts/install.py --key-file")
    # 2.5 takes the style inline (sometimes returns no audio, finishReason OTHER: just run again).
    # 3.8 reads an inline style line aloud and refuses systemInstruction (HTTP 400, 06.11): style is dropped there.
    sys_style = False
    if a.style and a.model.startswith("gemini-3"):
        print("note: style ignored for 3.x models (they read it aloud)")
        a.style = ""
    prompt = f"{a.style}\n\n{a.text}" if a.style else a.text
    if a.speakers:
        pairs = [p.split("=", 1) for p in a.speakers.split(",")]
        speech = {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": n.strip(), "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": v.strip()}}} for n, v in pairs]}}
    else:
        speech = {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": a.voice}}}
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": speech}}
    if sys_style and a.style:
        body["systemInstruction"] = {"parts": [{"text": f"Voice direction for the speech: {a.style}"}]}
    req = urllib.request.Request(API.format(model=a.model), data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode(errors='replace')[:600]}")
    c = d["candidates"][0]
    if "content" not in c:
        sys.exit(f"no audio: finishReason={c.get('finishReason')} usage={d.get('usageMetadata')}")
    part = c["content"]["parts"][0]["inlineData"]
    raw = base64.b64decode(part["data"])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if raw[:4] == b"RIFF":  # 3.x models return a ready WAV
        a.out.write_bytes(raw)
    else:  # 2.5 returns raw PCM s16le 24 kHz mono
        with wave.open(str(a.out), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(raw)
    with wave.open(str(a.out)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, ch).mean(axis=1) / 32768
    n = sr // 100
    db = 20 * np.log10(np.sqrt((x[: len(x) // n * n].reshape(-1, n) ** 2).mean(axis=1)) + 1e-9)
    on = np.where(db > -45)[0]
    span = f"{on[0] * 0.01:.2f}-{(on[-1] + 1) * 0.01:.2f} s" if len(on) else "silent"
    print(f"{a.out.name}: {len(x) / sr:.2f} s, {sr} Hz, speech {span}, mime {part.get('mimeType')}, usage {d.get('usageMetadata')}")


if __name__ == "__main__":
    main()

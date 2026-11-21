"""Print the Whisper words of a take with indices, for the word counts in prep.py LINES.

    python tools/words.py <skit>/voice/take1.words.json [--per-line 12]
    python tools/words.py take1.words.json --lines "5,6,4,5"      # check: do these counts sum to the total?

Prints  index  word  start-end  for every word (0-based, as prep.py uses them) and the total.
Whisper emits punctuation marks like «—» or «?»» as separate words: count them in LINES too.
Output is UTF-8 whatever the console code page is.
"""
import argparse
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def load_words(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return [w for s in d["segments"] for w in s["words"]]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words_json", type=Path)
    ap.add_argument("--lines", help="comma list of word counts per caption line, e.g. 5,6,4")
    a = ap.parse_args(argv)
    words = load_words(a.words_json)
    for i, w in enumerate(words):
        print(f"{i:3d}  {w['word'].strip():<16} {w['start']:.2f}-{w['end']:.2f}")
    print(f"total {len(words)} words")
    if a.lines:
        counts = [int(x) for x in a.lines.split(",")]
        i = 0
        for k, n in enumerate(counts, 1):
            print(f"L{k}: words {i}-{i + n - 1}: " + " ".join(w["word"].strip() for w in words[i:i + n]))
            i += n
        print("OK: counts sum to total" if i == len(words) else f"MISMATCH: counts sum to {i}, Whisper has {len(words)}")
        return 0 if i == len(words) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

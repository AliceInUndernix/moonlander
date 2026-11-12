"""Split a word into syllables by British English word-division rules.

Uses the British hyphenation patterns (data/hyph_en_GB.dic, from
"ukhyphen.tex" by Dominik Wujastyk and Graham Toal; BSD-style licence, see
LICENSE-hyphenation) with Frank Liang's method, the one TeX and LibreOffice
use. These are the places a British dictionary or printer may divide a
word, so they follow spelling and meaning (walk-ing, un-happy), not only
sound.

    split("dictionary") -> ["dic", "tion", "ary"]
"""

import os
import re

FILE = os.path.join(os.path.dirname(__file__), "data", "hyph_en_GB.dic")
LEFT = 2   # never fewer letters than this before the first break
RIGHT = 2  # ... or after the last one

_patterns = None


def _load():
    global _patterns
    if _patterns is None:
        _patterns = {}
        with open(FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip the header (UTF-8, LEFTHYPHENMIN 2 ...).
                if not line or " " in line or line == "UTF-8" or "%" in line:
                    continue
                # "ab3ol" -> letters "abol", numbers [0,0,3,0,0]
                letters = re.sub(r"\d", "", line)
                numbers = [0] * (len(letters) + 1)
                i = 0
                for ch in line:
                    if ch.isdigit():
                        numbers[i] = int(ch)
                    else:
                        i += 1
                _patterns[letters] = numbers
    return _patterns


def split(word):
    """The syllables of one word, as a list of strings."""
    if not word or not word.isalpha() or len(word) < LEFT + RIGHT:
        return [word] if word else []
    patterns = _load()
    w = "." + word.lower() + "."
    points = [0] * (len(w) + 1)
    for i in range(len(w)):
        for j in range(i + 1, len(w) + 1):
            p = patterns.get(w[i:j])
            if p:
                for k, n in enumerate(p):
                    points[i + k] = max(points[i + k], n)
    out, start = [], 0
    for i in range(LEFT, len(word) - RIGHT + 1):
        # An odd number between two letters means "a break may go here".
        if points[i + 1] % 2:
            out.append(word[start:i])
            start = i
    out.append(word[start:])
    return out


def show(text):
    """'dic·tion·ary' (each word of a phrase split on its own)."""
    return " ".join("·".join(split(w)) for w in text.split())

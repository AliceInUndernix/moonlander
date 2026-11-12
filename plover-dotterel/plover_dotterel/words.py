"""Word lists the Builder uses. Every list is read once, then kept.

- popular_words(): the "Popular words" list for the Builder (data/missing-words.txt):
  most common first, UK spelling with Oxford -ize, without words you can
  already make from a word + an affix (cats, walked, unhappy).
- rank(word): how common a word is in English, 1 = "the" (data/frequency.txt).
- lapwing_outlines(word): how original Lapwing writes a word, as a hint.
"""

import gzip
import os

DATA = os.path.join(os.path.dirname(__file__), "data")

_cache = {}


def _lines(name):
    """The words of a data file, without # comment lines."""
    if name not in _cache:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            _cache[name] = [w.strip() for w in f if w.strip() and not w.startswith("#")]
    return _cache[name]


def popular_words():
    return _lines("missing-words.txt")


def rank(word):
    """1 for the most common English word; None if it isn't in the list."""
    if "rank" not in _cache:
        table = {}
        for i, w in enumerate(_lines("frequency.txt"), 1):
            table.setdefault(w, i)
            table.setdefault(w.lower(), i)
        _cache["rank"] = table
    table = _cache["rank"]
    if not word:
        return None
    return table.get(word) or table.get(word.lower())


def _lapwing():
    if "lapwing" not in _cache:
        table = {}
        with gzip.open(os.path.join(DATA, "lapwing-outlines.tsv.gz"), "rt", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or "\t" not in line:
                    continue
                word, outlines = line.rstrip("\n").split("\t", 1)
                table[word] = outlines.split()
        _cache["lapwing"] = table
    return _cache["lapwing"]


def lapwing_outlines(word):
    """Lapwing's outlines for a word ([] if Lapwing doesn't have it).

    Lapwing's list is in -ise spelling, so realize also finds realise.
    """
    table = _lapwing()
    for w in (word, word.lower(), word.replace("iz", "is"), word.lower().replace("iz", "is")):
        if w in table:
            return table[w]
    return []

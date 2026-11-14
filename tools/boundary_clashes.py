#!/usr/bin/env python3
"""Find word-boundary clashes: outlines that eat a phrase you meant to write.

Plover always takes the longest outline it knows. So if you write "all"
(AUL) and then "most" (PHOEFT), Plover sees AUL/PHOEFT, finds "almost" in
the dictionary and writes that instead of "all most".

This script goes through every multi-stroke outline and checks whether its
strokes can be split into pieces that are each a word on their own. If so,
it joins those words into the phrase you would get by writing them one
after another ("all most"), and counts how often that phrase appears in the
texts you give it. The phrases that come up most are the clashes that will
bite in real writing.

Usage:
    python3 tools/boundary_clashes.py TEXTS... [--dict FILE ...] [--out FILE]

TEXTS are plain text files or folders of them (the Brown corpus's word/tag
format is handled too). Without --dict it reads the plugin's own JSON
dictionaries in Plover's order (the first one wins, as in Plover).
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DICT_DIR = HERE.parent / "plover-dotterel" / "plover_dotterel" / "dictionaries"
# Same order as DEFAULT_DICTIONARIES in system.py (only the JSON ones).
DEFAULT_DICTS = [
    "dotterel-base.json",
    "dotterel-proper-nouns.json",
    "dotterel-affixes.json",
    "dotterel-punctuation.json",
    "dotterel-commands.json",
    "dotterel-fingerspelling.json",
    "dotterel-numbers.json",
]

# A translation counts as "plain words" when it is letters, apostrophes,
# hyphens and spaces only: no {^affix}, no punctuation, no commands.
PLAIN = re.compile(r"^[A-Za-z][A-Za-z'\- ]*$")
# Hyphens stay inside a token, so "twenty-five" is one word and only
# "twenty five" written with a space counts as the phrase.
TOKEN = re.compile(r"[a-z]+(?:['’-][a-z]+)*")
MAX_PIECES = 4


def load_dicts(paths):
    merged = {}
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for outline, text in json.load(f).items():
                merged.setdefault(outline, text)  # first dictionary wins
    return merged


def load_lapwing():
    """word -> set of Lapwing's outlines for it (from the plugin's data)."""
    import gzip
    path = DICT_DIR.parent / "data" / "lapwing-outlines.tsv.gz"
    out = {}
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                word, _, outlines = line.rstrip("\n").partition("\t")
                out[word.lower()] = set(outlines.split())
    return out


def text_files(paths):
    for p in map(Path, paths):
        if p.is_dir():
            yield from (f for f in sorted(p.rglob("*")) if f.is_file())
        else:
            yield p


def corpus_tokens(paths):
    for f in text_files(paths):
        raw = f.read_text(encoding="utf-8", errors="replace")
        words = raw.split()
        # Brown corpus: "The/at jury/nn" -> keep the part before the tag.
        if words and sum("/" in w for w in words[:200]) > len(words[:200]) * 0.6:
            raw = " ".join(w.rsplit("/", 1)[0] for w in words)
        yield from TOKEN.findall(raw.lower().replace("’", "'"))


def cost(outline):
    """(strokes, keys): how much an outline costs to write."""
    return (outline.count("/") + 1,
            sum(ch not in "-/" for ch in outline))


def splits(strokes, entries, max_pieces):
    """Every way to cut the strokes into 2+ pieces that are plain words."""
    n = len(strokes)

    def go(start, acc):
        if start == n:
            if len(acc) >= 2:
                yield list(acc)
            return
        if len(acc) == max_pieces:
            return
        for end in range(start + 1, n + 1):
            if start == 0 and end == n:
                continue  # the whole outline is the word itself
            key = "/".join(strokes[start:end])
            text = entries.get(key)
            # A piece that needs # (a proper noun, a number) is never
            # written by accident, so it can't cause a clash.
            if (text is not None and PLAIN.match(text)
                    and not key.startswith("#")):
                acc.append((key, text))
                yield from go(end, acc)
                acc.pop()

    yield from go(0, [])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("texts", nargs="+", help="text files or folders")
    ap.add_argument("--dict", action="append", dest="dicts",
                    help="dictionary JSON, first wins (default: the plugin's)")
    ap.add_argument("--out", help="write the TSV here (default: stdout)")
    ap.add_argument("--try", action="append", dest="tries", default=[],
                    metavar="OUTLINE=WORD",
                    help="check an outline before adding it, e.g. "
                         "--try AUL/PHOEFT=almost (added on top)")
    ap.add_argument("--all", action="store_true",
                    help="also list clashes you'd never hit because one of "
                         "the words has a shorter outline (go TKPW, not "
                         "TKPWOE)")
    ap.add_argument("--min", type=int, default=1,
                    help="only list phrases seen at least this often")
    args = ap.parse_args()

    dicts = args.dicts or [str(DICT_DIR / d) for d in DEFAULT_DICTS]
    entries = load_dicts(dicts)
    tried = {}
    for t in args.tries:
        outline, _, word = t.partition("=")
        tried[outline] = word
    entries = {**entries, **tried}
    lapwing = load_lapwing()

    # The outline you'd actually write for each word: fewest strokes, then
    # fewest keys. A clash whose piece is a longer outline (go TKPWOE when
    # go is TKPW) only happens if you write the long one, so it's rare.
    best = {}
    for outline, text in entries.items():
        if outline.startswith("#"):
            continue
        c = cost(outline)
        if text not in best or c < best[text][0]:
            best[text] = (c, outline)

    # 1. Every outline that swallows a phrase, and the phrase it swallows.
    candidates = []  # (outline, word, pieces, phrase)
    for outline, word in entries.items():
        if args.tries and outline not in tried:
            continue
        strokes = outline.split("/")
        if len(strokes) < 2 or not PLAIN.match(word):
            continue
        seen = set()
        for pieces in splits(strokes, entries, MAX_PIECES):
            phrase = " ".join(t for _, t in pieces).lower()
            if phrase == word.lower() or phrase in seen:
                continue
            seen.add(phrase)
            candidates.append((outline, word, pieces, phrase))

    # 2. Count those phrases (and the words) in the texts.
    wanted = {tuple(c[3].split()) for c in candidates}
    longest = max((len(w) for w in wanted), default=1)
    phrase_n, word_n = Counter(), Counter()
    window = []
    for tok in corpus_tokens(args.texts):
        word_n[tok] += 1
        window.append(tok)
        if len(window) > longest:
            window.pop(0)
        for k in range(2, len(window) + 1):
            gram = tuple(window[-k:])
            if gram in wanted:
                phrase_n[gram] += 1

    # 3. Report, most common phrase first.
    rows = []
    for outline, word, pieces, phrase in candidates:
        count = phrase_n[tuple(phrase.split())]
        if count < (0 if args.tries else args.min):
            continue
        wcount = word_n[word.lower()] if " " not in word else ""
        how = " + ".join(f"{k} {t}" for k, t in pieces)
        shorter = [f"{t} {best[t][1]}" for k, t in pieces
                   if cost(k) > best[t][0]]
        if shorter and not args.all and not args.tries:
            continue
        usual = "no, you'd write " + ", ".join(shorter) if shorter else "yes"
        # "spacing": the word is the phrase without its spaces (onto / on
        # to), so a clash only costs a space. "other word": you get a
        # different word altogether (tumour for "to more").
        same = re.sub(r"[ \-']", "", word.lower()) == phrase.replace(" ", "")
        kind = "spacing" if same else "other word"
        in_lapwing = "yes" if outline in lapwing.get(word.lower(), ()) else ""
        rows.append((count, phrase, outline, word, kind, usual, wcount,
                     in_lapwing, how))
    rows.sort(key=lambda r: (-r[0], r[1], r[2]))

    out = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    out.write("phrase count\tphrase you meant\toutline\tPlover writes"
              "\tkind\tpieces are your usual outlines\tword count\tLapwing's outline\tpieces\n")
    for r in rows:
        out.write("\t".join(map(str, r)) + "\n")
    if args.out:
        out.close()
    seen = sum(1 for r in rows if r[0] > 0)
    print(f"{len(candidates)} outlines can swallow a phrase; "
          f"{seen} of those phrases appear in the texts.",
          file=sys.stderr)


if __name__ == "__main__":
    main()

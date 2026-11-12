"""What a word means: an English definition and the Russian translation.

Both come from data/meanings.tsv.gz, built offline, so they show at once
and work without the internet:
- English: WordNet 3.0 (Princeton University), in UK spelling;
- Russian: the Mueller English-Russian dictionary, 7th edition (GPL-2.0+).

A word that is only a form of another (walking, cats, ran) points to its
base word, and the base word's meaning is shown under it.
"""

import gzip
import html
import json
import os
import re
import urllib.parse

FILE = os.path.join(os.path.dirname(__file__), "data", "meanings.tsv.gz")
_ROWS = None

# Mueller's own abbreviations for the part of speech, in Russian.
_POS = {
    "_n.": "сущ.", "_v.": "гл.", "_a.": "прил.", "_adv.": "нареч.",
    "_prep.": "предл.", "_cj.": "союз", "_pron.": "мест.", "_int.": "межд.",
    "_num.": "числ.", "_pl.": "мн. ч.", "_p.": "прош. вр.", "_p. p.": "прич. прош. вр.",
    "_comp.": "сравн. ст.", "_superl.": "превосх. ст.",
}


def _rows():
    global _ROWS
    if _ROWS is None:
        _ROWS = {}
        try:
            with gzip.open(FILE, "rt", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("# ") or "\t" not in line:
                        continue
                    word, base, en, ru = line.rstrip("\n").split("\t", 3)
                    _ROWS[word] = (base, en, ru)
        except OSError:
            pass
    return _ROWS


def _row(word):
    rows = _rows()
    return rows.get(word) or rows.get(word.lower())


def _unescape(ru):
    return re.sub(r"\\(.)", lambda m: "\n" if m.group(1) == "n" else m.group(1), ru)


def lookup(word):
    """{"word", "base", "en": [[pos, [[definition, example], …]], …],
    "ru": text, "base_en": …, "base_ru": …}, or None if nothing is known."""
    word = (word or "").strip()
    row = _row(word) if word else None
    if not row:
        return None
    base, en, ru = row
    out = {"word": word, "base": base, "en": json.loads(en), "ru": _unescape(ru)}
    if base:
        brow = _row(base)
        if brow:
            out["base_en"] = json.loads(brow[1])
            out["base_ru"] = _unescape(brow[2])
    return out


def _clean(text):
    """Mueller's markers: _n. -> сущ., other _labels lose the underscore."""
    for k in sorted(_POS, key=len, reverse=True):
        text = text.replace(k, _POS[k])
    return re.sub(r"_(\w)", r"\1", text)


def _shorten(text, n=48):
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0].rstrip(" ,.(") + "…"


def russian_short(ru, limit=3):
    """The first meaning of each part of speech: 'вода; мочить'."""
    if not ru:
        return ""
    found = []
    for entry in ru.split("\n—\n"):  # homonyms: may (май) / may (мочь)
        text = " ".join(entry.split())
        # Blocks per part of speech: "1. _n. …", "2. _v. …" (or one block).
        for block in re.split(r"(?:^|\s)(?:\d+|I{1,3}|IV|V)\.\s+", text):
            block = re.sub(r"^(_\S+\s*|\([^)]*\)\s*)+", "", block.strip())
            m = re.search(r"(?:^|\s)1\)\s*(.*?)(?=\s\d+\)|$)", block)
            sense = m.group(1) if m else re.split(r"\s\d+\)", block)[0]
            for piece in re.split(r"[;:]", sense):
                piece = re.sub(r"^\s*(_\S+\s*)+", "", piece).strip(" ,.")
                # the first piece in Russian (English phrases are examples)
                if re.search("[а-яё]", piece, re.I) and not re.match(r"[A-Za-z]{2}", piece):
                    piece = _shorten(_clean(piece).strip())
                    if piece and piece not in found:
                        found.append(piece)
                    break
            if len(found) >= limit:
                return "; ".join(found)
    return "; ".join(found)


def preferred_pos(word, base):
    """Which part of speech a word form most likely is: cans -> noun,
    owns -> verb (after noun), walked -> verb."""
    w = (word or "").lower()
    b = (base or "").lower()
    if w.endswith(("ed", "ing")) or (b and w in (b + "en", b + "n", b + "ne")):
        return ("verb", "adjective", "noun")
    if w.endswith("s") and not (base or "").lower().endswith("s"):
        return ("noun", "verb")
    return ()


def english_short(en, prefer=()):
    """The first definition: 'a clear liquid …' (of a preferred part of
    speech when there is one)."""
    for want in tuple(prefer) + (None,):
        for pos, senses in en or []:
            if want is not None and pos != want:
                continue
            for definition, _ex in senses:
                return definition
    return ""


def english_html(en):
    rows = []
    for pos, senses in en or []:
        items = []
        for definition, example in senses:
            item = html.escape(definition)
            if example:
                item += f' <i style="color:#9a9da3">“{html.escape(example)}”</i>'
            items.append(item)
        rows.append(f'<b>{html.escape(pos)}</b> ' + " &nbsp;·&nbsp; ".join(
            f"{n}. {t}" if len(items) > 1 else t for n, t in enumerate(items, 1)))
    return "<br>".join(rows)


def russian_html(ru):
    if not ru:
        return ""
    lines = []
    for line in ru.split("\n"):
        depth = len(line) - len(line.lstrip(" "))
        text = html.escape(_clean(line.strip()))
        # part of speech headers in bold: "1. сущ."
        text = re.sub(r"^(\d+\.\s*)?((?:сущ|гл|прил|нареч|предл|мест|межд|числ)\.|союз)",
                      lambda m: f"{m.group(1) or ''}<b>{m.group(2)}</b>", text)
        lines.append("&nbsp;" * max(0, depth - 3) + text)
    return "<br>".join(lines)


def cambridge_ru_url(word):
    slug = urllib.parse.quote(word.strip().lower().replace(" ", "-"))
    return f"https://dictionary.cambridge.org/dictionary/english-russian/{slug}"

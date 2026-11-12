"""Dotterel modifiers: Ctrl, Shift, Alt, Super for the next stroke.

Write a modifier stroke, then any of your strokes that presses one key or
types one character; that key gets the modifiers.

    KHR  then  STPH-L     Ctrl+Up        (movement)
    KHR  then  KR*        Ctrl+C         (fingerspelling)
    SH   then  R-R        Shift+Enter
    SH   then  #-R        Shift+1 = !    (any symbol on your keyboard)
    KHR  then  SH  then  #TPH-T          Ctrl+Shift+Right (they add up)
    KHR  then  KHR        cancelled: the next stroke is just itself
                          (* would also undo the word before it)

Modifier strokes (Lapwing's left-hand chords):

    KHR     Ctrl            SH      Shift
    THRA    Alt             KPW     Super
    SKHR    Ctrl+Shift      TKHRA   Ctrl+Alt
    STHRA   Alt+Shift       STKHRA  Ctrl+Alt+Shift
    KPWHR   Ctrl+Super      SKPWHR  Shift+Super

The second stroke can be any stroke from these dictionaries next to this
file that makes one key or one character (checked in this order):
punctuation, commands, fingerspelling, numbers, movement. They are read
when Plover loads this dictionary, so after you change one of them,
restart Plover.
"""

import json
import os
import re

LONGEST_KEY = 4  # up to three modifier strokes, then the key

MODIFIERS = {
    "KHR": {"control"},
    "SH": {"shift"},
    "THRA": {"alt"},
    "KPW": {"super"},
    "SKHR": {"control", "shift"},
    "TKHRA": {"control", "alt"},
    "STHRA": {"alt", "shift"},
    "STKHRA": {"control", "alt", "shift"},
    "KPWHR": {"control", "super"},
    "SKPWHR": {"shift", "super"},
}
ORDER = ("control", "alt", "shift", "super")  # Ctrl+Alt+Shift+Super+key

SOURCES = (
    "dotterel-punctuation.json",
    "dotterel-commands.json",
    "dotterel-fingerspelling.json",
    "dotterel-numbers.json",
    "dotterel-movement.modal",
)

# One typed character -> the key that types it.
CHARACTER_KEYS = {
    "\n": "Return", "\t": "Tab", " ": "space",
    ".": "period", ",": "comma", "/": "slash", ";": "semicolon", "'": "apostrophe",
    "[": "bracketleft", "]": "bracketright", "\\": "backslash", "-": "minus",
    "=": "equal", "`": "grave",
}

_SPACING = re.compile(r"\{(?:\^|-\||~\||>|<)\}")  # {^} {-|} {~|} {>} {<}
_ONE_COMBO = re.compile(r"\{#([^{}()\s]+)\}")  # {#Up}: one key, no modifiers inside
_ONE_CHAR = re.compile(r"\{(?:&|\^?~?\|?)(.)\^?\}|(.)", re.DOTALL)  # {&c} {^.} {^~|\n^} or c


def key_of(translation):
    """The one key a translation presses or types, or None.

    "{#Up}{^}" -> "Up", "{>}{&c}" -> "c", "{&C}" -> "shift_l(c)", "{^.}" -> "period"."""
    rest = _SPACING.sub("", translation or "")
    combo = _ONE_COMBO.fullmatch(rest)
    if combo:
        return combo.group(1)
    char = _ONE_CHAR.fullmatch(rest)
    if not char:
        return None
    c = char.group(1) or char.group(2)
    if c.isascii() and c.isalnum():
        return c if not c.isupper() else "shift_l(" + c.lower() + ")"
    return CHARACTER_KEYS.get(c)


def _entries(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if path.endswith(".modal"):
        data = data.get("entry", {})  # the strokes that start movement
    return data.items()


def _read_keys():
    here = os.path.dirname(os.path.abspath(__file__))
    keys = {}
    for name in SOURCES:
        try:
            items = _entries(os.path.join(here, name))
        except (OSError, ValueError):
            continue
        for stroke, translation in items:
            if "/" in stroke or stroke in MODIFIERS or stroke in keys:
                continue
            key = key_of(translation)
            if key:
                keys[stroke] = key
    return keys


KEYS = _read_keys()  # stroke -> key, e.g. "STPH-L" -> "Up"


def press(key, mods):
    for mod in reversed([m for m in ORDER if m in mods]):
        key = f"{mod}_l({key})"
    return "{^}{#" + key + "}{^}"


def lookup(outline):
    *first, last = outline
    if not all(s in MODIFIERS for s in first):
        raise KeyError(outline)
    if last in MODIFIERS:
        return "{#}"  # waiting for the key (nothing is pressed yet)
    if any(a == b for a, b in zip(first, first[1:])):
        raise KeyError(outline)  # the same modifier twice: cancelled
    if not first or last not in KEYS:
        raise KeyError(outline)
    mods = set().union(*(MODIFIERS[s] for s in first))
    return press(KEYS[last], mods)


def reverse_lookup(text):
    return set()

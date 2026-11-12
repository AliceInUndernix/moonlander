"""Steno facts for the Builder: no windows here, only answers.

Everything works on Plover's dictionary collection (engine.dictionaries):
a list of dictionaries, top one wins. An outline is a tuple of strokes,
("KAT",) or ("RE", "TKO"); in text it's written "KAT" or "RE/TKO".

    outlines_for(dicts, "cat")       -> outlines that write "cat" now
    writes(dicts, ("KAT",))          -> what that outline writes now
    from_parts(dicts, "walking")     -> ways to write it from your words + affixes
    suggestions(dicts, "walking")    -> ideas: from parts, Lapwing, with *
    clash(dicts, outline, word)      -> who already has this outline
    plan_save / plan_take / plan_move / plan_swap
                                     -> the dictionary changes for each choice

A "plan" is a list of changes [(dictionary path, outline, new text or None)].
The Builder hands it to the outline table, which saves it as ONE step, so
Ctrl+Z undoes all of it at once.
"""

import re
from collections import namedtuple

from plover import system
from plover.orthography import add_suffix
from plover.steno import Stroke, normalize_steno

from . import words

Clash = namedtuple("Clash", "outline other path others")
# outline: the outline you wrote
# other:   the word it writes now
# path:    the dictionary that wins (where "other" comes from)
# others:  [(path, text)] every enabled dictionary that has this outline
#          with another text (so it can't win the outline back later)


def text(outline):
    return "/".join(outline)


GREEN = "#6fbf73"  # "this is what you wrote" (the Builder's green)


def same_outline(a, b):
    """True if two outlines are the same strokes (tuples or text, any case)."""
    def norm(o):
        if isinstance(o, str):
            try:
                return parse(o)
            except ValueError:
                return None
        return tuple(o)
    a, b = norm(a), norm(b)
    return bool(a) and a == b


def match_html(outline, typed):
    """An outline as HTML, lit up against the outline you are writing.

    The same outline: all green, bold, with a tick. The first strokes of it
    (you are part-way through): those strokes green. Otherwise plain.
    """
    import html
    outline, typed = tuple(outline), tuple(typed or ())
    plain = html.escape(text(outline))
    if not typed:
        return plain
    if outline == typed:
        return f"<b style='color:{GREEN}'>✓ {plain}</b>"
    n = len(typed)
    if n < len(outline) and outline[:n] == typed:
        head, tail = html.escape(text(outline[:n])), html.escape(text(outline[n:]))
        return f"<span style='color:{GREEN}'>{head}</span>/{tail}"
    return plain


def parse(outline_text):
    """'kat/-s' -> ('KAT', '-S'). ValueError if it isn't valid steno."""
    parts = [p for p in re.split(r"[/\s]+", outline_text.strip().upper()) if p]
    if not parts:
        return ()
    return tuple(normalize_steno("/".join(parts)))


def lapwing(word, limit=None):
    """Lapwing's outlines for a word, as outlines (tuples); bad ones left out."""
    out = []
    for o in words.lapwing_outlines(word):
        try:
            k = parse(o)
        except ValueError:
            continue
        if k and k not in out:
            out.append(k)
    return out[:limit] if limit else out


def _enabled(dicts):
    return [d for d in dicts.dicts if getattr(d, "enabled", True)]


def writes(dicts, outline):
    """(text, path) of what the outline writes now, or (None, None)."""
    for d in _enabled(dicts):
        try:
            value = d.get(outline)
        except Exception:  # Python dictionaries can refuse odd keys
            continue
        if value is not None:
            return value, d.path
    return None, None


def outlines_for(dicts, word):
    """[(outline, path)] that write this word now, shortest first.

    Outlines hidden by a higher dictionary are left out: they don't work.
    """
    out = []
    for key in dicts.reverse_lookup(word):
        value, path = writes(dicts, key)
        if value == word:
            out.append((key, path))
    out.sort(key=lambda kp: (len(kp[0]), sum(len(s) for s in kp[0]), kp[0]))
    return out


def clash(dicts, outline, word):
    """Clash(...) if the outline already writes another word, else None."""
    value, path = writes(dicts, outline)
    if value is None or value == word:
        return None
    others = []
    for d in _enabled(dicts):
        try:
            v = d.get(outline)
        except Exception:
            continue
        if v is not None and v != word:
            others.append((d.path, v))
    return Clash(outline, value, path, others)


# Ways to write a word from what you have ---------------------------------

_AFFIXES = {}  # id(dicts) -> (suffixes, prefixes), until forget()
_SUFFIX_RX = re.compile(r"\{\^([^{}^]+)\}")
_PREFIX_RX = re.compile(r"\{([^{}^]+)\^\}")


def forget():
    """Call after the dictionaries change."""
    _AFFIXES.clear()


def _affixes(dicts):
    """{'ing': [('-G',), ...]}, {'un': [('*UPB',)]} from your dictionaries."""
    if id(dicts) in _AFFIXES:
        return _AFFIXES[id(dicts)]
    suffixes, prefixes = {}, {}
    for d in _enabled(dicts):
        try:
            items = list(d.items())
        except Exception:  # Python dictionaries can't be listed
            continue
        for key, value in items:
            # Most of 130,000 entries are plain words: look closer only at
            # "{^...}" and "{...^}".
            if value[:1] != "{" or value[-1:] != "}":
                continue
            if value[1:2] == "^":
                m = _SUFFIX_RX.fullmatch(value)
                if m:
                    suffixes.setdefault(m.group(1), []).append(key)
            elif value[-2:-1] == "^":
                m = _PREFIX_RX.fullmatch(value)
                if m:
                    prefixes.setdefault(m.group(1), []).append(key)
    _AFFIXES[id(dicts)] = (suffixes, prefixes)
    return suffixes, prefixes


def _fold(base, key):
    """KAT + -S -> KATS (one stroke), if Plover folds that ending in.

    Only for the endings in system.py's SUFFIX_KEYS, and only if the
    base's last stroke doesn't already use those keys.
    """
    if len(key) != 1 or key[0] not in system.SUFFIX_KEYS:
        return None
    last, extra = Stroke(base[-1]), Stroke(key[0])
    if set(last.keys()) & set(extra.keys()):
        return None
    joined = Stroke(list(last.keys()) + list(extra.keys()))
    return base[:-1] + (joined.rtfcre,)


def from_parts(dicts, word, limit=6):
    """[(outline, 'walk + ing')] using outlines and affixes you already have."""
    suffixes, prefixes = _affixes(dicts)
    found = []
    low = word.lower()
    for suffix, keys in suffixes.items():
        s = suffix.lower()
        # The spelling rules change where the ending joins (happy + ly ->
        # happily), never its last letter: skip the endings that can't fit.
        if s[-1:] != low[-1:]:
            continue
        cands = set()
        # The base word, before the spelling rules changed it.
        for cut in range(len(s) + 2):
            b = low[: len(low) - cut] if cut else low
            for v in (b, b + "e", b[:-1] if len(b) > 2 and b[-1] == b[-2] else None,
                      b[:-1] + "y" if b.endswith("i") else None):
                if v and len(v) >= 2 and v != low:
                    cands.add(v)
        for base in cands:
            try:
                if add_suffix(base, suffix).lower() != low:
                    continue
            except Exception:
                continue
            for bkey, _p in outlines_for(dicts, base):
                for key in keys:
                    found.append((bkey + key, f"{base} + {suffix}"))
                    folded = _fold(bkey, key)
                    if folded:
                        found.append((folded, f"{base} + {suffix}, in one stroke"))
    for prefix, keys in prefixes.items():
        p = prefix.lower()
        if low.startswith(p) and len(low) > len(p) + 1:
            rest = word[len(p):].lstrip("-")
            for rkey, _p in outlines_for(dicts, rest):
                for key in keys:
                    found.append((key + rkey, f"{prefix} + {rest}"))
    # Keep the first of each outline, shortest first.
    seen, out = set(), []
    for outline, why in sorted(found, key=lambda f: (len(f[0]), sum(map(len, f[0])))):
        if outline not in seen:
            seen.add(outline)
            out.append((outline, why))
    return out[:limit]


def with_star(outline):
    """KAT -> KA*T (the asterisk tells two words apart). None if it has one."""
    first = Stroke(outline[0])
    if "*" in first.keys():
        return None
    return (Stroke(list(first.keys()) + ["*"]).rtfcre,) + tuple(outline[1:])


Idea = namedtuple("Idea", "outline why taken")
# taken: the word that outline writes now (None = free)


def suggestions(dicts, word, limit=8):
    """Ideas for a word's outline, best first: from parts, Lapwing, with *."""
    ideas = []
    for outline, why in from_parts(dicts, word):
        ideas.append((outline, why))
    for o in words.lapwing_outlines(word):
        try:
            ideas.append((parse(o), "as in Lapwing"))
        except ValueError:
            pass
    for outline, _why in list(ideas):
        starred = with_star(outline)
        if starred:
            ideas.append((starred, f"{text(outline)} with *"))
    out, seen = [], set()
    for outline, why in ideas:
        if outline in seen:
            continue
        seen.add(outline)
        value, _path = writes(dicts, outline)
        if value == word:
            continue  # it's already yours
        out.append(Idea(outline, why, value))
    return out[:limit]


def free_outline(dicts, word, avoid=()):
    """The first free idea for a word, or None."""
    for idea in suggestions(dicts, word, limit=20):
        if idea.taken is None and idea.outline not in avoid:
            return idea.outline
    return None


# What saving does: plans ---------------------------------------------------

def plan_save(path, outline, word):
    """No clash: just write it."""
    return [(path, outline, word)]


def plan_take(dicts, path, outline, word):
    """Take the outline: it writes your word, and leaves the other word in
    every dictionary (so the other word can't win it back from higher up)."""
    c = clash(dicts, outline, word)
    changes = [(path, outline, word)]
    if c:
        changes += [(p, outline, None) for p, _v in c.others if p != path]
    return changes


def plan_move(dicts, path, outline, word, new_outline):
    """Take it, and give the old word new_outline (in its own dictionary)."""
    c = clash(dicts, outline, word)
    changes = plan_take(dicts, path, outline, word)
    if c:
        changes.append((c.path, new_outline, c.other))
    return changes


def plan_swap(dicts, path, outline, word):
    """Swap: your word takes the outline, the old word gets your word's
    current outline. None if your word has no outline to give."""
    c = clash(dicts, outline, word)
    mine = [o for o in outlines_for(dicts, word) if o[0] != outline]
    if not c or not mine:
        return None
    my_outline, my_path = mine[0]
    changes = plan_take(dicts, path, outline, word)
    changes.append((my_path, my_outline, c.other))
    return changes

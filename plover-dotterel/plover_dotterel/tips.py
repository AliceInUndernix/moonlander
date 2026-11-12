"""Tips in Practice: the shortest way to write each word of the text.

For a word as it stands in the text ("London," or "walking." or "The"):

  1. the word itself: your shortest outline (fewest strokes, then fewest
     keys). If you have none: built from your words and affixes, folded
     into one stroke when Plover can (jump + ing -> SKWRUPLG), unless
     another word has that stroke.
  2. a capital you need to make yourself: the "next word capital" outline,
     unless the word follows . ! ? (Plover capitalises those itself).
  3. punctuation around it: your outline for , . ; : ! ? " ( ) and so on.

Everything comes from your dictionaries as they are now.
"""

import re

from . import steno

LEAD = re.compile(r"^([\"'(\[]*)(.*?)([\"').,;:!?\]]*)$")
# Punctuation after a word: glued to it, with a space after it as usual
# ({:} or {^:}, never {^}:{^} which glues the next word on too, as in 10:30).
TRAILING = ("{%s}", "{^%s}", "{^}%s", "{^~|%s}")
# Punctuation before a word (an opening quote or bracket): glued to the next word.
LEADING = ("{%s^}", "%s{^}", "{~|%s^}")
PUNCT_CAPS = ("{.}", "{!}", "{?}")


def _shortest(dicts, texts):
    best = None
    for t in texts:
        for outline, _p in steno.outlines_for(dicts, t):
            key = (len(outline), sum(map(len, outline)))
            if best is None or key < best[0]:
                best = (key, outline)
    return best[1] if best else None


class Tips:
    def __init__(self, dicts):
        self.dicts = dicts
        self._cache = {}

    def punct(self, ch, leading=False):
        key = ("p", ch, leading)
        if key not in self._cache:
            forms = LEADING if leading else TRAILING
            self._cache[key] = _shortest(self.dicts, [f % ch for f in forms])
        return self._cache[key]

    def word(self, w):
        """(outline, how) for a bare word, or (None, why)."""
        key = ("w", w)
        if key in self._cache:
            return self._cache[key]
        own = _shortest(self.dicts, [w])
        if own:
            out = (own, "")
        else:
            # A folded stroke only works if no other word has it.
            parts = [(o, why) for o, why in steno.from_parts(self.dicts, w)
                     if steno.writes(self.dicts, o)[0] in (None, w)]
            out = (parts[0][0], parts[0][1]) if parts else (None, "no outline yet")
        self._cache[key] = out
        return out

    def capital(self):
        return _shortest(self.dicts, ["{-|}", "{^}{-|}"])

    def for_token(self, token, after_stop=True):
        """[(outline text, what it writes)] for one word of the text, in order."""
        m = LEAD.match(token)
        lead, core, trail = m.groups() if m else ("", token, "")
        steps = []
        for ch in lead:
            o = self.punct(ch, leading=True)
            steps.append((steno.text(o) if o else "?", ch))
        if core:
            outline, how = self.word(core)
            if outline is None and core[:1].isupper():
                lower, how_lower = self.word(core.lower())
                if lower is not None:
                    if not after_stop:
                        cap = self.capital()
                        steps.append((steno.text(cap) if cap else "?", "capital"))
                    outline, how = lower, how_lower
            steps.append((steno.text(outline) if outline else "?", core + (f" ({how})" if how else "")))
        for ch in trail:
            o = self.punct(ch)
            steps.append((steno.text(o) if o else "?", ch))
        return steps

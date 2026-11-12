"""{:retro_us} - switch the last word between US and UK spelling.

colour -> color, color -> colour: one stroke (#SU) works both ways.

Word list: hyperreality/American-British-English-Translator (MIT),
see LICENSE-uk-us-list.
"""

import json
import os

_MAP = None
_US2UK = None


def _load():
    global _MAP
    if _MAP is None:
        path = os.path.join(os.path.dirname(__file__), "data", "uk_to_us.json")
        with open(path, encoding="utf-8") as f:
            _MAP = json.load(f)
    return _MAP


def _us2uk():
    global _US2UK
    if _US2UK is None:
        _US2UK = {}
        for uk, us in _load().items():
            _US2UK.setdefault(us, uk)
    return _US2UK


def _lookup(table, word):
    if word in table:
        return table[word]
    other = table.get(word.lower())
    if other is None:
        return None
    if word.isupper() and len(word) > 1:
        return other.upper()
    if word[0].isupper():
        return other[0].upper() + other[1:]
    return other


def switch(word):
    """US spelling -> UK, UK spelling -> US; other words unchanged."""
    if not word:
        return word
    uk = _lookup(_us2uk(), word)
    if uk is not None and uk != word:
        return uk
    us = _lookup(_load(), word)
    return us if us is not None else word


def to_us(word):
    """Return the US spelling of word, keeping its capitalisation."""
    table = _load()
    if word in table:
        return table[word]
    us = table.get(word.lower())
    if us is None:
        return word
    if word.isupper() and len(word) > 1:
        return us.upper()
    if word[0].isupper():
        return us[0].upper() + us[1:]
    return us


def meta_retro_us(ctx, cmdline):
    action = ctx.copy_last_action()
    action.prev_attach = True
    last_words = ctx.last_words(count=1)
    if last_words:
        action.prev_replace = last_words[0]
        action.text = switch(last_words[0])
    else:
        action.text = ""
    return action

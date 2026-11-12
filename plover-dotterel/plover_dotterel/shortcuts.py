"""Shortcuts for every button, and the steno outline that presses each one.

Every button, toggle and field in the Builder gets a keyboard shortcut.
When you hover over it, the tooltip says three things:

    Take the outline
    Keys:   Alt+1
    Steno:  THRA/#-R   (dotterel-modifiers)

The steno line is looked up in YOUR dictionaries, at the moment you hover,
so it is always true for what you have now:

  1. Dictionaries that can be listed (.json): every entry that presses keys,
     like "TKHR": "{#Delete}{^}". If a higher dictionary hides that outline,
     it isn't shown (it doesn't work).
  2. Dotterel modifiers (a .py dictionary, which can't be listed): the
     outline is a modifier stroke (KHR = Ctrl, SH = Shift, THRA = Alt,
     KPW = Super) then the stroke for the key, and is then checked by
     asking your dictionaries what that outline really writes.

Strokes from dotterel-modifiers press real keys even while you write in the
Outline field (Plover lets key presses through there), so every steno
shortcut works anywhere in the window.
"""

import os
import re
import runpy


from . import steno
from ._qt import QEvent, QKeySequence, QShortcut, Qt

_HERE = os.path.dirname(__file__)
MODIFIERS_FILE = os.path.join(_HERE, "dictionaries", "dotterel-modifiers.py")

MODS = {"control": "ctrl", "ctrl": "ctrl", "shift": "shift", "alt": "alt",
        "option": "alt", "super": "super", "meta": "super", "windows": "super"}
KEY_ALIASES = {"enter": "return", "esc": "escape", "del": "delete",
               "pgup": "page_up", "pageup": "page_up", "prior": "page_up",
               "pgdown": "page_down", "pagedown": "page_down", "next": "page_down",
               "ins": "insert", ".": "period", ",": "comma", "-": "minus",
               "=": "equal", "/": "slash", ";": "semicolon", "'": "apostrophe",
               "\\": "backslash", "`": "grave", "[": "bracketleft", "+": "plus",
               "]": "bracketright", "space": "space"}
OURS = {"ctrl": "control", "shift": "shift", "alt": "alt", "super": "super"}


def _key(name):
    k = name.strip().lower()
    return KEY_ALIASES.get(k, k)


def _mod(name):
    m = re.sub(r"_[lr]$", "", name.strip().lower())
    return MODS.get(m)


def from_qt(keys):
    """'Ctrl+Shift+M' -> (frozenset({'ctrl', 'shift'}), 'm')."""
    parts = QKeySequence(keys).toString().split("+")
    if parts[-1] == "" and len(parts) > 1:  # "Ctrl++"
        parts = parts[:-2] + ["+"]
    mods = frozenset(_mod(p) for p in parts[:-1])
    return mods, _key(parts[-1])


_COMBO_RX = re.compile(r"(?:\{\^\}|\{~\|\}|\{-\|\})*\{#([^{}]+)\}(?:\{\^\}|\{~\|\}|\{-\|\})*")


def from_plover(text):
    """'{^}{#control(shift(m))}{^}' -> (frozenset({'ctrl', 'shift'}), 'm').
    None if the entry isn't exactly one key combination."""
    m = _COMBO_RX.fullmatch(text or "")
    if not m:
        return None
    combo, mods = m.group(1).strip(), set()
    while True:
        n = re.fullmatch(r"([A-Za-z_]+)\((.*)\)", combo)
        if not n:
            break
        mod = _mod(n.group(1))
        if mod is None:
            return None
        mods.add(mod)
        combo = n.group(2).strip()
    if not combo or " " in combo or "(" in combo:
        return None
    return frozenset(mods), _key(combo)


class Finder:
    """Which outlines press which keys, in the current dictionaries."""

    def __init__(self, get_dicts):
        self._get_dicts = get_dicts
        self._listed = None  # {(mods, key): [(outline, path)]}
        self._mods = None

    def forget(self):
        """Call after the dictionaries change."""
        self._listed = None

    def _scan(self):
        dicts = self._get_dicts()
        found = {}
        for d in steno._enabled(dicts):
            if d.path.endswith(".modal"):
                continue  # those only work inside their mode
            try:
                items = list(d.items())
            except Exception:  # .py dictionaries can't be listed
                continue
            for key, value in items:
                if "{#" not in value:
                    continue
                combo = from_plover(value)
                if combo and steno.writes(dicts, key)[0] == value:
                    found.setdefault(combo, []).append((key, d.path))
        self._listed = found

    def _modifier_tables(self):
        if self._mods is None:
            try:
                ns = runpy.run_path(MODIFIERS_FILE)
                self._mods = (ns["MODIFIERS"], ns["KEYS"])
            except Exception:
                self._mods = ({}, {})
        return self._mods

    def _modifier_candidates(self, mods, key):
        """Outlines Dotterel modifiers would give: a modifier stroke (or a few
        that add up), then a stroke for the key. Each is checked afterwards."""
        if not mods or None in mods:
            return []
        modifiers, keys = self._modifier_tables()
        want = {OURS[m] for m in mods}
        exact = [s for s, m in modifiers.items() if set(m) == want]
        if not exact:  # no one chord for it: one stroke per modifier
            single = {next(iter(m)): s for s, m in modifiers.items() if len(m) == 1}
            if all(m in single for m in want):
                exact = ["/".join(single[m] for m in ("control", "alt", "shift", "super") if m in want)]
        key_strokes = [s for s, k in keys.items() if _key(k) == key]
        key_strokes.sort(key=len)
        return [tuple(m.split("/")) + (k,) for m in exact for k in key_strokes[:2]]

    def outlines(self, keys):
        """[(outline, path)] that press these keys now, shortest first."""
        combo = from_qt(keys)
        if self._listed is None:
            self._scan()
        found = list(self._listed.get(combo, []))
        dicts = self._get_dicts()
        for outline in self._modifier_candidates(*combo):
            value, path = steno.writes(dicts, outline)
            if value and from_plover(value) == combo and (outline, path) not in found:
                found.append((outline, path))
        found.sort(key=lambda op: (len(op[0]), sum(map(len, op[0]))))
        return found


def _name(path):
    return os.path.splitext(path.replace("\\", "/").rsplit("/", 1)[-1])[0]


class Hints:
    """Shortcuts plus their tooltips: action · keys · outline.

        hints.add(window, button, "Take the outline", ["Alt+1"], slot)

    The tooltip is written when you hover, from your dictionaries then.
    `steno` adds outlines the Builder reads itself (R-R for Enter).
    """

    def __init__(self, get_dicts):
        self.finder = Finder(get_dicts)
        self._hints = {}  # widget -> [(action, [keys], [(outline, why)])]
        self.shortcuts = []  # (keys, action, QShortcut)

    def add(self, window, widget, action, keys, slot=None, steno_extra=(),
            context=Qt.ShortcutContext.WindowShortcut):
        """Make the shortcuts (unless slot is None) and the hover hint."""
        keys = [keys] if isinstance(keys, str) else list(keys)
        if slot is not None:
            for k in keys:
                sc = QShortcut(QKeySequence(k), window)
                sc.setContext(context)
                sc.activated.connect(slot)
                self.shortcuts.append((k, action, sc))
        if widget is not None:
            if widget not in self._hints:
                widget.installEventFilter(_TipFilter.get(self))
            self._hints.setdefault(widget, []).append((action, keys, list(steno_extra)))

    def forget(self):
        self.finder.forget()

    def describe(self, action, keys, extra=()):
        """'<b>Action</b><br>Keys: …<br>Steno: …' for a tooltip."""
        keys = [keys] if isinstance(keys, str) else list(keys)
        lines = [f"<b>{_esc(action)}</b>"]
        shown = [(QKeySequence(k).toString() or k).replace("Return", "Enter") for k in keys]
        lines.append("Keys: " + ", ".join(_esc(k) for k in shown))
        outs = []
        for outline, why in extra:
            outs.append(f"<tt>{_esc(outline)}</tt> <span style='color:#8a8d93'>({_esc(why)})</span>")
        for k in keys:
            for outline, path in self.finder.outlines(k)[:2]:
                outs.append(f"<tt>{_esc(steno.text(outline))}</tt> "
                            f"<span style='color:#8a8d93'>({_esc(_name(path))})</span>")
        lines.append("Steno: " + (", ".join(outs) if outs else
                                  "<span style='color:#8a8d93'>none in your dictionaries</span>"))
        return "<br>".join(lines)

    def tooltip(self, widget):
        return "<hr>".join(self.describe(a, k, e) for a, k, e in self._hints.get(widget, []))

    def keys_for(self, action):
        return [k for k, a, _sc in self.shortcuts if a == action]


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class _TipFilter:
    """Writes a widget's tooltip just before Qt shows it."""

    _filters = {}

    @classmethod
    def get(cls, hints):
        from ._qt import QObject

        if id(hints) not in cls._filters:
            class F(QObject):
                def eventFilter(self, watched, event):
                    if event.type() == QEvent.Type.ToolTip:
                        watched.setToolTip(hints.tooltip(watched))
                    return False
            cls._filters[id(hints)] = F()
        return cls._filters[id(hints)]


class KeepShortcuts:
    """For a text field: let these shortcuts through instead of the field's
    own (an empty Outline field would otherwise eat Ctrl+Z)."""

    def __init__(self, hints, keys):
        from ._qt import QObject

        wanted = {QKeySequence(k).toString() for k in keys}

        class F(QObject):
            def eventFilter(self, watched, event):
                if event.type() == QEvent.Type.ShortcutOverride:
                    seq = QKeySequence(event.keyCombination() if hasattr(event, "keyCombination")
                                       else int(event.modifiers()) | event.key()).toString()
                    if seq in wanted:
                        event.ignore()
                        return True
                return False

        self.filter = F()

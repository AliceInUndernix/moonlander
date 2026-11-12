"""Quick add: a small window to give a word an outline, from a stroke.

TK*UPT opens it (dotterel-commands.json maps it to {PLOVER:DOTTEREL_ADD}).

    Word     the last word you wrote, selected: keep it, or type another
    Enter    go to the outline
    Outline  write it in steno; a clash shows under it
    Enter        add it (and any extra ones) to the dictionary, close
    Shift+Enter  keep this outline, write one more for the same word
    Escape       close, add nothing
    Up / Down    another dictionary (or click the list)

Names (London) go to dotterel-proper-nouns.json, other words to
dotterel-base.json, like in the Builder, until you pick one yourself.
"""

import html

try:  # Plover 5
    from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
    from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QLabel, QVBoxLayout
except ImportError:  # Plover 4
    from PyQt5.QtCore import QObject, Qt, QTimer, pyqtSignal as Signal, pyqtSlot as Slot
    from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QLabel, QVBoxLayout

from plover.gui_qt.add_translation_widget import AddTranslationWidget

from . import steno, words

WORDS_DICTIONARY = "dotterel-base.json"
NAMES_DICTIONARY = "dotterel-proper-nouns.json"
ENTER_STROKES = ("R-R", "R*R")  # your steno Enter: adds, like the Enter key

STYLE = """
QLineEdit { font-size: 15pt; padding: 4px 6px; }
QLabel#info { color: #888; }
QComboBox#target { color: #888; }
"""


def writable(dicts):
    """The dictionaries a word can be added to, top first."""
    return [d for d in dicts.dicts if not d.readonly and d.path.endswith(".json")]


def target_path(dicts, word):
    """Where the word goes: proper nouns for a name, base for the rest."""
    name = NAMES_DICTIONARY if word[:1].isupper() and word != "I" else WORDS_DICTIONARY
    writable_ = writable(dicts)
    for d in writable_:
        if _file(d.path) == name:
            return d.path
    pick = [d for d in writable_ if getattr(d, "enabled", True)] or writable_
    return pick[0].path if pick else None


def _file(path):
    return path.replace("\\", "/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]


class QuickAdd(QDialog):
    _open = None  # the one window, while it is open

    def __init__(self, engine):
        super().__init__()
        self._engine = engine
        self.setWindowTitle("Add")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.WindowCloseButtonHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setStyleSheet(STYLE)

        # Plover's own add-translation fields: they switch the engine so steno
        # in the Outline field comes out as strokes, and grab the last word.
        self.add = AddTranslationWidget()
        a = self.add
        self.word, self.outline = a.translation, a.strokes
        self.word.setObjectName("word")
        self.outline.setObjectName("outline")
        self.word.setPlaceholderText("Word")
        self.outline.setPlaceholderText("Outline")

        self.info = QLabel()
        self.info.setObjectName("info")
        self.info.setWordWrap(True)
        self.info.setTextFormat(Qt.TextFormat.RichText)

        # Which dictionary: picked from the word, until you pick one yourself.
        self.target = QComboBox()
        self.target.setObjectName("target")
        self.target.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.target.setToolTip("Dictionary  ·  Up / Down")
        for d in writable(engine.dictionaries):
            off = "" if getattr(d, "enabled", True) else "  (off)"
            self.target.addItem("→ " + _file(d.path) + off, d.path)
        self._picked = False
        self.target.activated.connect(self._pick)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(6)
        layout.addWidget(self.word)  # word on top, outline under it
        layout.addWidget(self.outline)
        layout.addWidget(self.target)
        layout.addWidget(self.info)
        a.setParent(self)
        a.hide()  # its fields live in this window; the rest stays hidden
        self.setTabOrder(self.word, self.outline)
        self.setMinimumWidth(340)

        self._extra = []  # outlines kept with Shift+Enter
        self._ideas_for, self._ideas_found = None, ([], [], [])
        self.word.textChanged.connect(self._auto_target)
        self.word.textChanged.connect(self._show)
        self.outline.textChanged.connect(self._on_outline)
        self.word.returnPressed.connect(self._to_outline)
        self.outline.installEventFilter(self)  # Enter / Shift+Enter, Up/Down
        self.word.installEventFilter(self)  # Up/Down
        self.finished.connect(self.add.reject)  # the engine back as it was
        self.finished.connect(self._closed)

        if self.outline.text() and not self.word.text():
            self.outline.clear()  # the last stroke was raw steno: start from the word
        self.word.selectAll()
        self.word.setFocus()
        self._auto_target()
        self._show()

    # What it shows ---------------------------------------------------------

    def _word(self):
        return self.word.text().strip()

    def _outline(self):
        try:
            return steno.parse(self.outline.text())
        except ValueError:
            return ()

    def _auto_target(self, *_):
        if self._picked:
            return
        i = self.target.findData(target_path(self._engine.dictionaries, self._word()))
        if i >= 0:
            self.target.setCurrentIndex(i)

    def _pick(self, *_):
        """You chose a dictionary: it stays, whatever word you write."""
        self._picked = True
        self._show()

    def next_dictionary(self, step):
        n = self.target.count()
        if n:
            self.target.setCurrentIndex((self.target.currentIndex() + step) % n)
            self._pick()

    def _ideas(self, word):
        """(yours, Lapwing's, free ideas) for the word; looked up once per word."""
        if self._ideas_for != word:
            dicts = self._engine.dictionaries
            try:
                found = ([o for o, _p in steno.outlines_for(dicts, word)][:6],
                         steno.lapwing(word, limit=4),
                         [i.outline for i in steno.suggestions(dicts, word) if i.taken is None][:6])
            except Exception:
                found = ([], [], [])
            self._ideas_for, self._ideas_found = word, found
        return self._ideas_found

    def _show(self, *_):
        dicts, word, outline = self._engine.dictionaries, self._word(), self._outline()
        lines = []
        if self._extra:
            lines.append(html.escape("+ " + ", ".join(steno.text(o) for o in self._extra)))
        c = steno.clash(dicts, outline, word) if outline and word else None
        if c is not None:
            clash = [f"⚠ {steno.text(outline)} writes “{c.other}” · {_file(c.path)}"]
            for p, v in c.others:  # the same outline lower down, with other words
                if p != c.path:
                    clash.append(f"also “{v}” · {_file(p)}")
            lines += [f'<span style="color:#d9822b">{html.escape(x)}</span>' for x in clash]
        if word:
            # What the word has, how Lapwing writes it, and free ideas. The one
            # you are writing turns green (its first strokes, while you are
            # part-way through), so you can see your outline is a known one.
            have, lap, ideas = self._ideas(word)
            shown = set()
            for label, group in (("has", have), ("Lapwing", lap), ("ideas", ideas)):
                group = [o for o in group if label == "Lapwing" or o not in shown]
                shown.update(group)
                if group:
                    lines.append(label + " " + ", ".join(steno.match_html(o, outline) for o in group))
        self.info.setText("<br>".join(lines))
        self.info.setVisible(bool(lines))
        self.adjustSize()

    def _on_outline(self, text):
        if text.startswith("/"):
            self.outline.setText(text.lstrip("/"))  # never a "/" in front
            return
        parts = [p for p in text.split("/") if p]
        if parts and parts[-1] in ENTER_STROKES:  # your steno Enter
            self.outline.setText("/".join(parts[:-1]))
            QTimer.singleShot(0, self.save)
            return
        self._show()

    # Keys ------------------------------------------------------------------

    def eventFilter(self, watched, event):
        if event.type() == event.Type.KeyPress and event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down) \
                and not event.modifiers() & ~Qt.KeyboardModifier.KeypadModifier:
            self.next_dictionary(-1 if event.key() == Qt.Key.Key_Up else 1)
            return True
        if watched is self.outline and event.type() == event.Type.KeyPress \
                and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.one_more()
            else:
                self.save()
            return True
        return super().eventFilter(watched, event)

    def _to_outline(self):
        if self._word():
            self.outline.setFocus()

    def _new_outline(self):
        """Empty the Outline field, and let Plover start a fresh outline there."""
        self.outline.clear()
        try:
            if self.add._focus == "strokes":
                with self._engine as engine:
                    engine.clear_translator_state()
                    engine.starting_stroke_state = self.add._strokes_state.starting_stroke
        except Exception:
            pass

    def one_more(self):
        """Shift+Enter: keep this outline, write another one."""
        outline = self._outline()
        if outline and outline not in self._extra:
            self._extra.append(outline)
        self._new_outline()
        self._show()

    def save(self):
        """Enter: add every outline to the dictionary, then close."""
        word = self._word()
        outlines = self._extra + [o for o in [self._outline()] if o and o not in self._extra]
        if not word:
            self.word.setFocus()
            return
        if not outlines:
            return
        path = self.target.currentData()
        if path is None:
            self.info.setText("No dictionary to add it to.")
            self.info.show()
            return
        self.add._unfocus()  # the engine back to normal before it changes
        word = words.curly(word)  # don't -> don’t, as the dictionaries have it
        plan = [(path, o, word) for o in outlines]
        builder = _open_builder()
        if builder is not None:
            builder.panel.apply_changes(plan)  # its table and Ctrl+Z know about it
        else:
            _apply(self._engine, plan)
        self.accept()

    def _closed(self, *_):
        QuickAdd._open = None


def _apply(engine, plan):
    from .outlines import OutlinePanel

    dicts = engine.dictionaries
    paths = []
    with engine:
        for path, key, new in plan:
            d = dicts[path]
            if d.get(key) != new:
                d[key] = new
                if path not in paths:
                    paths.append(path)
        if paths:
            OutlinePanel._save_later(dicts, paths)


def _open_builder():
    from .builder import DotterelBuilder

    for w in QApplication.topLevelWidgets():
        if isinstance(w, DotterelBuilder) and w.isVisible():
            return w
    return None


# The stroke ----------------------------------------------------------------

class _Opener(QObject):
    """Plover runs commands in its engine thread; windows open in the main one."""
    wanted = Signal(object)

    @Slot(object)
    def open(self, engine):
        show(engine)


_opener = None


def show(engine):
    w = QuickAdd._open
    if w is None:
        try:
            from plover.oslayer import wmctrl
            previous = wmctrl.GetForegroundWindow()
        except Exception:
            wmctrl = previous = None
        w = QuickAdd._open = QuickAdd(engine)
        if previous is not None:
            w.finished.connect(lambda *_: wmctrl.SetForegroundWindow(previous))
    w.show()
    w.raise_()
    w.activateWindow()
    return w


def quick_add(engine, cmdline=""):
    """{PLOVER:DOTTEREL_ADD}: open the window."""
    global _opener
    app = QApplication.instance()
    if app is None:
        return
    if _opener is None:
        _opener = _Opener()
        _opener.moveToThread(app.thread())
        _opener.wanted.connect(_opener.open)
    _opener.wanted.emit(engine)

"""Dotterel Builder: a Plover window for filling your dictionary.

Left, the "Add words" tab:
    the word list   Popular words (most common English words you don't
                    have yet) or My words (from a text you paste, or typed)
    the word card   the word, big; UK and US pronunciation with play
                    buttons; the UK sound in Russian letters; syllables;
                    the meaning, folded away until you open it
    steno           the outline field (write on your machine), what writes
                    the word now, ideas, and the clash box when the outline
                    you wrote already writes another word

Right, the all-outlines table (outlines.py): every entry of your
dictionaries, to search, edit, move, delete and undo.

Where the facts come from: steno.py (outlines, ideas, clashes), cambridge.py
(pronunciation, audio, English meaning), meaning.py (Russian), russian.py
(sound in Russian letters), syllables.py, words.py (word lists).
"""

import concurrent.futures
import html
import re

from plover.gui_qt.add_translation_widget import AddTranslationWidget
from plover.gui_qt.tool import Tool

from . import cambridge, meaning, russian, steno, syllables, words
from .shortcuts import Hints, KeepShortcuts
from ._qt import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QKeySequence,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QShortcut,
    QSplitter,
    QTabWidget,
    Qt,
    QTimer,
    QVBoxLayout,
    QWidget,
)
from .outlines import OutlinePanel
from .practice import PracticeTab, StatsTab, Store

WORDS_DICTIONARY = "dotterel-base.json"
NAMES_DICTIONARY = "dotterel-proper-nouns.json"
ENTER_STROKES = ("R-R", "R*R")  # your steno Enter: saves, like the Enter key
LIST_SIZE = 300  # Popular words shown at a time (the rest come as you go)
WORD_RX = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")
ROLE = Qt.ItemDataRole.UserRole
CLASH_ACTIONS = {
    "take": "Take it: the outline writes your word now",
    "move": "Take it, and give the old word a free outline",
    "swap": "Swap: the old word gets your word's other outline",
    "keep": "Keep it for the old word: write another outline",
}

STYLE = """
QLineEdit#word { font-size: 30pt; font-weight: 600; border: none; background: transparent;
                 padding: 0; }
QLineEdit#word:focus { border-bottom: 2px solid palette(highlight); }
QLabel#pron { font-size: 14pt; }
QLabel#russian { font-size: 13pt; color: #8a8d93; }
QLabel#syllables { font-size: 13pt; }
QLabel#meaning { font-size: 11.5pt; }
QLabel#dim { color: #8a8d93; }
QLabel#facts { font-size: 12pt; }
QLabel#note { font-size: 11.5pt; color: #6fbf73; }
QLabel#history { font-size: 10.5pt; color: #8a8d93; }
QLabel#warn { font-size: 11.5pt; color: #e0a030; }
QFrame#clash { border: 1px solid #d4a017; border-radius: 6px; }
QLabel#clashtitle { color: #e0a030; font-size: 13pt; font-weight: 600; }
QPushButton#play { padding: 2px 10px; }
QPushButton#primary { font-weight: 600; padding: 6px 18px; }
QPushButton:checked { background: palette(highlight); color: palette(highlighted-text); }
QLineEdit#strokes { font-size: 15pt; font-family: monospace; padding: 4px; }
QListWidget#queue { font-size: 11pt; }
"""


def esc(text):
    return html.escape(str(text), quote=True)


def words_in(text):
    """The words of a text, each once, in order."""
    seen, out = set(), []
    for w in WORD_RX.findall(text):
        w = w.replace("’", "'")
        if w.lower() not in seen:
            seen.add(w.lower())
            out.append(w)
    return out


class DotterelBuilder(Tool):
    """Fill your Dotterel dictionary, word by word."""

    TITLE = "Dotterel Builder"
    ICON = ":/resources/translation_add.svg"
    ROLE = "dotterel_builder"
    SHORTCUT = "Ctrl+B"

    def __init__(self, engine):
        super().__init__(engine)
        # A normal window, so tiling window managers tile it.
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint
                            | Qt.WindowType.WindowCloseButtonHint)
        self.setMinimumSize(760, 480)
        self.resize(1300, 820)
        self.setStyleSheet(STYLE)

        self._word = None          # the word on the card
        self._clash = None         # steno.Clash for the outline in the field
        self._replacing = {}       # word -> (path, outline) to replace on save
        self._last_saved = None    # (word, outline, changes done): for Redo last word
        self._facts_due = False
        self._facts = None         # (yours, Lapwing's, ideas) for the word on the card
        self.generation = 0        # goes up whenever the dictionaries change
        self._active = None        # words with an outline, from the table (see _has_outline)
        self._has = {}  # word -> has a working outline (until the dictionaries change)
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self._pron = {}            # word -> Cambridge info (or a Future)

        self.hints = Hints(lambda: self.dicts)
        self.panel = OutlinePanel(engine, write_new=self.open_word, is_busy=self.isActiveWindow,
                                  on_changed=self.refresh, redo_word=self.redo_entries,
                                  hints=self.hints)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_add_words(), "Add words")
        self.store = Store()
        self.practice = PracticeTab(self, self.store)
        self.stats = StatsTab(self, self.store)
        self.tabs.addTab(self.practice, "Practice")
        self.tabs.addTab(self.stats, "Stats")
        self.tabs.currentChanged.connect(self._on_tab)
        # Text size for the whole window: Ctrl+= bigger, Ctrl+- smaller, Ctrl+0 back.
        self.zoom = 1.0
        self._base_pt = self.font().pointSizeF()
        corner = QWidget()
        zl = QHBoxLayout(corner)
        zl.setContentsMargins(0, 0, 6, 0)
        self.smaller_button = QPushButton("A-")
        self.zoom_label = QLabel("100%")
        self.bigger_button = QPushButton("A+")
        self.smaller_button.clicked.connect(lambda: self.set_zoom(self.zoom - 0.1))
        self.bigger_button.clicked.connect(lambda: self.set_zoom(self.zoom + 0.1))
        for w in (self.smaller_button, self.zoom_label, self.bigger_button):
            zl.addWidget(w)
        self.tabs.setCornerWidget(corner, Qt.Corner.TopRightCorner)
        self.tabs.tabBar().setUsesScrollButtons(False)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self._make_shortcuts()

        self._poll = QTimer(self)
        self._poll.setInterval(150)
        self._poll.timeout.connect(self._check_pron)
        engine.signal_connect("stroked", self.practice.on_stroked)
        engine.signal_connect("dictionaries_loaded", lambda *_: (self.panel.reload(), self.refresh()))
        self._source = "popular"
        self.finished.connect(self.add.reject)
        self.finished.connect(lambda *_: self._pool.shutdown(wait=False, cancel_futures=True))
        self.finished.connect(lambda *_: OutlinePanel.wait_saves())
        self.restore_state()
        self.finished.connect(self.save_state)
        self.finished.connect(lambda *_: self.practice._abandon())  # keep a book's place
        self.panel.reload()  # first: the word list is checked against its rows
        self.set_source("popular")

    # Layout ---------------------------------------------------------------

    def _build_add_words(self):
        page = QWidget()
        row = QHBoxLayout(page)

        # Left column: where the words come from, and the list.
        left = QVBoxLayout()
        switch = QHBoxLayout()
        self.popular_button = QPushButton("Popular words")
        self.mine_button = QPushButton("My words")
        for b, name in ((self.popular_button, "popular"), (self.mine_button, "mine")):
            b.setCheckable(True)
            b.clicked.connect(lambda _c=False, n=name: self.set_source(n))
            switch.addWidget(b)
        left.addLayout(switch)
        self.paste = QPlainTextEdit()
        self.paste.setPlaceholderText("Paste a text, then press Find words")
        self.paste.setMaximumHeight(90)
        self.find_button = QPushButton("Find words")
        self.find_button.clicked.connect(self.find_words)
        self.own_word = QLineEdit()
        self.own_word.setPlaceholderText("+ a word of your own, Enter")
        self.own_word.returnPressed.connect(self.add_own_word)
        for w in (self.paste, self.find_button, self.own_word):
            left.addWidget(w)
        self.count = QLabel("")
        self.count.setObjectName("dim")
        left.addWidget(self.count)
        self.queue = QListWidget()
        self.queue.setObjectName("queue")
        self.queue.currentItemChanged.connect(self._on_pick)
        left.addWidget(self.queue, 1)
        holder = QWidget()
        holder.setLayout(left)
        holder.setMaximumWidth(260)
        row.addWidget(holder)

        # Right column: the word card and the steno part.
        card = QVBoxLayout()
        # Click the word to fix its spelling; Enter keeps the change.
        self.word_label = QLineEdit("")
        self.word_label.setObjectName("word")
        self.word_label.setPlaceholderText("No word yet")
        self.word_label.setFrame(False)
        self.word_label.returnPressed.connect(self._word_edited_enter)
        self.word_label.editingFinished.connect(self._word_edited)
        card.addWidget(self.word_label)

        pron = QHBoxLayout()
        self.uk_label = QLabel("")
        self.uk_label.setObjectName("pron")
        self.uk_play = QPushButton("Play UK")
        self.us_label = QLabel("")
        self.us_label.setObjectName("pron")
        self.us_play = QPushButton("Play US")
        for b, region in ((self.uk_play, "uk"), (self.us_play, "us")):
            b.setObjectName("play")
            b.clicked.connect(lambda _c=False, r=region: self.play(r))
        for w in (self.uk_label, self.uk_play, QLabel("   "), self.us_label, self.us_play):
            pron.addWidget(w)
        pron.addStretch()
        card.addLayout(pron)
        self.russian_label = QLabel("")
        self.russian_label.setObjectName("russian")
        self.russian_label.setTextFormat(Qt.TextFormat.RichText)
        self.russian_label.setToolTip("The UK sound in Russian letters: only a last resort.\n\n"
                                      + russian.LEGEND)
        card.addWidget(self.russian_label)
        self.syllables_label = QLabel("")
        self.syllables_label.setObjectName("syllables")
        card.addWidget(self.syllables_label)

        self.meaning_button = QPushButton("Show meaning")
        self.meaning_button.setCheckable(True)
        self.meaning_button.setFlat(True)
        self.meaning_button.toggled.connect(self._show_meaning)
        self.meaning_label = QLabel("")
        self.meaning_label.setObjectName("meaning")
        self.meaning_label.setWordWrap(True)
        self.meaning_label.setTextFormat(Qt.TextFormat.RichText)
        self.meaning_label.setOpenExternalLinks(True)
        self.meaning_label.hide()
        top = QHBoxLayout()
        top.addWidget(self.meaning_button)
        top.addStretch()
        card.addLayout(top)
        card.addWidget(self.meaning_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        card.addWidget(line)

        # Steno: the outline field is Plover's own, so it reads your machine.
        self.add = AddTranslationWidget()
        for w in (self.add.label_2, self.add.translation, self.add.label_3,
                  self.add.dictionary, self.add.strokes_info, self.add.translation_info):
            w.hide()
        self.add.label.setText("Outline:")
        self.add.strokes.setObjectName("strokes")
        self.add.strokes.textChanged.connect(self._on_strokes)
        self.add.strokes.returnPressed.connect(self.save)
        from ._qt import QSizePolicy
        self.add.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.add.layout().setContentsMargins(0, 0, 0, 0)
        card.addWidget(self.add)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self.save)
        self.skip_button = QPushButton("Skip")
        self.skip_button.clicked.connect(self.skip)
        self.redo_last_button = QPushButton("Redo last word")
        self.redo_last_button.setEnabled(False)
        self.redo_last_button.clicked.connect(self.redo_last)
        self.target = QComboBox()
        self.target.setToolTip("The dictionary new outlines go to")
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.skip_button)
        buttons.addWidget(self.redo_last_button)
        buttons.addStretch()
        buttons.addWidget(QLabel("Save to"))
        buttons.addWidget(self.target)
        card.addLayout(buttons)

        self.note = QLabel("")
        self.note.setObjectName("note")
        self.note.setWordWrap(True)
        card.addWidget(self.note)

        self.facts = QLabel("")
        self.facts.setObjectName("facts")
        self.facts.setWordWrap(True)
        self.facts.setTextFormat(Qt.TextFormat.RichText)
        self.facts.linkActivated.connect(self.use_outline)
        card.addWidget(self.facts)

        card.addWidget(self._build_clash_box())
        card.addStretch()
        # What you saved, newest first, at the very bottom.
        self.history = QLabel("")
        self.history.setObjectName("history")
        self.history.setWordWrap(True)
        self.history.setTextFormat(Qt.TextFormat.RichText)
        self._history = []
        card.addWidget(self.history)
        holder = QWidget()
        holder.setLayout(card)
        row.addWidget(holder, 1)
        return page

    def _build_clash_box(self):
        box = QFrame()
        box.setObjectName("clash")
        v = QVBoxLayout(box)
        self.clash_title = QLabel("")
        self.clash_title.setObjectName("clashtitle")
        self.clash_text = QLabel("")
        self.clash_text.setWordWrap(True)
        self.clash_text.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(self.clash_title)
        v.addWidget(self.clash_text)
        self.clash_buttons = {}
        for how in ("take", "move", "swap", "keep"):
            b = QPushButton("")
            b.setStyleSheet("text-align: left; padding: 5px 10px;")
            b.clicked.connect(lambda _c=False, h=how: self.resolve(h))
            v.addWidget(b)
            self.clash_buttons[how] = b
        box.hide()
        self.clash_box = box
        return box

    # Shortcuts: every button has one; hover shows it and its steno outline.

    def _make_shortcuts(self):
        h, me = self.hints, self
        bar = self.tabs.tabBar()
        for i, (keys, name) in enumerate((("Alt+A", "Add words"), ("Alt+P", "Practice"),
                                          ("Alt+G", "Stats"))):
            h.add(me, bar, f"Tabs: {name}", keys,
                  lambda k=i: self.tabs.setCurrentIndex(k))
        self.practice.make_shortcuts(h, me)
        h.add(me, self.bigger_button, "Bigger text", ["Ctrl+=", "Ctrl++"], lambda: self.set_zoom(self.zoom + 0.1))
        h.add(me, self.smaller_button, "Smaller text", "Ctrl+-", lambda: self.set_zoom(self.zoom - 0.1))
        h.add(me, self.zoom_label, "Text size back to 100%", "Ctrl+0", lambda: self.set_zoom(1.0))
        self.stats.make_shortcuts(h, me)

        def focus(w):
            return lambda: (w.setFocus(), w.selectAll() if hasattr(w, "selectAll") else None)

        def step(by):
            def go():
                n = self.queue.count()
                if n:
                    self.queue.setCurrentRow(min(max(self.queue.currentRow() + by, 0), n - 1))
            return go

        def next_target():
            if self.target.count():
                self.target.setCurrentIndex((self.target.currentIndex() + 1) % self.target.count())

        h.add(me, self.popular_button, "Popular words: common English words you don't have yet",
              "Ctrl+1", lambda: self.set_source("popular"))
        h.add(me, self.mine_button, "My words: from a text you paste, or typed in", "Ctrl+2",
              lambda: self.set_source("mine"))
        h.add(me, self.paste, "Paste a text here (opens My words)", "Ctrl+T",
              lambda: (self.set_source("mine"), self.paste.setFocus()))
        h.add(me, self.find_button, "Find words: the words of the text you don't have yet",
              "Ctrl+Return", lambda: self._source == "mine" and self.find_words())
        h.add(me, self.own_word, "Add a word of your own (opens My words)", "Ctrl+N",
              lambda: (self.set_source("mine"), self.own_word.setFocus()))
        h.add(me, self.queue, "Go to the word list", "Ctrl+L", focus(self.queue))
        h.add(me, self.queue, "Next word in the list", "Ctrl+Down", step(1))
        h.add(me, self.queue, "Previous word in the list", "Ctrl+Up", step(-1))
        h.add(me, self.uk_play, "Play the UK pronunciation", "Ctrl+U", lambda: self.play("uk"))
        h.add(me, self.us_play, "Play the US pronunciation", "Ctrl+Shift+U", lambda: self.play("us"))
        h.add(me, self.meaning_button, "Meaning: show or hide (English, then Russian)", "Ctrl+M",
              self.meaning_button.toggle)
        h.add(me, self.meaning_button, "Open the word in the Cambridge Dictionary", "Ctrl+Shift+M",
              self.open_cambridge)
        h.add(me, self.add.strokes, "Go to the Outline field", "Ctrl+O", focus(self.add.strokes))
        h.add(me, self.word_label, "Fix the word's spelling (click it, or this; Enter keeps it)", "Ctrl+W",
              lambda: (self.word_label.setFocus(), self.word_label.selectAll()))
        h.add(me, self.facts, "Put the next free idea in the Outline field", "Ctrl+I", self.next_idea)
        h.add(me, None, "Save", "Ctrl+S", self.save)
        h.add(me, self.save_button, "Save the outline (in a clash: Take it)", ["Return", "Ctrl+S"],
              steno_extra=[(o, "your Enter") for o in ENTER_STROKES])
        h.add(me, self.skip_button, "Skip this word (it leaves the list)", "Ctrl+K", self.skip)
        h.add(me, self.redo_last_button, "Redo last word: write the word you just saved again; "
              "the new outline replaces the one you saved", "Ctrl+R", self.redo_last)
        h.add(me, self.target, "Save to: the next dictionary", "Ctrl+D", next_target)
        for i, how in enumerate(("take", "move", "swap", "keep")):
            h.add(me, self.clash_buttons[how], CLASH_ACTIONS[how], f"Alt+{i + 1}",
                  lambda x=how: self.resolve(x))
        # The text fields would eat these keys; let them through.
        keep = KeepShortcuts(h, ["Ctrl+Z", "Ctrl+Shift+Z", "Ctrl+Y", "Ctrl+Return", "Ctrl+I",
                                 "Ctrl+Up", "Ctrl+Down", "Ctrl+K", "Ctrl+D", "Ctrl+U"])
        self._keep = keep
        for w in (self.add.strokes, self.paste, self.own_word, self.word_label):
            w.installEventFilter(keep.filter)

    def _on_tab(self, index):
        widget = self.tabs.widget(index)
        if widget is self.stats:
            self.stats.refresh_tests()
            self.stats.refresh_log()
        elif widget is self.practice and self.practice.test is None:
            self.practice.new_test()
        if widget is not self.practice:
            self.practice._abandon()  # a book keeps what you wrote

    def on_practice_saved(self):
        """A test is done: nothing to redo here yet (Stats reads it when opened)."""

    def next_idea(self):
        """Ctrl+I: the free ideas one after another."""
        if not self._word:
            return
        ideas = self._facts[2] if getattr(self, "_facts", None) and not self._facts_due \
            else steno.suggestions(self.dicts, self._word)
        free = [i.outline for i in ideas if i.taken is None]
        if not free:
            self.note.setText("No free idea: write your own outline.")
            return
        now = self._outline_in_field()
        i = (free.index(now) + 1) % len(free) if now in free else 0
        self.use_outline(steno.text(free[i]))

    def open_cambridge(self):
        if self._word:
            from ._qt import QDesktopServices, QUrl
            QDesktopServices.openUrl(QUrl(cambridge.page_url(self._word)))

    # Dictionaries --------------------------------------------------------

    @property
    def dicts(self):
        return self._engine.dictionaries

    def _path(self, name):
        for d in self.dicts.dicts:
            if d.path.replace("\\", "/").endswith("/" + name) and not d.readonly:
                return d.path
        return None

    def _fill_targets(self):
        current = self.target.currentData()
        self.target.blockSignals(True)
        self.target.clear()
        for d in self.dicts.dicts:
            if not d.readonly and d.path.endswith(".json"):
                self.target.addItem(d.path.replace("\\", "/").rsplit("/", 1)[-1], d.path)
        i = self.target.findData(current)
        self.target.setCurrentIndex(max(i, 0))
        self.target.blockSignals(False)

    def _pick_target(self, word):
        """Names (London) go to proper nouns, other words to base."""
        name = NAMES_DICTIONARY if word[:1].isupper() and word != "I" else WORDS_DICTIONARY
        path = self._path(name)
        i = self.target.findData(path) if path else -1
        if i >= 0:
            self.target.setCurrentIndex(i)

    def refresh(self, done=None):
        """After any dictionary change: list, card and facts are redone.

        done: the changes [(path, key, old, new)] if known; then only the
        words they touch are looked up again. None: everything is."""
        self._forget_words(done)
        self.generation += 1  # anything kept from the dictionaries is old now
        affix = re.compile(r"\{\^[^{}^]+\}|\{[^{}^]+\^\}")
        if done is None or any(affix.fullmatch(x or "") for _p, _k, o, n in done for x in (o, n)):
            steno.forget()  # the affixes changed: read them again
        self.hints.forget()
        self._fill_targets()
        if self._source == "popular":
            self._fill_popular(keep=self._word)
        else:
            self._drop_done()
        self._update_facts()

    # The word list --------------------------------------------------------

    def set_source(self, name):
        self._source = name
        self.popular_button.setChecked(name == "popular")
        self.mine_button.setChecked(name == "mine")
        for w in (self.paste, self.find_button, self.own_word):
            w.setVisible(name == "mine")
        self._fill_targets()
        self.queue.clear()
        if name == "popular":
            self._fill_popular()
        else:
            for w in getattr(self, "_mine", []):
                self._queue_word(w)
            self._update_count()
        if self.queue.count():
            self.queue.setCurrentRow(0)
        else:
            self._show_word(None)

    def _has_outline(self, word):
        v = self._has.get(word)
        if v is None:
            if self._active is None:
                # Every word some outline writes now, from the table's rows
                # (one pass, instead of a look-up for each of 25,000 words).
                self._active = {e.translation for e in self.panel._entries
                                if e.enabled and e.hidden_by is None}
            v = self._has[word] = word in self._active
        return v

    def _forget_words(self, done=None):
        if done is None:
            self._has, self._active = {}, None
            return
        touched = set()
        for path, key, old, new in done:
            touched.update((old, new))
            for d in self.dicts.dicts:  # what that outline wrote elsewhere
                try:
                    touched.add(d.get(key))
                except Exception:
                    pass
        for w in touched - {None}:  # looked up again, now
            self._has[w] = bool(steno.outlines_for(self.dicts, w))

    def _fill_popular(self, keep=None):
        todo = [w for w in words.popular_words() if not self._has_outline(w)]
        self._popular_left = len(todo)
        again = [w for w in self._replacing if w not in todo]  # being written again
        self.queue.blockSignals(True)
        self.queue.clear()
        for w in again:
            self._queue_word(w, mark="redo:")
        for w in todo[:LIST_SIZE]:
            self._queue_word(w, mark="redo:" if w in self._replacing else "")
        self.queue.blockSignals(False)
        self._update_count()
        if keep:
            self._select(keep)

    def _queue_word(self, word, mark="", top=False):
        item = QListWidgetItem((mark + " " if mark else "") + word)
        item.setData(ROLE, word)
        if top:
            self.queue.insertItem(0, item)
        else:
            self.queue.addItem(item)
        return item

    def _select(self, word):
        for i in range(self.queue.count()):
            if self.queue.item(i).data(ROLE) == word:
                self.queue.setCurrentRow(i)
                return True
        return False

    def _update_count(self):
        if self._source == "popular":
            self.count.setText(f"{self._popular_left:,} popular words without an outline")
        else:
            self.count.setText(f"{self.queue.count():,} words to do")

    def find_words(self):
        # "The" at the start of a sentence is "the": Plover makes the capital.
        found = [w for w in words_in(self.paste.toPlainText())
                 if not self._has_outline(w) and not self._has_outline(w.lower())]
        found.sort(key=lambda w: words.rank(w) or 10 ** 9)  # most common first
        self._mine = found
        self.set_source("mine")

    def add_own_word(self):
        new = [w.strip() for w in self.own_word.text().split(",") if w.strip()]
        self.own_word.clear()
        if not new:
            return
        self._mine = new + [w for w in getattr(self, "_mine", []) if w not in new]
        self.set_source("mine")

    def _drop_done(self):
        """My words: take off the words that have an outline now."""
        keep = []
        for i in reversed(range(self.queue.count())):
            w = self.queue.item(i).data(ROLE)
            if self._has_outline(w) and w not in self._replacing and w != self._word:
                self.queue.takeItem(i)
            else:
                keep.append(w)
        self._mine = list(reversed(keep))
        self._update_count()

    def _on_pick(self, item, _previous=None):
        self._show_word(item.data(ROLE) if item else None)

    def _word_edited_enter(self):
        self._word_edited()
        self.add.strokes.setFocus()  # then write its outline

    def _word_edited(self):
        """The word on the card was changed by hand: a misspelling fixed."""
        new = self.word_label.text().strip()
        old = self._word
        if not old or not new:
            self.word_label.setText(old or "")
            return
        if new == old:
            return
        item = self.queue.currentItem()
        if item is not None and item.data(ROLE) == old:
            mark = item.text()[: len(item.text()) - len(old)]
            item.setText(mark + new)
            item.setData(ROLE, new)
        if old in getattr(self, "_mine", []):
            self._mine = [new if w == old else w for w in self._mine]
        if old in self._replacing:
            self._replacing[new] = self._replacing.pop(old)
        if self.practice.back_after == old:
            self.practice.back_after = new
        self.queue.blockSignals(True)
        self._show_word(new)
        self.queue.blockSignals(False)
        self.note.setText(f"Spelling fixed: “{old}” is now “{new}”.")

    def open_word(self, word):
        """Open any word (the outline table's "write another outline")."""
        if not self._select(word):
            self._queue_word(word, top=True)
            self.queue.setCurrentRow(0)
        self.tabs.setCurrentIndex(0)

    def redo_entries(self, entries):
        """Write these entries again: [(word, path, outline)]."""
        for word, path, outline in reversed(entries):
            self._replacing[word] = (path, tuple(outline.split("/")))
            if self._source == "mine" and word not in getattr(self, "_mine", []):
                self._mine = [word] + getattr(self, "_mine", [])
            for i in reversed(range(self.queue.count())):
                if self.queue.item(i).data(ROLE) == word:
                    self.queue.takeItem(i)
            self._queue_word(word, mark="redo:", top=True)
        self.queue.setCurrentRow(0)
        self._show_word(self.queue.currentItem().data(ROLE))
        self.tabs.setCurrentIndex(0)

    def _add_history(self, message):
        self._history.insert(0, message)
        del self._history[8:]
        lines = [f"<span style='color:#6fbf73'>{esc(m)}</span>" if i == 0 else esc(m)
                 for i, m in enumerate(self._history)]
        self.history.setText("<br>".join(lines))

    def redo_last(self):
        """Ctrl+R: you saved a wrong outline (Enter by mistake): write it again.

        The whole save is taken back first: if the outline was taken from
        another word, that word gets it back. Then the word opens again.
        """
        if not self._last_saved:
            return
        word, outline, done = self._last_saved
        dicts = self.dicts
        changed = [k for p, k, _old, new in done if p in dicts and dicts[p].get(k) != new]
        if changed:
            self.note.setText(f"Can't redo “{word}”: {steno.text(changed[0])} was changed since.")
            return
        self._last_saved = None
        self.redo_last_button.setEnabled(False)
        self.redo_last_button.setText("Redo last word")
        back = [(p, k, old) for p, k, old, _new in reversed(done)]
        self.panel.apply_changes(back)  # one step: Ctrl+Z puts the save back
        for p, k, old, _new in done:
            if old is not None and old != word:
                self._unqueue(old)  # it has its outline back
        self.open_word(word)
        gave_back = [f"{steno.text(k)} → “{old}”" for p, k, old, _n in done if old not in (None, word)]
        self.note.setText(f"Write “{word}” again." + (" Given back: " + ", ".join(gave_back) + "."
                                                    if gave_back else ""))

    def _unqueue(self, word):
        if steno.outlines_for(self.dicts, word):
            for i in reversed(range(self.queue.count())):
                if self.queue.item(i).data(ROLE) == word and i != self.queue.currentRow():
                    self.queue.takeItem(i)
            if word in getattr(self, "_mine", []):
                self._mine.remove(word)

    def _next(self):
        row = self.queue.currentRow()
        word = self._word
        if row >= 0:
            self.queue.takeItem(row)
        if word in getattr(self, "_mine", []):
            self._mine.remove(word)
        if self._source == "popular":
            self._popular_left = max(0, self._popular_left - 1)
        self._update_count()
        if self.queue.count():
            self.queue.setCurrentRow(min(max(row, 0), self.queue.count() - 1))
            self._show_word(self.queue.currentItem().data(ROLE))
        else:
            self._show_word(None)

    def skip(self):
        self._replacing.pop(self._word, None)
        self._next()

    # The word card -------------------------------------------------------

    def _show_word(self, word):
        self._word = word
        self._facts = None  # the old word's facts must not be drawn for this one
        self._clear_outline()
        self.note.setText("")
        self.word_label.setText(word or "")
        for w in (self.uk_label, self.us_label, self.russian_label, self.syllables_label):
            w.setText("")
        self.uk_play.setEnabled(False)
        self.us_play.setEnabled(False)
        if not word:
            self.facts.setText("")
            self.clash_box.hide()
            return
        self._pick_target(word)
        self.syllables_label.setText("Syllables: " + syllables.show(word))
        self.uk_label.setText("UK …")
        self._want_pron(word)
        self._show_meaning(self.meaning_button.isChecked())
        self._update_facts()
        self.add.strokes.setFocus()

    def _want_pron(self, word):
        info = self._pron.get(word)
        if info is None:
            self._pron[word] = self._pool.submit(cambridge.lookup, word)
        self._poll.start()
        self._check_pron()

    def _check_pron(self):
        word = self._word
        info = self._pron.get(word)
        if info is None:
            self._poll.stop()
            return
        if isinstance(info, concurrent.futures.Future):
            if not info.done():
                return
            try:
                info = info.result()
            except Exception as exc:
                info = {"word": word, "error": str(exc)}
            self._pron[word] = info
        self._poll.stop()
        self._set_pron(info)

    def _set_pron(self, info):
        uk, us = info.get("uk") or {}, info.get("us") or {}
        self.uk_label.setText(f"UK /{uk['ipa']}/" if uk.get("ipa") else "UK —")
        self.us_label.setText(f"US /{us['ipa']}/" if us.get("ipa") else "US —")
        self.uk_play.setEnabled(bool((uk.get("files") or {})))
        self.us_play.setEnabled(bool((us.get("files") or {})))
        if uk.get("ipa"):
            self.russian_label.setText(russian.html_from_ipa(uk["ipa"]))
        if info.get("error") and not (uk or us):
            self.uk_label.setText("No pronunciation: " + info["error"])
        if self.meaning_button.isChecked():
            self._show_meaning(True)

    def play(self, region):
        info = self._pron.get(self._word)
        if isinstance(info, dict):
            files = (info.get(region) or {}).get("files") or {}
            for path in files.values():
                if cambridge.play(path):
                    return

    def _show_meaning(self, on):
        self.meaning_button.setText("Hide meaning" if on else "Show meaning")
        self.meaning_label.setVisible(on)
        if not on or not self._word:
            return
        parts = []
        info = self._pron.get(self._word)
        defs = info.get("defs") if isinstance(info, dict) else None
        if defs:
            for pos, senses in defs:
                lines = "".join(
                    f"<li>{esc(d)}" + (f" <i style='color:#8a8d93'>{esc(ex)}</i>" if ex else "") + "</li>"
                    for d, ex in senses)
                parts.append(f"<b>{esc(pos)}</b><ul style='margin:0'>{lines}</ul>")
        elif isinstance(info, concurrent.futures.Future):
            parts.append("<span style='color:#8a8d93'>English: loading from Cambridge…</span>")
        else:
            parts.append("<span style='color:#8a8d93'>English: Cambridge has no definition.</span>")
        found = meaning.lookup(self._word)
        ru = found.get("ru") or found.get("base_ru") if found else None
        if ru:
            parts.append("<b>Русский</b><br>" + esc(meaning.russian_short(ru, limit=4)))
        url = esc(cambridge.page_url(self._word))
        parts.append(f"<a href='{url}'>Open in the Cambridge Dictionary</a>")
        self.meaning_label.setText("<br>".join(parts))

    # Steno facts ----------------------------------------------------------

    def _outline_in_field(self):
        """The outline written in the field, or () if empty or not steno."""
        try:
            return steno.parse(self.add.strokes.text())
        except ValueError:
            return ()

    def _clear_outline(self):
        """Empty the Outline field, and let Plover start a new outline there
        (otherwise its next stroke comes with a "/" in front)."""
        self.add.strokes.clear()
        try:
            if self.add._focus == "strokes":
                with self._engine as engine:
                    engine.clear_translator_state()
                    engine.starting_stroke_state = self.add._strokes_state.starting_stroke
        except Exception:
            pass

    def _on_strokes(self, text):
        if text.startswith("/"):
            self.add.strokes.setText(text.lstrip("/"))  # never a "/" in front
            return
        # Your steno Enter stroke at the end of the outline saves it.
        parts = [p for p in text.split("/") if p]
        if parts and parts[-1] in ENTER_STROKES:
            self.add.strokes.setText("/".join(parts[:-1]))
            QTimer.singleShot(0, self.save)
            return
        self._draw_facts()    # a matching idea or Lapwing outline turns green
        self._update_clash()  # nothing is looked up again for the word itself

    def _update_facts(self):
        """Redo the facts once, after the current burst of changes."""
        if not self._facts_due:
            self._facts_due = True
            QTimer.singleShot(0, self._update_facts_now)

    def _update_facts_now(self):
        """Look the word up again (slow part), then draw it."""
        self._facts_due = False
        word = self._word
        if not word:
            self._facts = None
            self.facts.setText("")
            self.clash_box.hide()
            return
        d = self.dicts
        # Kept until the word or the dictionaries change: drawing it again
        # for every stroke you write must not look anything up.
        self._facts = (steno.outlines_for(d, word), steno.lapwing(word, limit=5),
                       steno.suggestions(d, word))
        self._draw_facts()
        self._update_clash()

    def _draw_facts(self):
        """The facts lines. An outline that is the one in the Outline field
        turns green with a tick; while you are part-way through a longer
        one, the strokes you have written so far turn green."""
        if not getattr(self, "_facts", None):
            return
        mine, lap, ideas = self._facts
        typed = self._outline_in_field()

        def link(outline, tip=""):
            o = esc(steno.text(outline))
            same = bool(typed) and tuple(outline) == typed
            style = f" style='color:{steno.GREEN}'" if same else ""
            title = f" title='{esc(tip)}'" if tip else ""
            return f"<a href='{o}'{title}{style}>{steno.match_html(outline, typed)}</a>"

        lines = []
        if mine:
            lines.append("You write it: " + ", ".join(link(o) for o, _p in mine))
        else:
            lines.append("<span style='color:#8a8d93'>Not in your dictionaries yet.</span>")
        if lap:
            lines.append("Lapwing: " + ", ".join(steno.match_html(o, typed) for o in lap))
        if ideas:
            shown = []
            for idea in ideas:
                if idea.taken is None:
                    shown.append(link(idea.outline, idea.why))
                else:
                    shown.append(f"<span style='color:#8a8d93' title='{esc(idea.why)}'>"
                                 f"{steno.match_html(idea.outline, typed)} ({esc(idea.taken)})</span>")
            lines.append("Ideas: " + " · ".join(shown))
        if typed and self._word:
            known = ([("yours already", o) for o, _p in mine] + [("as in Lapwing", o) for o in lap]
                     + [(i.why, i.outline) for i in ideas])
            hit = [why for why, o in known if tuple(o) == typed]
            if hit:
                lines.append(f"<span style='color:{steno.GREEN}'>✓ {esc(steno.text(typed))}: "
                             f"{esc(hit[0])}</span>")
        self.facts.setText("<br>".join(lines))

    def use_outline(self, outline_text):
        self.add.strokes.setText(outline_text)
        self.add.strokes.setFocus()

    def _update_clash(self):
        outline = self._outline_in_field()
        c = steno.clash(self.dicts, outline, self._word) if outline and self._word else None
        self._clash = c
        if not c:
            self.clash_box.hide()
            return
        word, other = self._word, c.other
        o = steno.text(outline)
        self.clash_title.setText(f"Clash: {o} already writes “{other}”")

        def facts(w, without):
            r = words.rank(w)
            have = [steno.text(x) for x, _p in steno.outlines_for(self.dicts, w) if x != without]
            bits = [f"#{r:,} in English" if r else "rare"]
            bits.append("its other outlines: " + ", ".join(have[:3]) if have else "no other outline")
            return " · ".join(bits)

        self.clash_text.setText(
            f"<b>{esc(word)}</b>: {esc(facts(word, outline))}<br>"
            f"<b>{esc(other)}</b>: {esc(facts(other, outline))}")
        others_left = [x for x, _p in steno.outlines_for(self.dicts, other) if x != outline]
        take = self.clash_buttons["take"]
        take.setText(f"Alt+1   Take it" + (f"  ·  “{other}” keeps {steno.text(others_left[0])}"
                                           if others_left else f"  ·  write “{other}” again later"))
        self._move_to = steno.free_outline(self.dicts, other, avoid=[outline]) if not others_left else None
        move = self.clash_buttons["move"]
        move.setVisible(bool(self._move_to))
        if self._move_to:
            move.setText(f"Alt+2   Take it  ·  “{other}” moves to {steno.text(self._move_to)}")
        mine = [x for x, _p in steno.outlines_for(self.dicts, word) if x != outline]
        swap = self.clash_buttons["swap"]
        swap.setVisible(bool(mine))
        if mine:
            swap.setText(f"Alt+3   Swap  ·  “{other}” gets {steno.text(mine[0])}")
        self.clash_buttons["keep"].setText(f"Alt+4   Keep it for “{other}”, try another outline")
        self.clash_box.show()

    # Saving ---------------------------------------------------------------

    def save(self):
        """Enter: save the outline. In a clash, Enter means Take it."""
        self._update_clash()
        if self._clash:
            self.resolve("take")
            return
        word, outline, path = self._word, self._outline_in_field(), self.target.currentData()
        if not (word and outline and path):
            return
        self._apply(steno.plan_save(path, outline, word), word, outline)

    def resolve(self, how):
        if self._facts_due:
            self._update_clash()
        c, word, path = self._clash, self._word, self.target.currentData()
        if not c or not word or not path:
            return
        outline = c.outline
        if how == "keep":
            self._clear_outline()
            self.note.setText(f"Kept {steno.text(outline)} for “{c.other}”. Write another outline.")
            self.add.strokes.setFocus()
            return
        if how == "move" and self._move_to:
            plan = steno.plan_move(self.dicts, path, outline, word, self._move_to)
        elif how == "swap":
            plan = steno.plan_swap(self.dicts, path, outline, word)
            if plan is None:
                return
        else:
            plan = steno.plan_take(self.dicts, path, outline, word)
        lost = c.other
        self._apply(plan, word, outline, clash_with=lost)

    def _apply(self, plan, word, outline, clash_with=None):
        """Save the plan as one undo step, then check it really worked."""
        rep = self._replacing.pop(word, None)
        if rep and rep[1] != outline:
            plan = plan + [(rep[0], rep[1], None)]  # the old outline it replaces
        done = self.panel.apply_changes(plan)
        now, _p = steno.writes(self.dicts, outline)
        if now != word:
            self.note.setObjectName("warn")
            self.note.setStyleSheet("")
            self.note.setText(f"Could not save: {steno.text(outline)} still writes “{now}”. "
                              "Is the dictionary read-only, or lower in the list?")
            return
        if self.note.objectName() != "note":
            self.note.setObjectName("note")
            self.note.setStyleSheet("")  # back to green (it stayed amber after a failed save)
        self._last_saved = (word, steno.text(outline), done)
        self.redo_last_button.setEnabled(True)
        self.redo_last_button.setText(f"Redo “{word}”")
        message = f"Saved {steno.text(outline)} → “{word}”."
        if clash_with and not steno.outlines_for(self.dicts, clash_with):
            # The old word has no outline left: it comes up next, marked ⚡.
            if self._source == "popular":
                self._mine = [clash_with] + [w for w in getattr(self, "_mine", []) if w != clash_with]
            self._queue_word(clash_with, mark="!", top=False)
            self.queue.insertItem(self.queue.currentRow() + 1, self.queue.takeItem(self.queue.count() - 1))
            message += f" “{clash_with}” needs a new outline: it's next."
        elif clash_with:
            moved = [steno.text(o) for o, _p in steno.outlines_for(self.dicts, clash_with)]
            message += f" “{clash_with}” is now {', '.join(moved)}."
        self._next()
        self.note.setText("")
        self._add_history(message)
        if self.practice.back_after == word:
            # Opened from a book in Practice: back to your place in it.
            self.practice.back_after = None
            self.tabs.setCurrentWidget(self.practice)

    # Window state ----------------------------------------------------------

    def _save_state(self, settings):
        self.panel.save_settings(settings)
        settings.setValue("dotterel_zoom", self.zoom)

    def _restore_state(self, settings):
        self.panel.restore_settings(settings)
        try:
            self.set_zoom(float(settings.value("dotterel_zoom", 1.0)))
        except (TypeError, ValueError):
            pass

    def set_zoom(self, zoom):
        """Every text in the window, bigger or smaller (70% to 250%)."""
        from .practice import STYLE as PRACTICE_STYLE, scale_css
        self.zoom = z = round(min(max(zoom, 0.7), 2.5), 2)
        self.zoom_label.setText(f"{z * 100:.0f}%")
        f = self.font()
        f.setPointSizeF(self._base_pt * z)
        self.setFont(f)
        self.setStyleSheet(scale_css(STYLE, z) + f"QWidget {{ font-size: {self._base_pt * z:.1f}pt; }}"
                           if z != 1.0 else STYLE)
        self.practice.zoom = z
        self.practice.setStyleSheet(scale_css(PRACTICE_STYLE, z))
        self.stats.widget().setStyleSheet(scale_css(PRACTICE_STYLE, z))
        for t in [self.panel.table] + list(self.stats.tables.values()) + [self.stats.recent]:
            t.verticalHeader().setDefaultSectionSize(int(26 * z))
        self.practice._render()

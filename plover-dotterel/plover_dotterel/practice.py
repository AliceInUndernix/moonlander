"""Practice and Stats: the Builder's two other tabs.

Practice  a typing test like Monkeytype. You write into your own field
          (exactly: capitals, punctuation, spaces); the text above shows
          what's right, what's wrong and where you are. Words from your
          dictionaries (mainly), a time limit, or a book (EPUB) that
          remembers where you stopped.
Stats     your tests (bests, a chart, the last tests) and your stroke log:
          what you undo, what you write instead, misstrokes, words you
          fingerspell, delete or pause before.

The look comes from the window's colours (Plover's, or the dark theme), so
it matches the rest of Plover.
"""

import bisect
import html
import json
import os
import random
import re
import time
from collections import Counter
from datetime import datetime, timedelta

from . import epub, logstats, meaning, steno, tips, typetest, words
from ._qt import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPointF,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    Qt,
    QTimer,
    QTextBrowser,
    QTextCursor,
    QVBoxLayout,
    QWidget,
    QColor,
    QHeaderView,
    QAbstractItemView,
)

WRONG = "#e06c6c"     # a wrong letter
EXTRA = "#a8484f"     # letters past the end of a word
DIM = "#8a8d93"       # words still to write, small labels (as in the Builder)
WORD_RX = re.compile(r"^[A-Za-z][A-Za-z']*$")

# Steno is about writing long, so tests are long: no time limits.
MODES = ("words", "book")
LENGTHS = {"words": (50, 100, 200), "book": ()}  # a book has no length: it just goes on
BOOK_AHEAD = 300  # words of the book loaded ahead of you


def length_name(mode, n, unit=None):
    """'50 words', '3 paragraphs' (old book tests counted words)."""
    if mode == "book" and unit == "paragraphs":
        return f"{n} paragraph" + ("" if n == 1 else "s")
    return f"{n} words"
BOOKS_DIR = os.path.expanduser("~/Dotterel books")  # what you wrote of each book
SOURCES = (("top200", "Your 200 most common words"), ("top1000", "Your 1,000 most common words"),
           ("all", "All your words"), ("missed", "Words you missed in tests"))
PERIODS = (("today", "Today"), ("week", "Last 7 days"), ("month", "Last 30 days"), ("all", "All time"))

STYLE = """
QPushButton#mode { border: none; padding: 3px 10px; color: %(dim)s; background: transparent; }
QPushButton#mode:checked { color: palette(highlight); background: transparent; font-weight: 600; }
QPushButton#mode:hover { color: palette(window-text); }
QLabel#counter { font-size: 20pt; color: palette(highlight); font-weight: 600; }
QTextBrowser#drilltext { font-size: 17pt; background: transparent; border: none; }
QLineEdit#input { font-size: 13pt; padding: 6px; }
QLabel#big { font-size: 40pt; color: palette(highlight); font-weight: 600; }
QLabel#bigname { font-size: 15pt; color: %(dim)s; }
QLabel#small { color: %(dim)s; }
QLabel#value { font-size: 15pt; color: palette(highlight); }
QLabel#booktitle { color: %(dim)s; font-size: 11pt; }
QLabel#section { font-size: 14pt; font-weight: 600; }
QLabel#tips { font-size: 13pt; }
""" % {"dim": DIM}


def scale_css(css, zoom):
    """Every 'NNpt' in a style sheet, times zoom."""
    return re.sub(r"(\d+(?:\.\d+)?)pt", lambda m: f"{float(m.group(1)) * zoom:.1f}pt", css)


def esc(text):
    return html.escape(str(text), quote=True)


def bare_word(token, sentence_start=False, dicts=None):
    """The word to give an outline, from a word of the text as it stands.

    '"Well,"' -> Well, "locker—for" -> locker, "suit's" -> suit (but "it's"
    stays), and "The" at the start of a sentence -> the (but "London" stays).
    """
    text = token.replace("\u2019", "'")
    parts = [x for x in re.split(r"\u2014|\u2013|\.\.\.|\u2026|/", text) if re.search(r"[A-Za-z0-9]", x)]
    if not parts:
        return token
    m = re.search(r"[A-Za-z0-9](?:.*[A-Za-z0-9])?", parts[0])
    core = m.group(0)
    rows = meaning._rows()

    def known(w):  # in the meanings dictionary, or in your dictionaries
        return w in rows or bool(dicts is not None and steno.outlines_for(dicts, w))

    if re.search(r"'s$", core, re.I) and len(core) > 3 and not known(core) and not known(core.lower()):
        core = core[:-2]  # Julie's -> Julie: Plover adds the 's
    # A capital only because a sentence starts there: the dictionaries say
    # whether the word is a name (London, in them with its capital) or not.
    if sentence_start and core[:1].isupper() and core[1:].islower() and not known(core) \
            and known(core.lower()):
        core = core.lower()  # Plover makes the capital after . ! ?
    return core


class DrillText(QTextBrowser):
    """The text to write. It never moves under you: the whole test is laid
    out once per change, and it scrolls a whole line at a time, so the line
    you're on is always the second one (like Monkeytype)."""

    def __init__(self):
        super().__init__()
        self._html = ""
        self.spans = []          # (first letter, word index) of each word drawn
        self.on_click = None     # called with the word index you click
        self.setReadOnly(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def text(self):
        return self._html

    def setText(self, html_, caret=None):
        """caret: where you are, in letters from the start of the text."""
        bar = self.verticalScrollBar()
        self.viewport().setUpdatesEnabled(False)
        if html_ != self._html:
            self._html = html_
            self.setHtml(html_)
            self.document().setDocumentMargin(0)  # lines start at 0: whole lines scroll
        if caret is None:
            bar.setValue(0)
        else:
            doc = self.document()
            pos = min(caret, doc.characterCount() - 1)
            block = doc.findBlock(pos)
            layout = block.layout()
            line = layout.lineForTextPosition(pos - block.position())
            block_top = doc.documentLayout().blockBoundingRect(block).top()
            if line.isValid() and line.lineNumber() > 0:
                # The line before yours is the first one you see.
                top = block_top + layout.lineAt(line.lineNumber() - 1).y()
            else:
                top = block_top + (line.y() if line.isValid() else 0) - doc.documentMargin()
            bar.setValue(max(0, int(top)))
        self.viewport().setUpdatesEnabled(True)

    def mousePressEvent(self, event):
        if self.on_click and self.spans:
            p = event.position().toPoint() if hasattr(event, "position") else event.pos()
            at = self.cursorForPosition(p).position()
            k = bisect.bisect_right([a for a, _i in self.spans], at) - 1
            if k >= 0:
                self.on_click(self.spans[k][1])
        event.accept()

    def wheelEvent(self, event):
        event.ignore()  # the text scrolls itself


# Saved results and books -------------------------------------------------

class Store:
    """CONFIG_DIR/dotterel_practice.json: tests and your place in each book."""

    def __init__(self, path=None):
        if path is None:
            from plover.oslayer.config import CONFIG_DIR
            path = os.path.join(CONFIG_DIR, "dotterel_practice.json")
        self.path = path
        try:
            with open(path, encoding="utf-8") as f:
                self.data = json.load(f)
        except (OSError, ValueError):
            self.data = {}
        self.data.setdefault("tests", [])
        self.data.setdefault("books", {})
        self.data.setdefault("last_book", None)

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)  # never a half-written file

    @property
    def tests(self):
        return self.data["tests"]

    def book(self, book_id):
        return self.data["books"].get(book_id)


# A chart (the result's, and the history's) ---------------------------------

class Chart(QWidget):
    """Lines like Monkeytype's: main line in the highlight colour, a second
    one grey, red crosses for errors (their own scale, on the right)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []  # (x, main, second, errors)
        self.names = ("wpm", "raw", "errors")
        self.setMinimumHeight(170)

    def set_points(self, points, names=None):
        self.points = list(points)
        if names:
            self.names = names
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = self.palette()
        text = pal.color(QPalette.ColorRole.WindowText)
        grid = QColor(text)
        grid.setAlpha(35)
        hi = pal.color(QPalette.ColorRole.Highlight)
        dim = QColor(DIM)
        left, right, top, bottom = 38, 34, 10, 22
        w, h = self.width() - left - right, self.height() - top - bottom
        if w <= 10 or h <= 10:
            return
        pts = self.points
        top_value = max([max(pt[1], pt[2]) for pt in pts] + [10])
        top_value = (int(top_value / 10) + 1) * 10
        top_err = max([pt[3] for pt in pts] + [1])
        p.setPen(QPen(grid, 1))
        small = p.font()
        small.setPointSizeF(max(small.pointSizeF() * 0.8, 7))
        p.setFont(small)
        for i in range(5):
            y = top + h - h * i / 4
            p.drawLine(QPointF(left, y), QPointF(left + w, y))
            p.setPen(dim)
            p.drawText(QPointF(4, y + 4), str(round(top_value * i / 4)))
            p.setPen(QPen(grid, 1))
        if not pts:
            return
        xs = [pt[0] for pt in pts]
        x0, x1 = min(xs), max(xs)

        def px(x):
            return left + (w * (x - x0) / (x1 - x0) if x1 > x0 else w / 2)

        def py(v):
            return top + h - h * v / top_value

        p.setPen(dim)
        for x in sorted({x0, x1, xs[len(xs) // 2]}):
            p.drawText(QPointF(px(x) - 6, top + h + 16), str(x))
        for idx, colour, width in ((2, dim, 1.5), (1, hi, 2.5)):
            path = QPainterPath()
            for i, pt in enumerate(pts):
                (path.moveTo if i == 0 else path.lineTo)(QPointF(px(pt[0]), py(pt[idx])))
            p.setPen(QPen(colour, width))
            p.drawPath(path)
        p.setPen(QPen(QColor(WRONG), 1.6))
        for pt in pts:
            if pt[3]:
                x, y = px(pt[0]), top + h - h * pt[3] / top_err * 0.9
                p.drawLine(QPointF(x - 3, y - 3), QPointF(x + 3, y + 3))
                p.drawLine(QPointF(x - 3, y + 3), QPointF(x + 3, y - 3))
        # Legend, top right.
        x = left + w
        for name, colour in ((self.names[2], QColor(WRONG)), (self.names[1], dim), (self.names[0], hi)):
            if not name:
                continue
            width = p.fontMetrics().horizontalAdvance(name)
            x -= width + 18
            p.setPen(QPen(colour, 2))
            p.drawLine(QPointF(x, top + 6), QPointF(x + 10, top + 6))
            p.setPen(text)
            p.drawText(QPointF(x + 13, top + 10), name)


def _table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().setVisible(False)
    t.setShowGrid(False)
    t.setAlternatingRowColors(True)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    t.horizontalHeader().setStretchLastSection(True)
    t.verticalHeader().setDefaultSectionSize(24)
    t.setMinimumHeight(150)
    return t


def _fill(table, rows):
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            if isinstance(value, (int, float)):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(r, c, item)


def _tile(name):
    box = QVBoxLayout()
    value = QLabel("–")
    value.setObjectName("value")
    label = QLabel(name)
    label.setObjectName("small")
    box.addWidget(label)
    box.addWidget(value)
    return box, value


def _fmt_time(seconds):
    seconds = int(seconds)
    h, m = divmod(seconds // 60, 60)
    return f"{h}:{m:02d}:{seconds % 60:02d}" if h else f"{m}:{seconds % 60:02d}"


# Practice ------------------------------------------------------------------

class PracticeTab(QWidget):
    """The typing test."""

    def __init__(self, builder, store):
        super().__init__()
        self.b = builder
        self.store = store
        self.setStyleSheet(STYLE)
        self.mode = "words"
        self.length = {"words": 50, "book": 0}
        self.zoom = 1.0
        self._tips = None
        self.source = "top200"
        self.test = None
        self._last_words = None
        self._book = None        # {'title', 'chapters', 'id', 'words', 'starts', 'path'}
        self._book_start = 0     # where the current book test starts
        self._saved_words = 0    # book test: words already kept
        self.back_after = None   # the word whose outline you went to write
        self._book_map = []      # book test: the book index of each of its words
        self._last_result = None

        v = QVBoxLayout(self)
        v.setContentsMargins(24, 12, 24, 12)

        # Settings bar: mode | length | words or book.
        bar = QHBoxLayout()
        bar.addStretch()
        self.mode_buttons = {}
        for m in MODES:
            btn = self._mode_button(m)
            btn.clicked.connect(lambda _c=False, x=m: self.set_mode(x))
            self.mode_buttons[m] = btn
            bar.addWidget(btn)
        bar.addWidget(self._divider())
        self.length_buttons = []
        for i in range(4):
            btn = self._mode_button("")
            btn.clicked.connect(lambda _c=False, k=i: self.set_length(LENGTHS[self.mode][k])
                                if k < len(LENGTHS[self.mode]) else None)
            self.length_buttons.append(btn)
            bar.addWidget(btn)
        self.unit_label = QLabel("words")
        self.unit_label.setObjectName("small")
        bar.addWidget(self.unit_label)
        bar.addWidget(self._divider())
        self.source_box = QComboBox()
        for key, name in SOURCES:
            self.source_box.addItem(name, key)
        self.source_box.currentIndexChanged.connect(self._on_source)
        bar.addWidget(self.source_box)
        self.open_button = QPushButton("Open EPUB…")
        self.open_button.clicked.connect(self.open_book)
        bar.addWidget(self.open_button)
        self.chapter_box = QComboBox()
        self.chapter_box.setMaximumWidth(260)
        self.chapter_box.activated.connect(self._on_chapter)
        bar.addWidget(self.chapter_box)
        bar.addWidget(self._divider())
        self.tips_button = self._mode_button("tips")
        self.tips_button.toggled.connect(lambda _on: self._render())
        bar.addWidget(self.tips_button)
        bar.addStretch()
        v.addLayout(bar)

        self.book_label = QLabel("")
        self.book_label.setObjectName("booktitle")
        self.book_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.book_label)
        nav = QHBoxLayout()
        nav.addStretch()
        self.nav = {}
        for key, text in (("prev_chapter", "Previous chapter"), ("back_para", "Back a paragraph"),
                          ("next_para", "Skip a paragraph"), ("next_chapter", "Next chapter"),
                          ("skip_chapter", "Always skip this chapter"),
                          ("outline_word", "Outline for this word")):
            b = QPushButton(text)
            nav.addWidget(b)
            self.nav[key] = b
        self.nav["skip_chapter"].setCheckable(True)
        self.nav["prev_chapter"].clicked.connect(lambda: self.move_chapter(-1))
        self.nav["next_chapter"].clicked.connect(lambda: self.move_chapter(1))
        self.nav["back_para"].clicked.connect(lambda: self.move_paragraph(-1))
        self.nav["next_para"].clicked.connect(lambda: self.move_paragraph(1))
        self.nav["skip_chapter"].clicked.connect(self.toggle_skip_chapter)
        self.nav["outline_word"].clicked.connect(self.outline_current_word)
        nav.addStretch()
        self.nav_box = QWidget()
        self.nav_box.setLayout(nav)
        v.addWidget(self.nav_box)
        v.addSpacing(12)

        # The test.
        self.test_box = QWidget()
        tv = QVBoxLayout(self.test_box)
        tv.setContentsMargins(0, 0, 0, 0)
        self.counter = QLabel("")
        self.counter.setObjectName("counter")
        tv.addWidget(self.counter)
        self.text = DrillText()
        self.text.setObjectName("drilltext")
        self.text.on_click = self.outline_word_at
        self.text.setToolTip("Click a word to give it an outline (or Alt+D for the word you're at)")
        self.text.setMinimumHeight(170)
        tv.addWidget(self.text, 1)
        self.tips_label = QLabel("")
        self.tips_label.setObjectName("tips")
        self.tips_label.setTextFormat(Qt.TextFormat.RichText)
        self.tips_label.setWordWrap(False)
        self.tips_label.hide()
        tv.addWidget(self.tips_label)
        tv.addSpacing(10)
        self.input = QLineEdit()
        self.input.setObjectName("input")
        self.input.setPlaceholderText("Write here: click, or Alt+I")
        self.input.textChanged.connect(self._on_typed)
        tv.addWidget(self.input)
        self.hint = QLabel("")
        self.hint.setObjectName("small")
        self.hint.hide()  # only for a problem, such as a book that can't be read
        tv.addWidget(self.hint)
        v.addWidget(self.test_box, 1)

        # The result.
        self.result_box = QWidget()
        self._build_result(self.result_box)
        self.result_box.hide()
        v.addWidget(self.result_box, 1)
        row = QHBoxLayout()
        row.addStretch()
        self.new_button = QPushButton("New test")
        self.new_button.clicked.connect(self.new_or_stop)
        self.repeat_button = QPushButton("Repeat")
        self.repeat_button.clicked.connect(self.repeat)
        self.missed_button = QPushButton("Practise missed words")
        self.missed_button.clicked.connect(self.practise_missed)
        self.missed_button.setEnabled(False)
        for w in (self.new_button, self.repeat_button, self.missed_button):
            row.addWidget(w)
        row.addStretch()
        v.addLayout(row)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick)
        self._restore_book()
        self.set_mode("words", start=False)

    def _mode_button(self, text):
        b = QPushButton(text)
        b.setObjectName("mode")
        b.setCheckable(True)
        b.setFlat(True)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        return b

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFixedHeight(18)
        return line

    def _build_result(self, box):
        g = QVBoxLayout(box)
        g.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        left = QVBoxLayout()
        self.big = {}
        for name in ("wpm", "acc"):
            label = QLabel(name)
            label.setObjectName("bigname")
            value = QLabel("–")
            value.setObjectName("big")
            left.addWidget(label)
            left.addWidget(value)
            self.big[name] = value
        left.addStretch()
        top.addLayout(left)
        self.chart = Chart()
        top.addWidget(self.chart, 1)
        g.addLayout(top)
        row = QHBoxLayout()
        self.small = {}
        for name in ("test type", "raw", "characters", "consistency", "time",
                     "strokes", "strokes / word", "undos (*)"):
            box_, value = _tile(name)
            self.small[name] = value
            row.addLayout(box_)
            row.addStretch()
        g.addLayout(row)
        g.addSpacing(8)
        self.missed_label = QLabel("")
        self.missed_label.setWordWrap(True)
        self.missed_label.setTextFormat(Qt.TextFormat.RichText)
        self.missed_label.linkActivated.connect(self._open_word)
        g.addWidget(self.missed_label)

    def make_shortcuts(self, hints, window):
        h = hints
        h.add(window, self.mode_buttons["words"], "Words: your words, 50, 100 or 200 of them", "Alt+5",
              lambda: self._go(lambda: self.set_mode("words")))
        h.add(window, self.mode_buttons["book"], "Book: your EPUB from where you stopped, 1, 3, 5 or 10 paragraphs",
              "Alt+6", lambda: self._go(lambda: self.set_mode("book")))
        first = self.length_buttons[0]
        h.add(window, None, "Length: the next one", "Alt+7", self._next_length)
        for b in self.length_buttons:
            h.add(window, b, "Length: the next one", "Alt+7")
        h.add(window, self.source_box, "Which words: the next list", "Alt+8",
              lambda: self._go(lambda: self.source_box.setCurrentIndex(
                  (self.source_box.currentIndex() + 1) % self.source_box.count())))
        h.add(window, self.tips_button, "Tips: show the shortest outline for each word", "Alt+T",
              lambda: self._go(self.tips_button.toggle))
        h.add(window, self.open_button, "Open an EPUB book", "Alt+E", lambda: self._go(self.open_book))
        h.add(window, self.chapter_box, "Chapters: open the list", "Alt+K",
              lambda: self._go(lambda: self._book and self.chapter_box.showPopup()))
        for key, action, keys, slot in (
                ("prev_chapter", "Previous chapter", "Alt+PgUp", lambda: self.move_chapter(-1)),
                ("next_chapter", "Next chapter", "Alt+PgDown", lambda: self.move_chapter(1)),
                ("back_para", "Back a paragraph", "Alt+Up", lambda: self.move_paragraph(-1)),
                ("next_para", "Skip a paragraph", "Alt+Down", lambda: self.move_paragraph(1)),
                ("skip_chapter", "Always skip this chapter (contents, notes...): "
                 "the book goes past it from now on; press again to take it back", "Alt+Del",
                 self.toggle_skip_chapter),
                ("outline_word", "Outline for this word: write it in Add words; "
                 "after you save it you come back to the same place", "Alt+D",
                 self.outline_current_word)):
            h.add(window, self.nav[key], action, keys,
                  lambda f=slot: self._go(lambda: self.mode == "book" and f()))
        h.add(window, self.input, "Write here", "Alt+I", lambda: self._go(self.focus_input))
        h.add(window, self.new_button, "New test (in a book: stop and see how you did)", "Alt+N", lambda: self._go(self.new_or_stop))
        h.add(window, self.repeat_button, "Repeat the same text", "Alt+R", lambda: self._go(self.repeat))
        h.add(window, self.missed_button, "Practise the words you just missed", "Alt+X",
              lambda: self._go(self.practise_missed))
        del first

    def _go(self, action):
        """Shortcuts of this tab open it first."""
        self.b.tabs.setCurrentWidget(self)
        action()

    # Settings -------------------------------------------------------------

    def set_mode(self, mode, start=True):
        self._abandon()
        self.mode = mode
        for m, btn in self.mode_buttons.items():
            btn.setChecked(m == mode)
        for i, btn in enumerate(self.length_buttons):
            n = LENGTHS[mode][i] if i < len(LENGTHS[mode]) else None
            btn.setVisible(n is not None)
            if n is not None:
                btn.setText(str(n))
                btn.setChecked(n == self.length[mode])
        book = mode == "book"
        self.unit_label.setVisible(not book)
        self.source_box.setVisible(not book)
        self.open_button.setVisible(book)
        self.chapter_box.setVisible(book and self._book is not None)
        self.nav_box.setVisible(book and self._book is not None)
        self._show_book_label()
        if start:
            self.new_test()

    def set_length(self, n):
        self._abandon()
        self.length[self.mode] = n
        for btn, x in zip(self.length_buttons, LENGTHS[self.mode]):
            btn.setChecked(x == n)
        for btn in self.length_buttons[len(LENGTHS[self.mode]):]:
            btn.setChecked(False)
        self.new_test()

    def _next_length(self):
        self.b.tabs.setCurrentWidget(self)
        options = LENGTHS[self.mode]
        if not options:
            return
        i = options.index(self.length[self.mode]) if self.length[self.mode] in options else -1
        self.set_length(options[(i + 1) % len(options)])

    def _on_source(self, _i):
        self.source = self.source_box.currentData()
        if self.mode != "book":
            self._abandon()
            self.new_test()

    # Words ----------------------------------------------------------------

    def your_words(self):
        """Single words your dictionaries write now, most common first."""
        gen = getattr(self.b, "generation", None)
        cached = getattr(self, "_your_words", None)
        if cached and gen is not None and cached[0] == gen:
            return cached[1]
        words_ = self._find_your_words()
        self._your_words = (gen, words_)
        return words_

    def _find_your_words(self):
        # The outline table already knows which entries work (not hidden by
        # a higher dictionary): one pass over its rows.
        found = {e.translation for e in self.b.panel._entries
                 if e.writable and e.enabled and e.hidden_by is None and WORD_RX.match(e.translation or "")}
        return sorted(found, key=lambda w: (words.rank(w) or 10 ** 9, w))

    def _pick_words(self, n):
        mine = self.your_words()
        if self.source == "top200":
            pool = mine[:200]
        elif self.source == "top1000":
            pool = mine[:1000]
        elif self.source == "missed":
            counts = Counter(w for t in self.store.tests for w, _typed in t.get("missed", []))
            pool = [w for w, _c in counts.most_common(200)]
        else:
            pool = mine
        if len(pool) < 2:
            return pool
        out = []
        for _ in range(n):
            w = random.choice(pool)
            while out and w == out[-1]:
                w = random.choice(pool)
            out.append(w)
        return out

    # Books ----------------------------------------------------------------

    def open_book(self, path=None):
        if not path:
            path, _f = QFileDialog.getOpenFileName(self, "Open a book", os.path.expanduser("~"),
                                                   "EPUB books (*.epub)")
        if not path:
            return
        try:
            self._load_book(path)
        except Exception as exc:
            self.hint.setText(f"Could not read that book: {exc}")
            self.hint.show()
            return
        self.set_mode("book")

    def _load_book(self, path):
        book = epub.read(path)
        book["words"], book["starts"], book["ends"] = epub.words_of(book)
        book["path"] = path
        saved = self.store.book(book["id"]) or {"position": 0}
        saved.update({"title": book["title"], "path": path, "total": len(book["words"])})
        saved.setdefault("position", 0)
        self.store.data["books"][book["id"]] = saved
        self.store.data["last_book"] = book["id"]
        self.store.save()
        self._book = book
        self.chapter_box.clear()
        for start, title in book["starts"]:
            self.chapter_box.addItem(title[:60], start)
        self._sync_chapter()
        self._label_chapters()

    def _restore_book(self):
        book_id = self.store.data.get("last_book")
        info = self.store.book(book_id) if book_id else None
        if info and os.path.exists(info.get("path", "")):
            try:
                self._load_book(info["path"])
            except Exception:
                self._book = None

    def _position(self):
        return self.store.book(self._book["id"])["position"] if self._book else 0

    def _set_position(self, pos):
        if not self._book:
            return
        info = self.store.book(self._book["id"])
        pos = max(0, min(pos, len(self._book["words"])))
        if pos < len(self._book["words"]):
            pos = self._not_skipped(pos)
        info["position"] = pos
        info["when"] = datetime.now().isoformat(timespec="seconds")
        self.store.save()  # at once, so nothing is lost
        self._sync_chapter()
        self._show_book_label()

    # What you wrote of the book: kept word by word, and written out as a
    # plain text file in ~/Dotterel books, named after the book.

    def _typed_path(self):
        from plover.oslayer.config import CONFIG_DIR
        folder = os.path.join(CONFIG_DIR, "dotterel_books")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, self._book["id"] + ".json")

    def _load_typed(self):
        try:
            with open(self._typed_path(), encoding="utf-8") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except (OSError, ValueError):
            return {}

    def book_file(self):
        return os.path.join(BOOKS_DIR, epub.safe_name(self._book["title"])) if self._book else None

    def _save_typed(self, typed_words):
        """Your words, exactly as you wrote them, at their place in the book."""
        if not self._book or not typed_words:
            return
        typed = self._load_typed()
        for i, w in zip(self._book_map, typed_words):
            typed[i] = w
        tmp = self._typed_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in sorted(typed.items())}, f, ensure_ascii=False)
        os.replace(tmp, self._typed_path())
        self._write_book_file(typed)

    def _write_book_file(self, typed):
        book = self._book
        starts = dict(book["starts"])
        out, line = [book["title"], ""], []
        for i in sorted(typed):
            if i in starts:
                if line:
                    out.append(" ".join(line))
                    line = []
                if out[-1] != "":
                    out.append("")  # a blank line before each chapter
            line.append(typed[i])
            if i in book["ends"]:
                out.append(" ".join(line))
                line = []
        if line:
            out.append(" ".join(line))
        os.makedirs(BOOKS_DIR, exist_ok=True)
        path = self.book_file()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(out).rstrip() + "\n")
        os.replace(tmp, path)

    def _sync_chapter(self):
        if not self._book:
            return
        pos = self._position()
        idx = 0
        for i, (start, _t) in enumerate(self._book["starts"]):
            if start <= pos:
                idx = i
        self.chapter_box.blockSignals(True)
        self.chapter_box.setCurrentIndex(idx)
        self.nav["skip_chapter"].setChecked(idx in self._skipped())
        self.chapter_box.blockSignals(False)

    def _show_book_label(self):
        if self.mode != "book":
            self.book_label.setText("")
            return
        if not self._book:
            self.book_label.setText("Open an EPUB book (Alt+E). Your place in it is saved after every paragraph.")
            return
        pos, total = self._position(), len(self._book["words"])
        chapter = self.chapter_box.currentText()
        self.book_label.setText(f"{self._book['title']}  ·  {chapter}  ·  "
                                f"{100 * pos / max(total, 1):.1f}%  ·  word {pos:,} of {total:,}  ·  "
                                f"what you wrote: {self.book_file()}")

    # Chapters and paragraphs ----------------------------------------------

    def _info(self):
        return self.store.book(self._book["id"])

    def _skipped(self):
        return set(self._info().setdefault("skipped", []))

    def _chapter_of(self, pos):
        starts = [st for st, _t in self._book["starts"]]
        return max(bisect.bisect_right(starts, pos) - 1, 0)

    def _chapter_range(self, idx):
        starts = [st for st, _t in self._book["starts"]] + [len(self._book["words"])]
        return starts[idx], starts[idx + 1]

    def _not_skipped(self, pos):
        """pos, or the start of the next chapter you don't skip."""
        skipped = self._skipped()
        idx = self._chapter_of(pos)
        while idx in skipped and idx < len(self._book["starts"]):
            idx += 1
            if idx >= len(self._book["starts"]):
                return len(self._book["words"])
            pos = self._chapter_range(idx)[0]
        return pos

    def _go_to(self, pos):
        self._abandon()
        self._set_position(pos)
        self.new_test()

    def _on_chapter(self, i):
        if self._book and 0 <= i < len(self._book["starts"]):
            self._go_to(self._chapter_range(i)[0])

    def move_chapter(self, step):
        if not self._book:
            return
        self._abandon()
        skipped, n = self._skipped(), len(self._book["starts"])
        idx = self._chapter_of(self._position()) + step
        while 0 <= idx < n and idx in skipped:
            idx += step
        if 0 <= idx < n:
            self._go_to(self._chapter_range(idx)[0])
        else:
            self.new_test()  # no chapter there: go on where you were

    def outline_current_word(self):
        """Give the word you're at an outline, then come back here."""
        t = self.test
        if not t:
            return
        cur, letter = t.position()
        if cur < len(t.words) and letter >= len(t.words[cur]) and cur + 1 < len(t.words):
            cur += 1  # that word is written: the caret waits on the next one
        self.outline_word_at(cur)

    def outline_word_at(self, i):
        t = self.test
        if not t or not 0 <= i < len(t.words):
            return
        if i:
            prev = t.words[i - 1]
            start = (self.mode == "book" and self._book_map and self._book_end_after(i - 1)) \
                or prev.rstrip("\"')]").endswith((".", "!", "?"))
        elif self.mode == "book" and self._book_map and self._book_map[0]:
            prev = self._book["words"][self._book_map[0] - 1]
            start = self._book_map[0] - 1 in self._book["ends"] or prev.rstrip("\"')]").endswith((".", "!", "?"))
        else:
            start = True
        word = bare_word(t.words[i], start, self.b.dicts)
        self.back_after = word
        self.b.open_word(word)  # leaving Practice keeps your place in the book
        self.b.add.strokes.setFocus()

    def move_paragraph(self, step):
        if not self._book:
            return
        self._abandon()
        paras = sorted({0} | {e + 1 for e in self._book["ends"]})
        pos = self._position()
        i = bisect.bisect_right(paras, pos) - 1  # the paragraph you are in
        if step > 0:
            target = paras[i + 1] if i + 1 < len(paras) else len(self._book["words"])
        else:
            target = paras[i - 1] if pos == paras[i] and i > 0 else paras[i]
        self._go_to(target)

    def toggle_skip_chapter(self):
        if not self._book:
            return
        self._abandon()
        idx = self._chapter_of(self._position())
        skipped = self._skipped()
        skipped ^= {idx}
        self._info()["skipped"] = sorted(skipped)
        self.store.save()
        self._label_chapters()
        if idx in skipped:
            self._go_to(self._chapter_range(idx)[1])  # past it
        else:
            self._go_to(self._chapter_range(idx)[0])

    def _label_chapters(self):
        skipped = self._skipped()
        for i, (_start, title) in enumerate(self._book["starts"]):
            self.chapter_box.setItemText(i, ("(skipped) " if i in skipped else "") + title[:60])

    # The test -------------------------------------------------------------

    def new_test(self, words_=None):
        self._abandon()
        self._book_map = []
        n = self.length[self.mode]
        if words_ is None:
            if self.mode == "book":
                if not self._book:
                    self._show_message("Open an EPUB book first (Alt+E).")
                    return
                self._book_start = self._position()
                self._book_map = []
                words_ = self._book_more(self._book_start, BOOK_AHEAD)
                if not words_:
                    self._show_message("You have reached the end of the book. Choose a chapter to start again.")
                    return
            else:
                words_ = self._pick_words(n)
            if len(words_) < 2 and self.mode != "book":
                self._show_message(
                    "Not enough words here yet. Add words in the Add words tab, "
                    "or choose another list (Alt+9).")
                return
        self._last_words = list(words_)
        self.test = typetest.Test(words_)
        self._saved_words = 0
        self._tips = tips.Tips(self.b.dicts)
        self.result_box.hide()
        self.test_box.show()
        self.input.blockSignals(True)
        self.input.clear()
        self.input.blockSignals(False)
        self.input.setEnabled(True)
        self.hint.hide()
        self._render()
        self.focus_input()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.test and self.mode == "book":
            QTimer.singleShot(0, self._render)  # fill the new size

    def new_or_stop(self):
        """In a book you write on and on: this stops and shows how you did."""
        t = self.test
        if self.mode == "book" and t and t.end is None and t.typed.count(" ") >= 1:
            self._finish()
        else:
            self.new_test()

    def _book_more(self, start, n):
        """The next n words of the book from index start, past chapters you
        skip. Their book indices are added to self._book_map."""
        book, out = self._book, []
        chapter_starts = {st for st, _t in book["starts"]}
        i = start
        while len(out) < n and i < len(book["words"]):
            if i in chapter_starts or not out:
                i = self._not_skipped(i)
                if i >= len(book["words"]):
                    break
            out.append(book["words"][i])
            self._book_map.append(i)
            i += 1
        return out

    def _words_to_fill(self):
        """About how many words fill the text area below you (plus some)."""
        fm = self.text.fontMetrics()
        lines = self.text.viewport().height() // max(fm.lineSpacing(), 1) + 2
        per_line = self.text.viewport().width() // max(fm.averageCharWidth() * 6, 1) + 1
        return max(BOOK_AHEAD, int(lines * per_line * 1.5))

    def _book_fill(self, upto):
        """Load the book into the test up to word `upto` (if the book goes on)."""
        t = self.test
        if t and self._book_map and len(t.words) < upto:
            more = self._book_more(self._book_map[-1] + 1, upto - len(t.words) + BOOK_AHEAD)
            if more:
                t.words.extend(more)
                t.target = " ".join(t.words)

    def _book_end_after(self, j):
        """Does test word j end a paragraph (or come before a skipped part)?"""
        m = self._book_map
        return m[j] in self._book["ends"] or (j + 1 < len(m) and m[j + 1] != m[j] + 1)

    def _book_progress(self, done):
        """Keep the first `done` words you wrote, and your place after them."""
        if not self._book or done <= 0 or not self.test:
            return
        self._save_typed(self.test.typed.split(" ")[:done])
        m = self._book_map
        self._set_position(m[done] if done < len(m) else m[-1] + 1)
        self._saved_words = done

    def repeat(self):
        if self._last_words:
            if self.mode == "book" and self._book:
                start = self._book_start
                self._abandon()
                self._set_position(start)
                self.new_test()
                return
            self.new_test(list(self._last_words))

    def practise_missed(self):
        missed = [w for w, _t in (self._last_result or {}).get("missed", [])]
        if missed:
            words_ = (missed * (1 + 20 // len(missed)))[:max(10, len(missed))]
            random.shuffle(words_)
            self.new_test(words_)

    def focus_input(self):
        self.input.setFocus()
        self.input.end(False)

    def _show_message(self, text):
        self.test = None
        self.result_box.hide()
        self.test_box.show()
        self.counter.setText("")
        self.text.setText(f"<span style='color:{DIM}'>{esc(text)}</span>")
        self.input.setEnabled(False)

    def on_stroked(self, stroke):
        if self.test and self.input.hasFocus():
            from plover import system
            self.test.stroke(stroke.rtfcre if hasattr(stroke, "rtfcre") else str(stroke),
                             getattr(system, "UNDO_STROKE_STENO", "*"))

    def _on_typed(self, text):
        if not self.test:
            return
        t = self.test
        if self.mode == "book" and self._book and self._book_map:
            # Endless: more of the book comes before you get near the end.
            self._book_fill(text.lstrip(" ").count(" ") + self._words_to_fill())
        done = self.test.update(text)
        if self.mode == "book" and self._book and not done:
            # Saved after every paragraph, so nothing is lost.
            cur = len(t.typed.split(" ")) - 1
            if cur > self._saved_words and self._book_end_after(cur - 1):
                self._book_progress(cur)
        if self.test.start is not None and not self._timer.isActive():
            self._timer.start()
        if done:
            self._finish()
        else:
            self._render()

    def _tick(self):
        if not self.test or self.test.end is not None:
            self._timer.stop()
            return
        if self.test.time_up():
            self._finish()
        else:
            self._render_counter()

    def _abandon(self):
        """Leaving a test half-way: in a book, keep the words you wrote."""
        t = self.test
        if t and t.end is None and self.mode == "book" and self._book and t.typed:
            typed = t.typed.split(" ")
            done_words = len(typed) - 1
            if done_words < len(t.words) and typed[-1] == t.words[done_words]:
                done_words += 1  # the last word is written right: it counts
            if done_words > 0:
                self._book_progress(done_words)
            if done_words >= 10:  # your session counts in Stats too
                t.end = t.clock()
                self._record(t.result())
        self.test = None
        self._timer.stop()

    def _finish(self):
        t = self.test
        self._timer.stop()
        if t.end is None:  # stopped by you (Alt+N in a book)
            t.end = t.clock()
        if self.mode == "book" and self._book:
            done_words = len(t.typed.split(" ")) - (0 if t.is_done() else 1)
            self._book_progress(done_words)
        r = self._record(t.result())
        self._last_result = r
        self.test = None
        self.input.setEnabled(False)
        self._show_result(r)
        self.b.on_practice_saved()

    def _record(self, r):
        """Keep a test's result for Stats."""
        r.update({"date": datetime.now().isoformat(timespec="seconds"), "mode": self.mode,
                  "length": self.length[self.mode] if self.mode != "book" else r["words_typed"]})
        if self.mode == "book" and self._book:
            r["book"] = self._book["title"]
            r["unit"] = "session"
        else:
            r["source"] = self.source
        self.store.tests.append({k: v for k, v in r.items() if k != "chart"})
        self.store.save()
        return r

    # Drawing --------------------------------------------------------------

    def _colours(self):
        pal = self.palette()
        return (pal.color(QPalette.ColorRole.WindowText).name(),
                pal.color(QPalette.ColorRole.Highlight).name(),
                pal.color(QPalette.ColorRole.HighlightedText).name())

    def _render_counter(self):
        t = self.test
        if not t:
            return
        if t.seconds is not None:
            left = t.seconds - (t.elapsed() if t.start is not None else 0)
            self.counter.setText(str(max(0, int(left + 0.999))))
        elif self.mode == "book" and self._book_map:
            cur, _l = t.position()
            self.counter.setText(f"{cur:,}")
        else:
            cur, _l = t.position()
            self.counter.setText(f"{min(cur, len(t.words))}/{len(t.words)}")

    def _render(self):
        t = self.test
        if not t:
            return
        self._render_counter()
        text_c, hi, hi_text = self._colours()
        states = t.word_states()
        cur, letter = t.position()
        book = self.mode == "book" and self._book is not None and len(self._book_map) == len(t.words)
        if book:  # enough of the book to fill the text area to its end
            need = self._words_to_fill()
            if len(t.words) < cur + need:
                self._book_fill(cur + need)
                states = t.word_states()
        first, last = 0, len(states)
        if book:
            # Drawn from the start of the paragraph before yours: what is
            # above it is scrolled away anyway, and each paragraph starts on
            # its own line, so nothing you can see moves.
            starts_seen, j = 0, min(cur, len(states) - 1)
            while j > 0:
                if self._book_end_after(j - 1):
                    starts_seen += 1
                    if starts_seen == 2:
                        break
                j -= 1
            first, last = j, min(len(states), cur + need)
        out, caret, pos, next_caret = [], 0, 0, False
        spans = []
        for i in range(first, last):
            word, typed, state = states[i]
            spans.append((pos, i))
            sep = "<br>" if book and self._book_end_after(i) else " "
            if i == cur:
                caret = pos + min(letter, len(word))
            if state == "todo":
                if i == cur + 1 and next_caret and word:
                    # Your word is done: the caret waits on the next one.
                    out.append(f"<span style='background-color:{hi};color:{hi_text}'>{esc(word[0])}</span>"
                               f"<span style='color:{DIM}'>{esc(word[1:])}</span>" + sep)
                    caret = pos
                else:
                    out.append(f"<span style='color:{DIM}'>{esc(word)}</span>" + sep)
                pos += len(word) + 1
                continue
            if state == "done":
                out.append(f"<span style='color:{text_c}'>{esc(word)}</span>" + sep)
                pos += len(word) + 1
                continue
            bits = []
            typed = typed or ""
            for k, ch in enumerate(word):
                if k < len(typed):
                    colour = text_c if typed[k] == ch else WRONG
                    bits.append(f"<span style='color:{colour}'>{esc(ch)}</span>")
                elif state == "now" and k == letter:
                    bits.append(f"<span style='background-color:{hi};color:{hi_text}'>{esc(ch)}</span>")
                else:
                    colour = WRONG if state == "wrong" else DIM
                    bits.append(f"<span style='color:{colour}'>{esc(ch)}</span>")
            extra = typed[len(word):]
            if extra:
                bits.append(f"<span style='color:{EXTRA}'>{esc(extra)}</span>")
            word_html = "".join(bits)
            if state == "wrong":
                word_html = f"<u style='color:{WRONG}'>{word_html}</u>"
            if state == "now" and letter >= len(word):
                caret = pos + len(word) + len(extra)
                next_caret = True
            out.append(word_html + sep)
            pos += len(word) + len(extra) + 1
        html_ = "".join(out)
        self.text.setText(html_, caret)
        self.text.spans = spans
        self._render_tips(cur)

    def _render_tips(self, cur):
        on = self.tips_button.isChecked() and self.test is not None
        self.tips_label.setVisible(on)
        if not on:
            return
        t, text_c, hi = self.test, *self._colours()[:2]
        parts = []
        for i in range(cur, min(cur + 5, len(t.words))):
            token = t.words[i]
            prev = t.words[i - 1] if i else ""
            if self.mode == "book" and i == 0 and self._book_map and self._book_map[0]:
                prev = self._book["words"][self._book_map[0] - 1]
            after_stop = not prev or prev.rstrip("\"')")[-1:] in ".!?"
            steps = self._tips.for_token(token, after_stop)
            outline = " ".join(o for o, _w in steps)
            colour = hi if i == cur else DIM
            size = "" if i == cur else f"font-size:{11 * self.zoom:.1f}pt;"
            parts.append(f"<span style='{size}color:{DIM}'>{esc(token)}</span> "
                         f"<span style='{size}color:{colour};font-family:monospace'>{esc(outline)}</span>")
        self.tips_label.setText("&nbsp;&nbsp;·&nbsp;&nbsp;".join(parts))

    def _show_result(self, r):
        self.test_box.hide()
        self.result_box.show()
        self.big["wpm"].setText(f"{r['wpm']:.0f}")
        self.big["acc"].setText(f"{r['acc']:.0f}%")
        self.big["wpm"].setToolTip(f"{r['wpm']:.2f} wpm")
        self.big["acc"].setToolTip(f"{r['acc']:.2f}%")
        kind = f"{r['mode']} {r['length']}"
        right, wrong, extra, missed = r["chars"]
        self.small["test type"].setText(kind)
        self.small["raw"].setText(f"{r['raw']:.0f}")
        self.small["characters"].setText(f"{right}/{wrong}/{extra}/{missed}")
        self.small["characters"].setToolTip("right / wrong / extra / missed")
        self.small["consistency"].setText(f"{r['consistency']:.0f}%")
        self.small["time"].setText(f"{r['seconds']:.0f}s")
        self.small["strokes"].setText(str(r["strokes"]))
        per = r["strokes"] / r["words_typed"] if r["words_typed"] else 0
        self.small["strokes / word"].setText(f"{per:.2f}")
        self.small["undos (*)"].setText(str(r["undos"]))
        self.chart.set_points(r["chart"])
        self.missed_button.setEnabled(bool(r["missed"]))
        if r["missed"]:
            rows = []
            for word, typed in r["missed"][:12]:
                outlines = [steno.text(o) for o, _p in steno.outlines_for(self.b.dicts, word)]
                outline = (", ".join(outlines[:2]) if outlines
                           else "<i>no outline</i>")
                rows.append(f"<b>{esc(word)}</b> <span style='color:{DIM}'>you wrote</span> "
                            f"<span style='color:{WRONG}'>{esc(typed) or '—'}</span> "
                            f"<span style='color:{DIM}'>· your outline</span> {outline if outlines else outline} "
                            f"<a href='{esc(word)}'>open in Add words</a>")
            self.missed_label.setText("<b>Words you missed</b><br>" + "<br>".join(rows))
        else:
            self.missed_label.setText("<b>No words missed.</b>")
        self.new_button.setFocus()

    def _open_word(self, word):
        self.b.open_word(word)


# Stats ---------------------------------------------------------------------

class StatsTab(QScrollArea):
    """Your tests, and what your stroke log says about your writing."""

    def __init__(self, builder, store):
        super().__init__()
        self.b = builder
        self.store = store
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        page = QWidget()
        page.setStyleSheet(STYLE)
        self.setWidget(page)
        v = QVBoxLayout(page)
        v.setContentsMargins(20, 12, 20, 12)

        title = QLabel("Your tests")
        title.setObjectName("section")
        v.addWidget(title)
        tiles = QHBoxLayout()
        self.tiles = {}
        for name in ("tests completed", "time writing", "average wpm (last 10)",
                     "average accuracy (last 10)"):
            box, value = _tile(name)
            self.tiles[name] = value
            tiles.addLayout(box)
            tiles.addStretch()
        v.addLayout(tiles)
        bests = QHBoxLayout()
        self.best_labels = {}
        for mode in ("words", "book"):
            grid = QGridLayout()
            for c, n in enumerate(LENGTHS[mode] or ("session",)):
                head = QLabel(f"words, {n}" if mode == "words" else "book, best session")
                head.setObjectName("small")
                value = QLabel("–")
                value.setObjectName("value")
                acc = QLabel("")
                acc.setObjectName("small")
                grid.addWidget(head, 0, c)
                grid.addWidget(value, 1, c)
                grid.addWidget(acc, 2, c)
                self.best_labels[(mode, n)] = (value, acc)
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame.setLayout(grid)
            bests.addWidget(frame)
        v.addWidget(self._small("Personal bests (wpm)"))
        v.addLayout(bests)
        self.history = Chart()
        self.history.names = ("wpm", "raw", "")
        v.addWidget(self._small("Every test, oldest to newest"))
        v.addWidget(self.history)
        self.recent = _table(["Date", "Test", "wpm", "raw", "accuracy", "consistency", "missed"])
        v.addWidget(self._small("Last tests"))
        v.addWidget(self.recent)

        v.addSpacing(16)
        head = QHBoxLayout()
        title = QLabel("Your stroke log")
        title.setObjectName("section")
        head.addWidget(title)
        head.addStretch()
        self.period = QComboBox()
        for key, name in PERIODS:
            self.period.addItem(name, key)
        self.period.setCurrentIndex(1)
        self.period.currentIndexChanged.connect(self.refresh_log)
        head.addWidget(self.period)
        self.reread_button = QPushButton("Read the log again")
        self.reread_button.clicked.connect(self.refresh_log)
        head.addWidget(self.reread_button)
        self.logging_button = QPushButton("Turn on logging")
        self.logging_button.clicked.connect(self.turn_on_logging)
        head.addWidget(self.logging_button)
        v.addLayout(head)
        self.log_note = QLabel("")
        self.log_note.setObjectName("small")
        self.log_note.setWordWrap(True)
        v.addWidget(self.log_note)
        tiles = QHBoxLayout()
        for name in ("words written", "wpm while writing", "strokes per word",
                     "undo strokes (*)", "backspace strokes"):
            box, value = _tile(name)
            self.tiles[name] = value
            tiles.addLayout(box)
            tiles.addStretch()
        v.addLayout(tiles)

        grid = QGridLayout()
        self.tables = {}
        specs = (
            ("fixes", "Mistakes you fix most: what * took back, and what you wrote instead",
             ["You wrote", "outline", "then", "outline", "times"]),
            ("undone", "Outlines you undo most", ["Outline", "wrote", "times"]),
            ("untranslated", "Misstrokes: strokes with no word", ["Stroke", "times"]),
            ("fingerspelled", "Words you fingerspell (double-click: add it)", ["Word", "times"]),
            ("backspaced", "Words you delete with backspace", ["Word", "times"]),
            ("slow", "Words you pause before", ["Word", "pause", "times"]),
        )
        for i, (key, text, headers) in enumerate(specs):
            box = QVBoxLayout()
            box.addWidget(self._small(text))
            t = _table(headers)
            box.addWidget(t)
            self.tables[key] = t
            grid.addLayout(box, i // 2, i % 2)
        for key in ("fingerspelled", "backspaced", "slow"):
            self.tables[key].cellDoubleClicked.connect(
                lambda r, _c, k=key: self.b.open_word(self.tables[k].item(r, 0).text()))
        self.tables["fixes"].cellDoubleClicked.connect(
            lambda r, _c: self.b.panel.show_outline(self.tables["fixes"].item(r, 1).text()))
        v.addLayout(grid)
        v.addStretch()

    def _small(self, text):
        label = QLabel(text)
        label.setObjectName("small")
        return label

    def make_shortcuts(self, hints, window):
        h = hints
        h.add(window, self.period, "Which days of the log: the next choice", "Alt+Y",
              lambda: self._go(lambda: self.period.setCurrentIndex(
                  (self.period.currentIndex() + 1) % self.period.count())))
        h.add(window, self.reread_button, "Read the stroke log again", "Alt+U",
              lambda: self._go(self.refresh_log))
        h.add(window, self.logging_button,
              "Turn on Plover's stroke and translation logging (Configure > Logging)",
              "Alt+J", lambda: self._go(self.turn_on_logging))

    def _go(self, action):
        self.b.tabs.setCurrentWidget(self)
        action()

    # Tests ----------------------------------------------------------------

    def refresh_tests(self):
        tests = self.store.tests
        self.tiles["tests completed"].setText(f"{len(tests):,}")
        self.tiles["time writing"].setText(_fmt_time(sum(t.get("seconds", 0) for t in tests)))
        last = tests[-10:]
        if last:
            self.tiles["average wpm (last 10)"].setText(f"{sum(t['wpm'] for t in last) / len(last):.0f}")
            self.tiles["average accuracy (last 10)"].setText(
                f"{sum(t['acc'] for t in last) / len(last):.0f}%")
        for (mode, n), (value, acc) in self.best_labels.items():
            if mode == "book":  # sessions of 50 words or more
                mine = [t for t in tests if t.get("mode") == "book" and t.get("unit") == "session"
                        and t.get("words_typed", 0) >= 50]
            else:
                mine = [t for t in tests if t.get("mode") == mode and t.get("length") == n]
            if mine:
                best = max(mine, key=lambda t: t["wpm"])
                value.setText(f"{best['wpm']:.0f}")
                acc.setText(f"{best['acc']:.0f}% · {best['date'][:10]}")
            else:
                value.setText("–")
                acc.setText("")
        self.history.set_points([(i + 1, t["wpm"], t["raw"], 0) for i, t in enumerate(tests)])
        rows = []
        for t in reversed(tests[-30:]):
            kind = f"{t['mode']}, {length_name(t['mode'], t['length'], t.get('unit'))}"
            rows.append((t["date"].replace("T", " ")[:16], kind, round(t["wpm"]), round(t["raw"]),
                         f"{t['acc']:.0f}%", f"{t['consistency']:.0f}%",
                         ", ".join(w for w, _x in t.get("missed", [])[:6])))
        _fill(self.recent, rows)

    # The log --------------------------------------------------------------

    def _config(self):
        try:
            return self.b._engine.config
        except Exception:
            return {}

    def logging_on(self):
        cfg = self._config()
        try:
            return bool(cfg["enable_stroke_logging"]) and bool(cfg["enable_translation_logging"])
        except Exception:
            return False

    def turn_on_logging(self):
        try:
            self.b._engine.config = {"enable_stroke_logging": True, "enable_translation_logging": True}
        except Exception as exc:
            self.log_note.setText(f"Could not change the setting: {exc}")
            return
        self.refresh_log()

    def refresh_log(self):
        self.logging_button.setVisible(not self.logging_on())
        path = logstats.log_path(self._config())
        key = self.period.currentData()
        now = datetime.now()
        since = {"today": now.replace(hour=0, minute=0, second=0, microsecond=0),
                 "week": now - timedelta(days=7), "month": now - timedelta(days=30)}.get(key)
        since_ts = since.timestamp() if since else None
        try:
            events = logstats.read_log(path, since_ts)
        except OSError:
            events = []
        note = f"From {path}."
        if not self.logging_on():
            note += " Logging is off, so nothing new is written there: press Turn on logging (Alt+J)."
        self.log_note.setText(note)
        from plover import system
        st = logstats.analyse(events, undo_outlines=(getattr(system, "UNDO_STROKE_STENO", "*"),))
        self.tiles["words written"].setText(f"{st.words:,}")
        self.tiles["wpm while writing"].setText(f"{st.wpm:.0f}")
        self.tiles["strokes per word"].setText(f"{st.strokes_per_word:.2f}")
        self.tiles["undo strokes (*)"].setText(f"{st.undo_strokes:,}")
        self.tiles["backspace strokes"].setText(f"{st.backspace_strokes:,}")
        _fill(self.tables["fixes"], [(w or "—", wo, r or "—", ro, n)
                                     for w, wo, r, ro, n in logstats.top_fixes(st, 50)])
        undone = []
        for outline, n in st.corrected.most_common(50):
            wrote = next((w for (w, o) in st.fixes if o == outline), "")
            undone.append((outline, wrote or "", n))
        _fill(self.tables["undone"], undone)
        _fill(self.tables["untranslated"], st.untranslated.most_common(50))
        _fill(self.tables["fingerspelled"], st.fingerspelled.most_common(50))
        _fill(self.tables["backspaced"], st.backspaced.most_common(50))
        _fill(self.tables["slow"], [(w, f"{p:.1f}s", n) for w, p, n in st.slowest(50, 2)])
        return st

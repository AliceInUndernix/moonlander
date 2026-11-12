"""The "All outlines" panel of the Dotterel Builder.

Every entry of your dictionaries in one table: search, filter, sort, edit,
move, delete, undo and export.
"""

import bisect
import concurrent.futures
import csv
import functools
import os
import json
import re
from collections import Counter, namedtuple

from plover import log, system
from plover.steno import Stroke, normalize_steno, steno_to_sort_key
from plover.translation import escape_translation, unescape_translation

from .words import rank
from .shortcuts import Hints

from ._qt import (
    QAbstractItemView,
    QAction,
    QApplication,
    QBrush,
    QCheckBox,
    QColor,
    QComboBox,
    QEvent,
    QFileDialog,
    QFont,
    QHBoxLayout,
    QHeaderView,
    QKeySequence,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QShortcut,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QTimer,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

USER_ROLE = Qt.ItemDataRole.UserRole
MAX_ROWS = 500  # rows drawn at once; search or sort to see others
GREY = QColor(128, 128, 128)

COL_OUTLINE, COL_TRANSLATION, COL_RANK, COL_STROKES, COL_DICT = range(5)
HEADERS = ["Outline", "Translation", "Popularity", "Strokes", "Dictionary"]

# Search: what to look in, and how to match.
SCOPES = ["Outline or word", "Outline", "Word"]
MODES = ["Contains", "Starts with", "Ends with", "Exact", "Regex"]
# Show: which entries.
SHOW = [
    "All entries",
    "Active only",
    "Overridden (hidden by a higher dictionary)",
    "Words with several outlines",
    "Outlines in several dictionaries",
    "One-stroke outlines",
    "Multi-stroke outlines",
]

Entry = namedtuple(
    "Entry",
    "outline translation path writable strokes prio enabled hidden_by",
)


# Helpers (no Qt) -----------------------------------------------------------


def dict_name(path):
    """A dictionary's file name: "user.json", not its whole path."""
    return re.split(r"[/\\:]", path or "")[-1] or path


def clean_strokes(text):
    """Strokes typed or written into a field, as a tuple of normalised strokes.

    Stray slashes and spaces are dropped: "/KAT/", "KAT / -S" and "KAT -S"
    become ("KAT",) and ("KAT", "-S"). Returns () if nothing is left.
    """
    parts = [p for p in re.split(r"[\s/]+", text.strip()) if p]
    if not parts:
        return ()
    return tuple(normalize_steno("/".join(parts)))


def _slow_sort_key(outline):
    key = []
    for part in outline.split("/"):
        try:
            key.append(tuple(system.KEY_ORDER[k] for k in Stroke(part).keys()))
        except Exception:  # not valid steno in this system
            key.append((99, part))
    return tuple(key)


@functools.lru_cache(maxsize=None)  # the same outlines are sorted again and again
def steno_sort_key(outline):
    """Sort outlines in steno order (#STKPWHRAO*EUFRPBLGTSDZ), stroke by stroke."""
    try:
        # Plover's own key for an outline: the same order, made in one call
        # (about 8 times faster than going through every key of every stroke).
        return (0, steno_to_sort_key(outline, strict=False))
    except Exception:
        return (1, _slow_sort_key(outline))


def make_matcher(query, scope=0, mode=0):
    """Return (match(outline, translation) -> bool, error or None).

    scope: 0 outline or word, 1 outline, 2 word. mode: index in MODES.
    Matching is case-insensitive, except that Exact on a word is exact.
    """
    if not query:
        return (lambda o, t: True), None
    if MODES[mode] == "Regex":
        try:
            rx = re.compile(query, re.IGNORECASE)
        except re.error as e:
            return (lambda o, t: True), str(e)
        test = lambda s: rx.search(s) is not None
    else:
        q = query.lower()
        test = {
            "Contains": lambda s: q in s.lower(),
            "Starts with": lambda s: s.lower().startswith(q),
            "Ends with": lambda s: s.lower().endswith(q),
            "Exact": lambda s: s.lower() == q,
        }[MODES[mode]]
    if MODES[mode] == "Exact" and scope != 2:
        # "/KAT/" or "KAT / -S" typed in the box: compare as steno.
        try:
            strokes = clean_strokes(query.upper())
        except Exception:  # not steno: compare as typed
            strokes = ()
        wanted = "/".join(strokes).lower() if strokes else q
        out_test = lambda s: s.lower() == wanted
    else:
        out_test = test
    if scope == 1:
        return (lambda o, t: out_test(o)), None
    if scope == 2:
        return (lambda o, t: test(t)), None
    return (lambda o, t: out_test(o) or test(t)), None


def collect_entries(dicts):
    """Every entry of the listable dictionaries, highest priority first.

    hidden_by is the path of a higher, enabled dictionary that has the same
    outline (so this entry never gets used), or None.
    """
    entries = []
    first = {}  # outline key -> path of the first enabled dictionary with it
    unlisted = []  # enabled dictionaries we can't list (Python), in order
    for prio, d in enumerate(dicts):
        try:
            items = list(d.items())
        except Exception:
            if d.enabled and "python" in type(d).__name__.lower():
                unlisted.append(d)
            continue
        for key, value in items:
            hidden = first.get(key)
            if hidden is None:
                for u in unlisted:
                    try:
                        if key in u:
                            hidden = u.path
                            break
                    except Exception:
                        pass
            if d.enabled and key not in first:
                first[key] = d.path
            entries.append(
                Entry(
                    "/".join(key),
                    value,
                    d.path,
                    not d.readonly,
                    len(key),
                    prio,
                    d.enabled,
                    hidden,
                )
            )
    return entries


def entries_for(dicts, keys):
    """Like collect_entries, but only for these outline keys (after a change)."""
    entries = []
    unlisted = []
    listed = []
    for prio, d in enumerate(dicts):
        try:
            next(iter(d.items()), None)  # can it be listed? (as collect_entries)
            listed.append((prio, d))
        except Exception:
            listed.append((prio, None))
            if d.enabled and "python" in type(d).__name__.lower():
                unlisted.append((prio, d))
    for key in keys:
        first = None
        for prio, d in enumerate(dicts):
            if listed[prio][1] is None:
                continue
            value = d.get(key)
            if value is None:
                continue
            hidden = first
            if hidden is None:
                for uprio, u in unlisted:
                    if uprio >= prio:
                        break
                    try:
                        if key in u:
                            hidden = u.path
                            break
                    except Exception:
                        pass
            if d.enabled and first is None:
                first = d.path
            entries.append(Entry("/".join(key), value, d.path, not d.readonly, len(key),
                                 prio, d.enabled, hidden))
    return entries


def _write_json(d, path, items):
    """What Plover's JsonDictionary.save writes, from a snapshot of it."""
    from plover.resource import resource_timestamp
    from plover.steno import steno_to_sort_key

    try:
        items.sort(key=lambda i: steno_to_sort_key(i[0], strict=False))
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fp:
            json.dump(dict(items), fp, ensure_ascii=False, indent=0, separators=(",", ": "))
            fp.write("\n")
        os.replace(tmp, path)
        d.timestamp = resource_timestamp(path)
    except Exception:
        log.error("Dotterel: could not save %s", path, exc_info=True)


def ascending_key(column):
    """The key sort_entries uses for this column, ascending (to insert rows)."""
    if column == COL_RANK:
        def key(e):
            r = rank(e.translation)
            if r is None:
                return (1, 0, e.translation.casefold(), steno_sort_key(e.outline))
            return (0, r, "", steno_sort_key(e.outline))
        return key
    if column == COL_OUTLINE:
        return lambda e: (steno_sort_key(e.outline), e.prio)
    if column == COL_STROKES:
        return lambda e: (e.strokes, steno_sort_key(e.outline))
    if column == COL_DICT:
        return lambda e: (e.prio, steno_sort_key(e.outline))
    return lambda e: (e.translation.casefold(), e.translation, steno_sort_key(e.outline))


def sort_entries(entries, column, descending=False):
    if column == COL_RANK:
        # Most common words first; entries that aren't words always last.
        ranked = [(rank(e.translation), e) for e in entries]
        words = sorted(
            [x for x in ranked if x[0] is not None],
            key=lambda x: (x[0], steno_sort_key(x[1].outline)),
            reverse=descending,
        )
        rest = sorted(
            [e for r, e in ranked if r is None],
            key=lambda e: (e.translation.casefold(), steno_sort_key(e.outline)),
        )
        return [e for _r, e in words] + rest
    if column == COL_OUTLINE:
        key = lambda e: (steno_sort_key(e.outline), e.prio)
    elif column == COL_STROKES:
        key = lambda e: (e.strokes, steno_sort_key(e.outline))
    elif column == COL_DICT:
        key = lambda e: (e.prio, steno_sort_key(e.outline))
    else:
        key = lambda e: (e.translation.casefold(), e.translation, steno_sort_key(e.outline))
    return sorted(entries, key=key, reverse=descending)


# The panel -----------------------------------------------------------------


# Keys for the right-click menu of the table (they work on the selected rows).
# The menu itself opens with the Menu key or Shift+F10.
TABLE_KEYS = {
    "edit_outline": "F2",
    "edit_translation": "Shift+F2",
    "write_new": "Ctrl+Shift+N",
    "word": "Alt+W",
    "outline": "Alt+O",
    "hider": "Alt+H",
    "copy_outline": "Ctrl+Shift+C",
    "copy_translation": "Alt+C",
    "copy_json": "Ctrl+C",
    "delete": "Del",
}


class OutlinePanel(QWidget):
    """All outlines: search, filter, sort, edit, move, delete, undo, export.

    write_new(translation) is called to write a new outline for a word (the
    Builder puts the word in its add field). is_busy() returns True while the
    Builder is taking strokes, so "Follow my writing" ignores them.
    """

    def __init__(self, engine, write_new=None, is_busy=None, on_changed=None, parent=None, redo_word=None,
                 hints=None):
        super().__init__(parent)
        self.hints = hints or Hints(lambda: engine.dictionaries)
        self._on_changed = on_changed
        self._engine = engine
        self._write_new = write_new
        self._redo_word = redo_word
        self._is_busy = is_busy or (lambda: False)
        self._entries = []
        self._visible = []
        self._loading = False
        self._undo = []  # list of change lists: (path, key, old, new)
        self._redo = []  # changes taken back by Undo, for Redo
        self._sort = (COL_RANK, False)  # most common words first
        self._dict_paths = []  # writable dictionaries, for Move/Copy to

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search outlines or words…  (Ctrl+F)")
        self.search.setClearButtonEnabled(True)
        self.scope = QComboBox()
        self.scope.addItems(SCOPES)
        self.mode = QComboBox()
        self.mode.addItems(MODES)
        self.show_filter = QComboBox()
        self.show_filter.addItems(SHOW)
        # Which dictionaries to show: a drop-down of tick boxes.
        self._hidden = set()  # paths not shown
        self._listed = []
        self.dict_button = QToolButton()
        self.dict_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.dict_button.setToolTip("Choose which dictionaries to show")
        self.dict_menu = QMenu(self.dict_button)
        self.dict_button.setMenu(self.dict_menu)
        self.only_mine = QCheckBox("Only editable")
        self.only_mine.setToolTip("Hide the read-only and bundled tool dictionaries")
        self.only_mine.setChecked(True)
        self.follow = QCheckBox("Follow my writing")
        self.follow.setToolTip(
            "Show the outline of every stroke you write, to check or fix it"
        )

        self.table = QTableWidget(0, len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_OUTLINE, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_TRANSLATION, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_RANK, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_STROKES, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_DICT, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self.on_header_clicked)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.on_context_menu)
        self.table.itemChanged.connect(self.on_cell_edited)
        self.table.installEventFilter(self)

        self.count_label = QLabel("")
        self.undo_button = QPushButton("Undo")
        self.undo_button.setToolTip("Undo the last change (Ctrl+Z)")
        self.undo_button.clicked.connect(self.undo)
        self.undo_button.setEnabled(False)
        self.redo_button = QPushButton("Redo")
        self.redo_button.setToolTip("Redo what Undo took back (Ctrl+Shift+Z or Ctrl+Y)")
        self.redo_button.clicked.connect(self.redo)
        self.redo_button.setEnabled(False)
        export = QPushButton("Export…")
        export.setToolTip("Save the entries shown to a JSON or CSV file")
        export.clicked.connect(self.export)
        self.redo_words_button = QPushButton("Redo selected")
        self.redo_words_button.setToolTip(
            "Send the selected words to Add words to write them again; "
            "each new outline replaces the old one"
        )
        self.redo_words_button.clicked.connect(self.redo_selected)
        self.redo_words_button.setVisible(redo_word is not None)
        delete = QPushButton("Delete")
        delete.setToolTip("Delete the selected entries (Delete)")
        delete.clicked.connect(self.delete_selected)

        self._export_button = export
        self._delete_button = delete

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self.fill_table)
        self.search.textChanged.connect(self._search_timer.start)
        for combo in (self.scope, self.mode, self.show_filter):
            combo.currentIndexChanged.connect(self.fill_table)
        self.only_mine.toggled.connect(self.fill_table)

        self.filters_button = QPushButton("Filters")
        self.filters_button.setCheckable(True)
        self.filters_button.setToolTip("Search options, which entries and which dictionaries")
        self.filters = QWidget()
        fv = QVBoxLayout(self.filters)
        fv.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(QLabel("Look in"))
        row.addWidget(self.scope)
        row.addWidget(QLabel("match"))
        row.addWidget(self.mode)
        row.addStretch()
        fv.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(QLabel("Show"))
        row.addWidget(self.show_filter, 1)
        fv.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(self.dict_button, 1)
        row.addWidget(self.only_mine)
        fv.addLayout(row)
        self.filters.setVisible(False)
        self.filters_button.toggled.connect(self.filters.setVisible)

        title = QLabel("All outlines")
        title.setObjectName("heading")
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        row.addWidget(title)
        row.addStretch()
        row.addWidget(self.follow)
        v.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(self.search, 1)
        row.addWidget(self.filters_button)
        v.addLayout(row)
        v.addWidget(self.filters)
        v.addWidget(self.table)
        row = QHBoxLayout()
        row.addWidget(self.count_label)
        row.addStretch()
        row.addWidget(self.undo_button)
        row.addWidget(self.redo_button)
        row.addWidget(self.redo_words_button)
        row.addWidget(export)
        row.addWidget(delete)
        v.addLayout(row)

        engine.signal_connect("translated", self.on_translated)
        self._update_sort_indicator()
        self._make_shortcuts()

    # Shortcuts: every button has one; hover shows it and its steno outline.

    def _make_shortcuts(self):
        h, me = self.hints, self

        def cycle(combo):
            def go():
                self.filters_button.setChecked(True)
                combo.setCurrentIndex((combo.currentIndex() + 1) % combo.count())
                combo.setFocus()
            return go

        def show_dicts():
            self.filters_button.setChecked(True)
            self.dict_button.showMenu()

        h.add(me, self.search, "Search outlines or words", "Ctrl+F", self.focus_search)
        h.add(me, self.filters_button, "Show or hide the search options", "Ctrl+Shift+F",
              self.filters_button.toggle)
        h.add(me, self.follow, "Follow my writing: show the outline of every stroke you write",
              "Ctrl+Shift+W", self.follow.toggle)
        h.add(me, self.scope, "Look in: outlines, words, or both (next choice)", "Alt+L", cycle(self.scope))
        h.add(me, self.mode, "Match: how the search matches (next choice)", "Alt+M", cycle(self.mode))
        h.add(me, self.show_filter, "Show: which entries (next choice)", "Alt+S", cycle(self.show_filter))
        h.add(me, self.dict_button, "Choose which dictionaries to show", "Ctrl+Shift+D", show_dicts)
        h.add(me, self.only_mine, "Only editable: hide read-only and bundled tool dictionaries",
              "Ctrl+Shift+E", self.only_mine.toggle)
        h.add(me, self.undo_button, "Undo the last change", "Ctrl+Z", self.undo)
        h.add(me, self.redo_button, "Redo what Undo took back", ["Ctrl+Shift+Z", "Ctrl+Y"], self.redo)
        h.add(me, self.redo_words_button,
              "Redo selected: write the selected words again in Add words; "
              "each new outline replaces the old one", "Ctrl+Shift+R", self.redo_selected)
        h.add(me, self._export_button, "Export the entries shown to a JSON or CSV file", "Ctrl+E",
              self.export)
        h.add(me, self._delete_button, "Delete the selected entries (in the table)", "Del")
        header = self.table.horizontalHeader()
        for i, name in enumerate(HEADERS):
            h.add(me, header, f"Sort by {name} (again: reverse)", f"Ctrl+Alt+{i + 1}",
                  lambda c=i: self.on_header_clicked(c))
        # The right-click menu's actions work on the selected rows, from the table.
        for name, keys in TABLE_KEYS.items():
            if name in ("delete", "copy_json"):
                continue  # done in eventFilter, so cell editing keeps them
            h.add(self.table, None, name, keys, lambda n=name: self._table_action(n),
                  context=Qt.ShortcutContext.WidgetWithChildrenShortcut)

    def _table_action(self, name):
        entries = self.selected_entries()
        for action in self._actions(entries):
            if action[0] == name and action[4]:
                action[3]()
                return

    # Settings (saved with the Builder window) ------------------------------

    def save_settings(self, settings):
        settings.setValue("outlines_scope", self.scope.currentIndex())
        settings.setValue("outlines_mode", self.mode.currentIndex())
        settings.setValue("outlines_show", self.show_filter.currentIndex())
        settings.setValue("outlines_only_mine", int(self.only_mine.isChecked()))
        settings.setValue("outlines_follow", int(self.follow.isChecked()))
        settings.setValue("outlines_filters_open", int(self.filters_button.isChecked()))
        settings.setValue("outlines_sort2", "%d,%d" % (self._sort[0], self._sort[1]))
        settings.setValue("outlines_hidden", json.dumps(sorted(self._hidden)))

    def restore_settings(self, settings):
        def get_int(name, default):
            try:
                return int(settings.value(name, default))
            except (TypeError, ValueError):
                return default

        self.scope.setCurrentIndex(get_int("outlines_scope", 0))
        self.mode.setCurrentIndex(get_int("outlines_mode", 0))
        self.show_filter.setCurrentIndex(get_int("outlines_show", 0))
        self.only_mine.setChecked(bool(get_int("outlines_only_mine", 1)))
        self.follow.setChecked(bool(get_int("outlines_follow", 0)))
        self.filters_button.setChecked(bool(get_int("outlines_filters_open", 0)))
        try:
            col, desc = str(settings.value("outlines_sort2", "2,0")).split(",")
            self._sort = (min(max(int(col), 0), len(HEADERS) - 1), bool(int(desc)))
        except (TypeError, ValueError):
            pass
        try:
            self._hidden = set(json.loads(str(settings.value("outlines_hidden", "[]"))))
        except (TypeError, ValueError):
            self._hidden = set()
        self._update_sort_indicator()
        self._build_dict_menu()
        self.fill_table()

    # Loading and showing ---------------------------------------------------

    _sorted = None  # every entry, in the table's order (kept between changes)
    _sorted_for = None

    def _sorted_entries(self):
        if self._sorted is None or self._sorted_for != self._sort:
            self._sorted = sort_entries(self._entries, *self._sort)
            self._sorted_for = self._sort
        return self._sorted

    def reload_keys(self, keys):
        """After a change to only these outlines: redo just their rows."""
        with self._engine as engine:
            dicts = list(engine.dictionaries.dicts)
        if [d.path for d in dicts] != getattr(self, "_loaded_paths", None):
            self.reload()
            return
        names = {"/".join(k) for k in keys}
        new = entries_for(dicts, keys)
        self._entries = [e for e in self._entries if e.outline not in names] + new
        if self._sorted is not None and self._sorted_for == self._sort and not self._sort[1]:
            # Only the changed rows move: no need to sort 100,000 rows again.
            key = ascending_key(self._sort[0])
            self._sorted = [e for e in self._sorted if e.outline not in names]
            for e in new:
                bisect.insort(self._sorted, e, key=key)
        else:
            self._sorted = None
        self.fill_table()

    def reload(self):
        with self._engine as engine:
            dicts = list(engine.dictionaries.dicts)
        self._loaded_paths = [d.path for d in dicts]
        self._entries = collect_entries(dicts)
        self._sorted = None
        self._dict_paths = [d.path for d in dicts if not d.readonly]

        listed = []
        for e in self._entries:
            if e.path not in listed:
                listed.append(e.path)
        self._listed = listed
        self._build_dict_menu()
        self.fill_table()

    def _build_dict_menu(self):
        menu = self.dict_menu
        menu.clear()
        for text, slot in (
            # Deferred: rebuilding the menu deletes the action being clicked.
            ("Show all", lambda: QTimer.singleShot(0, lambda: self.set_hidden(()))),
            ("Show only editable", lambda: QTimer.singleShot(0, lambda: self.set_hidden(
                [p for p in self._listed if p not in self._dict_paths]))),
        ):
            a = QAction(text, menu)
            a.triggered.connect(slot)
            menu.addAction(a)
        menu.addSeparator()
        for path in self._listed:
            a = QAction(dict_name(path), menu)
            a.setCheckable(True)
            a.setChecked(path not in self._hidden)
            a.toggled.connect(lambda on, p=path: self._toggle_dict(p, on))
            menu.addAction(a)
        shown = len([p for p in self._listed if p not in self._hidden])
        self.dict_button.setText(
            "All dictionaries" if shown == len(self._listed)
            else f"Dictionaries: {shown} of {len(self._listed)}"
        )

    def _toggle_dict(self, path, on):
        if on:
            self._hidden.discard(path)
        else:
            self._hidden.add(path)
        QTimer.singleShot(0, self._build_dict_menu)
        self.fill_table()

    def set_hidden(self, paths):
        self._hidden = set(paths)
        self._build_dict_menu()
        self.fill_table()

    def _filtered(self):
        match, error = make_matcher(
            self.search.text().strip(),
            self.scope.currentIndex(),
            self.mode.currentIndex(),
        )
        self.search.setToolTip(f"Bad regex: {error}" if error else "")
        self.search.setStyleSheet("border: 1px solid #d9534f;" if error else "")
        show = SHOW[self.show_filter.currentIndex()]
        entries = self._sorted_entries()
        if self.only_mine.isChecked():
            entries = [e for e in entries if e.writable]
        if self._hidden:
            entries = [e for e in entries if e.path not in self._hidden]
        active = lambda e: e.enabled and e.hidden_by is None
        if show == "Active only":
            entries = [e for e in entries if active(e)]
        elif show.startswith("Overridden"):
            entries = [e for e in entries if e.hidden_by is not None]
        elif show == "Words with several outlines":
            counts = Counter(e.translation for e in self._entries if active(e))
            entries = [e for e in entries if active(e) and counts[e.translation] > 1]
        elif show == "Outlines in several dictionaries":
            counts = Counter(e.outline for e in self._entries)
            entries = [e for e in entries if counts[e.outline] > 1]
        elif show == "One-stroke outlines":
            entries = [e for e in entries if e.strokes == 1]
        elif show == "Multi-stroke outlines":
            entries = [e for e in entries if e.strokes > 1]
        active_filters = sum([
            self.scope.currentIndex() != 0,
            self.mode.currentIndex() != 0,
            self.show_filter.currentIndex() != 0,
            bool(self._hidden),
            not self.only_mine.isChecked(),
        ])
        self.filters_button.setText(f"Filters ({active_filters})" if active_filters else "Filters")
        return [e for e in entries if match(e.outline, e.translation)]

    def fill_table(self):
        visible = self._filtered()
        self._visible = visible
        shown = visible[:MAX_ROWS]
        self._loading = True
        header = self.table.horizontalHeader()
        # Sized-to-contents columns would be measured again after every cell.
        sized = [c for c in range(self.table.columnCount())
                 if header.sectionResizeMode(c) == QHeaderView.ResizeMode.ResizeToContents]
        for c in sized:
            header.setSectionResizeMode(c, QHeaderView.ResizeMode.Fixed)
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(shown))
        grey = QBrush(GREY)
        # Worked out once: "~flag" on a Qt flag is slow, and this ran three
        # times for each of 500 rows (a quarter of a second per search).
        # Asking every cell for its flags is slow too: all cells start with
        # the same ones, so ask one cell.
        read_only = QTableWidgetItem().flags() & ~Qt.ItemFlag.ItemIsEditable
        for row, e in enumerate(shown):
            r = rank(e.translation)
            cells = (
                e.outline,
                escape_translation(e.translation),
                f"#{r:,}" if r else "",
                str(e.strokes),
                dict_name(e.path),
            )
            note = ""
            if not e.enabled:
                note = "This dictionary is switched off"
            elif e.hidden_by:
                note = f"Never used: {dict_name(e.hidden_by)} has this outline too"
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setData(USER_ROLE, e)
                if col in (COL_RANK, COL_STROKES, COL_DICT) or not e.writable:
                    item.setFlags(read_only)
                if col in (COL_RANK, COL_STROKES):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == COL_RANK:
                    item.setToolTip("How common the word is in English (#1 = most common)")
                if col == COL_DICT:
                    item.setToolTip(e.path)
                if note:
                    item.setForeground(grey)
                    item.setToolTip(note)
                    if col == COL_OUTLINE and e.hidden_by:
                        font = QFont(item.font())
                        font.setStrikeOut(True)
                        item.setFont(font)
                self.table.setItem(row, col, item)
        self.table.blockSignals(False)
        for c in sized:
            header.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setUpdatesEnabled(True)
        self._loading = False
        total = len(visible)
        text = f"{total} entr{'ies' if total != 1 else 'y'}"
        if total > len(shown):
            text = f"Showing {len(shown)} of {total}: search or sort to see others"
        self.count_label.setText(text)

    def on_header_clicked(self, column):
        col, desc = self._sort
        self._sort = (column, not desc if column == col else False)
        self._update_sort_indicator()
        self.fill_table()

    def _update_sort_indicator(self):
        col, desc = self._sort
        order = Qt.SortOrder.DescendingOrder if desc else Qt.SortOrder.AscendingOrder
        self.table.horizontalHeader().setSortIndicator(col, order)

    def focus_search(self):
        self.search.setFocus()
        self.search.selectAll()

    def show_outline(self, outline):
        """Search for one outline exactly."""
        self.scope.setCurrentIndex(1)
        self.mode.setCurrentIndex(MODES.index("Exact"))
        self.search.setText(outline)
        self.fill_table()

    def show_word(self, word):
        """Search for every outline of one word."""
        self.scope.setCurrentIndex(2)
        self.mode.setCurrentIndex(MODES.index("Exact"))
        self.search.setText(word)
        self.fill_table()

    def on_translated(self, _old, new):
        if not self.follow.isChecked() or not new or self._is_busy():
            return
        if not self.isVisible():
            return
        outline = "/".join(new[-1].rtfcre)
        if outline:
            self.show_outline(outline)

    # Selection -------------------------------------------------------------

    def selected_entries(self):
        rows = sorted({i.row() for i in self.table.selectedItems()})
        return [self.table.item(r, 0).data(USER_ROLE) for r in rows]

    def eventFilter(self, watched, event):
        if watched is self.table and event.type() == QEvent.Type.KeyPress:
            editing = self.table.state() == QAbstractItemView.State.EditingState
            if not editing and event.key() == Qt.Key.Key_Delete:
                self.delete_selected()
                return True
            if not editing and event.matches(QKeySequence.StandardKey.Copy):
                self.copy_entries(self.selected_entries())
                return True
        return super().eventFilter(watched, event)

    def _actions(self, entries):
        """The right-click menu: [(name, text, keys, slot, enabled)]; None = a line."""
        if not entries:
            return []
        e = entries[0]
        out = []
        writable = [x for x in entries if x.writable]
        if self._redo_word is not None:
            redo = [x for x in writable if x.translation]
            label = (
                f"Redo “{e.translation}” (new outline replaces {e.outline})"
                if len(entries) == 1
                else f"Redo {len(redo)} selected words (new outlines replace the old)"
            )
            out += [("redo", label, "Ctrl+Shift+R", self.redo_selected, bool(redo)), None]
        if len(entries) == 1:
            out.append(("edit_outline", "Edit outline", TABLE_KEYS["edit_outline"],
                        lambda: self._edit_cell(COL_OUTLINE), e.writable))
            out.append(("edit_translation", "Edit translation", TABLE_KEYS["edit_translation"],
                        lambda: self._edit_cell(COL_TRANSLATION), e.writable))
            if self._write_new is not None:
                out.append(("write_new", f"Write another outline for “{e.translation}”",
                            TABLE_KEYS["write_new"], lambda: self._write_new(e.translation), True))
            out.append(("word", f"All outlines for “{e.translation}”", TABLE_KEYS["word"],
                        lambda: self.show_word(e.translation), True))
            out.append(("outline", f"Everything on {e.outline}", TABLE_KEYS["outline"],
                        lambda: self.show_outline(e.outline), True))
            if e.hidden_by:
                out.append(("hider", f"Go to the entry hiding it ({dict_name(e.hidden_by)})",
                            TABLE_KEYS["hider"], lambda: self._show_hider(e), True))
            out.append(None)
        out.append(("copy_outline", "Copy outline", TABLE_KEYS["copy_outline"],
                    lambda: self._copy("\n".join(x.outline for x in entries)), True))
        out.append(("copy_translation", "Copy translation", TABLE_KEYS["copy_translation"],
                    lambda: self._copy("\n".join(x.translation for x in entries)), True))
        out.append(("copy_json", "Copy as JSON", TABLE_KEYS["copy_json"],
                    lambda: self.copy_entries(entries), True))
        out.append(None)
        out.append("transfer")
        out.append(None)
        n = len(writable)
        out.append(("delete", f"Delete{' %d entries' % n if n > 1 else ''}", TABLE_KEYS["delete"],
                    self.delete_selected, bool(n)))
        return out

    def on_context_menu(self, pos):
        entries = self.selected_entries()
        if not entries:
            return
        writable = [x for x in entries if x.writable]
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        for item in self._actions(entries):
            if item is None:
                menu.addSeparator()
            elif item == "transfer":
                move = menu.addMenu("Move to")
                copy = menu.addMenu("Copy to")
                for path in self._dict_paths:
                    name = dict_name(path)
                    a = QAction(name, move)
                    a.triggered.connect(lambda _=False, p=path: self.transfer(entries, p, move=True))
                    a.setEnabled(bool(writable) and any(x.path != path for x in writable))
                    move.addAction(a)
                    a = QAction(name, copy)
                    a.triggered.connect(lambda _=False, p=path: self.transfer(entries, p, move=False))
                    a.setEnabled(any(x.path != path for x in entries))
                    copy.addAction(a)
            else:
                _name, text, keys, slot, enabled = item
                keys = [keys] if isinstance(keys, str) else keys
                action = QAction(text + "\t" + QKeySequence(keys[0]).toString(), menu)
                action.setToolTip(self.hints.describe(text, keys))
                action.triggered.connect(slot)
                action.setEnabled(enabled)
                menu.addAction(action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _edit_cell(self, column):
        row = self.table.currentRow()
        if row >= 0:
            self.table.editItem(self.table.item(row, column))

    def _show_hider(self, e):
        self.show_filter.setCurrentIndex(0)
        self.set_hidden(())
        self.only_mine.setChecked(False)
        self.show_outline(e.outline)

    def _copy(self, text):
        QApplication.clipboard().setText(text)

    def copy_entries(self, entries):
        if entries:
            lines = [
                f"{json.dumps(e.outline)}: {json.dumps(e.translation, ensure_ascii=False)}"
                for e in entries
            ]
            self._copy(",\n".join(lines))

    # Changing dictionaries -------------------------------------------------

    def apply_changes(self, changes, record=True):
        """changes: [(path, key, new or None)]. Saves, and records for undo."""
        dicts = self._engine.dictionaries
        done = []
        paths = []
        with self._engine:
            for path, key, new in changes:
                if path not in dicts:
                    continue
                d = dicts[path]
                if d.readonly:
                    continue
                old = d.get(key)
                if old == new:
                    continue
                if new is None:
                    del d[key]
                else:
                    d[key] = new
                done.append((path, key, old, new))
                if path not in paths:
                    paths.append(path)
            if paths:
                self._save_later(dicts, paths)
        if record and done:
            self.record(done)
        self.reload_keys({key for _p, key, _o, _n in done})
        if done and self._on_changed is not None:
            self._on_changed(done)
        return done

    _saver = None  # one thread writes the files, in order

    @classmethod
    def _save_later(cls, dicts, paths):
        """Write the changed dictionaries in the background: a big one (Lapwing's
        base is 3 MB) takes half a second. Called with the engine locked, so
        the snapshot is taken while nothing else changes it."""
        if OutlinePanel._saver is None:
            OutlinePanel._saver = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        for path in paths:
            d = dicts[path]
            if type(d).__name__ != "JsonDictionary":
                d.save()  # other kinds: Plover's own way, now
                continue
            items = [("/".join(k), v) for k, v in d.items()]
            OutlinePanel._saver.submit(_write_json, d, path, items)

    @classmethod
    def wait_saves(cls):
        """Wait until every change is written to its file."""
        if cls._saver is not None:
            cls._saver.submit(lambda: None).result()

    def record(self, done, keep_redo=False):
        """Remember changes (path, key, old, new) so Undo can revert them."""
        self._undo.append(list(done))
        del self._undo[:-100]
        if not keep_redo:
            self._redo.clear()
        self._update_undo_buttons()

    def _update_undo_buttons(self):
        self.undo_button.setEnabled(bool(self._undo))
        self.redo_button.setEnabled(bool(self._redo))

    def redo_selected(self):
        """Send the selected entries to the Add words list to write again."""
        if self._redo_word is None:
            return
        entries = [x for x in self.selected_entries() if x.writable and x.translation]
        self._redo_word([(x.translation, x.path, x.outline) for x in entries])

    def undo(self):
        if not self._undo:
            return
        done = self._undo.pop()
        self.apply_changes(
            [(path, key, old) for path, key, old, _new in reversed(done)],
            record=False,
        )
        self._redo.append(done)
        del self._redo[:-100]
        self._update_undo_buttons()

    def redo(self):
        if not self._redo:
            return
        done = self._redo.pop()
        self.apply_changes([(path, key, new) for path, key, _old, new in done], record=False)
        self.record(done, keep_redo=True)

    def _ask(self, title, text):
        answer = QMessageBox.question(self, title, text)
        return answer == QMessageBox.StandardButton.Yes

    def on_cell_edited(self, item):
        if self._loading:
            return
        # Finish the edit first: rebuilding the table from inside Qt's
        # itemChanged signal would delete the item that is sending it.
        e, column, text = item.data(USER_ROLE), item.column(), item.text()
        QTimer.singleShot(0, lambda: self.apply_cell_edit(e, column, text))

    def apply_cell_edit(self, e, column, text):
        old_key = tuple(e.outline.split("/"))
        if column == COL_OUTLINE:
            try:
                new_key = clean_strokes(text.upper())
            except Exception:
                new_key = ()
            new_translation = e.translation
        else:
            new_key = old_key
            new_translation = unescape_translation(text.strip())
        if not new_key or not new_translation or (
            new_key == old_key and new_translation == e.translation
        ):
            self.fill_table()  # empty or unchanged: put the cell back
            return
        dicts = self._engine.dictionaries
        if e.path not in dicts:
            self.reload()
            return
        d = dicts[e.path]
        if new_key != old_key:
            taken = d.get(new_key)
            if taken is not None and not self._ask(
                "Replace outline?",
                f"{'/'.join(new_key)} is already “{taken}” in "
                f"{dict_name(e.path)}. Replace it?",
            ):
                self.fill_table()
                return
            changes = [(e.path, old_key, None), (e.path, new_key, new_translation)]
        else:
            changes = [(e.path, old_key, new_translation)]
        self.apply_changes(changes)

    def transfer(self, entries, target, move):
        """Move or copy entries to the dictionary at target."""
        dicts = self._engine.dictionaries
        if target not in dicts:
            return
        d = dicts[target]
        entries = [e for e in entries if e.path != target and (e.writable or not move)]
        if not entries:
            return
        clashes = []
        for e in entries:
            taken = d.get(tuple(e.outline.split("/")))
            if taken is not None and taken != e.translation:
                clashes.append(f"{e.outline}: “{taken}” → “{e.translation}”")
        if clashes:
            more = f"\n… and {len(clashes) - 10} more" if len(clashes) > 10 else ""
            if not self._ask(
                "Replace entries?",
                f"{dict_name(target)} already has:\n\n"
                + "\n".join(clashes[:10])
                + more
                + "\n\nReplace them?",
            ):
                return
        changes = []
        for e in entries:
            key = tuple(e.outline.split("/"))
            changes.append((target, key, e.translation))
            if move:
                changes.append((e.path, key, None))
        self.apply_changes(changes)

    def delete_selected(self):
        targets = [e for e in self.selected_entries() if e.writable]
        if not targets:
            return
        listing = "\n".join(f"{e.outline} → {e.translation}" for e in targets[:10])
        more = f"\n… and {len(targets) - 10} more" if len(targets) > 10 else ""
        if not self._ask(
            "Delete entries?",
            f"Delete these entries?\n\n{listing}{more}\n\n(Ctrl+Z undoes it.)",
        ):
            return
        self.apply_changes(
            [(e.path, tuple(e.outline.split("/")), None) for e in targets]
        )

    # Export ----------------------------------------------------------------

    def export(self):
        if not self._visible:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export entries", "outlines.json", "JSON (*.json);;CSV (*.csv)"
        )
        if not path:
            return
        try:
            export_entries(self._visible, path)
        except OSError as e:
            QMessageBox.warning(self, "Export failed", str(e))
            return
        log.info("dotterel builder: exported %d entries to %s", len(self._visible), path)


def export_entries(entries, path):
    """Write entries to path: CSV (outline, translation, dictionary) or JSON."""
    if path.lower().endswith(".csv"):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["outline", "translation", "dictionary"])
            for e in entries:
                w.writerow([e.outline, e.translation, dict_name(e.path)])
    else:
        data = {}
        for e in entries:
            data.setdefault(e.outline, e.translation)  # first = highest priority
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0, sort_keys=True)
            f.write("\n")

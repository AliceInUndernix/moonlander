"""Click, type and stroke through the Builder, like you would.

A real Plover engine (no machine), the real Dotterel dictionaries, and an
offscreen window. Steno strokes go through Plover, so KHR then PH* really
presses Ctrl+M through Dotterel modifiers.

Run:  QT_QPA_PLATFORM=offscreen python tests/ui_builder.py [rounds]
"""

import json
import os
import shutil
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QLineEdit,
                               QPlainTextEdit, QPushButton, QToolButton)

from plover import system
from plover.config import Config
from plover.dictionary.base import load_dictionary
from plover.engine import StenoEngine
from plover.registry import registry
from plover.steno import Stroke

registry.update()
import plover_dotterel.system  # noqa: E402

registry.register_plugin("system", "Dotterel", plover_dotterel.system)
system.setup("Dotterel")

from plover_dotterel import cambridge, shortcuts, steno  # noqa: E402
from plover_dotterel import builder as builder_mod  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DICTS = os.path.join(HERE, "..", "plover_dotterel", "dictionaries")
app = QApplication.instance() or QApplication([])
results = []


def pe(n=6):
    for _ in range(n):
        QCoreApplication.processEvents()
        time.sleep(0.005)


QT_KEYS = {"return": Qt.Key.Key_Return, "escape": Qt.Key.Key_Escape, "delete": Qt.Key.Key_Delete,
           "up": Qt.Key.Key_Up, "down": Qt.Key.Key_Down, "left": Qt.Key.Key_Left,
           "right": Qt.Key.Key_Right, "tab": Qt.Key.Key_Tab, "backspace": Qt.Key.Key_Backspace}
QT_MODS = {"ctrl": Qt.KeyboardModifier.ControlModifier, "shift": Qt.KeyboardModifier.ShiftModifier,
           "alt": Qt.KeyboardModifier.AltModifier, "super": Qt.KeyboardModifier.MetaModifier}


class KB:
    """Plover's keyboard output, sent into the Qt window instead."""

    pressed = []

    def send_string(self, s):
        for i, part in enumerate(s.split("\n")):
            if i:
                QTest.keyClick(app.focusWidget(), Qt.Key.Key_Return)
            w = app.focusWidget()
            if part and hasattr(w, "insert"):
                w.insert(part)

    def send_backspaces(self, n):
        w = app.focusWidget()
        for _ in range(n):
            if hasattr(w, "backspace"):
                w.backspace()

    def send_key_combination(self, combo):
        KB.pressed.append(combo)
        parsed = shortcuts.from_plover("{#" + combo + "}")
        if not parsed:
            return
        mods, key = parsed
        k = QT_KEYS.get(key) or (getattr(Qt.Key, "Key_" + key.upper(), None))
        if k is None:
            return
        m = Qt.KeyboardModifier.NoModifier
        for x in mods:
            m |= QT_MODS[x]
        QTest.keyClick(app.focusWidget() or b, k, m)

    def set_key_press_delay(self, *a):
        pass


class Eng(StenoEngine):
    def __init__(self, tmp):
        cfg = Config(os.path.join(tmp, "plover.cfg"))
        cfg.update(machine_type="Gemini PR", system_name="Dotterel")
        super().__init__(cfg, None, KB())
        self._sigs = {}

    def signal_connect(self, name, cb):
        self._sigs.setdefault(name, []).append(cb)


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name, "" if cond else extra)


def click(w):
    QTest.mouseClick(w, Qt.MouseButton.LeftButton)
    pe()


def key(w, k, mod=Qt.KeyboardModifier.NoModifier):
    QTest.keyClick(w, k, mod)
    pe()


def typ(w, text):
    QTest.keyClicks(w, text)
    pe()


def stroke(outline):
    for s in outline.split("/"):
        e._on_stroked(Stroke(s).keys())
        pe()


CTRL, ALT, SHIFT = (Qt.KeyboardModifier.ControlModifier, Qt.KeyboardModifier.AltModifier,
                    Qt.KeyboardModifier.ShiftModifier)


def one_round(n):
    global e, b
    tmp = tempfile.mkdtemp()
    base = os.path.join(tmp, "dotterel-base.json")  # small stand-ins for yours
    names = os.path.join(tmp, "dotterel-proper-nouns.json")
    json.dump({"KAT": "cat", "KOT": "cot", "TKOG": "dog", "THE": "the"}, open(base, "w"))
    json.dump({}, open(names, "w"))
    e = Eng(tmp)
    ds = [load_dictionary(base), load_dictionary(names),
          load_dictionary(os.path.join(HERE, "affixes.json"))]  # base's affix entries (from Lapwing)
    ds += [load_dictionary(os.path.join(DICTS, d)) for d in system.DEFAULT_DICTIONARIES[2:]]
    e._dictionaries.set_dicts(ds)
    e._is_running = False
    e._set_output(True)
    app.engine = e
    cambridge.lookup = lambda w: {"word": w, "uk": {"ipa": "kæt", "files": {}},
                                  "us": {"ipa": "kæt", "files": {}},
                                  "defs": [("noun", [("a small animal", "the cat sat")])]}

    import plover.oslayer.config as pconf
    from plover_dotterel import practice as pr
    pconf.CONFIG_DIR = tmp
    pr.BOOKS_DIR = os.path.join(tmp, "Dotterel books")
    if not hasattr(pr.Store, "_orig_init"):
        pr.Store._orig_init = pr.Store.__init__
    pr.Store.__init__ = lambda self, path=None: pr.Store._orig_init(
        self, path or os.path.join(pconf.CONFIG_DIR, "dotterel_practice.json"))

    from plover_dotterel.builder import DotterelBuilder
    b = DotterelBuilder(e)
    b.show()
    b.activateWindow()
    pe(20)
    tag = f"[{n}] "

    def mine():
        return {"/".join(k): v for k, v in e._dictionaries[base].items()}

    def theirs():
        return {"/".join(k): v for k, v in e._dictionaries[names].items()}

    def queue():
        return [b.queue.item(i).data(Qt.ItemDataRole.UserRole) for i in range(b.queue.count())]

    # --- Every button, toggle and field has a shortcut and a hover hint.
    kinds = (QPushButton, QCheckBox, QToolButton, QComboBox, QLineEdit, QPlainTextEdit)
    missing = []
    for w in [w for k in kinds for w in b.findChildren(k)]:
        if w.parent() is b.add and w is not b.add.strokes:
            continue  # Plover's own hidden parts of the outline field
        if w.parent() is not None and isinstance(w.parent(), QComboBox):
            continue
        if w not in b.hints._hints and w.isVisibleTo(b):
            missing.append((type(w).__name__, w.text() if hasattr(w, "text") else ""))
    check(tag + "every visible button/field has a hint", not missing, missing)
    tip = b.hints.tooltip(b.meaning_button)
    check(tag + "Meaning hint: action, keys, steno", "Meaning" in tip and "Ctrl+M" in tip
          and "KHR/PH*" in tip and "dotterel-modifiers" in tip, tip)
    tip = b.hints.tooltip(b.save_button)
    check(tag + "Save hint shows R-R", "R-R" in tip and "Ctrl+S" in tip, tip)
    tip = b.hints.tooltip(b.panel._delete_button)
    check(tag + "Delete hint shows TKHR from commands", "TKHR" in tip and "dotterel-commands" in tip, tip)
    keys = [k for k, _a, _s in b.hints.shortcuts]
    dupes = {k for k in keys if keys.count(k) > 1}
    check(tag + "no shortcut is used twice", not dupes, dupes)
    nosteno = [k for k in set(keys) if not b.hints.finder.outlines(k)]
    # = has no stroke in your dictionaries yet, so zooming in has none
    check(tag + "every shortcut has a steno outline", set(nosteno) <= {"Ctrl++", "Ctrl+="}, nosteno)

    # --- The all-outlines table is filled when the window opens.
    check(tag + "table filled at start", b.panel.table.rowCount() >= 4, b.panel.table.rowCount())

    # --- Popular words, the card.
    check(tag + "opens on Popular words", b.popular_button.isChecked() and b.queue.count() > 50)
    check(tag + "popular list has no word you already write",
          not ({"cat", "the", "dog"} & set(queue())))
    first = queue()[0]
    check(tag + "first word on the card", b.word_label.text() == first, b.word_label.text())
    pe(30)
    check(tag + "UK and US pronunciation", "kæt" in b.uk_label.text() and "kæt" in b.us_label.text(),
          b.uk_label.text())
    check(tag + "syllables shown", b.syllables_label.text().startswith("Syllables:"))

    # --- Meaning: Ctrl+M, from the Outline field, and by steno KHR then PH*.
    check(tag + "meaning hidden at first", not b.meaning_label.isVisible())
    b.add.strokes.setFocus(); pe()
    key(b.add.strokes, Qt.Key.Key_M, CTRL)
    check(tag + "Ctrl+M opens meaning", b.meaning_label.isVisible()
          and "small animal" in b.meaning_label.text(), b.meaning_label.text()[:80])
    b.add.strokes.setFocus(); pe()
    stroke("KHR/PH*")
    check(tag + "steno KHR/PH* closes it again", not b.meaning_label.isVisible(), KB.pressed[-3:])
    check(tag + "the stroke didn't land in the Outline field", b.add.strokes.text() == "",
          b.add.strokes.text())

    # --- My words: Ctrl+2, paste, Ctrl+Return.
    key(b, Qt.Key.Key_2, CTRL)
    check(tag + "Ctrl+2 = My words", b.mine_button.isChecked() and b.paste.isVisible())
    b.paste.setPlainText("The cat walked to London, apple and cot.")
    b.paste.setFocus(); pe()
    key(b.paste, Qt.Key.Key_Return, CTRL)
    check(tag + "Ctrl+Return finds the new words",
          set(queue()) == {"walked", "London", "apple", "to", "and"}, queue())
    # walked: from parts (walk isn't there) -> no; just check the card follows the list
    check(tag + "card follows list", b.word_label.text() == queue()[0])

    # --- Save with Enter, steno R-R; proper nouns routing.
    b.open_word("apple"); pe()
    click(b.add.strokes); typ(b.add.strokes, "AP/-L"); key(b.add.strokes, Qt.Key.Key_Return)
    check(tag + "Enter saves", mine().get("AP/-L") == "apple", mine())
    rows = [b.panel.table.item(r, 0).text() for r in range(b.panel.table.rowCount())]
    check(tag + "the table shows the new entry", "AP/-L" in rows, rows[:10])
    check(tag + "apple leaves the list", "apple" not in queue())
    b.open_word("London"); pe()
    check(tag + "London -> proper nouns", b.target.currentText() == "dotterel-proper-nouns.json",
          b.target.currentText())
    b.add.strokes.setFocus(); pe()
    stroke("HRUPB/TKUPB"); stroke("R-R")
    check(tag + "steno R-R saves into proper nouns", theirs().get("HRUPB/TKUPB") == "London",
          (theirs(), b.add.strokes.text()))
    check(tag + "London not in base", "HRUPB/TKUPB" not in mine())
    b.add.strokes.setFocus(); pe()
    stroke("SKWRUPL")
    check(tag + "after a steno save, no / in front", b.add.strokes.text() == "SKWRUPL",
          repr(b.add.strokes.text()))
    stroke("-G")
    check(tag + "the next stroke joins with /", b.add.strokes.text() == "SKWRUPL/-G",
          repr(b.add.strokes.text()))
    b._clear_outline(); pe()

    # --- Ctrl+D cycles the dictionary; Ctrl+I puts ideas in.
    b.open_word("and"); pe()
    t0 = b.target.currentText()
    key(b, Qt.Key.Key_D, CTRL)
    check(tag + "Ctrl+D: next dictionary", b.target.currentText() != t0, b.target.currentText())
    for _ in range(b.target.count() - 1):
        key(b, Qt.Key.Key_D, CTRL)
    check(tag + "Ctrl+D round the list comes back", b.target.currentText() == t0)

    # --- Clash: take (Alt+1).
    b.open_word("to"); pe()
    b.add.strokes.setFocus(); b.add.strokes.setText("TKOG"); pe()
    check(tag + "clash box for TKOG (dog)", b.clash_box.isVisible() and "dog" in b.clash_title.text(),
          b.clash_title.text())
    tip = b.hints.tooltip(b.clash_buttons["take"])
    check(tag + "Take hint: Alt+1 / THRA/#-R", "Alt+1" in tip and "THRA/#-R" in tip, tip)
    key(b.add.strokes, Qt.Key.Key_1, ALT)
    check(tag + "Alt+1 takes it", mine().get("TKOG") == "to", mine())
    check(tag + "dog is next, marked", b.word_label.text() == "dog"
          and b.queue.currentItem().text().startswith("!"), (b.word_label.text(), queue()))
    # --- Undo from the Outline field: one step puts dog back.
    b.add.strokes.setFocus(); pe()
    key(b.add.strokes, Qt.Key.Key_Z, CTRL)
    check(tag + "Ctrl+Z in the Outline field undoes the take", mine().get("TKOG") == "dog", mine())
    key(b.add.strokes, Qt.Key.Key_Z, CTRL | SHIFT)
    check(tag + "Ctrl+Shift+Z redoes it", mine().get("TKOG") == "to", mine())
    stroke("KHR/STKPW*")  # Ctrl+Z by steno
    check(tag + "steno KHR/STKPW* undoes", mine().get("TKOG") == "dog", (mine(), KB.pressed[-2:]))

    # --- Enter in a clash means Take.
    b.open_word("to"); pe()
    b.add.strokes.setFocus(); b.add.strokes.setText("TKOG"); pe()
    key(b.add.strokes, Qt.Key.Key_Return)
    check(tag + "Enter in a clash takes", mine().get("TKOG") == "to")
    b.panel.undo(); pe()
    check(tag + "panel Undo puts dog back", mine().get("TKOG") == "dog")

    # --- Move (Alt+2): cat gets a free outline (KA*T).
    b.open_word("to"); pe()
    b.add.strokes.setFocus(); b.add.strokes.setText("KAT"); pe()
    check(tag + "move offered", b.clash_buttons["move"].isVisible(), b.clash_buttons["move"].text())
    target = b._move_to
    key(b.add.strokes, Qt.Key.Key_2, ALT)
    check(tag + "Alt+2: KAT = to", mine().get("KAT") == "to")
    check(tag + "Alt+2: cat moved", target and mine().get(steno.text(target)) == "cat",
          (target, mine()))
    b.panel.undo(); pe()
    check(tag + "undo the move: exactly as before", mine().get("KAT") == "cat"
          and steno.text(target) not in mine(), mine())

    # --- Swap (Alt+3): cot takes KAT, cat gets KOT.
    b.open_word("cot"); pe()
    b.add.strokes.setFocus(); b.add.strokes.setText("KAT"); pe()
    check(tag + "swap offered", b.clash_buttons["swap"].isVisible())
    key(b.add.strokes, Qt.Key.Key_3, ALT)
    check(tag + "Alt+3 swaps", mine().get("KAT") == "cot" and mine().get("KOT") == "cat", mine())
    key(b, Qt.Key.Key_Z, CTRL)
    check(tag + "undo the swap", mine().get("KAT") == "cat" and mine().get("KOT") == "cot", mine())

    # --- Keep (Alt+4): nothing changes.
    b.open_word("to"); pe()
    before = mine()
    b.add.strokes.setFocus(); b.add.strokes.setText("KAT"); pe()
    key(b.add.strokes, Qt.Key.Key_4, ALT)
    check(tag + "Alt+4 keeps", mine() == before and b.add.strokes.text() == ""
          and not b.clash_box.isVisible(), mine())

    # --- Redo selected from the table: the new outline replaces the old one.
    b.redo_entries([("apple", base, "AP/-L")]); pe()
    check(tag + "redo opens apple", b.word_label.text() == "apple")
    b.add.strokes.setFocus(); b.add.strokes.setText("A*PL"); pe()
    key(b.add.strokes, Qt.Key.Key_Return)
    check(tag + "redo: new outline replaces the old", mine().get("A*PL") == "apple"
          and "AP/-L" not in mine(), mine())

    # --- Redo last word (Ctrl+R): Enter pressed on a wrong outline.
    key(b, Qt.Key.Key_1, CTRL)  # Popular words
    w = b.word_label.text()
    b.add.strokes.setFocus(); b.add.strokes.setText("TPHRAOEUFP"); pe()
    key(b.add.strokes, Qt.Key.Key_Return)
    check(tag + "wrong outline saved", mine().get("TPHRAOEUFP") == w)
    check(tag + "Redo button names the word", w in b.redo_last_button.text() and b.redo_last_button.isEnabled())
    tip = b.hints.tooltip(b.redo_last_button)
    check(tag + "Redo last hint: Ctrl+R / KHR/R*", "Ctrl+R" in tip and "KHR/R*" in tip, tip)
    key(b.add.strokes, Qt.Key.Key_R, CTRL)
    check(tag + "Ctrl+R reopens it, still Popular", b.word_label.text() == w and b.popular_button.isChecked()
          and queue()[0] == w, (b.word_label.text(), queue()[:3]))
    b.add.strokes.setText("TPHRAOEUFPS"); pe()
    key(b.add.strokes, Qt.Key.Key_Return)
    check(tag + "new outline replaces the wrong one", mine().get("TPHRAOEUFPS") == w
          and "TPHRAOEUFP" not in mine(), mine())
    check(tag + "word leaves the list again", w not in queue())
    # Redo last word after taking an outline from another word: it goes back.
    w = b.word_label.text()
    b.add.strokes.setFocus(); b.add.strokes.setText("TKOG"); pe()
    key(b.add.strokes, Qt.Key.Key_Return)  # Enter in a clash = take
    check(tag + "took TKOG from dog by mistake", mine().get("TKOG") == w, mine())
    key(b.add.strokes, Qt.Key.Key_R, CTRL)
    check(tag + "Ctrl+R gives TKOG back to dog", mine().get("TKOG") == "dog", mine())
    check(tag + "and reopens the word", b.word_label.text() == w and "dog" not in queue(),
          (b.word_label.text(), queue()[:4]))
    check(tag + "note says what was given back", "dog" in b.note.text(), b.note.text())
    key(b, Qt.Key.Key_Z, CTRL)
    check(tag + "Ctrl+Z undoes the give-back", mine().get("TKOG") == w, mine())
    key(b, Qt.Key.Key_Z, CTRL | SHIFT)
    check(tag + "Ctrl+Shift+Z gives it back again", mine().get("TKOG") == "dog", mine())
    key(b, Qt.Key.Key_2, CTRL)  # back to My words

    # --- Skip (Ctrl+K), next/previous (Ctrl+Down/Up).
    b.own_word.setText("one, two, three"); b.add_own_word(); pe()
    w0 = b.word_label.text()
    b.add.strokes.setFocus(); pe()
    key(b.add.strokes, Qt.Key.Key_Down, CTRL)
    w1 = b.word_label.text()
    key(b.add.strokes, Qt.Key.Key_Up, CTRL)
    check(tag + "Ctrl+Down / Ctrl+Up", w1 != w0 and b.word_label.text() == w0, (w0, w1))
    # Fix the word's spelling on the card.
    key(b, Qt.Key.Key_W, CTRL)
    check(tag + "Ctrl+W: the word can be changed", b.word_label.hasFocus())
    b.word_label.setText(w0 + "q"); b.word_label.returnPressed.emit(); pe()
    check(tag + "spelling fixed: card, list and Outline field", b._word == w0 + "q"
          and b.queue.currentItem().data(builder_mod.ROLE) == w0 + "q" and b.add.strokes.hasFocus(),
          (b._word, b.queue.currentItem().data(builder_mod.ROLE)))
    b.word_label.setText(w0); b.word_label.editingFinished.emit(); pe()
    check(tag + "and back", b._word == w0 and b.queue.currentItem().text().endswith(w0))
    n_before = b.queue.count()
    key(b.add.strokes, Qt.Key.Key_K, CTRL)
    check(tag + "Ctrl+K skips", b.queue.count() == n_before - 1 and w0 not in queue())

    # --- Ctrl+1 back to Popular; Ctrl+I ideas.
    key(b, Qt.Key.Key_1, CTRL)
    check(tag + "Ctrl+1 = Popular words", b.popular_button.isChecked())
    b.open_word("cats"); pe()
    key(b, Qt.Key.Key_I, CTRL)
    first_idea = b.add.strokes.text()
    check(tag + "Ctrl+I puts a free idea", first_idea != "" and
          steno.writes(e.dictionaries, steno.parse(first_idea))[0] is None, first_idea)

    # --- Panel shortcuts.
    key(b, Qt.Key.Key_F, CTRL)
    check(tag + "Ctrl+F: search", app.focusWidget() is b.panel.search)
    f0 = b.panel.filters.isVisibleTo(b)
    key(b, Qt.Key.Key_F, CTRL | SHIFT)
    check(tag + "Ctrl+Shift+F: filters", b.panel.filters.isVisibleTo(b) != f0)
    s0 = b.panel.scope.currentIndex()
    key(b, Qt.Key.Key_L, ALT)
    check(tag + "Alt+L: next Look in", b.panel.scope.currentIndex() != s0)
    fo = b.panel.follow.isChecked()
    key(b, Qt.Key.Key_W, CTRL | SHIFT)
    check(tag + "Ctrl+Shift+W: follow", b.panel.follow.isChecked() != fo)

    # --- Filters: tick dictionaries off and on in the table.
    def dict_rows():
        return {b.panel.table.item(r, 4).text() for r in range(b.panel.table.rowCount())}
    b.panel.search.clear(); b.panel.only_mine.setChecked(False); pe(40)
    b.panel.fill_table(); pe()
    menu_actions = [a for a in b.panel.dict_menu.actions() if a.isCheckable()]
    base_action = [a for a in menu_actions if a.text() == "dotterel-base.json"]
    check(tag + "dictionaries menu lists every dictionary", len(menu_actions) >= 7 and base_action,
          [a.text() for a in menu_actions])
    check(tag + "base shown at first", "dotterel-base.json" in dict_rows(), dict_rows())
    base_action[0].setChecked(False); pe(10)
    check(tag + "untick base: its rows go", "dotterel-base.json" not in dict_rows(), dict_rows())
    check(tag + "button says how many shown", "Dictionaries:" in b.panel.dict_button.text(),
          b.panel.dict_button.text())
    base_action = [a for a in b.panel.dict_menu.actions() if a.text() == "dotterel-base.json"]
    base_action[0].setChecked(True); pe(10)
    check(tag + "tick it again: back", "dotterel-base.json" in dict_rows())

    practice_round(tag, tmp, base, mine)
    b.close()
    pe()
    shutil.rmtree(tmp, ignore_errors=True)


def practice_round(tag, tmp, base, mine):
    from plover_dotterel import practice as pr, logstats
    sys.path.insert(0, HERE)
    from test_practice_facts import make_epub
    p = b.practice

    # --- Alt+P opens Practice with a words test.
    key(b, Qt.Key.Key_P, ALT)
    check(tag + "Alt+P: Practice tab", b.tabs.currentWidget() is p)
    check(tag + "words mode, 50 words", p.mode == "words" and p.test and len(p.test.words) == 50,
          (p.mode, p.test and len(p.test.words)))
    check(tag + "only your words", set(p.test.words) <= set(p.your_words()), set(p.test.words))
    check(tag + "focus in the input field", app.focusWidget() is p.input)
    kinds = (QPushButton, QCheckBox, QToolButton, QComboBox, QLineEdit)
    missing = [w.text() if hasattr(w, "text") else type(w).__name__
               for k in kinds for w in p.findChildren(k)
               if w.isVisibleTo(b) and w not in b.hints._hints and not isinstance(w.parent(), QComboBox)]
    check(tag + "Practice: every visible button has a hint", not missing, missing)
    keys = [k for k, _a, _s in b.hints.shortcuts]
    check(tag + "still no shortcut used twice", len(keys) == len(set(keys)),
          {k for k in keys if keys.count(k) > 1})
    check(tag + "every shortcut has steno (but zoom in: no =)",
          {k for k in set(keys) if not b.hints.finder.outlines(k)} <= {"Ctrl++", "Ctrl+="},
          [k for k in set(keys) if not b.hints.finder.outlines(k)])
    check(tag + "no time mode", "time" not in p.mode_buttons)
    check(tag + "lengths 50 100 200", [x.text() for x in p.length_buttons if x.isVisibleTo(b)]
          == ["50", "100", "200"])

    # --- Steno into the field: strokes are counted, text is exact.
    first = p.test.words[0]
    outline = steno.text(steno.outlines_for(e.dictionaries, first)[0][0])
    stroke(outline)
    check(tag + "a stroke writes into the field", p.input.text().strip() == first, p.input.text())
    check(tag + "the stroke is counted", p.test.strokes in (0, 1))

    # --- Write all 50 right (Plover's space before each word).
    text = p.input.text()
    for w in p.test.words[1:]:
        text += " " + w
        p.input.setText(text); pe(1)
    check(tag + "50 right words end the test", p.result_box.isVisible() and not p.test_box.isVisible())
    check(tag + "accuracy 100", p.big["acc"].text() == "100%",
          (p.big["acc"].text(), first, outline, p._last_result["chars"], p._last_result["missed"]))
    check(tag + "saved", len(p.store.tests) == 1 and p.store.tests[0]["mode"] == "words")
    check(tag + "no missed words", "No words missed" in p.missed_label.text())

    # --- Alt+N: a test with a mistake; missed word shows your outline.
    key(b, Qt.Key.Key_N, ALT)
    check(tag + "Alt+N new test", p.test_box.isVisible() and p.input.text() == "")
    ws = p.test.words
    typed = ["xyz"] + ws[1:]
    p.input.setText(" ".join(typed)); pe(3)
    check(tag + "mistake: missed word listed", ws[0] in p.missed_label.text()
          and "xyz" in p.missed_label.text(), p.missed_label.text()[:200])
    shown = steno.text(steno.outlines_for(e.dictionaries, ws[0])[0][0])
    check(tag + "missed word shows its outline", shown in p.missed_label.text())
    check(tag + "accuracy below 100", p.big["acc"].text() != "100%")
    check(tag + "Practise missed on", p.missed_button.isEnabled())
    key(b, Qt.Key.Key_X, ALT)
    check(tag + "Alt+X drills the missed word", set(p.test.words) == {ws[0]}, set(p.test.words))

    # --- Lengths and tips.
    key(b, Qt.Key.Key_7, ALT)
    check(tag + "Alt+7: next length (100)", len(p.test.words) == 100 and p.length["words"] == 100)
    key(b, Qt.Key.Key_T, ALT)
    w0 = p.test.words[0]
    best = steno.text(steno.outlines_for(e.dictionaries, w0)[0][0])
    check(tag + "Alt+T tips show the outline", p.tips_label.isVisible() and best in p.tips_label.text(),
          p.tips_label.text()[:200])

    # --- A wrong letter is shown red on the text, the caret after it.
    p.input.setText("x"); pe()
    check(tag + "wrong letter red", pr.WRONG in p.text.text())
    p.input.setText(""); pe()

    # --- Book: open, write part, leave, place and text file saved.
    path = os.path.join(tmp, "small.epub")
    make_epub(path)
    p.open_book(path); pe()
    check(tag + "book mode after opening", p.mode == "book" and p.test is not None)
    check(tag + "book starts at the start", p.test.words[:3] == ["Chapter", "One", '"Well,"'],
          p.test.words[:5])
    written = ["Chapter", "One", '"Well,"', "said", "the", "cat,", "'it's", "a", "colour.'"]
    p.input.setText(" ".join(written) + " T"); pe()
    key(b, Qt.Key.Key_N, ALT)  # stop half-way: results, and what you wrote is kept
    check(tag + "Alt+N in a book: stop and see results", p.result_box.isVisible())
    info = json.load(open(os.path.join(tmp, "dotterel_practice.json")))["books"]
    pos = list(info.values())[0]["position"]
    check(tag + "place saved after stopping", pos == len(written), pos)
    check(tag + "the session is in Stats", p.store.tests[-1].get("unit") == "session"
          and p.store.tests[-1]["words_typed"] >= len(written), p.store.tests[-1])
    key(b, Qt.Key.Key_N, ALT)
    check(tag + "next test starts there", p.test.words[0] == "The", p.test.words[:3])
    check(tag + "no lengths in a book", not any(x.isVisibleTo(b) for x in p.length_buttons)
          and not p.unit_label.isVisibleTo(b))
    check(tag + "endless: the next chapter is part of the same text", "Chapter" in p.test.words
          and p.test.words[-1] == "fell.", p.test.words)
    check(tag + "no small hint under the field", not p.hint.isVisibleTo(b))
    book_file = os.path.join(tmp, "Dotterel books", "A Small Book")
    check(tag + "text file, no extension, named after the book", os.path.exists(book_file),
          os.listdir(os.path.join(tmp, "Dotterel books")) if os.path.isdir(os.path.join(tmp, "Dotterel books")) else None)
    content = open(book_file).read()
    check(tag + "the file has exactly what you wrote", "colour.'" in content and "Chapter One" in content,
          content)
    # Saved after each paragraph, without stopping.
    p.input.setText("The dog sat on the mat. C"); pe()
    pos = p.store.book(p._book["id"])["position"]
    check(tag + "saved after a paragraph", pos == len(written) + 6, pos)
    p.input.setText("The dog sat on the mat."); pe()
    p.outline_current_word(); pe()
    check(tag + "a written word: Alt+D takes the next one, where the caret is", b._word == "chapter", b._word)
    p.back_after = None; b.tabs.setCurrentWidget(p); pe()
    check(tag + "every word drawn can be clicked", len(p.text.spans) > 5)
    p.input.setText("C"); pe()
    # Outline for this word: Add words, save, back to the same place.
    key(b, Qt.Key.Key_D, ALT)
    check(tag + "Alt+D: the word in Add words", b.tabs.currentIndex() == 0 and b._word == "chapter", b._word)
    b.add.strokes.setText("KHAPT"); pe(); b.save(); pe()
    check(tag + "after saving: back in the book, same place",
          b.tabs.currentWidget() is p and p.test is not None and p.test.words[0] == "Chapter",
          (b.tabs.currentIndex(), p.test and p.test.words[:2]))
    p.input.setText(" ".join(p.test.words)); pe()
    content = open(book_file).read()
    check(tag + "whole book written, chapters and paragraphs",
          content.splitlines() == ["A Small Book", "", "Chapter One",
                                   "\"Well,\" said the cat, 'it's a colour.'",
                                   "The dog sat on the mat.", "", "Chapter Two",
                                   "London was grey and the rain fell."], content.splitlines())
    check(tag + "end of the book", p.result_box.isVisible())

    # --- Book navigation: paragraphs, chapters, skipping a chapter.
    p._go_to(0); pe()
    check(tag + "the next chapter shows, same size, to read ahead",
          ">Two<" in p.text.text() and ">London<" in p.text.text() and "font-size" not in p.text.text())
    check(tag + "paragraphs shown as lines", "<br>" in p.text.text())
    key(b, Qt.Key.Key_Down, ALT)
    check(tag + "Alt+Down: next paragraph", p._position() == 2 and p.test.words[0] == '"Well,"',
          (p._position(), p.test.words[:2]))
    key(b, Qt.Key.Key_Down, ALT)
    check(tag + "Alt+Down again", p.test.words[0] == "The", p.test.words[:2])
    key(b, Qt.Key.Key_Up, ALT)
    check(tag + "Alt+Up: back a paragraph", p.test.words[0] == '"Well,"', p.test.words[:2])
    key(b, Qt.Key.Key_PageDown, ALT)
    check(tag + "Alt+PgDown: next chapter", p.test.words[:2] == ["Chapter", "Two"], p.test.words[:2])
    key(b, Qt.Key.Key_PageUp, ALT)
    check(tag + "Alt+PgUp: previous chapter", p.test.words[:2] == ["Chapter", "One"], p.test.words[:2])
    key(b, Qt.Key.Key_Delete, ALT)
    check(tag + "Alt+Del skips chapter one", p.test.words[:2] == ["Chapter", "Two"]
          and p.chapter_box.itemText(0).startswith("(skipped)"), (p.test.words[:2], p.chapter_box.itemText(0)))
    p._go_to(0); pe()
    check(tag + "a skipped chapter is passed by", p.test.words[:2] == ["Chapter", "Two"], p.test.words[:2])
    key(b, Qt.Key.Key_PageUp, ALT)
    check(tag + "Previous chapter passes it too", p.test.words[:2] == ["Chapter", "Two"])
    saved = json.load(open(os.path.join(tmp, "dotterel_practice.json")))["books"]
    check(tag + "skip is saved", list(saved.values())[0]["skipped"] == [0])
    p.chapter_box.setCurrentIndex(1); p._sync_chapter(); pe()
    key(b, Qt.Key.Key_Delete, ALT)  # on chapter two now: skip it too...
    key(b, Qt.Key.Key_Delete, ALT)  # ...and take it back
    check(tag + "Alt+Del again takes the skip back", p.test.words[:2] == ["Chapter", "Two"]
          and not p.chapter_box.itemText(1).startswith("(skipped)"), (p.test.words[:2], p.chapter_box.itemText(1)))

    # --- Stats: tests and the log.
    log = os.path.join(tmp, "strokes.log")
    from test_practice_facts import LOG
    open(log, "w").write(LOG.replace("2026-11-07", time.strftime("%Y-%m-%d")))
    logstats.log_path = lambda _c: log
    key(b, Qt.Key.Key_G, ALT)
    s = b.stats
    check(tag + "Alt+G: Stats", b.tabs.currentWidget() is s)
    check(tag + "tests counted", s.tiles["tests completed"].text() == str(len(p.store.tests)),
          (s.tiles["tests completed"].text(), len(p.store.tests)))
    check(tag + "recent tests table", s.recent.rowCount() == len(p.store.tests))
    fixes = s.tables["fixes"]
    check(tag + "log: the fix cat -> cot", fixes.rowCount() == 1 and fixes.item(0, 0).text() == "cat"
          and fixes.item(0, 2).text() == "cot", fixes.rowCount())
    check(tag + "log: misstroke", s.tables["untranslated"].item(0, 0).text() == "TKPWOEU")
    check(tag + "log: backspaced dog", s.tables["backspaced"].item(0, 0).text() == "dog")
    key(b, Qt.Key.Key_A, ALT)
    check(tag + "Alt+A back to Add words", b.tabs.currentIndex() == 0)

    # --- Text size.
    size = b.word_label.fontInfo().pointSizeF()
    key(b, Qt.Key.Key_Equal, CTRL); key(b, Qt.Key.Key_Equal, CTRL)
    check(tag + "Ctrl+= twice: 120%", b.zoom_label.text() == "120%", b.zoom_label.text())
    check(tag + "the word is bigger", b.word_label.fontInfo().pointSizeF() > size,
          (size, b.word_label.fontInfo().pointSizeF()))
    check(tag + "the table is bigger too", b.panel.table.verticalHeader().defaultSectionSize() > 26)
    key(b, Qt.Key.Key_Minus, CTRL)
    check(tag + "Ctrl+- smaller", b.zoom_label.text() == "110%")
    key(b, Qt.Key.Key_0, CTRL)
    check(tag + "Ctrl+0 back to 100%", b.zoom_label.text() == "100%" and
          abs(b.word_label.fontInfo().pointSizeF() - size) < 0.6)


rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
for n in range(1, rounds + 1):
    one_round(n)
bad = [r for r in results if not r[1]]
print(f"\n{len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)

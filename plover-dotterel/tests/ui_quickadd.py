"""The small add window (TK*UPT), driven like you would.

Run:  QT_QPA_PLATFORM=offscreen python tests/ui_quickadd.py
"""

import json
import os
import sys
import tempfile
import threading
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

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

from plover_dotterel import quickadd  # noqa: E402
from plover_dotterel.outlines import OutlinePanel  # noqa: E402

registry.register_plugin("command", "dotterel_add", quickadd.quick_add)

HERE = os.path.dirname(os.path.abspath(__file__))
DICTS = os.path.join(HERE, "..", "plover_dotterel", "dictionaries")
app = QApplication.instance() or QApplication([])
results = []
SHIFT = Qt.KeyboardModifier.ShiftModifier


def pe(n=6):
    for _ in range(n):
        QCoreApplication.processEvents()
        time.sleep(0.005)


class KB:
    def send_string(self, s):
        w = app.focusWidget()
        if s and hasattr(w, "insert"):
            w.insert(s)

    def send_backspaces(self, n):
        w = app.focusWidget()
        for _ in range(n):
            if hasattr(w, "backspace"):
                w.backspace()

    def send_key_combination(self, combo):
        pass

    def set_key_press_delay(self, *a):
        pass


class Eng(StenoEngine):
    def __init__(self, tmp):
        cfg = Config(os.path.join(tmp, "plover.cfg"))
        cfg.update(machine_type="Gemini PR", system_name="Dotterel")
        super().__init__(cfg, None, KB())

    def signal_connect(self, name, cb):
        pass


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name, "" if cond else extra)


def stroke(outline):
    for s in outline.split("/"):
        e._on_stroked(Stroke(s).keys())
        pe()


def key(w, k, mod=Qt.KeyboardModifier.NoModifier):
    QTest.keyClick(w, k, mod)
    pe()


tmp = tempfile.mkdtemp()
base = os.path.join(tmp, "dotterel-base.json")
names = os.path.join(tmp, "dotterel-proper-nouns.json")
json.dump({"KAT": "cat", "KOT": "cot", "THE": "the"}, open(base, "w"))
json.dump({}, open(names, "w"))
e = Eng(tmp)
ds = [load_dictionary(base), load_dictionary(names)]
ds += [load_dictionary(os.path.join(DICTS, d)) for d in system.DEFAULT_DICTIONARIES[2:]
       if not d.endswith("affixes.json")]
e._dictionaries.set_dicts(ds)
e._is_running = False
e._set_output(True)
app.engine = e


def mine(path=base):
    return {"/".join(k): v for k, v in e._dictionaries[path].items()}


def on_disk(path=base):
    OutlinePanel.wait_saves()
    return json.load(open(path))


# --- TK*UPT opens it with the last word, from the engine's thread.
check("TK*UPT is in the commands", e._dictionaries.lookup(("TK*UPT",)) == "{PLOVER:DOTTEREL_ADD}")
stroke("THE")
stroke("KAT")
t = threading.Thread(target=quickadd.quick_add, args=(e,))
t.start(); t.join()
pe(10)
w = quickadd.QuickAdd._open
check("opens from another thread", w is not None and w.isVisible())
check("grabs the last word", w.word.text() == "cat", w.word.text())
check("the word is selected, focus on it", w.word.hasFocus() and w.word.selectedText() == "cat")
check("shows what it has", "KAT" in w.info.text(), w.info.text())
check("small", w.width() < 500, w.width())

# --- Type your own word, Enter, write outlines.
QTest.keyClicks(w.word, "dot"); pe()
check("typing replaces it", w.word.text() == "dot", w.word.text())
key(w.word, Qt.Key.Key_Return)
check("Enter: to the outline", w.outline.hasFocus())
stroke("KAT")
check("steno goes in as strokes", w.outline.text() == "KAT", w.outline.text())
check("clash shown", "⚠" in w.info.text() and "cat" in w.info.text()
      and "dotterel-base.json" in w.info.text(), w.info.text())
w._new_outline()
e._dictionaries[names][("KAT",)] = "Kat"  # the same outline lower down
w._new_outline(); stroke("KAT")
check("clash shows the lower one too", "also “Kat”" in w.info.text()
      and "dotterel-proper-nouns.json" in w.info.text(), w.info.text())
del e._dictionaries[names][("KAT",)]
w._new_outline()
stroke("TKOT")
check("no clash for a free outline", "⚠" not in w.info.text(), w.info.text())
key(w.outline, Qt.Key.Key_Return, SHIFT)
check("Shift+Enter keeps it, field empty", w.outline.text() == "" and "TKOT" in w.info.text()
      and w.isVisible(), (w.outline.text(), w.info.text()))
check("nothing saved yet", "TKOT" not in mine())
stroke("TKO*T")
check("second outline in the field", w.outline.text() == "TKO*T", w.outline.text())
key(w.outline, Qt.Key.Key_Return)
pe(10)
check("Enter: both saved", mine().get("TKOT") == "dot" and mine().get("TKO*T") == "dot", mine())
check("written to the file", on_disk().get("TKO*T") == "dot")
check("Enter closes it", quickadd.QuickAdd._open is None)
check("the engine writes words again", e._dictionaries.lookup(("KAT",)) == "cat"
      and not e._dictionaries.filters, e._dictionaries.filters)
stroke("KAT")
check("translator back to normal after", any(t.english == "cat" for t in e.translator_state.translations))

# --- Escape adds nothing.
stroke("TK*UPT")
pe(10)
w = quickadd.QuickAdd._open
check("the stroke itself opens it", w is not None and w.isVisible())
check("last word again", w.word.text() == "cat", w.word.text())
w.word.setText("fox"); key(w.word, Qt.Key.Key_Return)
stroke("TPOBGS")
key(w.outline, Qt.Key.Key_Return, SHIFT)
stroke("TPO*BGS")
key(w.outline, Qt.Key.Key_Escape)
pe(10)
check("Escape closes", quickadd.QuickAdd._open is None)
check("Escape added nothing", "fox" not in mine().values(), mine())

# --- A name goes to proper nouns; your steno Enter adds.
w = quickadd.show(e)
w.word.setText("London"); key(w.word, Qt.Key.Key_Return)
stroke("HROPB")
stroke("R-R")
pe(10)
check("R-R adds it", quickadd.QuickAdd._open is None)
check("name in proper nouns", mine(names).get("HROPB") == "London" and "HROPB" not in mine(), mine(names))

# --- Choosing the dictionary.
CTRL = Qt.KeyboardModifier.ControlModifier
w = quickadd.show(e)
w.word.setText("owl")
check("a word: base", w.target.currentData() == base, w.target.currentText())
w.word.setText("Paris")
check("a name: proper nouns", w.target.currentData() == names, w.target.currentText())
key(w.word, Qt.Key.Key_Up, CTRL)
check("Ctrl+Up does nothing", w.target.currentData() == names, w.target.currentText())
key(w.word, Qt.Key.Key_Up)
check("Up: the one above", w.target.currentData() == base, w.target.currentText())
w.word.setText("Rome")
check("your pick stays when the word changes", w.target.currentData() == base)
key(w.word, Qt.Key.Key_Return)
key(w.outline, Qt.Key.Key_Down)
check("Down works in the outline too", w.target.currentData() == names)
key(w.outline, Qt.Key.Key_Up)
stroke("RO*EPL")
key(w.outline, Qt.Key.Key_Return)
pe(10)
check("saved where you picked", mine().get("RO*EPL") == "Rome" and "RO*EPL" not in mine(names))
w = quickadd.show(e)
w.word.setText("Oslo")
check("a new window picks again", w.target.currentData() == names)
key(w.word, Qt.Key.Key_Escape)

# --- Enter with no outline does nothing.
w = quickadd.show(e)
w.word.setText("owl"); key(w.word, Qt.Key.Key_Return)
key(w.outline, Qt.Key.Key_Return)
check("Enter with no outline stays open", quickadd.QuickAdd._open is w and "owl" not in mine().values())
key(w.outline, Qt.Key.Key_Escape)

bad = [r for r in results if not r[1]]
print(f"\n{len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)

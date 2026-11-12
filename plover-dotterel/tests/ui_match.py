"""The outline you write lights up when it is a known one.

In the Builder and in the small add window: write an outline that Lapwing,
an idea or your own dictionary already has, and that one turns green with a
tick. Part-way through a longer outline, the strokes written so far are
green.

Run:  QT_QPA_PLATFORM=offscreen python tests/ui_match.py [folder for screenshots]
"""

import json
import os
import sys
import tempfile
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication
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

from plover_dotterel import cambridge, quickadd, steno  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DICTS = os.path.join(HERE, "..", "plover_dotterel", "dictionaries")
SHOTS = sys.argv[1] if len(sys.argv) > 1 else None
app = QApplication.instance() or QApplication([])
results = []
GREEN = steno.GREEN


def pe(n=8):
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
        self._sigs = {}

    def signal_connect(self, name, cb):
        self._sigs.setdefault(name, []).append(cb)


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name, "" if cond else extra)


def stroke(outline):
    for s in outline.split("/"):
        e._on_stroked(Stroke(s).keys())
        pe()


def shot(widget, name):
    if SHOTS:
        os.makedirs(SHOTS, exist_ok=True)
        widget.grab().save(os.path.join(SHOTS, name))


# --- steno.match_html, without a window.
m = steno.match_html
check("same outline: green with a tick", GREEN in m(("KAT",), ("KAT",)) and "✓" in m(("KAT",), ("KAT",)))
check("another outline: plain", m(("KAT",), ("KOT",)) == "KAT")
check("nothing written: plain", m(("KAT",), ()) == "KAT")
part = m(("SE", "KRE", "TREU"), ("SE", "KRE"))
check("part-way: the strokes so far are green", f"<span style='color:{GREEN}'>SE/KRE</span>/TREU" == part, part)
check("a longer outline than the idea: plain", m(("SE",), ("SE", "KRE")) == "SE")
check("same_outline reads text too", steno.same_outline("kat/-s", ("KAT", "-S")))

tmp = tempfile.mkdtemp()
base = os.path.join(tmp, "dotterel-base.json")
names = os.path.join(tmp, "dotterel-proper-nouns.json")
json.dump({"KAT": "cat", "THE": "the", "WAUBG": "walk"}, open(base, "w"))
json.dump({}, open(names, "w"))
e = Eng(tmp)
ds = [load_dictionary(base), load_dictionary(names), load_dictionary(os.path.join(HERE, "affixes.json"))]
ds += [load_dictionary(os.path.join(DICTS, d)) for d in system.DEFAULT_DICTIONARIES[3:]]
e._dictionaries.set_dicts(ds)
e._is_running = False
e._set_output(True)
app.engine = e
cambridge.lookup = lambda w: {"word": w, "uk": {"ipa": "", "files": {}}, "us": {"ipa": "", "files": {}},
                              "defs": []}

import plover.oslayer.config as pconf  # noqa: E402
from plover_dotterel import practice as pr  # noqa: E402

pconf.CONFIG_DIR = tmp
pr.BOOKS_DIR = os.path.join(tmp, "Dotterel books")
_init = pr.Store.__init__
pr.Store.__init__ = lambda self, path=None: _init(self, path or os.path.join(tmp, "dotterel_practice.json"))

from plover_dotterel.builder import DotterelBuilder  # noqa: E402

# --- The Builder.
b = DotterelBuilder(e)
b.show()
b.activateWindow()
pe(20)
b.set_source("mine")
b.own_word.setText("secretary")
b.add_own_word()
pe(20)
lap = [steno.text(o) for o in steno.lapwing("secretary")]
check("Builder: Lapwing's outlines are shown", lap and all(o in b.facts.text() for o in lap[:5]), b.facts.text())
check("Builder: nothing green before you write", GREEN not in b.facts.text(), b.facts.text())
target = lap[0]
b.add.strokes.setFocus()
pe()
first = target.split("/")[0]
stroke(first)
if "/" in target:
    check("Builder: part-way, the first stroke is green",
          f"<span style='color:{GREEN}'>{first}</span>" in b.facts.text(), b.facts.text())
    shot(b, "builder-part-way.png")
    stroke("/".join(target.split("/")[1:]))
check("Builder: the outline is in the field", b.add.strokes.text() == target, b.add.strokes.text())
check("Builder: Lapwing's outline is green with a tick",
      f"<b style='color:{GREEN}'>✓ {target}</b>" in b.facts.text(), b.facts.text())
check("Builder: a line says why", "as in Lapwing" in b.facts.text(), b.facts.text())
shot(b, "builder-match.png")
b.add.strokes.setText("KPWHR")
pe()
check("Builder: an outline of your own: nothing green", GREEN not in b.facts.text(), b.facts.text())
# A word made from parts: the idea turns green.
b.own_word.setText("walking")
b.add_own_word()
pe(20)
check("Builder: idea from parts shown", "WAUBG/-G" in b.facts.text() or "WAUBGG" in b.facts.text(), b.facts.text())
b.add.strokes.setFocus()
pe()
stroke("WAUBG/-G")
check("Builder: the idea you wrote is green", f"✓ WAUBG/-G" in b.facts.text(), b.facts.text())
check("Builder: with its reason", "walk + ing" in b.facts.text(), b.facts.text())
b.close()
pe(10)

# --- The small add window.
w = quickadd.show(e)
pe(10)
w.word.setText("secretary")
pe()
check("Add: Lapwing's outlines are shown", "Lapwing" in w.info.text() and lap[0] in w.info.text(), w.info.text())
check("Add: nothing green before you write", GREEN not in w.info.text())
w.outline.setFocus()
pe()
stroke(target)
check("Add: Lapwing's outline is green with a tick",
      f"<b style='color:{GREEN}'>✓ {target}</b>" in w.info.text(), w.info.text())
shot(w, "add-match.png")
w.word.setText("cat")
w.outline.setText("KAT")
pe()
check("Add: an outline the word already has is green", f"✓ KAT" in w.info.text(), w.info.text())
w.outline.setText("KOT")
pe()
check("Add: another outline: not green", GREEN not in w.info.text(), w.info.text())
w.reject()
pe(10)

bad = [r for r in results if not r[1]]
print(f"\n{len(results) - len(bad)}/{len(results)} passed")
sys.exit(1 if bad else 0)

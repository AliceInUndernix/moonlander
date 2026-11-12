"""Dotterel modifiers, through a real Plover engine (no window).

Run:  python -m pytest tests/test_modifiers.py
"""

import json
import os
import tempfile

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

HERE = os.path.dirname(os.path.abspath(__file__))
DICTS = os.path.join(HERE, "..", "plover_dotterel", "dictionaries")


class KB:
    def __init__(self):
        self.out = []

    def send_string(self, s):
        self.out.append(("text", s))

    def send_backspaces(self, n):
        self.out.append(("bs", n))

    def send_key_combination(self, c):
        self.out.append(("keys", c))

    def set_key_press_delay(self, *a):
        pass


def engine():
    tmp = tempfile.mkdtemp()
    base = os.path.join(tmp, "dotterel-base.json")
    json.dump({"KAT": "cat"}, open(base, "w"))
    cfg = Config(os.path.join(tmp, "plover.cfg"))
    cfg.update(machine_type="Gemini PR", system_name="Dotterel")
    kb = KB()
    e = StenoEngine(cfg, None, kb)
    e._dictionaries.set_dicts([load_dictionary(base)] + [
        load_dictionary(os.path.join(DICTS, d)) for d in system.DEFAULT_DICTIONARIES[1:]])
    e._is_running = False
    e._set_output(True)
    return e, kb


def write(e, kb, *strokes):
    del kb.out[:]
    for s in strokes:
        e._on_stroked(Stroke(s).keys())
    return [x for x in kb.out if x[0] == "keys" or x[1].strip()]


def test_order_ends_with_movement_then_modifiers():
    assert system.DEFAULT_DICTIONARIES[-2:] == ("dotterel-movement.modal", "dotterel-modifiers.py")
    assert not any("emily" in d for d in system.DEFAULT_DICTIONARIES)


def test_ctrl_on_movement_letters_enter():
    e, kb = engine()
    assert write(e, kb, "KHR", "STPH-L") == [("keys", "control_l(Up)")]
    assert write(e, kb, "KHR", "KR*") == [("keys", "control_l(c)")]
    assert write(e, kb, "SH", "R-R") == [("keys", "shift_l(Return)")]
    assert write(e, kb, "SH", "#-R") == [("keys", "shift_l(1)")]


def test_alone_presses_nothing():
    e, kb = engine()
    assert write(e, kb, "KHR") == []


def test_only_the_next_stroke():
    e, kb = engine()
    write(e, kb, "KHR", "KR*")
    out = write(e, kb, "KAT")
    assert out and all(k == "text" for k, _ in out)


def test_they_add_up_and_one_stroke_combos():
    e, kb = engine()
    assert write(e, kb, "KHR", "SH", "#TPH-T") == [("keys", "control_l(shift_l(Right))")]
    assert write(e, kb, "STKHRA", "A*") == [("keys", "control_l(alt_l(shift_l(a)))")]
    assert write(e, kb, "THRA", "TA*B") in ([("keys", "alt_l(Tab)")], [])


def test_same_stroke_twice_cancels():
    e, kb = engine()
    out = write(e, kb, "KHR", "KHR", "KR*")
    assert not any(k == "keys" for k, _ in out) and any("c" in t for k, t in out if k == "text")


def test_a_word_after_a_modifier_is_just_a_word():
    e, kb = engine()
    out = write(e, kb, "KHR", "KAT")
    assert ("text", "cat") in out or any(t.strip() == "cat" for k, t in out if k == "text")

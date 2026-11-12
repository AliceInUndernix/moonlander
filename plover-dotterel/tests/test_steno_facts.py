"""Tests for steno.py: outlines, ideas, clashes and the clash plans.

Uses real Plover dictionaries (JSON files in a temporary folder) on the
Dotterel system. Run:  python -m pytest tests
"""

import json
import os

import pytest

from plover import system
from plover.dictionary.base import load_dictionary
from plover.registry import registry
from plover.steno_dictionary import StenoDictionaryCollection

HERE = os.path.dirname(__file__)
AFFIXES = os.path.join(HERE, "affixes.json")  # every affix entry of dotterel-base.json (from Lapwing)


@pytest.fixture(scope="module", autouse=True)
def dotterel():
    registry.update()
    import plover_dotterel.system
    registry.register_plugin("system", "Dotterel", plover_dotterel.system)
    system.setup("Dotterel")


from plover_dotterel import steno  # noqa: E402  (after the system is set up)

P = steno.parse


def make(tmp_path, base=None, names=None):
    """Dictionaries in Dotterel's order: base, proper nouns, affixes."""
    files = []
    for name, data in (("dotterel-base.json", base or {}),
                       ("dotterel-proper-nouns.json", names or {})):
        path = tmp_path / name
        path.write_text(json.dumps(data))
        files.append(str(path))
    dicts = [load_dictionary(f) for f in files] + [load_dictionary(AFFIXES)]
    return StenoDictionaryCollection(dicts), files


def apply(dicts, changes):
    """Do what the outline table does with a plan."""
    for path, key, new in changes:
        d = dicts[path]
        if d.readonly:
            continue
        if new is None:
            if key in d:
                del d[key]
        else:
            d[key] = new


# Facts --------------------------------------------------------------------

def test_parse():
    assert P("kat/-s") == ("KAT", "-S")
    assert P(" /KAT/ ") == ("KAT",)
    with pytest.raises(ValueError):
        P("XYZ")


def test_outlines_and_writes(tmp_path):
    d, _ = make(tmp_path, {"KAT": "cat", "KA*T": "cat"})
    assert [o for o, _p in steno.outlines_for(d, "cat")] == [("KAT",), ("KA*T",)]
    assert steno.writes(d, ("KAT",))[0] == "cat"
    assert steno.writes(d, ("TKOG",)) == (None, None)


def test_hidden_outline_is_not_counted(tmp_path):
    # Base is above proper nouns: KAT in proper nouns never works.
    d, _ = make(tmp_path, {"KAT": "cat"}, {"KAT": "Kat"})
    assert steno.outlines_for(d, "Kat") == []


def test_from_parts(tmp_path):
    d, _ = make(tmp_path, {"WAUBG": "walk", "HAP/KWREU": "happy", "KAT": "cat", "SKWRUPL": "jump"})
    ways = dict(steno.from_parts(d, "walking"))
    assert ("WAUBG", "-G") in ways
    assert ("UPB", "HAP", "KWREU") in dict(steno.from_parts(d, "unhappy"))
    assert ("KATS",) in dict(steno.from_parts(d, "cats"))           # folded
    assert ("SKWRUPLG",) in dict(steno.from_parts(d, "jumping"))   # folded
    assert ("WAUBGD",) in dict(steno.from_parts(d, "walked"))      # folded
    assert ("KAT", "AES") in dict(steno.from_parts(d, "cat's"))     # Lapwing's 's


def test_suggestions_mark_taken(tmp_path):
    d, _ = make(tmp_path, {"WAUBG": "walk", "WAUBG/-G": "wok"})
    ideas = {i.outline: i for i in steno.suggestions(d, "walking")}
    assert ideas[("WAUBG", "-G")].taken == "wok"
    assert ideas[("WAUBGG",)].taken is None if ("WAUBGG",) in ideas else True


# Clashes ------------------------------------------------------------------

def test_no_clash(tmp_path):
    d, (base, _n) = make(tmp_path, {"KAT": "cat"})
    assert steno.clash(d, ("KAT",), "cat") is None
    assert steno.clash(d, ("TKOG",), "dog") is None
    changes = steno.plan_save(base, ("TKOG",), "dog")
    apply(d, changes)
    assert steno.writes(d, ("TKOG",))[0] == "dog"


def test_take(tmp_path):
    d, (base, _n) = make(tmp_path, {"KAT": "cat"})
    c = steno.clash(d, ("KAT",), "cot")
    assert c.other == "cat" and c.path == base
    apply(d, steno.plan_take(d, base, ("KAT",), "cot"))
    assert steno.writes(d, ("KAT",))[0] == "cot"
    assert steno.outlines_for(d, "cat") == []  # cat has to be written again


def test_take_from_another_dictionary(tmp_path):
    # The outline is in proper nouns; you save to base. It must leave
    # proper nouns too, or it would come back if base lost it.
    d, (base, names) = make(tmp_path, {}, {"PARS": "Paris"})
    apply(d, steno.plan_take(d, base, ("PARS",), "pairs"))
    assert steno.writes(d, ("PARS",))[0] == "pairs"
    assert d[names].get(("PARS",)) is None


def test_take_when_saving_lower_than_the_clash(tmp_path):
    # Saving to proper nouns while base has the outline: base must lose it.
    d, (base, names) = make(tmp_path, {"PARS": "pairs"})
    apply(d, steno.plan_take(d, names, ("PARS",), "Paris"))
    assert steno.writes(d, ("PARS",))[0] == "Paris"
    assert d[base].get(("PARS",)) is None


def test_move(tmp_path):
    d, (base, _n) = make(tmp_path, {"KAT": "cat"})
    new = steno.free_outline(d, "cat", avoid=[("KAT",)])
    assert new == ("KA*T",)  # the asterisk version is free
    apply(d, steno.plan_move(d, base, ("KAT",), "cot", new))
    assert steno.writes(d, ("KAT",))[0] == "cot"
    assert steno.writes(d, ("KA*T",))[0] == "cat"


def test_move_keeps_the_old_words_dictionary(tmp_path):
    d, (base, names) = make(tmp_path, {}, {"PARS": "Paris"})
    apply(d, steno.plan_move(d, base, ("PARS",), "pairs", ("PA*RS",)))
    assert d[names].get(("PA*RS",)) == "Paris"
    assert d[base].get(("PARS",)) == "pairs"


def test_swap(tmp_path):
    d, (base, _n) = make(tmp_path, {"KAT": "cat", "KOT": "cot"})
    plan = steno.plan_swap(d, base, ("KAT",), "cot")
    apply(d, plan)
    assert steno.writes(d, ("KAT",))[0] == "cot"
    assert steno.writes(d, ("KOT",))[0] == "cat"


def test_swap_needs_an_outline_to_give(tmp_path):
    d, (base, _n) = make(tmp_path, {"KAT": "cat"})
    assert steno.plan_swap(d, base, ("KAT",), "cot") is None


def test_clash_with_an_affix(tmp_path):
    # -G is "ing" in the affixes; base is higher, so taking it
    # in base works even though the affix file isn't touched.
    d, (base, _n) = make(tmp_path, {})
    c = steno.clash(d, ("-G",), "go")
    assert c.other == "{^ing}"
    apply(d, steno.plan_take(d, base, ("-G",), "go"))
    assert steno.writes(d, ("-G",))[0] == "go"


def test_every_plan_is_undoable(tmp_path):
    # Undo puts back the old text of every change: check nothing is lost.
    d, (base, names) = make(tmp_path, {"KAT": "cat", "KOT": "cot"}, {"KAT": "Kat"})
    before = {p: dict(d[p].items()) for p in (base, names)}
    for plan in (steno.plan_take(d, base, ("KAT",), "cot"),
                 steno.plan_move(d, base, ("KAT",), "cot", ("KA*T",)),
                 steno.plan_swap(d, base, ("KAT",), "cot")):
        olds = [(p, k, d[p].get(k)) for p, k, _n in plan]
        apply(d, plan)
        apply(d, list(reversed(olds)))
        assert {p: dict(d[p].items()) for p in (base, names)} == before

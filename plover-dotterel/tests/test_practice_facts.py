"""Tests for the parts of Practice that have no window: the typing test's
numbers, reading an EPUB, tips, and the stroke log.  Run: python -m pytest tests
"""

import json
import os
import zipfile

import pytest

from plover import system
from plover.dictionary.base import load_dictionary
from plover.registry import registry
from plover.steno_dictionary import StenoDictionaryCollection


@pytest.fixture(scope="module", autouse=True)
def dotterel():
    registry.update()
    import plover_dotterel.system
    registry.register_plugin("system", "Dotterel", plover_dotterel.system)
    system.setup("Dotterel")


from plover_dotterel import epub, logstats, tips, typetest  # noqa: E402

HERE = os.path.dirname(__file__)
DICTS = os.path.join(HERE, "..", "plover_dotterel", "dictionaries")


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


# The typing test ------------------------------------------------------------

def type_words(test, clock, words, step=1.0):
    text = ""
    for w in words:
        text += " " + w  # Plover puts the space before the word
        clock.t += step
        test.update(text)
    return text


def test_all_right():
    c = Clock()
    t = typetest.Test(["the", "cat", "sat"], clock=c)
    type_words(t, c, ["the", "cat", "sat"])
    assert t.end is not None
    r = t.result()
    assert r["acc"] == 100 and r["missed"] == [] and r["chars"] == [11, 0, 0, 0]
    # 11 letters ("the cat sat") in 2 seconds (the clock starts at the first word)
    assert round(r["wpm"]) == round(11 / 5 / (2 / 60))


def test_exact_text_counts():
    c = Clock()
    t = typetest.Test(["London,", "color", "The"], clock=c)
    type_words(t, c, ["london,", "colour", "The"])
    r = t.result()
    assert [w for w, _ in r["missed"]] == ["London,", "color"]
    right, wrong, extra, missed = r["chars"]
    assert wrong == 2 and extra == 1  # L/l, o/u ... colour has one letter too many
    assert r["acc"] < 100


def test_fixing_counts_as_typed_wrong_once():
    c = Clock()
    t = typetest.Test(["cat", "dog"], clock=c)
    t.update(" cot")
    c.t += 1
    t.update(" c")      # * took it back
    c.t += 1
    t.update(" cat")
    c.t += 1
    t.update(" cat dog")
    r = t.result()
    assert r["missed"] == []
    # c-o-t: only "o" was wrong. Then "a", "t" again, and " dog".
    assert t.wrong_keys == 1
    assert t.right_keys == 2 + 2 + 4


def test_unfinished_last_word_does_not_end():
    c = Clock()
    t = typetest.Test(["cat", "dog"], clock=c)
    assert not t.update("cat do")
    assert t.update("cat dog")


def test_consistency():
    assert typetest.kogasa(0) == 100
    assert typetest.kogasa(1) < 50


# EPUB -----------------------------------------------------------------------

def make_epub(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("META-INF/container.xml", """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
<rootfiles><rootfile full-path="OEBPS/book.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>""")
        z.writestr("OEBPS/book.opf", """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>A Small Book</dc:title></metadata>
<manifest><item id="c" href="cover.xhtml" media-type="application/xhtml+xml"/>
<item id="a" href="text/one.xhtml" media-type="application/xhtml+xml"/>
<item id="b" href="text/two.xhtml" media-type="application/xhtml+xml"/></manifest>
<spine><itemref idref="c"/><itemref idref="a"/><itemref idref="b"/></spine></package>""")
        z.writestr("OEBPS/cover.xhtml", "<html><body><img src='c.jpg'/></body></html>")
        z.writestr("OEBPS/text/one.xhtml", """<html><head><title>x</title><style>p{}</style></head>
<body><h1>Chapter One</h1><p>“Well,” said the cat, ‘it’s a color.’</p>
<p>The   dog&#160;sat on the mat.</p></body></html>""")
        z.writestr("OEBPS/text/two.xhtml", """<html><body><h2>Chapter Two</h2>
<p>London was grey and the rain fell.</p></body></html>""")


def test_epub(tmp_path):
    path = tmp_path / "small.epub"
    make_epub(path)
    book = epub.read(str(path))
    assert book["title"] == "A Small Book"
    assert [t for t, _ in book["chapters"]] == ["Chapter One", "Chapter Two"]
    words, starts, ends = epub.words_of(book)
    assert words[:3] == ["Chapter", "One", '"Well,"']
    assert "'it's" in words and "color.'" in words  # straight quotes, spelling kept
    assert words[words.index("dog") - 1] == "The"  # spaces made plain
    assert starts[1][1] == "Chapter Two"
    assert words.index("mat.") in ends
    assert epub.safe_name('A/B: "C"?') == "A B C"


# Tips -------------------------------------------------------------------------

def test_tips(tmp_path):
    base = tmp_path / "dotterel-base.json"
    base.write_text(json.dumps({"KAT": "cat", "KA*T": "cat", "SKWRUPL": "jump", "HRUPB/TKUPB": "London"}))
    ds = [load_dictionary(str(base)), load_dictionary(os.path.join(HERE, "affixes.json"))] + [
        load_dictionary(os.path.join(DICTS, n)) for n in ("dotterel-punctuation.json", "dotterel-commands.json")]
    t = tips.Tips(StenoDictionaryCollection(ds))
    assert t.for_token("cat")[0][0] == "KAT"            # shortest of KAT / KA*T
    steps = t.for_token("jumping")
    assert steps[0][0] == "SKWRUPLG"                     # folded: one stroke
    steps = t.for_token("London,")
    assert steps[0][0] == "HRUPB/TKUPB" and steps[1][1] == ","
    assert steps[1][0] != "?"
    steps = t.for_token("Cat", after_stop=False)        # a capital you make
    assert steps[0][1] == "capital" and steps[1][0] == "KAT"
    assert t.for_token("Cat", after_stop=True)[0][0] == "KAT"  # Plover does it after .
    assert t.for_token("zebra")[0][0] == "?"
    # A colon after a word is {:} (space after), not {^}:{^} (as in 10:30).
    assert t.for_token("cat:")[1][0] == "#TPH-FPLT"
    steps = t.for_token('"cat"')
    assert steps[0][0] == "KW-GS" and steps[2][0] == "KW*GS"  # opening, closing quote


# The stroke log ---------------------------------------------------------------

LOG = """2026-11-07 10:00:00,000 Stroke(KAT : ['K-', 'A-', '-T'])
2026-11-07 10:00:00,010 Translation(('KAT',) : "cat")
2026-11-07 10:00:01,000 Stroke(* : ['*'])
2026-11-07 10:00:01,010 *Translation(('KAT',) : "cat")
2026-11-07 10:00:01,500 Stroke(KOT : ['K-', 'O-', '-T'])
2026-11-07 10:00:01,510 Translation(('KOT',) : "cot")
2026-11-07 10:00:02,000 Stroke(TKOG : ['T-', 'K-', 'O-', '-G'])
2026-11-07 10:00:02,010 Translation(('TKOG',) : "dog")
2026-11-07 10:00:02,500 Stroke(PW-FP : ['P-', 'W-', '-F', '-P'])
2026-11-07 10:00:02,510 Translation(('PW-FP',) : "{#BackSpace}{^}")
2026-11-07 10:00:03,000 Stroke(TKPWOEU : ['T-'])
2026-11-07 10:00:03,010 Translation(('TKPWOEU',) : None)
"""


def test_log(tmp_path):
    path = tmp_path / "strokes.log"
    path.write_text(LOG)
    st = logstats.analyse(logstats.read_log(str(path)))
    assert logstats.top_fixes(st) == [("cat", "KAT", "cot", "KOT", 1)]
    assert st.corrected["KAT"] == 1 and st.undo_strokes == 1
    assert st.backspaced["dog"] == 1 and st.backspace_strokes == 1
    assert st.untranslated["TKPWOEU"] == 1
    assert st.words == 2  # cot, dog (cat was undone)


def test_one_extra_letter_does_not_spoil_the_rest():
    c = Clock()
    t = typetest.Test(["any", "house", "cat"], clock=c)
    type_words(t, c, ["anys", "house", "cat"])
    assert t.wrong_keys == 1  # only the "s"
    r = t.result()
    assert [w for w, _ in r["missed"]] == ["any"]


def test_log_is_read_again_only_where_it_grew(tmp_path):
    path = tmp_path / "strokes.log"
    path.write_text(LOG)
    first = logstats.read_log(str(path))
    with open(path, "a") as f:
        f.write(LOG)
    both = logstats.read_log(str(path))
    assert both == first + first
    path.write_text(LOG)  # a new (rotated) log starts again
    assert logstats.read_log(str(path)) == first


def test_bare_word():
    from plover_dotterel.practice import bare_word
    assert bare_word('"Well,"', True) == "well"
    assert bare_word("locker—for") == "locker"
    assert bare_word("suit's") == "suit"
    assert bare_word("it's") == "it's"
    assert bare_word("The", True) == "the"
    assert bare_word("London,", True) == "London"
    assert bare_word("Julie", True) == "Julie"

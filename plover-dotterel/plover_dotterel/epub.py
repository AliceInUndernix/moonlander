"""Read an EPUB book into plain text, for Practice.

An EPUB is a zip file: META-INF/container.xml names the book's .opf file,
the .opf lists the pages (XHTML) in reading order (the "spine"). We read
every page's text, in that order. Python's own zipfile and html.parser are
enough: nothing to install.

The text is kept as it is in the book (capitals, American spelling,
punctuation), with only what a keyboard can't type made plain:
curly quotes become ' and ", non-breaking spaces become spaces, and
each paragraph is one line (you write it as one text, with spaces).
"""

import hashlib
import posixpath
import re
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree

BLOCKS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6",
          "tr", "blockquote", "section", "article", "pre", "dt", "dd"}
HEADINGS = {"h1", "h2", "h3"}
SKIP = {"script", "style", "head", "title", "nav"}
PLAIN = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
    " ": " ", " ": " ", " ": " ", " ": " ",
    "­": None, "​": None, "﻿": None,
})


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.now, self.skip = [], [], 0
        self.heading, self.in_heading = None, 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        elif tag in BLOCKS:
            self._end()
        if tag in HEADINGS:
            self.in_heading += 1

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        elif tag in BLOCKS:
            if tag in HEADINGS and self.heading is None:
                self.heading = clean("".join(self.now))
            self._end()
        if tag in HEADINGS and self.in_heading:
            self.in_heading -= 1

    def handle_data(self, data):
        if not self.skip:
            self.now.append(data)

    def _end(self):
        text = clean("".join(self.now))
        if text:
            self.blocks.append(text)
        self.now = []

    def close(self):
        super().close()
        self._end()


def clean(text):
    return re.sub(r"\s+", " ", text.translate(PLAIN)).strip()


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def read(path):
    """{'title', 'chapters': [(title, text)], 'id'} from an .epub file.

    'id' is a short fingerprint of the file, so your place in the book is
    found again even if you move or rename it.
    """
    with open(path, "rb") as f:
        book_id = hashlib.sha1(f.read()).hexdigest()[:16]
    with zipfile.ZipFile(path) as z:
        container = ElementTree.fromstring(z.read("META-INF/container.xml"))
        opf_path = next(el.get("full-path") for el in container.iter()
                        if _local(el.tag) == "rootfile")
        opf = ElementTree.fromstring(z.read(opf_path))
        base = posixpath.dirname(opf_path)
        title = next((el.text for el in opf.iter() if _local(el.tag) == "title" and el.text),
                     posixpath.basename(path))
        manifest = {el.get("id"): el.get("href") for el in opf.iter() if _local(el.tag) == "item"}
        spine = [el.get("idref") for el in opf.iter() if _local(el.tag) == "itemref"]
        chapters = []
        for n, idref in enumerate(spine, 1):
            href = manifest.get(idref)
            if not href:
                continue
            name = posixpath.normpath(posixpath.join(base, href.split("#")[0]))
            try:
                raw = z.read(name).decode("utf-8", errors="replace")
            except KeyError:
                continue
            p = _Text()
            p.feed(raw)
            p.close()
            text = "\n".join(p.blocks)  # one line per paragraph
            if len(text.split()) < 5:
                continue  # covers, blank pages
            chapters.append((p.heading or f"Part {len(chapters) + 1}", text))
    return {"title": clean(title), "chapters": chapters, "id": book_id}


def words_of(book):
    """All words of the book in order, where each chapter starts, and the
    words that end a paragraph (their index)."""
    words, starts, ends = [], [], set()
    for title, text in book["chapters"]:
        starts.append((len(words), title))
        for para in text.split("\n"):
            ws = [w for w in para.split(" ") if w]
            if ws:
                words.extend(ws)
                ends.add(len(words) - 1)
    return words, starts, ends


def safe_name(title):
    """A file name from a book title: no slashes, no extension."""
    name = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", " ", title)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:120] or "book"

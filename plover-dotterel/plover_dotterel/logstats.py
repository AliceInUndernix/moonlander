"""Read Plover's stroke log (strokes.log) and work out stats.

Plover writes it when Configure > Logging has "Log strokes" and/or
"Log translations" ticked. Lines look like:

    2026-11-03 08:00:00,123 Stroke(KAT : ['K-', 'A-', '-T'])
    2026-11-03 08:00:00,125 Translation(('KAT',) : "cat")
    2026-11-03 08:00:01,002 *Translation(('KAT',) : "cat")     <- undone
"""

import bisect
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

LINE_RX = re.compile(
    r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)(?:,(\d+))? (\*?)(Stroke|Translation)\((.*)\)\s*$"
)
STROKE_RX = re.compile(r"^(\S*) : \[(.*)\]$")
TRANSLATION_RX = re.compile(r"^\((.*?)\) : (None|\"(.*)\"|'(.*)')$")
FINGERSPELL_RX = re.compile(r"^(?:\{>\})?\{&([A-Za-z])\}$|^\{>\}\{&([A-Za-z])\}$")
WORD_RX = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")

BACKSPACE_RX = re.compile(r"\{#(?:Control_[lr]\(|control\()?BackSpace", re.I)

SESSION_GAP = 10 * 60  # seconds: a longer pause starts a new session
ACTIVE_GAP = 5  # seconds: pauses longer than this don't count as writing
PAUSE_MIN = 1.5  # seconds: a pause before a word this long counts as a hesitation


_SECONDS = {}  # "2026-11-07 10:00:00" -> unix time
_READ = {}  # path -> (inode, bytes read, events): only new lines are read again


def parse_line(line):
    """Return (time, kind, undo, data) or None.

    kind "stroke": data = (rtfcre, keys). kind "translation": data =
    (outline, english or None).
    """
    m = LINE_RX.match(line)
    if not m:
        return None
    second = _SECONDS.get(m.group(1))
    if second is None:  # strptime is slow: once per second of log is enough
        try:
            second = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
        except ValueError:
            return None
        if len(_SECONDS) > 200000:
            _SECONDS.clear()
        _SECONDS[m.group(1)] = second
    ms = int((m.group(2) or "0")[:3].ljust(3, "0"))
    ts = second + ms / 1000
    undo = m.group(3) == "*"
    body = m.group(5)
    if m.group(4) == "Stroke":
        sm = STROKE_RX.match(body)
        if not sm:
            return None
        keys = [k.strip().strip("'\"") for k in sm.group(2).split(",") if k.strip()]
        return ts, "stroke", undo, (sm.group(1), keys)
    tm = TRANSLATION_RX.match(body)
    if not tm:
        return None
    strokes = [s.strip().strip("'\"") for s in tm.group(1).split(",") if s.strip()]
    outline = "/".join(strokes)
    if tm.group(2) == "None":
        english = None
    elif tm.group(3) is not None:
        english = tm.group(3).replace('\\"', '"')
    else:
        english = tm.group(4)
    return ts, "translation", undo, (outline, english)


def read_log(path, since=None):
    """Parsed events from a log file, oldest first (since: unix time).

    The file is read once; later calls read only what Plover added since.
    """
    st = os.stat(path)
    inode, done, events = _READ.get(path, (None, 0, []))
    if inode != st.st_ino or st.st_size < done:  # a new or rotated log
        done, events = 0, []
    if st.st_size > done:
        events = list(events)
        with open(path, "rb") as f:
            f.seek(done)
            data = f.read()
        end = data.rfind(b"\n") + 1  # a half-written last line waits
        for line in data[:end].decode("utf-8", errors="replace").splitlines():
            ev = parse_line(line)
            if ev:
                events.append(ev)
        _READ[path] = (st.st_ino, done + end, events)
    if since is None:
        return list(events)
    first = bisect.bisect_left([e[0] for e in events], since)
    return events[first:]


def _letter(english):
    if english is None:
        return None
    m = FINGERSPELL_RX.match(english)
    if m:
        return m.group(1) or m.group(2)
    return None


class Stats:
    """Everything worked out from the events."""

    def __init__(self):
        self.strokes = 0
        self.words = 0
        self.first = None
        self.last = None
        self.sessions = 0
        self.active_seconds = 0.0
        self.key_counts = Counter()
        self.outline_counts = Counter()  # outline -> times used (not undone)
        self.word_counts = Counter()
        self.corrected = Counter()  # outline -> times undone with the undo stroke
        self.untranslated = Counter()  # raw strokes that had no translation
        self.fingerspelled = Counter()  # words written letter by letter
        self.hesitations = defaultdict(list)  # word -> pauses before it
        self.undo_strokes = 0
        self.daily = Counter()  # date -> words
        # Mistakes and how you fixed them:
        # (what you wrote, its outline) -> Counter of (what came instead, its outline)
        self.fixes = defaultdict(Counter)
        self.backspaced = Counter()  # words right before a backspace stroke
        self.backspace_strokes = 0

    @property
    def wpm(self):
        minutes = self.active_seconds / 60
        return self.words / minutes if minutes else 0.0

    @property
    def strokes_per_word(self):
        return self.strokes / self.words if self.words else 0.0

    def slowest(self, n=50, min_count=3):
        rows = [
            (w, sum(p) / len(p), len(p))
            for w, p in self.hesitations.items()
            if len(p) >= min_count
        ]
        rows.sort(key=lambda r: -r[1])
        return rows[:n]


def analyse(events, undo_outlines=("*",)):
    """Work out Stats from parsed events.

    undo_outlines: outlines that mean "undo" (=undo), so the translations
    they take back count as corrections.
    """
    st = Stats()
    undo_outlines = set(undo_outlines)
    last_stroke_time = None
    last_stroke = None
    pause_before = 0.0
    undone = []  # what * took back, waiting to see what you wrote instead
    last_word = None
    fs_letters = []  # current run of fingerspelled letters

    def end_fingerspelling():
        if len(fs_letters) >= 2:
            st.fingerspelled["".join(fs_letters).lower()] += 1
        fs_letters.clear()

    for ts, kind, undo, data in events:
        if kind == "stroke":
            rtfcre, keys = data
            st.strokes += 1
            st.key_counts.update(keys)
            if st.first is None:
                st.first = ts
            st.last = ts
            if last_stroke_time is None or ts - last_stroke_time > SESSION_GAP:
                st.sessions += 1
                pause_before = 0.0
            else:
                gap = ts - last_stroke_time
                st.active_seconds += min(gap, ACTIVE_GAP)
                pause_before = gap
            last_stroke_time = ts
            last_stroke = rtfcre
            if rtfcre in undo_outlines:
                st.undo_strokes += 1
            continue
        outline, english = data
        if undo:
            if last_stroke in undo_outlines:
                st.corrected[outline] += 1
                undone.append((english, outline))
            # Take back what was counted for it.
            if st.outline_counts[outline] > 0:
                st.outline_counts[outline] -= 1
            if english:
                for w in WORD_RX.findall(english):
                    if st.word_counts[w.lower()] > 0:
                        st.word_counts[w.lower()] -= 1
                        st.words -= 1
                        day = datetime.fromtimestamp(ts).date().isoformat()
                        if st.daily[day] > 0:
                            st.daily[day] -= 1
            continue
        if outline in undo_outlines:
            continue
        if english and BACKSPACE_RX.search(english):
            st.backspace_strokes += 1
            if last_word:
                st.backspaced[last_word] += 1
            last_word = None
            continue
        if undone:
            # The first thing written after undoing is the fix.
            for wrong in undone[-1:]:
                st.fixes[wrong][(english, outline)] += 1
            undone.clear()
        st.outline_counts[outline] += 1
        letter = _letter(english)
        if letter:
            fs_letters.append(letter)
            continue
        end_fingerspelling()
        if english is None:
            st.untranslated[outline] += 1
            continue
        found = WORD_RX.findall(english)
        if found:
            last_word = found[-1].lower()
        for w in found:
            st.word_counts[w.lower()] += 1
            st.words += 1
            st.daily[datetime.fromtimestamp(ts).date().isoformat()] += 1
        if len(found) == 1 and pause_before >= PAUSE_MIN and pause_before <= SESSION_GAP:
            st.hesitations[found[0].lower()].append(pause_before)
    end_fingerspelling()
    # Drop counters that went to zero after undos.
    for c in (st.outline_counts, st.word_counts, st.daily):
        for k in [k for k, v in c.items() if v <= 0]:
            del c[k]
    return st


def top_fixes(st, n=30):
    """[(wrong text, wrong outline, right text, right outline, times)], most first."""
    rows = []
    for (wtext, woutline), fixes in st.fixes.items():
        for (rtext, routline), count in fixes.items():
            if (wtext, woutline) != (rtext, routline):
                rows.append((wtext, woutline, rtext, routline, count))
    rows.sort(key=lambda r: -r[4])
    return rows[:n]


def log_path(config):
    """Plover's stroke log file, from its settings."""
    try:
        return config["log_file_name"]
    except Exception:
        import os
        from plover.oslayer.config import CONFIG_DIR
        return os.path.join(CONFIG_DIR, "strokes.log")

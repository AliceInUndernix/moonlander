"""The typing test itself, without windows: what counts and how.

You write into one field; the test compares it with the target text,
letter by letter, exactly (capitals, punctuation, spaces). The numbers
are worked out the way Monkeytype does:

    wpm          letters of the words you got right (plus their spaces),
                 divided by 5, per minute
    raw          every letter you typed, right or wrong, / 5, per minute
    accuracy     letters typed right / all letters typed (a letter Plover
                 typed and you undid with * still counts as typed)
    consistency  how even your speed was, second by second (100% = even)
    characters   right / wrong / extra (past the word's end) / missed
"""

import math
import time


def kogasa(cov):
    """Monkeytype's consistency: 100 for an even speed, less for uneven."""
    return 100 * (1 - math.tanh(cov + cov ** 3 / 3 + cov ** 5 / 5))


class Test:
    """One test. Call update(field text) on every change of the field."""

    def __init__(self, words, seconds=None, clock=time.monotonic):
        self.words = list(words)          # the target, word by word
        self.target = " ".join(self.words)
        self.seconds = seconds            # time mode: a limit; None = words mode
        self.clock = clock
        self.typed = ""
        self.start = None
        self.end = None
        self.right_keys = 0               # letters typed that were right there
        self.wrong_keys = 0
        self.per_second = {}              # second -> [letters typed, wrong]
        self.strokes = 0                  # steno strokes during the test
        self.undos = 0                    # * strokes during the test

    # Typing ---------------------------------------------------------------

    def update(self, text):
        """The field now holds `text`. Returns True when the test is done."""
        if self.end is not None:
            return True
        # Plover puts its space BEFORE a word: the first one is not yours.
        text = text.lstrip(" ")
        now = self.clock()
        if text and self.start is None:
            self.start = now
        old = self.typed
        same = 0
        while same < min(len(old), len(text)) and old[same] == text[same]:
            same += 1
        second = int(now - self.start) if self.start is not None else 0
        bucket = self.per_second.setdefault(second, [0, 0])
        # Each letter is checked against its own word, so one extra or
        # missing letter doesn't make the rest of the text wrong.
        wi = text.count(" ", 0, same)
        k = same - (text.rfind(" ", 0, same) + 1)
        for i in range(same, len(text)):
            ch = text[i]
            if ch == " ":
                ok = wi < len(self.words) - 1
                wi, k = wi + 1, 0
            else:
                w = self.words[wi] if wi < len(self.words) else ""
                ok = k < len(w) and w[k] == ch
                k += 1
            if ok:
                self.right_keys += 1
            else:
                self.wrong_keys += 1
                bucket[1] += 1
            bucket[0] += 1
        self.typed = text
        if self.is_done():
            self.end = now
            return True
        return False

    def is_done(self):
        typed = self.typed.split(" ")
        if self.seconds is not None and self.start is not None:
            if self.clock() - self.start >= self.seconds:
                return True
        if len(typed) > len(self.words):
            return True  # a space after the last word
        return len(typed) == len(self.words) and typed[-1] == self.words[-1]

    def time_up(self):
        """Time mode: call from a timer; True once the time is over."""
        if self.end is None and self.seconds is not None and self.start is not None \
                and self.clock() - self.start >= self.seconds:
            self.end = self.start + self.seconds
        return self.end is not None

    def stroke(self, rtfcre, undo_stroke="*"):
        if self.start is not None and self.end is None:
            self.strokes += 1
            if rtfcre == undo_stroke:
                self.undos += 1

    # Where you are ---------------------------------------------------------

    def position(self):
        """(word index, letter index in it) of the caret."""
        typed = self.typed.split(" ")
        return len(typed) - 1, len(typed[-1])

    def word_states(self):
        """For drawing: [(target word, typed word or None, state)].

        state: 'done' (right), 'wrong', 'now' (being typed), 'todo'.
        """
        typed = self.typed.split(" ") if self.typed else [""]
        cur = len(typed) - 1
        out = []
        for i, w in enumerate(self.words):
            if i < cur:
                out.append((w, typed[i], "done" if typed[i] == w else "wrong"))
            elif i == cur:
                out.append((w, typed[i], "now"))
            else:
                out.append((w, None, "todo"))
        return out

    # Results ---------------------------------------------------------------

    def elapsed(self):
        if self.start is None:
            return 0.0
        end = self.end if self.end is not None else self.clock()
        if self.seconds is not None:
            end = min(end, self.start + self.seconds)
        return max(end - self.start, 0.001)

    def chars(self):
        """(right, wrong, extra, missed) letters, Monkeytype's way."""
        right = wrong = extra = missed = 0
        typed = self.typed.split(" ") if self.typed else []
        last = len(typed) - 1
        for i, t in enumerate(typed[: len(self.words)]):
            w = self.words[i]
            for a, b in zip(t, w):
                if a == b:
                    right += 1
                else:
                    wrong += 1
            if len(t) > len(w):
                extra += len(t) - len(w)
            elif len(t) < len(w) and i < last:
                missed += len(w) - len(t)
            if i < last:
                right += 1  # the space after it
        for t in typed[len(self.words):]:
            extra += len(t)
        return right, wrong, extra, missed

    def result(self):
        minutes = self.elapsed() / 60
        typed = self.typed.split(" ") if self.typed else []
        good = 0
        for i, t in enumerate(typed[: len(self.words)]):
            if t == self.words[i]:
                good += len(t) + (1 if i < len(typed) - 1 else 0)
        keys = self.right_keys + self.wrong_keys
        raw_secs = [v[0] / 5 * 60 for k, v in sorted(self.per_second.items())]
        if len(raw_secs) > 1:
            mean = sum(raw_secs) / len(raw_secs)
            sd = math.sqrt(sum((x - mean) ** 2 for x in raw_secs) / len(raw_secs))
            consistency = kogasa(sd / mean) if mean else 0.0
        else:
            consistency = 100.0 if raw_secs else 0.0
        right, wrong, extra, missed = self.chars()
        missed_words = [(w, typed[i]) for i, w in enumerate(self.words)
                        if i < len(typed) - 1 and typed[i] != w]
        if typed and len(typed) <= len(self.words) and typed[-1] != self.words[len(typed) - 1] \
                and self.end is not None and self.seconds is None:
            missed_words.append((self.words[len(typed) - 1], typed[-1]))
        return {
            "wpm": good / 5 / minutes if minutes else 0.0,
            "raw": len(self.typed) / 5 / minutes if minutes else 0.0,
            "acc": 100 * self.right_keys / keys if keys else 0.0,
            "consistency": consistency,
            "chars": [right, wrong, extra, missed],
            "seconds": round(self.elapsed(), 2),
            "words_typed": min(len(typed), len(self.words)),
            "missed": missed_words,
            "strokes": self.strokes,
            "undos": self.undos,
            "chart": self.chart(),
        }

    def chart(self):
        """Per second: (second, wpm so far, raw that second, wrong that second)."""
        out, total = [], 0
        last = int(self.elapsed())
        for s in range(0, max(last, 1)):
            letters, wrong = self.per_second.get(s, [0, 0])
            total += letters - wrong
            out.append((s + 1, total / 5 / ((s + 1) / 60), letters / 5 * 60, wrong))
        return out

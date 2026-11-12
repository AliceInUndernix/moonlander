"""A word's UK pronunciation written in Russian letters, for a Russian reader.

From the UK IPA (Cambridge): walking /ˈwɔː.kɪŋ/ -> УО·кин.
Split into syllables like the English (·), the stressed one in CAPITALS. Sounds
Russian doesn't have are underlined (in the HTML version); LEGEND says how
to say them. The r after a vowel is silent in British English, so it is
left out (car -> ка:).
"""

import html

# IPA symbols, longest first, and the spellings that mean the same sound
# (Britfone writes ɛ ɐ ɹ where Cambridge writes e ʌ r).
_SYMBOLS = sorted(
    """tʃ dʒ eɪ aɪ ɔɪ əʊ oʊ aʊ ɪə eə ɛə ʊə iː uː ɑː ɔː ɜː ɝ ɚ
    p b t d k g ɡ f v θ ð s z ʃ ʒ h m n ŋ l r ɹ w j
    æ e ɛ ɪ ɒ ʌ ɐ ʊ ə i u ɑ ɔ ɜ o a ɫ""".split(),
    key=len,
    reverse=True,
)
_NORMAL = {"ɛ": "e", "ɐ": "ʌ", "ɹ": "r", "ɡ": "g", "ɛə": "eə", "oʊ": "əʊ", "ɝ": "ɜː",
           "ɚ": "ə", "ɑ": "ɑː", "ɔ": "ɔː", "ɜ": "ɜː", "u": "uː", "o": "əʊ", "a": "æ", "ɫ": "l"}

VOWELS = {
    "æ": "э", "e": "э", "ɪ": "и", "i": "и", "iː": "и:", "ɒ": "о", "ʌ": "а",
    "ʊ": "у", "uː": "у:", "ə": "э", "ɔː": "о:", "ɑː": "а:", "ɜː": "ё:",
    "eɪ": "эй", "aɪ": "ай", "ɔɪ": "ой", "əʊ": "эу", "aʊ": "ау",
    "ɪə": "иэ", "eə": "э:", "ʊə": "уэ",
}
# After /j/ the two letters merge, as in Russian: you /juː/ -> ю:, yes -> ес.
J_VOWELS = {"uː": "ю:", "ʊ": "ю", "ʊə": "юэ", "e": "е", "æ": "я", "ʌ": "я",
            "ɑː": "я:", "ɒ": "ё", "ɔː": "ё:", "ɜː": "ё:"}
CONSONANTS = {
    "p": "п", "b": "б", "t": "т", "d": "д", "k": "к", "g": "г", "f": "ф",
    "v": "в", "θ": "с", "ð": "з", "s": "с", "z": "з", "ʃ": "ш", "ʒ": "ж",
    "h": "х", "m": "м", "n": "н", "ŋ": "н", "l": "л", "r": "р", "w": "у",
    "j": "й", "tʃ": "ч", "dʒ": "дж",
}
# Sounds Russian lacks: underlined in the HTML version.
ODD = {"θ", "ð", "w", "ŋ", "h", "r", "æ", "əʊ"}
LEGEND = (
    "Underlined sounds aren't in Russian:\n"
    "с з (th): tip of the tongue between the teeth (think, this)\n"
    "у (w): a short у with rounded lips, like the start of «уо» (we, water)\n"
    "н (ng): the back of the tongue, as in «гонг» without the г (sing)\n"
    "х (h): only a breath, much softer than х (hat)\n"
    "р (r): no trill, the tongue curls back and doesn't touch (red)\n"
    "э (a in cat): between э and а, mouth wide open\n"
    "эу (o in go): э gliding into у, not «оу»\n"
    "· splits the syllables; CAPITALS = the stressed syllable.\n"
    "э in unstressed syllables is short and weak (the 'a' in about)."
)


def _tokens(ipa):
    """IPA -> phonemes, with "ˈ" (stressed syllable starts) and "." (a
    syllable starts) between them. Cambridge writes the dots: ˈwɔː.kɪŋ."""
    if not isinstance(ipa, str):
        ipa = " ".join(ipa)
    text = ipa.split("/")[0] if ipa.count("/") > 1 else ipa
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in "ˈˌ.":
            out.append("ˈ" if ch == "ˈ" else ".")
            i += 1
            continue
        for sym in _SYMBOLS:
            if text.startswith(sym, i):
                out.append(_NORMAL.get(sym, sym))
                i += len(sym)
                break
        else:
            i += 1  # spaces, length marks, brackets
    return out


def _items(ipa):
    """[[text, odd, vowel?, stressed?, syllable starts here?]] for the word."""
    toks = _tokens(ipa)
    out = []
    stress = start = False
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in ("ˈ", "."):
            stress = stress or t == "ˈ"
            start = True
            i += 1
            continue
        nxt = next((x for x in toks[i + 1:] if x not in ("ˈ", ".")), None)
        if t == "r" and nxt not in VOWELS:
            i += 1  # silent r (car, water) in British English
            continue
        if t == "j" and nxt in J_VOWELS:
            # one Russian letter for both (you -> ю); a mark between still counts
            j = i + 1
            while toks[j] in ("ˈ", "."):
                stress = stress or toks[j] == "ˈ"
                j += 1
            out.append([J_VOWELS[nxt], nxt in ODD, True, stress, start])
            stress = start = False
            i = j + 1
            continue
        if t in VOWELS:
            out.append([VOWELS[t], t in ODD, True, stress, start])
            stress = start = False
        elif t in CONSONANTS:
            out.append([CONSONANTS[t], t in ODD, False, False, start])
            start = False
        i += 1
    for item in out:
        item[0] = item[0].replace(":", "")  # no length marks: easier to read
    vowels = [k for k, item in enumerate(out) if item[2]]
    if out:
        out[0][4] = False
    if len(vowels) > 1 and not any(item[4] for item in out):
        # No dots in the IPA: a consonant before a vowel starts a syllable.
        for k in vowels[1:]:
            b = k - 1 if k - 1 > vowels[0] and not out[k - 1][2] else k
            out[b][4] = True
    return out


def _syllables(ipa):
    """[(stressed?, [(text, odd)])], one per syllable."""
    sylls = []
    for text, odd, _vowel, stressed, start in _items(ipa):
        if start or not sylls:
            sylls.append([False, []])
        sylls[-1][1].append((text, odd))
        sylls[-1][0] = sylls[-1][0] or stressed
    return sylls


def from_ipa(ipa):
    """'ˈwɔː.kɪŋ' -> 'УО·кин': syllables like the English split, the stressed
    one in capitals (empty if there is nothing to read)."""
    if not ipa:
        return ""
    sylls = _syllables(ipa)
    many = len(sylls) > 1
    return "·".join("".join(t for t, _ in parts).upper() if stressed and many
                    else "".join(t for t, _ in parts) for stressed, parts in sylls)


def html_from_ipa(ipa):
    """Like from_ipa, with the sounds Russian lacks underlined."""
    if not ipa:
        return ""
    sylls = _syllables(ipa)
    many = len(sylls) > 1
    out = []
    for stressed, parts in sylls:
        bits = []
        for t, odd in parts:
            t = html.escape(t.upper() if stressed and many else t)
            bits.append(f"<u>{t}</u>" if odd else t)
        out.append("".join(bits))
    return "·".join(out)

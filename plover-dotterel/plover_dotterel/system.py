"""The Dotterel steno system: keys, folding, the Moonlander and spelling rules.

Plover asks every system file the same list of questions. Each numbered
section below is one answer that we have agreed on together.
"""


# 1. The keys, in steno order. A stroke is always written in this order.
#    "S-" is the left-hand S, "-S" the right-hand S.
KEYS = (
    "#",
    "S-", "T-", "K-", "P-", "W-", "H-", "R-",
    "A-", "O-",
    "*",
    "-E", "-U",
    "-F", "-R", "-P", "-B", "-L", "-G", "-T", "-S", "-D", "-Z",
)

# 2. Where no "-" is needed when a stroke is written down: these keys already
#    show where the left hand ends. KAT, not KA-T. But -T needs it (right T).
IMPLICIT_HYPHEN_KEYS = ("A-", "O-", "-E", "-U", "*")

# 3. # is a plain key, like in Lapwing. #S stays #S (normal Plover makes it 1).
NUMBER_KEY = None
NUMBERS = {}
FERAL_NUMBER_KEY = False


# 4. Folding: you may add these keys to any outline to add an ending.
#    KATS isn't in a dictionary -> Plover tries KAT + -S -> "cat" + "{^s}".
#    -Z does the same, for when -S is awkward: card KARD -> cards KARDZ.
#    -Z works after every word, not only after -D.
#    -D adds "ed": walk WAUBG -> walked WAUBGD.
#    -G adds "ing": jump SKWRUPL -> jumping SKWRUPLG.
#    Only ONE ending is folded per stroke: WAUBGSD stays raw.
#    What the keys add is in dictionaries/dotterel-affixes.json; without an
#    entry there, the key can't be folded.
#    An outline that IS in a dictionary always wins over folding.
SUFFIX_KEYS = ("-Z", "-D", "-S", "-G")  # tried in this order (Lapwing's)


# 5. Which signal from the Moonlander is which key. The Moonlander speaks
#    Gemini PR (qmk/canary/keymap.c, layer 5). Left: our key, right: the
#    signal. "no-op" signals do nothing: #3 and #5 are the two inner thumb
#    keys, the rest are number-bar signals the Moonlander never sends. Plover
#    needs every signal listed somewhere, or it stops with an error.
KEYMAPS = {
    "Gemini PR": {
        "#":  "#1",
        "S-": ("S1-", "S2-"),
        "T-": "T-", "K-": "K-", "P-": "P-", "W-": "W-", "H-": "H-", "R-": "R-",
        "A-": "A-", "O-": "O-",
        "*":  ("*1", "*2", "*3", "*4"),
        "-E": "-E", "-U": "-U",
        "-F": "-F", "-R": "-R", "-P": "-P", "-B": "-B", "-L": "-L",
        "-G": "-G", "-T": "-T", "-S": "-S", "-D": "-D", "-Z": "-Z",
        "no-op": ("#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9",
                  "#A", "#B", "#C", "Fn", "pwr", "res1", "res2"),
    },
}

# 6. Dictionaries a new user gets, top = checked first.
DICTIONARIES_ROOT = "asset:plover_dotterel:dictionaries"
DEFAULT_DICTIONARIES = (
    "dotterel-base.json",           # YOUR words, starts empty (top = wins)
    "dotterel-proper-nouns.json",   # your names (London, John), starts empty
    "dotterel-affixes.json",        # prefixes and suffixes (Lapwing's)
    "dotterel-punctuation.json",    # . , ? ! etc., * = undo, # = repeat
    "dotterel-commands.json",       # capitals, spacing, Tab/Enter, #SU = US/UK
    "dotterel-fingerspelling.json", # one letter at a time
    "dotterel-numbers.json",        # numbers with #
    "dotterel-raw.json",            # RA*U: raw mode on/off (see raw_mode.py)
    # From Lapwing: #TPH or STPH + a right-hand key = arrows etc.;
    # after that, right-hand keys alone keep moving until another stroke.
    "dotterel-movement.modal",
    # KHR (Ctrl), SH (Shift), THRA (Alt), KPW (Super), then any key stroke:
    # KHR then STPH-L = Ctrl+Up. See the file for all of them.
    "dotterel-modifiers.py",
)


# 7. Spelling rules: how an ending is glued on. Used for EVERY {^...} ending,
#    folded or written as its own stroke. These are Plover's own English
#    rules, unchanged. The ones for s, ed and ing:
#      ends in s, sh, x, z, or ch said "tch" + s  -> es    box -> boxes, church -> churches
#      consonant + y, + s                        -> ies   city -> cities
#      silent e, + ed / ing                      -> drop e like -> liked, liking
#      short vowel + consonant, + ed / ing       -> double it   stop -> stopped
#      anything else                              -> just join  cat -> cats, walk -> walked
#    This is where the "sometimes es" comes from: it depends on the word before.
#
#    Plus one rule of ours, at the end: a word ending in o MAY take es.
#      potato -> potatoes, hero -> heroes, but photo -> photos, zero -> zeros
#    Which one is picked comes from the word list (section 8): Plover only
#    uses "oes" when that is the real (or more common) spelling. Only for a
#    word that isn't in the list at all does it guess "oes".
from plover.system import english_stenotype as _english

ORTHOGRAPHY_RULES = _english.ORTHOGRAPHY_RULES + [
    (r"^(.*o) \^ s$", r"\1es"),
]
ORTHOGRAPHY_RULES_ALIASES = _english.ORTHOGRAPHY_RULES_ALIASES  # able <-> ible


# 8. Word list for the spelling rules. When more than one rule fits, Plover
#    picks the result that is a real word. Without it, visit + ed would come
#    out "visitted" (the doubling rule for stop -> stopped fires).
#    Plover would only look for the list in its config folder and in OUR
#    dictionaries folder, so we give it the full path to Plover's own copy.
#    It is an American list (color, realize).
def _plover_wordlist():
    from plover.resource import resource_filename
    return resource_filename("asset:plover:assets/" + _english.ORTHOGRAPHY_WORDLIST)


ORTHOGRAPHY_WORDLIST = _plover_wordlist()


# 9. Undo: * alone takes back the last stroke.
UNDO_STROKE_STENO = "*"

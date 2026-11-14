# Dotterel

Dotterel is a steno theory and dictionary for [Plover](https://www.openstenoproject.org/plover/), written for British English (RP pronunciation, British spelling with Oxford -ize). It is built on [Lapwing](https://lapwing.aerick.ca/) by Aerick: the same theory and syllable splits, with the vowels and briefs changed where RP sounds different from General American.

It works with any steno keyboard that speaks the Gemini PR protocol, such as a ZSA Moonlander running QMK's steno feature.

## What's in it

- **113,816 word outlines** plus 602 prefixes and suffixes, 15,787 proper nouns, punctuation, numbers, commands, fingerspelling, movement and modifier keys.
- **British by default, American on demand:** `#SU` switches the last word between UK and US spelling (colour / color).
- **The Builder** (Ctrl+B in Plover, or in the toolbar), a window for growing your dictionary:
  - suggests outlines for a word from Lapwing and the Dotterel rules, and turns green when what you write matches one;
  - shows the UK pronunciation and audio from the Cambridge Dictionary, the meaning (WordNet), the Russian translation, and the sound written in Russian letters;
  - lists every outline in one table to search, edit, move or delete;
  - has a Practice tab, a typing test like Monkeytype on any text or EPUB book with tips for the shortest outline, and a Stats tab read from Plover's stroke log.
- **Quick add** (`TK*UPT`): a small window to give the last word an outline without leaving what you're writing.
- **Raw mode** (`RA*U`): see raw steno instead of words.
- **A dark theme** for Plover's windows, as its own small plugin.

## Layout

```
plover-dotterel/        the Plover plugin (version 1.5.0)
  plover_dotterel/
    system.py           keys, steno order, Gemini PR mapping, endings
    dictionaries/       every dictionary Plover loads
    builder.py ...      the Builder, Quick add and their helpers
    data/               word frequency, hyphenation, meanings, UK/US list
  dark-theme/           the dark theme plugin
  tests/
tools/
  boundary_clashes.py   finds outlines that swallow a phrase (AUL/PHOEFT
                        would turn "all most" into "almost")
docs/
  commands-cheat-sheet.md  every command stroke: keys, movement, modifiers, punctuation, capitals
  rp-rules.md           how Dotterel differs from Lapwing
  lapwing-rules.md      the full Lapwing theory it builds on
```

## Install

In Plover's own Python (Plover > Plugins Manager can't install from a folder):

```
plover -s plover_plugins install ./plover-dotterel
plover -s plover_plugins install ./plover-dotterel/dark-theme   # optional
```

Restart Plover, then in Configure pick **System: Dotterel** and **Machine: Gemini PR** (your keyboard's serial port). The plugin also installs `plover-auto-reconnect-machine`; tick it once in Configure > Plugins so Plover reconnects if the keyboard drops.

## Keys

Steno order: `# S T K P W H R A O * E U F R P B L G T S D Z`.

## Credits

- Lapwing theory and dictionaries: Aerick, MIT licence (`plover-dotterel/LICENSE-lapwing`).
- Definitions: WordNet 3.0, Princeton University (`LICENSE-meanings`).
- British hyphenation patterns: Dominik Wujastyk and Graham Toal (`LICENSE-hyphenation`).
- UK/US spelling list: hyperreality/American-British-English-Translator, MIT (`LICENSE-uk-us-list`).

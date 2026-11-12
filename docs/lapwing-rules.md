# Lapwing theory: complete rules reference

A single reference of every rule in Lapwing, the Plover-based English steno theory by Aerick, collected as a starting point for Dotterel.

**Sources** (read in full on 2026-11-02):

- *Lapwing for Beginners*, the official book: <https://lapwing.aerick.ca/> (source repo [aerickt/lapwing-for-beginners](https://github.com/aerickt/lapwing-for-beginners), commit `46b53e1`, June 2026). Chapter numbers below (Ch. N) refer to this book.
- The official dictionaries and system plugin: [aerickt/plover-lapwing-aio](https://github.com/aerickt/plover-lapwing-aio) (commit `4ac5d53`, July 2026): `lapwing-base.json` (114,885 entries), `lapwing-numbers.json`, `lapwing-commands.json`, `system.py`.
- Plover's English orthography rules, which Lapwing inherits: [plover/system/english_stenotype.py](https://github.com/openstenoproject/plover/blob/main/plover/system/english_stenotype.py).

The book says its own Appendix D ("Theory Reference Guide") is outdated and incomplete, so the rules here follow the chapters and the live dictionary. Where the book and the dictionary differ, it says so.

Notation: `/` separates strokes; a leading hyphen (`-T`) marks a right-hand key; `*` is the asterisk. "Write-out" means an outline that follows theory; "brief" means an abbreviation that does not.

---

## Contents

1. [Philosophy](#1-philosophy)
2. [Layout and steno order](#2-layout-and-steno-order)
3. [Left-hand (initial) consonants](#3-left-hand-initial-consonants)
4. [Vowels](#4-vowels)
5. [Right-hand (final) consonants](#5-right-hand-final-consonants)
6. [The asterisk: every use](#6-the-asterisk-every-use)
7. [Conflict resolution rules](#7-conflict-resolution-rules)
8. [Single-syllable words that break steno order](#8-single-syllable-words-that-break-steno-order)
9. [Prefixes](#9-prefixes)
10. [Suffixes](#10-suffixes)
11. [Compound words](#11-compound-words)
12. [Syllabic splitting](#12-syllabic-splitting)
13. [KWR: linker and glide](#13-kwr-linker-and-glide)
14. [Shortening techniques](#14-shortening-techniques)
15. [Briefs (top 200 words)](#15-briefs-top-200-words)
16. [Phrasing](#16-phrasing)
17. [Fingerspelling](#17-fingerspelling)
18. [Numbers](#18-numbers)
19. [Proper nouns and acronyms](#19-proper-nouns-and-acronyms)
20. [Punctuation](#20-punctuation)
21. [Formatting commands](#21-formatting-commands)
22. [Editing, movement, symbols, modifiers](#22-editing-movement-symbols-modifiers)
23. [UK spellings](#23-uk-spellings)
24. [Miscellaneous rules and special words](#24-miscellaneous-rules-and-special-words)
25. [Orthography rules (Plover engine)](#25-orthography-rules-plover-engine)
26. [How Lapwing differs from Plover theory](#26-how-lapwing-differs-from-plover-theory)
27. [Notes for Dotterel](#27-notes-for-dotterel)

---

## 1. Philosophy

- Lapwing is "Plover theory but more defined": for a given pronunciation there should be exactly **one correct write-out** (Appendix A).
- Consonants are mostly **phonetic** (sound), with a few **orthographic** (spelling) chords. Vowels are a mix: short vowels follow spelling, long vowels follow sound.
- Homophone **conflicts are resolved primarily by spelling**, using the asterisk or an alternative vowel chord.
- Multisyllable words use, in order of preference: affix strokes (prefix/suffix), compound-word rule, then strict syllabic splitting.
- Based on General North American English (the author's Canadian accent: cot–caught and father–bother merged). Speakers of other accents may need to subvocalise in an American accent (Ch. 7). Warbler theory is the suggested British alternative.
- Briefs exist but are secondary; the dictionary is meant to be personalised once basic theory is learnt.

## 2. Layout and steno order

Standard Ward Stone Ireland layout, with one change: **the number key `#` is moved to the top-left S key** (top S = `#`, bottom S = `S`). In `system.py`, Gemini `S1-` maps to `#`, `S2-` to `S`; `NUMBER_KEY = None` and `NUMBERS = {}` so `#` does **not** turn letters into digits (digits come from a dictionary, see §18).

```
#  T  P  H  *  F  P  L  T  D
S  K  W  R  *  R  B  G  S  Z
         A  O  E  U
```

**Steno order:** `# S T K P W H R A O * E U F R P B L G T S D Z`

A stroke is: initial consonant(s) + vowel(s) + final consonant(s). A single key in any of these parts means the sound of its letter (Ch. 5). Every sound in a stroke must appear in steno order; if it cannot (e.g. "trust" would need `-TS`), use another rule (§5 `-F` as s, §8).

Raw steno shows a hyphen before right-hand keys only when the stroke has no vowel or asterisk (`-T`, `-RPL`, but `KAT`).

## 3. Left-hand (initial) consonants

"Phonetic" = chosen by sound; "Orthographic" = chosen by spelling.

| Chord | Sound | Type | Examples |
|---|---|---|---|
| `S` | s (voiced or unvoiced) | P | sip `SEUP` |
| `T` | t | P | type `TAOEUP` |
| `K` | k (hard c, k) | P | cat `KAT`, king |
| `P` | p | P | pay `PAEU` |
| `W` | w | P | want `WAUPBT` |
| `H` | h | O | hour `HOUR` (silent h kept to avoid `OUR`) |
| `R` | r | P | root `RAOT` |
| `TK` | d | P | dad `TKAD` |
| `PW` | b | P | bar `PWAR` |
| `HR` | l | P | lap `HRAP` |
| `TP` | f | O | far `TPAR` |
| `TP*` | ph | O | phase, phone `TPO*EPB`, cipher `SAOEU/TP*ER` |
| `KW` | qu | O | quit `KWEUT`, equal `AOE/KWAUL` |
| `PH` | m | P | met `PHET` |
| `TKPW` | g (hard g only) | P | get `TKPWET` ("gel" uses `SKWR`) |
| `TPH` | n | P | not `TPHOT` |
| `KWH` | y (**only when spelled with initial "y"**) | O | yes `KWHES`, yurt `KWHURT` |
| `STKPW` | z | O | zap `STKPWAP` |
| `SR` | v | P | var `SRAR` |
| `SKWR` | j (incl. soft g) | P | jot `SKWROT`, roger `RO/SKWRER` |
| `SH` | sh | P | shoe `SHAOU` |
| `TH` | th | O | thug `THUG` |
| `KH` | ch | P | chug `KHUG`, culture `KUL/KHUR` |
| `WH` | wh | O | when `WHEPB` |
| `WR` | wr | O | write `WRAOEUT` |
| `KP` | x (initial) | O | x-ray `KP/RA*EU` |
| `TW` | tw, and chw | P | twig `TWEUG`, mutual `PHAOU/TWAL` |
| `ST` `SK` `SP` `TR` `KR` `PR` | the letter combinations | P | stop, scar, spot, trap, crop, prat |
| `STR` `SKR` `SPR` `THR` | str, skr, spr, thr | P | strap, scree, spray, thread |
| `PWR` `TKR` `TPR` `TKPWR` | br, dr, fr, gr | P | bring, drag, from, grade |
| `PHR` | pl | P | plat (why "f" is not `PH`: "fl" would collide) |
| `TPHR` | fl | P | flat `TPHRAT` |
| `PWHR` | bl | P | bled `PWHRED` |
| `TKPWHR` | gl | P | gloss `TKPWHROS` |
| `SPH` | sm | P | smell `SPHEL` |
| `KPR` | compr | P | comprise `KPRAOEUS` |
| `SHR` | shr; also "sl" | P | slug `SHRUG`, shrug `SHR*UG` (§7) |

General rule: **any chord whose keys spell the sound is valid** (e.g. `THR`).

**"y" sound** (Ch. 6, 12, 15):

| Situation | Chord | Example |
|---|---|---|
| Word begins with letter "y" | `KWH` | yell `KWHEL` |
| Word begins with a "y" sound not spelled "y" | none | use `AOUS`, usual `AOURB/WAL` |
| "y" sound inside a word | `KWR` | union `AOUPB/KWROPB` |

**Left-hand compound clusters** (Ch. 17, shortening):

| Chord | Represents | Examples |
|---|---|---|
| `SPW` | int-, ent- | entire `SPWAOEUR`, intern `SPWERPB` |
| `KP` | comp- | (compound cluster) |
| `KPW` | comb- | combine |
| `KPH` | com- | commend `KPHEPBD`, commit `KPHEUT` |
| `TKW` | div-/dev- (`W` = v) | divide `TKWAOEUD`, device `TKWAOEUS` |
| `STK` | d_s (des-, dis-) | decide `STKAOEUD`, disappear `STKPAOER` |

## 4. Vowels

There are four vowel keys; `EU` is the letter "i".

### 4.1 Short vowels and schwa (spelling-based)

| Sound | IPA | Chord | Example |
|---|---|---|---|
| short a | /æ/ | `A` | cat `KAT` |
| short e | /ɛ/ | `E` | pet `PET` |
| short i | /ɪ/ | `EU` | sit `SEUT` |
| short o | /ɑ/ (also /ɔ/, /ɒ/) | `O` | cot `KOT` |
| short u | /ʌ/ and /ʊ/ | `U` | hut `HUT`, pull `PUL` |
| schwa | /ə/ | spelled letter | about, pencil |

- **Rule 1:** a short vowel or schwa spelled with **one letter** uses the key matching the spelling ("son" = `SOPB`, "busy" = `PWEU/SEU`).
- **Rule 2:** a short vowel spelled with **several letters** uses the key matching the sound: could `KUD`, head `HED`, said `SED`, tough `TUF`, plaid `PHRAD`. A multi-letter schwa uses any of its letters.
- **Short o exception (`AU`):** short o is written `O` only when spelled with a single "o". Every other spelling of that sound uses `AU`: bought `PWAUT`, caught `KAUT`, watt `WAUT`, spa `SPAU`. The "-al-" words with silent l also use `AU` and drop the l: calm `KAUPL`, chalk `KHAUBG`, psalm `SAUPL`, stalk `STAUBG`.
- **R-coloured short vowels** (car, her, sir, pore, purr) count as short vowels, so Rule 1 applies: `KAR`, `HER`, `SEUR`, `POR`, `PUR`. Identify the vowel as short first: "cure" is long (`KAOUR`, not `KUR`).

### 4.2 Long vowels and diphthongs (sound-based)

| Sound | IPA | Chord | +R form | Examples |
|---|---|---|---|---|
| long a | /eɪ/ | `AEU` | `AEUR` /ɛr/ | pay `PAEU`, pair `PAEUR` |
| long e | /i/ | `AOE` | `AOER` /ɪər/ | beet, peer `PAOER` |
| long i | /aɪ/ | `AOEU` | `AOEUR` | ice, tire `TAOEUR` |
| long o | /oʊ/ | `OE` | (`OR`) | tote, foe `TPOE` |
| long u / "oo" | /ju/, /u/ | `AOU` | `AOUR` /ʊər/ | cube, glue, cure `KAOUR` |
| ow | /aʊ/ | `OU` | `OUR` | cow, hour `HOUR` |
| oy | /ɔɪ/ | `OEU` | | toy, coil `KOEUL` |

- `AOU` for the "oo" sound **only when not spelled "oo"** ("loo" is not `AOU`).
- Long a spelled with a single e (e.g. "herr") uses `ER`.
- `OEU` is rare in English, so Lapwing (like Plover) uses it as a wildcard in briefs (e.g. `OEUT` auto^).

### 4.3 Orthographic vowel chords

- **`AO`** = any word spelled **"oo"**, whatever the sound: wood `WAOD`, blood `PWHRAOD`, tool `TAOL`. Also "oa" words **only to resolve a conflict**: oar `AOR`, soar `SAOR`, boar `PWAOR`, road `RAOD`. ("boat" has no conflict so it is `PWOET`; `PWAOT` is "boot".)
- **`AE`** = secondary chord for conflicts, never tied to a sound by itself (see §7.2).
- **`OU`** is phonetic, but may disambiguate "ou" spellings when free: four `TPOUR`, soul `SOUL`.

### 4.4 When long e is `EU` (Ch. 15)

1. Spelled with a single "i" → `EU`: petite `PE/TEUT`, ski `SKEU`.
2. Spelled "ey" or "y" → `EU`: city `SEU/TEU`, key `KEU`.
3. If `EU` is taken by another word → `AOE`: marine `PHAR/KWRAOEPB` (since `PHAR/KWREUPB` is "marin").
4. Otherwise `AOE` (or `AE` in conflicts): cookie `KAO/KAOE`, here `HAOER`, hear `HAER`.

Final "i" vs "y" in names: `EU` for "i", `KWREU` for "y" (Terri `#TE/REU`, Terry `#TER/KWREU`).

## 5. Right-hand (final) consonants

| Chord | Sound | Examples |
|---|---|---|
| `-F` | f; also v (§7.4); also s before another consonant | puff, solve `SOF`, trust `TRUFT`, bask `PWAFBG` |
| `-R` | r | far `TPAR` |
| `-P` | p | tap `TAP` |
| `-B` | b | lab |
| `-L` | l | tell `TEL` |
| `-G` | g | sag `SAG` |
| `-T` | t | net `TPHET` |
| `-S` | **any final letter "s"**, even when pronounced z | pass, has, fuse `TPAOUS`, cruise `KRAOUS` |
| `-D` | d | cad `KAD` |
| `-Z` | z sound (jazz, fizz) and raise `RAEUZ` | |
| `-PB` | n | fin `TPEUPB` |
| `-PL` | m | form `TPORPL` |
| `-BG` | k | sack `SABG` |
| `-PBLG` | j (dge) | lodge `HROPBLG` |
| `-LG` | lj and lch | bulge, mulch `PHULG`, belch `PWELG` |
| `-PBG` | ng and nj | sing `SEUPBG`, strange |
| `-FP` | ch (also sp in dictionary) | couch, hitch `HEUFP` |
| `-RB` | sh (and rb, see §7) | trash, mash `PHARB` |
| `-FRPB` | rch and nch | arch, punch `PUFRPB` |
| `-FRB` | rv | curve `KUFRB` |
| `-FT` | ft and st | loft `HROFT`, host `HOEFT` |
| `-FR` | fer, ver | lover `HROFR` |
| `-FL` | f_l, v_l | playful, valve `SRAFL` |
| `-RP` `-RL` `-RT` `-RD` `-PT` `-LD` `-PBT` `-PBS` `-PBD` `-BGT` | the letter combinations | harp, curl, part, card, opt, sold, hint, dance, sand, pact |
| `-GT` | xt | text `TEGT`, next `TPHEGT` |
| `-GS` | shun | motion `PHOEGS`, caution `KAUGS` |
| `-BGS` | x, and kshun | tax `TABGS`, fax `TPABGS` |
| `-PLT` | ment | garment `TKPWARPLT`, torment `TORPLT` |
| `-LT` | let | wallet `WAULT`, roulette `RAOULT` |
| `-BL` | bl, and vowel+ble ("-able", "-ible") | rebel `REBL`, playable `PHRAEUBL`, terrible `TERBL` |
| `-BLT` | bility, vowel+bility | mobility `PHOEBLT`, viability `SRAOEUBLT` |
| `-RBS` | shus | cautious, luscious `HRURBS` |
| `-RBL` | shal | facial `TPAEURBL`, special `SPERBL` |

**Asterisk variants of finals:**

| Chord | Sound | Examples |
|---|---|---|
| `*PL` | mp (**always**, unlike Plover) | bump `PW*UPL`, crimp `KR*EUPL`, lamp `HRA*PL` |
| `*T` | th | bath `PWA*T`, moth `PHO*T` |
| `*LG` | lk | elk `*ELG`, talc `TA*LG` |
| `*FRB` | rf | turf `T*UFRB`, serf `S*EFRB` |
| `*PBG` | nk | tank `TA*PBG`, sink `S*EUPBG` |
| `*F` | v when "f" word conflicts (§7.4) | save `SA*EUF` |
| `*S` | st when `-FT` would mean ft | list `HR*EUS`, lost `HRO*S` |
| `*BGS` | kshun when `-BGS` is an x word | faction `TPA*BGS`, section `S*EBGS` |

`-FRPBLG` is the secondary "-nch" chord (lunch `HRUFRPBLG`, since `HRUFRPB` is "lurch").

**Compound clusters** (`-GS`, `-BGS`, `-PLT`, `-LT`, `-BL`, `-BLT`, `-RBS`, `-RBL`) can hold more than one syllable. They can be put into the first stroke whenever no key overlaps and steno order holds: cement `SEPLT`, ferment `TPERPLT`, arable `AEURBL`, bullet `PWULT`. If a key would overlap, split: probability `PROB/-BLT`, humble `HUPL/-BL`, omelet `OPL/-LT`, partial `PAR/-RBL`, possible `POS/-BL`, fragment `TPRAG/-PLT`, pamphlet `PAPL/*F/-LT`.

## 6. The asterisk: every use

1. **Undo** the last stroke on its own (`*`). It deletes a stroke, not a word.
2. **Alternative final chords**: `*PL` mp, `*T` th, `*LG` lk, `*FRB` rf, `*PBG` nk, `*S` st, `*BGS` kshun, `*F` v (§5).
3. **Ending a split word in t or f/v**: `*T`, `*F` instead of `-T` "the" / `-F` "of" (§8).
4. **Conflict resolution** between homophones (§7), e.g. caul `KA*UL`, haul `HA*UL`, bawl `PWA*UL`, carb `KA*RB`, shrug `SHR*UG`.
5. **Compound words**: on the first stroke of the second word (§11).
6. **Word version of a prefix**: on the last stroke of a multistroke prefix (`UPB/TK*ER` "under") and some single ones (`O*UT` "out", `O*PB` "on").
7. **Contractions**: he's `HAO*ES`, he'll `HAO*EL`, we're `WAO*ER`, who's `WHO*S`, what's `WHA*S`, that's `THA*S`, there's `THR*S`, they're `TH*ER`.
8. **Words ending in "h"**: hah `HA*`, heh `H*E`, meh `PH*E`.
9. **Fingerspelling** (§17), **"ph"** (`TP*`), **acronyms** (§19), **closing punctuation** (§20), **UK spellings** "-re" (§23).
10. **Selection** in movement commands; **negation** in Jeff's phrasing.

## 7. Conflict resolution rules

The general principle is **spelling decides priority**: the word whose spelling matches the keys more directly gets the plain outline; the other gets the asterisk or an alternative chord. Frequency is used only as a last resort.

### 7.1 Short o: `O` vs `AU`; "au"/"awl" conflicts
- Single "o" → `O`; any other spelling → `AU` (bot `PWOT`, bought `PWAUT`).
- Within `AU`, "au" and "awl" spellings get `A*U` on conflict: call `KAUL` / caul `KA*UL`; hall `HAUL` / haul `HA*UL`; all `AUL` / awl `A*UL`; ball `PWAUL` / bawl `PWA*UL`.

### 7.2 `AE` as the low-priority twin of `AEU` and `AOE`
**Long a** (`AEU` vs `AE`):
1. "ai"/"ei" spellings → always `AEU` (eight `AEUT`, fair `TPAEUR`, main `PHAEUPB`, pair `PAEUR`).
2. "a_e" spellings → `AEU` unless taken, then `AE` (ate `AET`, fare `TPAER`, mane `PHAEPB`; tare `TAEUR` since "tair" isn't a word).
3. "ea" spellings → `AE` if either of the above has the outline (tear `TAER`, pear `PAER`; swear `SWAEUR` stays since no conflict).

**Long e** (`AOE` vs `AE`):
1. "ee" → `AOE` (feet, pee, seed, tee).
2. "ie" → `AOE` (piece `PAOES`).
3. "ea" → `AE` on conflict (feat `TPAET`, pea `PAE`, peace `PAES`, tea `TAE`).

**"ea" vs short e**: lead `HRAED` (`HRED` = led), bread `PWRAED` (`PWRED` = bred).

**Three-way**: no rule; dictionary gives pear `PAER`, pare `PA*EUR` (by frequency).

### 7.3 Initial consonant conflicts
- **`KR` for soft c** when the s spelling has the outline: cent `KREPBT` (sent `SEPBT`), cite `KRAOEUT` (sight).
- **`KH` for hard "ch"**: chord `KHORD` (cord `KORD`). `KH` may also be used generally for hard-c "ch" words (charisma `KHA/REUS/PHA` or `KA/...`); the book recommends `K` except in conflicts.
- **Chord vs individual keys**: when a chord (e.g. `HR` = l) and the literal letters (h+r) give the same outline, the word where the **keys match the letters one to one gets lower priority** (asterisk): slug `SHRUG`, shrug `SHR*UG`.
- Names: "kr" beats "chr"/"cr" in `KR-`: Kristy `#KREUS/TEU`, Christy `#KR*EUS/TEU` (or `#KHREUS/TEU`).
- scene `SKAOEPB` (adds silent `K` since `SAOEPB` = seen).

### 7.4 Final consonant conflicts
- **f vs v**: `-F` for the "f" word, `*F` for the "v" word: safe `SAEUF` / save `SA*EUF`, waif / waive `WA*EUF`.
- **ft vs st**: `-FT` = ft word; `*S` = st word: lift `HREUFT` / list `HR*EUS`, loft / lost `HRO*S`.
- **x vs kshun**: `-BGS` = x/ks word; `*BGS` = kshun word: tracks `TRABGS` / traction `TRA*BGS`, reflex / reflection `RE/TPHR*EBGS`. Exception: diction `TKEUBGS`.
- **sh vs rb**: `-RB` = sh word; rb word asterisked: cash `KARB`, carb `KA*RB` (cache `KAERB`).
- **s vs z**: `-S` = s-sound word ("race"); `-Z` for a common s-spelled z word ("raise" `RAEUZ`); alternative vowel for the next ("raze" `RAEZ`); asterisk after that ("raiz" `RA*EUZ`). Expected to be personalised.
- Repeated letters in names take the asterisk: Hartman `#HART/PHAPB`, Hartmann `#HART/PHA*PB`.
- If two words differ in a vowel (esp. y vs i), the asterisk goes to the word whose spelling doesn't match the key: Lin `#HREUPB`, Lynn `#HR*EUPB`.

### 7.5 Prefix vs word
Prefixes get the intuitive outline; the word gets a brief, asterisk, or alternative vowel (§9.3).

## 8. Single-syllable words that break steno order

Write as much as possible in one stroke, then finish with the right-hand chord in a second stroke (Ch. 12):

- film `TPEUL/-PL`, helm `HEL/-PL`, help `HEL/-P`, kelp `KEL/-P`, peddle `PED/-L`, saddle `SAD/-L`, kiln `KEUL/-PB`.
- **To end with t use `*T`; to end with f/v use `*F`** (because `-T` = "the", `-F` = "of"): elf `EL/*F`, shelf `SHEL/*F`, sixth `SEUBGS/*T`.
- For **-st**, prefer `-FT` or `*S` over a split: list `HR*EUS` (not `HREUS/*T`), thirst `TH*EURS`.
- Words ending in a compound cluster after a clashing sound: `PAR/-RBL` partial, `KOPB/-RBS` conscious, `PWRAEUS/-LT` bracelet (or syllabic: `PAR/SHAL`).

## 9. Prefixes

### 9.1 How they work
A prefix stroke is defined `{xyz^}` and attaches to the next stroke (e.g. `TPHOPB` = `{non^}`, so `TPHOPB/KAT` → "noncat").

**Usage rule:** use a prefix stroke **only when it modifies a root word that can exist on its own and is related in meaning** (redo, preview `PRAOE/SRAOU`, forget `TPOR/TKPWET`). "confuse" is not con+fuse, so it is syllabically split. Exception: the **`A` prefix** (a^) may be used freely, regardless of meaning: about `A/PWOUT`, allow `A/HROU`, amend `A/PHEPBD`.

When syllabic splitting produces a stroke that happens to be a prefix (trident `TRAOEU/TKEPBT`), that is fine; it is splitting, not prefix usage.

### 9.2 Prefix strokes in the dictionary
Common, from the book: a^ `A`, co^ `KOE`, de^ `TKAOE`/`TKE`, for^ `TPOR`, in^ `EUPB`, mis^ `PHEUS`, non^ `TPHOPB`, pre^ `PRAOE`/`PRE`, pro^ `PROE`/`PRO`, re^ `RAOE`/`RE`, sub^ `SUB`. Alternate vowel versions exist for different pronunciations (defect `TKAOE/TPEBGT` or `TKE/TPEBGT`).

All single-stroke prefixes in `lapwing-base.json`:

a `A` · after `AFR` · ante `AEPBT` · auto `OEUT` (brief; write-out `AU/TOE`) · be `PWE` · bi `PWAOEU` · bio `PWO*E` · centi `KR*EPBT` · co `KOE` · con `KOPB` · counter `KOURPBT` · cyber `SAOEURB` · de `TKAOE`/`TKE` · demi `TKPHEU` · demo `TKPHO` · di `TKAOEU`/`TKEU` · dis `TKEUS` · dys `TK*EUZ` · e `AOE`/`E` · electro `HRERBGT` · em `EPL` · en `EPB` · epi `EP` · er `ER` · every `*FR` · ex `EBGS` · extra `KPRA` · fluoro `TPHRAOUR` · for `TPOR` · giga `TKPW*EUG` · heli `H*EL` · hetero `HERT` · hydro `HAO*EURD`/`HOEURD` · hyper `HAOEURP` · hypo `HOEUP` · im `EUPL` · in `EUPB` · inter `EURPBT` · intra `SPWRA` · intro `SPWRO`/`SPWROE` · ir `EUR` · iso `OEUS` · kilo `K*EUL` · mal `PHAL` · mega `PH*EG` · micro `PHAOEURBG` · mid `PHEUD` · milli `PH*EUL` · mini `PH*EUPB` · mis `PHEUS` · mono `PHO*PB` · multi `PHULT` · necro `TPHERBG` · neo `TPHO*EU` · neuro `TPHAOUR` · non `TPHOPB` · off `OF` · on `OPB` · or `OR` · ortho `O*RT` · out `OUT` · over `OEFR` · para `PA*R` · penta `P*EPBT` · pneumo `TPHAOUPL` · poly `PO*L` · pre `PRAOE`/`PRE` · pro `PRO`/`PROE` · proto `PROET` · radio `RO*EUD` · re `RAOE`/`RE` · rea `RAE` · retro `RERT` · sarco `SARBG` · semi `SPHEU` · stereo `STOEUR` · stylo `STO*EUL` · sub `SUB` · super `SAOURP` · sur `SUR` · tele `T*EL` · tera `T*ER` · tetra `TRERT` · thermo `THOEURPL` · trans `TRAPBS` · tri `TRAOEU` · ultra `URLT` · un `UPB` · under `URPBD` · uni `AOUPB` · xylo `KPAO*EUL`

### 9.3 Prefix priority over words

| Prefix/word | Prefix | Word outline(s) | Note |
|---|---|---|---|
| a | `A` | `AEU` | `A*` is fingerspelling |
| bi^ / by | `PWAOEU` | `PWEU` | bye `PW*EU`, buy `PWAO*EU` |
| be | `PWE` | `-B` | bee `PWAOE` |
| for | `TPOR` | `TP-R` or `TPAURT` | "for the" `TP-RT` |
| in | `EUPB` | `TPH` | "in the" `TPH-T` |
| or | `OR` | `AOUR` or `AUR` | `O*R` is ^or suffix |
| out | `OUT` | `AOUT` or `O*UT` | |
| on | `OPB` | `AUPB` or `O*PB` | |
| over | `OEFR` | `AUFR` | |
| off | `OF` | `AUF` | |
| tri^ / try | `TRAOEU` | `TREU` or `TRAO*EU` | |
| di^ / die / dye | `TKAOEU`/`TKEU` | die `TKAO*EU`, dye `TK*EU` | acknowledged theory gap |

Using `AU` instead of `O`/`OE` for the word form is preferred over the asterisk because it's easier to press.

**Multistroke prefixes:** the word takes the **asterisk on the last stroke**: auto `AU/TOE` vs `AU/TO*E`; intro `EUPB/TROE` vs `EUPB/TRO*E`; over `OE/SRER` vs `OE/SR*ER`; under `UPB/TKER` vs `UPB/TK*ER`.

**Brief prefix strokes** (one stroke standing for a multistroke prefix) can be used with syllabic splitting regardless of meaning: automate `OEUT/PHAEUT`, internet `EURPBT/TPHET`, paradise `PA*R/TKAOEUS`, supermarket `SAOURP/PHARBGT`, telecommunication `T*EL/KPHAOUPB/KAEUGS`.

### 9.4 Prefix exceptions to splitting rules
- After a prefix, **the next stroke may start with a vowel**: coordinate `KOE/OR/TKEU/TPHAEUT`, inequal `EUPB/AOE/KWAUL`, preordain `PRAOE/OR/TKAEUPB`, unattainable `UPB/A/TAEUPB/-BL`.
- After a prefix, **a consonant may be doubled** across strokes if the rest is a word: dissolves `TKEUS/SOFLS`, dissimilar `TKEUS/SEU/PHEU/HRAR`, immobile `EUPL/PHOE/PWAOEUL`, immobilize `EUPL/PHOEBL/KWRAOEUZ`.
- Words starting with an `EU` sound (illuminate, immense): syllabic (`EU/HRAOU/PHEU/TPHAEUT`, `EU/PHEPBS`) or prefix-style even when the remainder isn't a word (`EUL/HRAOU/...`, immense `EUPL/KWREPBS` or `EUPL/PHEPBS`, immune `EUPL/PHAOUPB`). The prefix forms are fallbacks that may be removed.
- "r" after a prefix may be treated as a consonant: arose `A/ROES`, derive `TKE/RAOEUF`, reroute `RE/RAOUT`.
- Prefix vs compound word is a judgment call; the dictionary treats "upright", "downwards" as compounds (`UP/RAO*EUT`, `TKOUPB/WA*RD/-Z`).

## 10. Suffixes

A suffix stroke is defined `{^xyz}` and attaches to the previous word. **Unless stated, use a suffix only to modify a related root word** (player `PHRAEU/*ER` yes; mutter `PHUT/*ER`, mentor `PHEPBT/O*R`, pillar `PEUL/A*R` no; those are syllabically split). Plover's orthography rules fix spelling at the join (§25): purist `PAOUR/KWREUFT`, hasty `HAEUFT/KWREU`, luckily `HRUBG/KWREU/HREU`, basic `PWAEUS/KWREUBG`.

### 10.1 Suffix keys (single right-hand keys)

| Key | Suffix | Example |
|---|---|---|
| `-G` | ^ing | patting `PAT/-G` |
| `-S` | ^s | cats `KAT/-S` |
| `-D` | ^ed | glued `TKPWHRAOU/-D` |
| `-Z` | ^s | sides `SAOEUD/-Z` |

`-Z` is the one to use as the standalone plural key. **Folding** suffix keys into the previous stroke works in Plover (it auto-applies to any defined word: `HAEPZ` → happies) but is **not recommended** in Lapwing because of conflicts (cease/sees `SAOES`, plague/playing `PHRAEUG`, raise/rays `RAEUZ`). Plural of a word ending in `-T` folds with `-S`, not `-Z` (crates `KRAEUTS`).

### 10.2 `*` + vowel + `R` suffixes
| `A*R` ^ar | `O*R` ^or | `*ER` ^er |
|---|---|---|
| cellar `KREL/A*R`, hangar | actor `ABGT/O*R`, sailor | teacher `TAOEFP/*ER`, upper `UP/*ER` |

They are kept out of the `KWR` family because `KWRAR`, `KWROR`, `KWRER` mean ^iar, ^ior, ^ier.

### 10.3 Right-hand chord suffixes
`-FL` ^ful (helpful `HEL/-P/-FL`, hopeful `HOEP/-FL`) and `-PBS` ^ness (illness `EUL/-PBS`): root-word only.

### 10.4 Compound-cluster suffixes (usable anywhere)
`-PLT` ^ment, `-BLT` ^ability/^ibility, `-BL` ^able, `-LT` ^let. Because they are also compound clusters, they may be used **even when the preceding part is not a root word** (cement `SE/-PLT`, humble `HUPL/-BL`, omelet `OPL/-LT`), and should be folded into the first stroke when keys don't overlap (`SEPLT`). Overlapped forms (`PROBLT`, `OPLT`) are acceptable personal briefs but not theory.

### 10.5 `KWR` suffixes (linker)
`KWR` is a silent linker meaning "attach to previous word":

| Stroke | Suffix | Example |
|---|---|---|
| `KWRAL` | ^al | spinal `SPAOEUPB/KWRAL` |
| `KWRAPBT` | ^ant | sealant, coolant |
| `KWRAEUGS` | ^ation | flotation `TPHROET/KWRAEUGS` |
| `KWRAOEUZ` | ^ize | mobilize `PHOEBL/KWRAOEUZ` |
| `KWROUT` | ^out | holdout, bailout |
| `KWREUF` | ^ive | festive, active |
| `KWREUFPL` | ^ism | tourism |
| `KWREUFT` | ^ist | artist, purist |
| `KWREUPB` | ^in | plugin, herein |
| `KWREUBG` | ^ic | basic, cubic |
| `KWREPB` | ^en | soften, rotten |
| `KWREPBT` | ^ent | dependent `TKE/PEPBD/KWREPBT` |

### 10.6 `EU` suffixes
`KWREU` ^y (crazy `KRAEUZ/KWREU`, chatty) and `HREU` ^ly (firmly `TPEURPL/HREU`, mostly). If the root ends in "l", use `KWREU` (hilly `HEUL/KWREU`, not `HEUL/HREU`; no doubling).

### 10.7 Full single-stroke suffix list from `lapwing-base.json`

'll `*L` · 's `AES` · 've `*F` · a `KWRA` · ability `-BLT` · able `KWRABL`/`-BL` · ably `PWHREU`/`EBL` · aceous `AEURBS` · ache `KWRAEUBG`/`A*EUBG` · adocious `TKOERBS` · age `KWRAPBLG` · aire `KWRAEUR` · al `KWRAL` · ality `KWRALT` · ally `KWRAEL` · als `A*LS` · an `KWRAPB` · ance `KWRAPBS` · ant `KWRAPBT` · ar `A*R` · arian `KWRAERPB` · aries `KWRAERS` · arity `KWRAERT`/`AERT` · arium `KWRAERPL` · ars `A*RS` · ary `KWRAER` · ate `KWRAT` · atic `KWRABGT` · ation `KWRAEUGS` · atize `TAO*EUZ` · back `PWA*BG` · bend `PW*EPBD` · book `PWAO*BG` · burg `PW*URG` · cal `KAL` · cate `KAEUT` · cation `KAEUGS` · ch `*FP` · cox `KOBGS` · cracy `KRAES` · cy `SEU` · dation `TKAEUGS` · den `TK*EPB` · dition `TKEUGS` · down `KWROUPB` · drawn `TKRA*UPB` · drome `TKROEPL` · e `KWRE` · ed `-D` · eer `KWRAOER` · el `KWREL` · en `KWREPB` · ence `KWR*EPBS` · ens `KWREPBS` · ent `KWREPBT` · ential `KWREPBL` · er `*ER` · erance `RAPBS` · ering `*ERG` · es `KWRES` · ese `KWRAOES` · esque `KWREFBG` · est `KWREFT` · et `KWRET` · eus `KWR*US` · ex `KWREBGS` · fiability `TPAOEUBLT` · flection `TPHR*EBGS` · fold `TPO*ELD` · ford `TPO*RD` · form `TPO*RPL` · fruit `TPRAO*UT` · ful `-FL` · gasm `TKPWAFPL` · grapher `TKPWRAFR` · graphy `TKPWRAEF` · ham `HA*PL` · hood `HAO*D` · i `SKWREU` · iability `KWRABLT` · ian `KWRA*PB` · iant `KWRA*PBT` · ias `KWRAS` · iastic `KWRAFBGT` · iate `KWRAEUT` · ible `KWREUBL` · ic `KWREUBG` · ically `KAEL` · ie `KWRAOE` · ien `KWR*EPB` · ient `KWR*EPBT` · ier `KWRER` · ification `TPAEUBGS` · ify `TPAOEU` · ile `KWRAOEUL` · ility `KWREULT`/`EULT` · im `KWREUPL` · in `KWREUPB` · in' `*G` · ination `TPHA*EUGS` · inative `TPHA*EUFT` · ine `KWRAOEUPB` · ing `-G` · ion `KWRO*PB` · iority `KWRORT` · iorly `KWRORL` · ish `KWREURB` · ishness `SH-PBS` · ism `KWREUFPL` · ist `KWREUFT` · istic `ST-BG` · it `KWREUT` · itarian `TAERPB` · ite `KWRAOEUT` · ition `KWREUGS` · itious `KWREURBS` · itis `KWRAOEUTS` · itude `TAOUD` · ity `TEU` · ium `KWRUPL` · ive `KWREUF` · ively `KWREUFL` · iveness `KWREUFPBS` · ives `KWREUFS` · ivity `KWR*EUFT` · ization `STKPWAEUGS` · ize `KWRAOEUZ` · ized `KWRAOEUDZ` · izer `KWRAOEURZ` · izes `KWRAOEUSZ` · izing `KWRAOEUGZ` · keep `KAO*EP` · keeper `KAO*ERP` · keeping `KAO*EPG` · key `KAO*E` · land `HRA*PBD` · lant `HRAPBT` · le `-L` · led `-LD` · less `-LS` · lessness `-PBLS` · let `-LT` · licious `HREURBS` · ling `-LG` · ly `HREU` · made `PHA*ED` · make `PHA*EUBG` · man `PHA*PB` · mation `PHAEUGS` · men `PH*EPB` · ment `-PLT` · ments `-PLTS` · most `PHO*EFT` · n't `*PBT` · nd `*PBD` · ness `-PBS` · o `KWRO` · oic `KWROEUBG` · oid `KWROEUD` · ol `KWROL` · ological `KWRO*LG` · ologist `KWROLGS` · ology `KWROLG` · or `O*R` · ories `KWROERS` · ory `KWROER` · os `KWROS` · ous `KWROUS` · out `KWROUT` · pad `PA*D` · pass `PA*S` · rd `*RD` · ress `R*ES` · room `RAO*PL` · rous `RUS` · ry `REU` · s `-S`/`-Z` · s' `A*ES` · saur `SA*UR` · saurus `SA*URS` · self `S*EFL` · selves `SEFS` · shaw `SHA*U` · shine `SHAO*EUPB` · ship `SH*EUP` · ships `SH*EUPS` · sm `*FPL` · some `SO*PL` · son `SO*PB` · spasm `SPA*FPL` · st `*S` · stand `STA*PBD` · stasis `STA*ES` · stein `STAO*EPB` · ston `STO*PB` · th `*T` · tial `-RBL` · tive `TEUF` · tivity `TEUFT` · top `TO*P` · torial `TOERL` · tory `TOER` · town `TO*UPB` · ual `WAL` · uance `WAPBS` · uation `WAEUGS` · ular `HRAR` · ulation `HRAEUGS` · ule `KWRAOUL` · um `SKWRUPL` · ure `KWRUR` · us `KWRUS` · ville `SR*EUL` · ware `WA*EUR` · way `WA*EU` · wood `WAO*D` · work `WO*RBG` · world `WO*RLD` · y `KWREU` · zoite `STKPWOEUT`

(Note the pattern: suffixes that are also whole words, such as ^book, ^man, ^work, carry the asterisk, matching the compound-word rule.)

## 11. Compound words

Closed compound words: **put the asterisk in the first stroke of the second word**; if that stroke already has an asterisk, leave it (Ch. 14).

- keyboard `KEU/PWAO*RD`, mousepad `PHOUS/PA*D`, textbook `TEGT/PWAO*BG`, storybook `STOR/KWREU/PWAO*RBG`
- candlelight `KAPBD/-L/HRAO*EUT`, grasshopper `TKPWRAS/HO*P/*ER`, eyelash `AOEU/HRA*RB`, teamwork `TAEPL/WO*RBG`, shatterproof `SHA/TER/PRAO*F`

This is what keeps "were wolves" vs "werewolves", "core net" vs "cornet" apart.

## 12. Syllabic splitting

Lapwing's key difference from Plover (Ch. 15). Rules, in order:

1. **Split off affixes and compound parts first**, even partially.
2. **Split the rest into syllables so that every stroke after the first begins with a consonant** (or `KWR`, §13).
3. **Never double a consonant sound across strokes** (shatter = `SHA/TER`, not `SHAT/TER`). Exceptions: after a prefix (§9.4), and "ng" (below).
4. If there are still several ways, **keep the natural sound** (where would you pause?).

Worked examples:
- components `KOPL/POE/TPHEPBT/-Z` (com/po/nent/s: "mp" can't start a stroke, a vowel can't start one either)
- exam `EBG/SAPL`: **an "x" split across strokes is `-BG` + `S`** (example `EBG/SA*PL/-L`)
- simile `SEU/PHEU/HRAOE`; ally `A/HRAOEU`; ludicrous `HRAOU/TKEU/KRUS`; efficient `AOE/TPEU/SHEPBT` or `E/TPEU/SHEPBT`
- wrinkly `WR*EUPBG/-L/KWREU`; dependent `TKE/PEPBD/KWREPBT`; dispatcher `TKEUS/PAFP/*ER`
- compromise `KOPL/PRO/PHAOEUS`; hubris `HAOU/PWREUS`; inadvertent `EUPB/AD/SRER/TEPBT`; occasion `OE/KAEUGS`; parliament `PAR/HRAPLT`; sentiment `SEPB/TEUPLT`; monotonous `PHO/TPHO/TO/TPHUS`; tomato `TO/PHAEU/TOE`

**Consonant groups** (use how the sounds group):
- `_r` groups stay together on the left hand: betray `PWE/TRAEU`, okra `OE/KRA`, regress `RE/TKPWRES`, hydrate `HAOEU/TKRAEUT` (not `HAOEUD/RAEUT`, which is "hide rate").
- Two-sound groups split in the middle: discover `TKEUS/KO/SRER`, pastor `PAS/TOR`.
- Three-plus groups depend on stress: astray `A/STRAEU`, astronaut `AS/TRO/TPHAUT`, astronomy `A/STRO/TPHO/PHEU`, distribute `TKEUS/TREU/PWAOUT`.
- After a dropped unstressed vowel, split where the vowel was (literal `HREUT/RAL`); if the vowel is completely silent, keep the consonants together.

**"ng"**: split as `…PBG/TKPW…` (the g may double): mango `PHAPBG/TKPWOE`, finger `TPEUPBG/TKPWER`, singular `SEUPBG/TKPWAOU/HRAR`. Alternatives: `…PB/TKPW…` or `…PBG/KWR…` (bingo `PWEUPBG/TKPWOE`, `PWEUPB/TKPWOE`, `PWEUPBG/KWROE`).

**R-coloured vowels**: the `-R` belongs to the previous stroke, so the next stroke uses `KWR` (§13).

## 13. KWR: linker and glide

`KWR` has these jobs:

1. **Suffix linker** (§10.5).
2. **Silent linker** when a stroke can't start with a consonant, especially after an R-coloured vowel: carry `KAEUR/KWREU`, fury `TPAOUR/KWREU`, hurry `HUR/KWREU`, berry `PWER/KWREU`. (Words treating r as a consonant may split before it: arose `A/ROES`.)
3. **"y" sound inside a word**: union `AOUPB/KWROPB`, bunion `PWUPB/KWROPB`, opinion `OE/PEUPB/KWROPB`, onion `OPB/KWROPB`.
4. **Glide between two vowels** that no single chord covers: piano `PEU/KWRA/TPHOE`, aioli `AOEU/KWROE/HREU`, chaos `KAEU/KWROS`, idea `AOEU/TKAOE/KWRA`, violet `SRAOEU/KWROLT`, diacritic `TKAOEU/KWRA/KREU/TEUBG`.
5. **Vowel pair**: `KWR` + vowel stands for a blended pair ("ia", "io", "eo", "iou"), letting the previous consonant move left: alleviate `A/HRAOEF/KWRAEUT`, appreciate `A/PRAOERB/KWRAEUT`, aficionado `A/TPEURB/KWRO/TPHA/TKOE`, nefarious `TPHE/TPAEUR/KWRUS`, video `SREUD/KWROE`.

**Ambiguous glide vowels:** when the vowel after a glide is spelled with two letters and is a schwa, **the second letter** chooses the key: caveat `KAF/KWRAT`, corneal `KORPB/KWRAL`, lenience `HRAOEPB/KWREPBS`, matrilineal `PHA/TREU/HREUPB/KWRAL`.

**`W` for glides** where closer phonetically: equity `EBG/WEU/TEU`, extinguish `EBGS/TEUPBG/WEURB`, intuitive `EUPB/TAOU/WEU/TEUF`, ubiquity `AOU/PWEUBG/WEU/TEU`.

## 14. Shortening techniques

Optional, for speed (Ch. 17). Many outlines are suggestions and may not be in the dictionary.

### 14.1 Folding
- **R-folding**: add `-R` for a final "r": humor `HAOURPL`, shimmer `SHEURPL`, equator `AOE/KWAEURT`. With vowel `A`, use `AE` to avoid conflicts: hammer `HAERPL`, tapper `TAERP`. Safe on the last stroke of multistroke words, conflict-prone on single strokes.
- **L-folding**: add `-L` for "-ly"/"-l": mostly `PHOEFLT`, portal `PORLT`, final `TPAOEUPBL`, funnel `TPUPBL`. If `-L` is taken, fold `HR` on the left: finally `TPHRAOEUPBL`, basically `PWHRAEUFBG`. Low conflict, use freely.
- **T-folding**: add `-T` for "-ity"/"-ty": sanity `SAPBT`, eternity `AOE/TERPBT`, porosity `POR/KWROFT`, entirety `EPB/TAOEURT`. Low conflict.
- **E-folding**: add `E` for a final long e: coffee `KOEF`, happy `HAEP` (happier `HAERP`), fancy `TPAEPBS`, auditory `AU/TKEU/TOER`, humbly `HUPL/EBL`, carefully `KAEUR/EFL`, numerically `TPHAOU/PHER/KAEL`. With `AEU` + r: `AER` (carry `KAER`, solitary `SO/HREU/TAER`). Safe on multistroke words.
- **Suffix-key folding** (§10.1): possible, discouraged.

### 14.2 Dropping unstressed vowels
Drop schwas/unstressed vowels to merge strokes: elephant `EL/TPA*PBT`, definite `TKEF/TPHEUT`, demand `TKPHAPBD`, deplorable `TKPHRORBL`, derivative `TKREUF/TEUF`, electric `HREBG/TREUBG`, differ `TKEUFR`, engineer `EPBG/TPHAOER`, geology `SKWRAOE/KWROL/SKWREU`, modulator `PHOPBLG/HRAEURT`, possible `POFBL`, suppose `SPOES`, consonant `KOPBS/TPHAPBT`. Fails on conflicts (`PWOUT` bout/about) or too many consonants.

### 14.3 Inversions
Swap two keys out of steno order when it saves a stroke: fabricate `TPARB/KAEUT`, migratory `PHAOEURG/TOER`, secretary `SERBG/TAER`, patrimony `PART/PHOEPB`, beside `SPWAOEUD`, first `TPEUFRT`, self `SEFL`.

### 14.4 Dropping other sounds
Drop weakly said consonants: assignment `A/SAOEUPLT`, confinement `KOPB/TPAOEUPLT`, consignment `KOPB/SAOEUPLT`, abutment `A/PWUPLT`, ambiguity `APL/TKPWAOUT`, discard `STKARD`, fragment `TPRAPLT`, efficient `TPEURBT`, patient `PAEURBT`. Highly personal.

### 14.5 Shortened prefix strokes, left-hand clusters
See §9.3 (brief prefix strokes) and §3 (`SPW`, `KP`, `KPW`, `KPH`, `TKW`, `STK`).

### 14.6 Common shortcuts
- `-FR` for "fer/ver" (differ `TKEUFR`, -grapher `TKPWRAFR`).
- "-ology" `OLG` (astrology `A/STROLG`, ecology `AOE/KOLG`; suffix `KWROLG`).
- "-graph" written as a separate `TKPWRAF` stroke (autograph `AU/TOE/TKPWRAF`); "-graphy" `TKPWRAF/KWREU` or `TKPWRAEF`; "-grapher" `TKPWRAF/*ER` or `TKPWRAFR`; "-graphic" `TKPWRAF/KWREUBG` or `TKPWRAFBG`.
- "-ual": `WAL` (manual `PHAPB/WAL`, equal `AOEBG/WAL`, usual `AOURB/WAL`, sexual `SEBGS/WAL`); "chwal" `TWAL` (factual `TPABG/TWAL`, virtual `SREUR/TWAL`).
- First stroke(s) of a write-out may be defined as the full word (usual `AOURB`).

## 15. Briefs (top 200 words)

From Ch. 16 (W = write-out, B = brief). Words not listed use their plain write-out.

| Word | Outline | Word | Outline |
|---|---|---|---|
| the | B `-T` | of | B `-F` |
| to | B `TO`, W `TAOU` | and | B `SKP` |
| a | W `AEU` (`A` = a^) | in | B `TPH` |
| is | B `S` | it | B `T` |
| you | B `U` | that | B `THA` |
| he | `HAOE` | for | B `TP-R` |
| on | B `AUPB`/`O*PB` | are | B `R` or `-R` |
| with | B `W` | I | B `EU` (eye `AOEU`) |
| they | B `THE` | be | B `-B` |
| have | B `SR` (half `HAF`) | this | B `TH` |
| from | `TPROPL` | or | B `AOUR`/`AUR` |
| had | B `H` | by | B `PWEU` |
| what | B `WHA` | there | B `THR` |
| we | `WAOE` (wee `WAO*E`) | can | B `K` |
| out | B `AOUT`/`O*UT` | other | B `OER`, W `O*T/KWRER` |
| were | B `WR`, W `WER` | your | `KWHUR` |
| when | B `WH` | said | B `SED` |
| which | B `WEU` or `KH` | do | B `TKO` (due `TKAOU`, dew `TKAO*U`) |
| if | B `TP` | will | B `HR` |
| about | B `PW` | many | B `PHA*EPB` |
| so | B `SO` (sow `SOE`) | two | B `TWO` |
| did | B `TK` | no | B `TPHO` (know `TPHOE`) |
| who | B `WHO` (whew `WHAOU`) | over | B `AUFR` |
| first | B `TPEUFRT`, W `TP*EURS` | people | B `P`, W `PAOEPL` |
| may | B `PHAEU` | been | B `PW-PB` |
| any | B `TPHEU` | new | B `TPHU` (knew `TPHAOU`) |
| where | B `W-R`, W `WHER` | after | B `AF`/`AFR`, W `AF/TER` |
| little | B `HREUL`, W `HREUT/-L` | only | B `OEPBL`, W `OEPB/HREU` |
| year | `KWRAO*ER` | every | B `EFR` |
| under | B `TPH-PB`/`UPBD`, W `UPB/TK*ER` | very | B `SRE`, W `SRER/KWREU` |
| through | B `THRU` (threw `THRAOU`) | just | `SKWRUFT` |
| think | B `THEU`, W `TH*EUPBG` | help | B `HEP`, W `HEL/-P` |
| before | B `PW-FR`, W `PWE/TPOR` | differ | B `TKEUFR`, W `TKEU/TPER` |
| sentence | B `STEPBS`, W `SEPB/TEPBS` | also | B `HR-S` |
| even | B `AOEFPB` | follow | B `TPOL`, W `TPO/HROE` |
| why | B `KWH` | ask | B `SK`, W `AFBG` |
| off | B `AUF` (`OF` = off^) | picture | B `P*EUFP`, W `PEUBG/KHUR` |
| try | B `TREU` | again | B `TKPWEPB`, W `A/TKPWEPB` |
| animal | B `PHAPBL`/`APB/PHAL`, W `A/TPHEU/PHAL` | mother | B `PHOER`/`PHO*RT`, W `PHO/THER` |
| self | B `SEFL`, W `SEL/*F` | father | B `TPA*URT`, W `TPAU/THER` |
| water | `WAU/TER` | earth | `*ERT` |
| one | `WUPB` | each | `AOEFP` |
| number | `TPHUPL/PWER` | light | `HRAOEUT` (lite asterisked) |
| could / would / should | `KUD` / `WUD` / `SHUD` | their | `THAEUR` |

Other common briefs in the book: hi `HEU`, mostly `PHOEFLT`, personal `PERPBL`, whenever `WH-FR`, into `TPHAO`, finger `TPEURPBG`, syllable `SEUBL`, everyone `EFRPB`, everywhere `WEFRB`, anyone `TPHEUPB`, anything `TPHEUG`, one of `WUFPB`.

**Problem words** (Ch. 22): ah `A*E`, alt `ALT` (`AULT` = "all the"), cache `KAERB`, doth `TKA*UT`, fore `TPOER`, herein `HAOER/KWREUPB` or `HAOERPB`, hour `HOUR`, lunch `HRUFRPBLG`, nought `TPHA*UT`, poll `POL` / pole `POEL`, scene `SKAOEPB`, wolf `WOEFL`/`WOFL`, I'll `AOEUL` / aisle `AO*EUL` (against the contraction rule, by frequency), tour `TAOUR`, mourn `PHAOURPB`.

## 16. Phrasing

### 16.1 Brief combinations
Single-key briefs combine in one stroke (left part + right part, or + `U`/`EU`/`E`):

is it `ST` · is the `S-T` · it is `T-S` · and the `SKP-T` · and he `SKPE` · and I `SKPEU` · and you `SKPU` · at the `TE` · in the `TPH-T` · for the `TP-RT` · if the `TP-T` · if you `TPU` · to the `TOT` · can you `KU` · did you `TKU` · do you `TKOU` · so the `SOT` · are the `R-T` · are you `RU` · have you `SRU` · had the `H-T` · this is `TH-S` · is this `STH` · there is `THR-S` · there are `THR-R` · when is `WH-S` · when are `WH-R` · when you `WHU` · why is `KWH-S` · why are `KWH-R` · will the `HR-T` · will you `HRU` · about the `PW-T` · that the `THAT` · that I `THAEU` · that is `THAS` · what the `WHAT` · what you `WHAU` · what I `WHAEU` · were the `WR-T` · were you `WRU` · who the `WHOT` · they are `THER` · where the `W-RT` · through the `THRUT` · with the `W-T` · with you `WU` · do the `TKO*T` · all the `AULT`

Adding `*` makes the contraction: there's `THR*S`, there're `THR*R`, when's `WH*S`, why's `KWH*S`, they're `TH*ER`.

### 16.2 Jeff's phrasing (bundled)
Lapwing recommends Jeff Lim's phrasing system instead of many phrase briefs (Ch. 24; full docs: <https://github.com/jthlim/jeff-phrasing>). Pronoun starter on the left, verb on the right; verbs conjugate automatically.

| Pronoun | Chord | | Verb | Chord |
|---|---|---|---|---|
| I | `SWR` | | go | `-G` |
| she | `SKWHR` | | find | `-PBLG` |
| he | `KWHR` | | want | `-P` |
| they | `TWH` | | need | `-RPG` |
| we | `TWR` | | | |
| it | `KPWH` | | | |

- `-D` = past tense (`SWR-RPGD` I needed); `*` = negation (`TWH*P` they don't want; `SWR*RPGD` I didn't need).
- Modifier vowels: `A` can, `O` shall, `AO` will (`SKWHRAORPG` she will need, `SWRORPGD` I should need, `TWHO*PD` they shouldn't want).
- Example: I think `SWR-PBG`.

## 17. Fingerspelling

Letter chord + `*`. Uses glue `{&}` so letters stick together but not to normal words (`HE/HROE/A*/PW*/KR*` → "hello abc").

| Letter | Chord | Letter | Chord | Letter | Chord |
|---|---|---|---|---|---|
| a | `A*` | j | `SKWR*` | s | `S*` |
| b | `PW*` | k | `K*` | t | `T*` |
| c | `KR*` | l | `HR*` | u | `*U` or `WR*` |
| d | `TK*` | m | `PH*` | v | `SR*` |
| e | `*E` or `SK*` | n | `TPH*` | w | `W*` |
| f | `TP*` | o | `O*` | x | `KP*` |
| g | `TKPW*` | p | `P*` | y | `KWH*` |
| h | `H*` | q | `KW*` | z | `STKPW*` (or `STK*`) |
| i | `*EU` or `SKW*` | r | `R*` | | |

Digraphs: `TH*` th, `SH*` sh, `KH*` ch, `WH*` wh.

- **Uppercase:** add `-P` (`A*P` A, `KH*P` Ch).
- **Letter + period:** add `-FPLT` (`AFPLT` a., `A*FPLT` A.).
- **Greek letters:** add `-LGTS` (lowercase without `*`, e.g. `ALGTS` α; uppercase with `*`, e.g. `A*LGTS` Α).

## 18. Numbers

Number key (top S) + a **right-hand number pad**, one digit per stroke (from `lapwing-numbers.json`):

```
-R = 1   -B = 2   -G = 3
-FR = 4  -PB = 5  -LG = 6
-F = 7   -P = 8   -L = 9
#E = 0   #U = 00  #EU = 000
```

- Thumb vowels add zeros to a digit: `E` +0, `U` +00, `EU` +000 (`#ER` 10, `#EB` 20, `#UP` 800, `#EUPB` 5000).
- Numbers are glued like fingerspelling (`A*/PW*/KR*/#-R/#-B/#-G` → abc123). **Add `T`** to get spaced, unglued numbers (`#T-R/#T-B/#T-G` → 1 2 3).
- Times: digit(s) then `#-BG` → "N:00", `#*BG` → "N o'clock" (`#-R/#-B/#-BG` 12:00, `#-F/#*BG` 7 o'clock).
- Plover's built-in number-key digit conversion is turned off in the Lapwing system.

## 19. Proper nouns and acronyms

- **Proper nouns:** write the word normally and **add `#` to the first stroke only**: Anna `#A/TPHA`, Calgary `#KAL/TKPWAR/KWREU`, Mat `#PHAT`, Bob `#PWOB`, Vancouver Island `#SRAPB/KAOU/SRER/AOEU/HRAPBD`.
- **Names with initial j:** `#STKPWHR` instead of the awkward `#SKWR`: Germany `#STKPWHRER/PHA/TPHEU`, Jonathan `#STKPWHRO/TPHO/THAPB`.
- **Alternative:** `#` as its own prefix stroke (`#/PHAT`), via `lapwing-prefixed-proper-nouns.json`, for machines that can't remap the top S.
- **Acronyms:** first stroke gets `#` and `*`, rest follows theory; steno order may be broken: AWOL `#A*EU/WOL`, LAN `#HRA*PB`, PDF `#P*FD`. Short ones can be fingerspelt.

## 20. Punctuation

| Char | Outline | Spacing | Mnemonic |
|---|---|---|---|
| . | `TP-PL` | attach left, capitalise next | symmetrical top row |
| ? | `KW-PL` | attach left, capitalise next | rising shape |
| ! | `TP-BG` | attach left, capitalise next | falling shape |
| , | `KW-BG` | attach left | bottom row |
| . (decimal) | `P-P` | attach both | |
| … | `SKW-BGS` | attach left, capitalise next | |
| " open / close | `KW-GS` / `KW*GS` | | "quotation" |
| ' open / close | `KR-RG` / `KR*RG` | | |
| \` open / close | `KH-FG` / `KH*FG` | | |
| ( / ) | `PREPB` / `PR*EPB` | | "pren" |
| { / } | `TPR-BGT` / `TPR*BGT` | | "French bracket" |
| [ / ] | `PWR-BGT` / `PWR*BGT` | | "bracket" |
| : (prose) / ; | `#TPH-FPLT` / `#TPH*FPLT` | attach left | whole top row (formerly `STPH-…`) |
| : (time) | `KHR-PB` | attach both | "colon" |
| — em dash | `PH-RB` | attach both | |
| – en dash | `TPH-RB` (attached) / `TPH*RB` (spaced) | | |
| - hyphen | `H-PB` (attached) / `H*PB` (spaced) | | |
| ‽ | `TRAPBG` | attach left, capitalise next | |
| / | `OEU` | attach both | |

**Rule of thumb:** a closing mark is its opening outline + `*`.

## 21. Formatting commands

| Command | Outline |
|---|---|
| Enter | `R-R` |
| Enter + capitalise next | `R*R` |
| Insert space | `S-P` (core net `KOR/S-P/TPHET`) |
| Retro-insert space | `S-PD` |
| Suppress next space | `SP-S` |
| Retro-suppress last space | `SP-LS` |
| Capitalise next word | `KPA` |
| Capitalise next + suppress space | `KPA*` |
| Retro-capitalise last word | `KA*PD` |
| Lowercase next | `HRO*ER` |
| Retro-lowercase | `HRO*ERD` |
| Add translation | `TKUPT` |
| Tab / Shift-Tab | `TA*B` / `#TA*B` |
| Repeat last stroke | `#` alone |

## 22. Editing, movement, symbols, modifiers

- **Movement** (`#TPH` + right hand): `-R` left, `-P` up, `-B` down, `-G` right, `-RB` word left, `-BG` word right, `-FR` Home, `-LG` End, `-FPL` Ctrl+Home, `-RBG` Ctrl+End, `-RPG` PgUp, `-FBL` PgDn. Repeat with `-S` ×2, `-T` ×3, `-TS` ×4. Add `*` to select. A modal/semi-modal dictionary drops the `#TPH`.
- **Deleting:** `PW-FP` Backspace, `PW*FP` delete word back, `TKHR` Delete, `TKHR*` delete word forward.
- **Emily's symbols:** starter `SKWH`; vowels set spacing, `*` capitalises, right hand picks symbol, `-T`/`-S` repeat (e.g. `SKWHO*FRTS` = "!!!! " + cap).
- **Emily's modifiers:** ender `-LGTS`; right index/middle choose Ctrl/Shift/Alt/Super, left hand picks key (Ctrl+Shift+C `KR-FRLGTS`).
- **Abby's left-hand modifiers:** two left-hand strokes (Ctrl+V `KHR/SR`).
- Firmware aids: first-up chord send and chord repeat (book recommends chord repeat).

## 23. UK spellings

From `lapwing-uk-additions.json` (Ch. 21); American forms take priority.

- **Universal switch:** add `#TPH` as a stroke after the word: centre `SEPB/TER/#TPH`, harbour `HAR/PWOR/#TPH`, organise `OR/TKPWA/TPHAOEUZ/#TPH`. **Switch before adding suffixes:** organising `…/#TPH/-G`.
- "ae" spellings → `AE`: haemoglobin `HAE/PHOE/TKPWHROE/PWEUPB`.
- "-ise" → `-S` instead of `-Z`: magnetise `PHAG/PHE/TAOEUS`.
- "oe" → `OE`: foetus `TPOE/TUS`.
- "-our" → `OU` only to disambiguate: colour `KO/HROUR`, favour `TPAEU/SROUR`.
- "-re" → asterisk in the `ER` stroke: litre `HREU/T*ER`, centimetre `SEPB/TEU/PHAO*ERT`.
- Asterisk into a brief usually gives the British form: metre `PHAO*ERT`, organise `O*RG`.

## 24. Miscellaneous rules and special words

- **Contractions:** asterisk (§6). Some unasterisked forms exist, but not all can be.
- **-graph, -ology, -ual:** §14.6.
- **Tricky "ou"**: tour `TAOUR`, mourn `PHAOURPB` (since `TOR`, `PHORPB` taken).
- **Words ending in h:** asterisk.
- **Personalisation:** never edit `lapwing-base.json` (updates overwrite it); add to `user.json`. Three-way conflicts and accent-dependent outlines are explicitly left to the writer.

## 25. Orthography rules (Plover engine)

Lapwing doesn't define its own; it uses Plover's English engine (`english_stenotype.py`). When a suffix stroke or folded suffix key attaches to a word, these regex rules fix spelling (checked in order; a word list `american_english_words.txt` also validates results). Aliases: "able" ↔ "ible", "ability" ↔ "ibility".

| Rule | Example |
|---|---|
| vowel+c + ly → ally | artistic → artistically |
| consonant+le + ly → ly | humble → humbly |
| te + ry/ary → tory | statute → statutory |
| m + tory → matory | confirm → confirmatory |
| se + ary → sory | supervise → supervisory |
| (t)e + cy → cy | frequent → frequency |
| s/sh/x/z/zh + s → es | establish → establishes |
| (soft) ch + s → es | speech → speeches |
| consonant+y + s → ies | cherry → cherries |
| ie + ing → ying | die → dying |
| y + ist (after c,d,f,g,h,l,m,n,p,r) → ist | metallurgy → metallurgist |
| consonant+y + suffix not starting with i → i | beauty → beautiful |
| te + en → tten | write → written |
| a/e + en → n | Minnesota → Minnesotan |
| y + ial → ial | ceremony → ceremonial |
| i/y + ify → fy/ify | pretty → prettify |
| ic + ical → ical | fantastic → fantastical |
| ology + ical → ological | |
| ry + ical → rical | oratory → oratorical |
| l + ist → list (no doubling) | radical → radicalist |
| ry + ity → rity; l + ity → lity | complementarity, proportionality |
| rm + tive → rmative; e + tive → ative | performative, restorative |
| y/al/ar/l,m,n,t,y + ize/ise → no doubling | tokenize, conditionalize, categorize |
| al + ology → ology | criminal → criminology |
| ar/er/or + ish → no doubling | similarish |
| ee + e… → drop one e | free + ed → freed |
| consonant+e + vowel suffix → drop e | narrate → narrating |
| CVC + vowel suffix → double final consonant | defer → deferred |

Suffix keys recognised by the engine for folding: `-Z`, `-D`, `-S`, `-G`.

## 26. How Lapwing differs from Plover theory

Summarised from Appendix A:

- `#` on the top S key; used for proper nouns and as a disambiguator.
- `KWH` for initial "y" (only when spelled y); `TP*` for "ph"; `WR`, `WH` orthographic.
- `AU` for non-"o" short o; `AO` for "oo"; `AE` conflict chord with spelling priorities.
- `*PL` always for -mp; `-PLT` ment; `-LT` let; `KR` for soft-c conflicts.
- Prefixes take the obvious outline (`OUT` = out^, so "out" is `AOUT`/`O*UT`); suffixes use `KWR`; affixes only when meaningful.
- Compound words: asterisk on the first stroke of the second word.
- Strict syllabic splitting: every stroke starts with a consonant or `KWR`; no doubled consonants.
- Right-hand number pad; `#` proper nouns.
- Compatible with Plover's `main.json` in the same stack (Harri's "Lapwing-compatible main.json" is recommended).

## 27. Notes for Dotterel

Places where Lapwing's rules exist only because steno has four vowel keys or a fixed key set. These are the obvious spots where Dotterel's two extra keys, `Y` (left thumb, where the schwa key was) and `I`, could replace a Lapwing workaround. Dotterel steno order: `# S T K P W H R A O Y * I E U F R P B L G T S D Z`.

| Lapwing workaround | Why it exists | Dotterel opportunity |
|---|---|---|
| `EU` = short i; long e sometimes `EU` (§4.4) | no I key | a real `I` key; decide whether long-e-spelled-i/y keeps `I` |
| `AE` as a conflict-only vowel (§7.2) | homophones need a spare chord | spelling-specific vowel chords, or keep `AE` |
| `AU` for non-"o" short o, `AO` for "oo" (§4.1, 4.3) | orthographic distinctions with few keys | could map to dedicated spelling chords |
| Schwa written as its spelled letter (§4.1) | no schwa key | stays as in Lapwing (Dotterel no longer has a schwa key) |
| `KWR` glides and vowel pairs (§13) | no glide key | `Y` could carry the "y" glide and vowel pairs directly (union, piano, video), freeing `KWR` to be only the suffix linker |
| `KWH` for initial "y" (§3) | no Y key | `Y` with no left consonant could spell initial y (yes, yet) |
| Asterisk overloaded (§6) | one disambiguator key | `Y` or `I` could take some asterisk jobs where they don't clash with their own meaning |
| `#` for proper nouns (§19) | needs an extra key | already on Alice's layout where the top S was |

Lapwing outlines that only use standard keys should still work unchanged on Dotterel, since Dotterel keeps every English stroke's meaning.

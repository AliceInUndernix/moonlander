# Dotterel command cheat sheet

Every command stroke in Dotterel 1.5.0: keys, modifiers, movement, punctuation, capitals, spacing, numbers, fingerspelling and Plover controls. Taken from the dictionaries in `plover-dotterel/plover_dotterel/dictionaries/`. None of these strokes is used by a word.

Strokes are written in steno order `# S T K P W H R A O * E U F R P B L G T S D Z`. A `-` means the keys after it are on the right hand (`-R` is right R, `R-` is left R).

**Rule of thumb:** adding `*` usually gives the "other half" of a pair: closing quote or bracket, select instead of move, Ctrl+key instead of key, capital instead of lower case.

---

## 1. Keys

| Key | Stroke | Also |
|---|---|---|
| Escape | `EFBG` | `TPEFBG` |
| Tab | `TA*B` | |
| Shift+Tab | `#TA*B` | |
| Enter | `R-R` | keeps the capitalisation state |
| Enter, then capital | `R*R` | new line, next word capitalised, no space |
| Shift+Enter | `#R-R` | |
| Shift+Enter (no space after) | `#R*R` | |
| Backspace | `PW-FP` | `SPW` |
| Ctrl+Backspace (delete word back) | `PW*FP` | |
| Delete | `TKHR` | `TKHRE` |
| Ctrl+Delete (delete word forward) | `TKHR*` | `TKHR*E` |
| Undo last stroke | `*` | |
| Repeat last word | `#` | |

### Function keys

`TPW` + the number's word.

| Key | Stroke | | Key | Stroke |
|---|---|---|---|---|
| F1 | `TPWUPB` | | F7 | `TPWEFPB` |
| F2 | `TPWO` | | F8 | `TPWAEUT` |
| F3 | `TPWRAOE` or `TPWAOE` | | F9 | `TPWAOEUPB` |
| F4 | `TPWOUR` | | F10 | `TPWEPB` |
| F5 | `TPWAOEUF` | | F11 | `TPWHREFPB` or `TPHREFPB` |
| F6 | `TPWEUBGS` | | F12 | `TPWEFL` |

---

## 2. Movement (arrows, Home, End, Page Up/Down)

Start with `STPH` or `#TPH`, then a right-hand key. Add `*` to **select** (Shift) as you move.

| Move | Stroke | Select (add `*`) |
|---|---|---|
| ← Left | `STPH-F` | `STPH*F` |
| ↓ Down | `STPH-P` | `STPH*P` |
| ↑ Up | `STPH-L` | `STPH*L` |
| → Right | `#TPH-T` | `STPH*T` |
| Word left (Ctrl+←) | `STPH-R` | `STPH*R` |
| Word right (Ctrl+→) | `#TPH-S` | `STPH*S` |
| Page Down | `STPH-B` | `STPH*B` |
| Page Up | `STPH-G` | `STPH*G` |
| Home | `STPH-FR` | `STPH*FR` |
| End | `#TPH-TS` | `STPH*TS` |
| Top of document (Ctrl+Home) | `STPH-LG` | `STPH*LG` |
| End of document (Ctrl+End) | `STPH-PB` | `STPH*PB` |

The shape: top row `-F -P -L -T` = ← ↓ ↑ → (like vim h j k l). Bottom row under the same fingers = word left, Page Down, Page Up, word right. Both keys of one finger = the far jump.

`#TPH` works for every key. `STPH-T`, `STPH-S` and `STPH-TS` are words, so for → , word right and End without selecting, use `#TPH-T`, `#TPH-S`, `#TPH-TS`.

**Keep moving:** after one movement stroke, the right-hand keys **alone** keep moving: `STPH-F` then `-F -F -F` = ← ← ← ←, and `*F` selects. Any other stroke leaves movement and is written as normal.

---

## 3. Modifiers (Ctrl, Shift, Alt, Super)

Stroke a modifier, then **any stroke that presses one key or types one character**: a letter (fingerspelling), a digit, a punctuation mark, a movement or a key from section 1.

| Modifier | Stroke | | Modifier | Stroke |
|---|---|---|---|---|
| Ctrl | `KHR` | | Ctrl+Shift | `SKHR` |
| Shift | `SH` | | Ctrl+Alt | `TKHRA` |
| Alt | `THRA` | | Alt+Shift | `STHRA` |
| Super (Win / Cmd) | `KPW` | | Ctrl+Alt+Shift | `STKHRA` |
| | | | Ctrl+Super | `KPWHR` |
| | | | Shift+Super | `SKPWHR` |

Examples:

| You want | Write |
|---|---|
| Ctrl+C (copy) | `KHR` / `KR*` |
| Ctrl+V (paste) | `KHR` / `SR*` |
| Ctrl+Z (undo) | `KHR` / `STKPW*` |
| Ctrl+S (save) | `KHR` / `S*` |
| Ctrl+Shift+T | `SKHR` / `T*` |
| Alt+Tab | `THRA` / `TA*B` |
| Alt+F4 | `THRA` / `TPWOUR` |
| Ctrl+Up | `KHR` / `STPH-L` |
| Shift+Enter | `SH` / `R-R` |
| Shift+1 | `SH` / `#-R` |
| Ctrl+Shift+→ | `KHR` / `SH` / `#TPH-T` (modifiers add up, up to three) |

Stroking the **same** modifier twice cancels it (`KHR` / `KHR`), and the next stroke is just itself.

Symbols with no stroke of their own (`$ + = * |` and so on) can be typed as Shift + the key that has them on your keyboard layout, e.g. `SH` / `#-PB` = Shift+5 = `%`.

---

## 4. Capitals

| Command | Stroke | Also |
|---|---|---|
| Capitalise next word | `KPA` | `SKWR-F` |
| Capitalise next word, no space before it | `KPA*` | |
| Capitalise last word (retro) | `KA*PD` | `KPA*D`, `SKWR-FD` |
| ALL CAPS next word | `KPA*L` | `SKWR-FP` |
| ALL CAPS last word (retro) | `KPA*LD` | `SKWR-FPD`, `*UPD` |
| Lower-case next word's first letter | `HRO*ER` | `SKWR-R` |
| Lower-case last word's first letter (retro) | `HRO*ERD` | `SKWR-RD` |
| Caps mode (everything in capitals) on | `KA*PS` | turn off with `R*EFT` |

---

## 5. Spaces and joining words

| Command | Stroke | Also |
|---|---|---|
| No space before the next word (attach) | `SP-S` | `SP`, `TK-LS` |
| Remove the space before the last word (retro) | `SP-LS` | `TK-FPS` |
| Insert a space | `S-P` | `TH-FL` |
| Add a space before the last word (retro) | `S-PD` | |
| No-space mode (words run together) | `#PHOED` / `TPHOG` | turn off with `R*EFT` |
| Back to normal (ends caps / no-space mode) | `R*EFT` | |
| Do nothing (breaks a word apart, cancels formatting) | `SKWR` | `TKAO*` |
| Toggle `*` on the last stroke (retro) | `#*` | |

---

## 6. Punctuation

"Attach" means no space on that side. Marks that end a sentence capitalise the next word.

Dotterel writes **typographic punctuation**: curly quotes “ ” ‘ ’, the apostrophe ’ in every word (don’t, it’s, o’clock, O’Neal), the ellipsis …, and dashes with no spaces (word—word, 1850–1899). The straight `'` and `"` that code and the shell need have their own strokes: `#` + the quote stroke.

### Sentence marks

| Mark | Stroke | Spacing |
|---|---|---|
| `.` full stop | `TP-PL` | attach left, capital next |
| `,` comma | `KW-BG` | attach left |
| `?` | `KW-PL` | attach left, capital next (also `H-F`) |
| `!` | `TP-BG` | attach left, capital next |
| `!?` | `TPH-FBG` | attach left, capital next |
| `‽` | `TRAPBG` | attach left, capital next (also `TRAEPBG`) |
| `:` colon | `STPH-FPLT` | attach left (also `#TPH-FPLT`) |
| `;` semicolon | `STPH*FPLT` | attach left (also `STPH*FPL`, `#TPH*FPLT`) |
| `…` ellipsis, ending | `SKW-BGS` | attach left, capital next |
| `…` ellipsis, inside | `SW-BS` | attach left |
| `s?` | `STPH-S` | adds `s` to the last word, then `?` (also `STH-S`) |
| `.` decimal point | `P-P` | attach both (3.5) |
| `:` in times | `KHR-PB` | attach both (10:30) (also `K-L`) |

### Quotes

Every opening stroke writes an opening curly quote, every closing stroke a closing one.

| Mark | Stroke | Spacing |
|---|---|---|
| `“` open double | `KW-GS` | attach right |
| `”` close double | `KW*GS` | attach left |
| `‘` open single | `KR-RG` | attach right |
| `’` close single, or an apostrophe | `KR*RG` | attach left |
| `, “` comma, then open double | `KWR-GS` | |
| `, ‘` comma, then open single | `KWR*GS` | |
| `“` open double, capital next | `KW-BGS` | spaced before |
| `‘` open single, capital next | `KW*BGS` | spaced before |
| `, “` comma, open double, capital next | `KWR-BGS` | |
| `.”` full stop and close double, capital next | `KWR*BGS` | |
| `“` open double, capital next | `SKWHA*FP` | attach right |

**Straight quotes** (for code and the shell):

| Mark | Stroke | Spacing |
|---|---|---|
| `"` open | `#KW-GS` | attach right |
| `"` close | `#KW*GS` | attach left |
| `'` open | `#KR-RG` | attach right |
| `'` close | `#KR*RG` | attach left |

**Backticks** (code, so always straight):

| Mark | Stroke | Spacing |
|---|---|---|
| `` ` `` open | `KH-FG` | attach right |
| `` ` `` close | `KH*FG` | attach left |

### Brackets

| Mark | Open | Close |
|---|---|---|
| `( )` | `PREPB` | `PR*EPB` |
| `( )` (other stroke) | `STPH-FPLTS` | `STPH*FPLTS` |
| `[ ]` | `PWR-BGT` | `PWR*BGT` |
| `{ }` | `TPR-BGT` | `TPR*BGT` |
| `< >` | `AEPBG` | `A*EPBG` |

### Dashes and slashes

| Mark | Stroke | Spacing |
|---|---|---|
| `-` hyphen | `H-PB` | attach both (well-known) |
| `-` hyphen, spaced | `H*PB` | |
| `-` hyphen, prefix | `H-PBS` | attach right (-ish) |
| `--` | `H-PBSZ` | attach both |
| `--` spaced | `H*PBZ` | |
| `--` prefix | `H-PBZ` | attach right |
| `–` en dash | `TPH-RB` | attach both (1850–1899) |
| `–` en dash, spaced | `TPH*RB` | |
| `—` em dash | `PH-RB` | attach both (word—word) |
| `—` em dash, spaced | `PH*RB` | |
| `/` | `OEU` | attach both |
| `_` | `RUPBD` | attach both |

### Symbols

| Symbol | Stroke | Spacing |
|---|---|---|
| `@` | `A*T` | attach both (name@mail) |
| `@` handle | `KWRA*T` | attach right (@name) |
| `#` hashtag | `HAERB` | attach right |
| `#` | `HA*ERB` | attach both |
| `&` | `SKP*` | spaced |
| `%` | `P*ERS` | attach left |
| `^` | `KA*RT` | attach both |
| `°` | `TKERG` | attach left (20°) |
| `°` | `TK*ERG` | attach both |
| `™` | `TR*PL` | attach left |
| `Δ` | `TKO*EULT` | attach right |
| `Ω` | `O*EPL` | attach left (also `O*EPLS`) |

---

## 7. Spelling words out with hyphens or dots

| Command | Stroke |
|---|---|
| Last word as `w-o-r-d` | `-RBGS` |
| Last 2, 3, 4 words with hyphens | `-RBGS` stroked 2, 3, 4 times in a row |
| Last word as `w.o.r.d` | `-FPLT` |
| Last 2, 3, 4 words with dots | `-FPLT` stroked 2, 3, 4 times in a row |
| Spell letter by letter with hyphens (`a-b-c`) | letter + `-RBGS`: `ARBGS` a, `PW-RBGS` b, `KR-RBGS` c … |
| Same, capital letters (`A-B-C`) | add `*`: `A*RBGS` A, `PW*RBGS` B … |

The letter part is the same as fingerspelling (section 9): `A E EU U O` vowels, `KR` c, `TK` d, `TKPW` g, `KWH` y, `STKPW` z and so on.

---

## 8. Numbers

Hold `#` and use the right hand for digits, the vowels for zeros. Digits stroked one after another join into one number.

| Digit | `#` + | | Digit | `#` + |
|---|---|---|---|---|
| 1 | `-R` | | 6 | `-LG` |
| 2 | `-B` | | 7 | `-F` |
| 3 | `-G` | | 8 | `-P` |
| 4 | `-FR` | | 9 | `-L` |
| 5 | `-PB` | | 0 | `E` |

| Add | Key | Example |
|---|---|---|
| a 0 after the digit | `E` | `#ER` = 10, `#EB` = 20 |
| 00 | `U` | `#UR` = 100, `#U` = 00 |
| 000 | `EU` | `#EUR` = 1000, `#EU` = 000 |
| a space before the number (start a new number) | `T` | `#T-R` = " 1", `#TUR` = " 100" |

**Times:** finish with `#-BG` for `:00` and `#*BG` for "o'clock": `#-R/#-BG` = 1:00, `#-F/#*BG` = 7 o'clock, `#-R/#-PB/#-BG` = 15:00, `#-R/#-B/#*BG` = 12 o'clock.

---

## 9. Fingerspelling (one letter at a time)

Letter + `*` for lower case, `*P` for a capital, `*B` for a space before it, `-FPLT` for the letter with a full stop.

| Letter | Lower | Capital | | Letter | Lower | Capital |
|---|---|---|---|---|---|---|
| a | `A*` | `A*P` | | n | `TPH*` | `TPH*P` |
| b | `PW*` | `PW*P` | | o | `O*` | `O*P` |
| c | `KR*` | `KR*P` | | p | `P*` | `P*P` |
| d | `TK*` | `TK*P` | | q | `KW*` | `KW*P` |
| e | `*E` | `*EP` | | r | `R*` | `R*P` |
| f | `TP*` | `TP*P` | | s | `S*` | `S*P` |
| g | `TKPW*` | `TKPW*P` | | t | `T*` | `T*P` |
| h | `H*` | `H*P` | | u | `*U` | `*UP` |
| i | `*EU` | `*EUP` | | v | `SR*` | `SR*P` |
| j | `SKWR*` | `SKWR*P` | | w | `W*` | `W*P` |
| k | `K*` | `K*P` | | x | `KP*` | `KP*P` |
| l | `HR*` | `HR*P` | | y | `KWH*` | `KWH*P` |
| m | `PH*` | `PH*P` | | z | `STKPW*` | `STKPW*P` |

Extras: `KH*` ch, `SH*` sh, `TH*` th, `WH*` wh (capitals `KH*P` Ch, `SH*P` Sh, `TH*P` Th). Other ways in: `SK*` e, `SKW*` i, `WR*` u, `STK*` z.

Initials with a full stop: `AFPLT` a., `A*FPLT` A., `PW-FPLT` b., `PW*FPLT` B. and so on.

**Greek:** letter + `-LGTS` for lower case, `*LGTS` for a capital: `ALGTS` α, `PW-LGTS` β, `TKPW-LGTS` γ, `TK-LGTS` δ, `ELGTS` ε, `STKPW-LGTS` ζ, `AOELGTS` η, `TH-LGTS` θ, `EULGTS` ι, `K-LGTS` κ, `HR-LGTS` λ, `PH-LGTS` μ, `TPH-LGTS` ν, `KP-LGTS` ξ, `OLGTS` ο, `P-LGTS` π, `R-LGTS` ρ, `S-LGTS` σ, `T-LGTS` τ, `ULGTS` υ, `TP-LGTS` φ, `KH-LGTS` χ, `SP-LGTS` ψ, `PHAEULGTS` ω. `TPHALGTS` gives ∇.

---

## 10. Plover and Dotterel controls

| Command | Stroke |
|---|---|
| Turn Plover on / off | `PHROLG` |
| Open Plover's window | `PHROEFBG` (also `PHROEFBGS`, `PHROEUFBGS`) |
| Plover settings | `PHROFG` |
| Look up a word's stroke | `PHRUP` (also `PHR*UP`) |
| Add a translation (Plover's window) | `TKUPT` |
| Quick add: give the last word an outline (Dotterel) | `TK*UPT` |
| Switch last word between UK and US spelling | `#SU` |
| Raw mode on / off (see the raw steno) | `RA*U` |
| The Builder window | Ctrl+B in Plover's window |

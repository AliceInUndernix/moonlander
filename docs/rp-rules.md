# Dotterel: how it differs from Lapwing

Dotterel is Lapwing written for British RP. The dictionary starts from Lapwing's UK dictionary, keeps every Lapwing syllable split, and applies the rules below. Where a split breaks a rule, it is fixed when the fixed stroke is free, and removed otherwise. Spelling is British with Oxford -ize; `#SU` switches output to American spelling.

The full Lapwing theory that Dotterel builds on is in [lapwing-rules.md](lapwing-rules.md).

## Rules

| Rule | What it does | Examples |
|---|---|---|
| P1: all splits kept | Every Lapwing syllable split stays, with the RP rules applied to each | atmosphere `AT/PHO/STPAO*ER`, `AT/PHOS/TPAO*ER`, brief `ATS/TPAO*ER`; secretary `SEBG/RE/TREU`, `SERBG/TREU` |
| R1: word beats prefix | When a word and a prefix share a stroke, the word gets it and the prefix moves to the asterisk | on `OPB` (on^ `O*PB`), off `OF`, over `OEFR`, be `PWE` (be^ `PW*E`), or `OR` |
| R2: RP "ah" is A | Words with the BATH/PALM vowel use A | father `TPA/THER`, palm `PA*PL`, calm `KAPL`, draught `TKRA*T` |
| R3: war/quar is AU | The "aw" sound after w/qu uses AU | warm `WAURPL`, ward `WAURD`, quarter `KWRAUR/TER`, warn `WAURPB` |
| R4: oo + r is AOU | The "oo" sound before r uses AOU | sure `SHAOUR`, during `TKAOURG`, mature `PHA/KHAOUR` |
| T2: RP -ary/-ory | Unstressed -ary/-ory/-ery is written consonant + `REU`; a stressed one keeps its vowel | secretary `SE/KRE/TREU`, history `HEUS/TREU`, necessary `TPHE/SE/SREU`; scary `SKAER` |
| T4: RP pronunciation | Outlines follow the British pronunciation | was `WAUS`, what `WHAUT`, schedule `SHED/KWRAOUL`, lieutenant `HREF/TEPB/TPHAPBT`, aluminium `A/HRAOU/PHEUPB/KWRUPL`, clerk `KHRA*RBG` |
| E1: modern spellings | A few etymological spellings are written the modern way | fetus, fetal, fetid, sulfur (sulfate, sulfide), molt |
| B1, B2: briefs | All of Lapwing's briefs stay, plus 35 new ones for common words | on `-PB`, today `T-D`, century `S-FP`, review `R-F`, release `R-S`, camera `K-R`, primary `P-R`, daily `TK-L`, interview `SPWRAOU`, secretary `S-R` |

## Kept as in Lapwing

- A short "u" spelled o stays O: come `KOPL`, son `SOPB`, love `HROF`.
- "aw" spelled with o keeps O / AO: more `PHOR`, board `PWAORD`, door `TKAOR`.
- Proper nouns are Lapwing's.

## Checks the dictionary passes

- Every outline is a valid stroke on the Dotterel keyboard.
- No word outline takes a stroke used by punctuation, commands, fingerspelling, numbers, movement, raw mode or proper nouns.
- Base dictionary: 113,814 outlines. Affixes: 602.

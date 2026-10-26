# Licence options: three, and what each one allows

Card `t_99a4a385` (H4 SUBMIT-KIT), written 2026-10-26. `SUBMISSION-CHECKLIST.md` item 2 needs a licence at the
repository root before the repository is public, and the choice is Nayil's. This file lists three options and does
not make the choice. No `LICENSE` file has been added, renamed or edited by this card.

## What is true on disk today

- `LICENCE` (British spelling) sits at the root, 5,040 bytes, last written 2026-10-23. It carries the copyright
  notice, says all rights reserved, states that no outbound grant has been chosen yet, and its section 6 records that
  decision as open.
- There is no file named `LICENSE` anywhere at the root, in any of the spellings but `LICENCE`. Item 2 asks for
  `LICENSE`; whether that is a rename of the existing file or a new file beside it is Nayil's call.
- Obligations a grant cannot override, all recorded in `LICENCE` sections 3 to 5: OpenStreetMap geometry under ODbL
  with the attribution kept inside the build, Press Start 2P under the SIL Open Font License 1.1 with its reserved
  name (notice at `knowledge/licences/PressStart2P-OFL.txt`), the GameMaker LTS2026 engine by YoYo Games under its own
  licence (the engine is not ours to redistribute), and `knowledge/LICENSES.md`, which records the ten libraries
  considered under the MIT or Apache 2.0 only rule and notes that none is imported.
- The waiver settles what the organisers may do with the submission, not what a reader may do with this repository:
  Nayil keeps ownership and grants the organisers a non exclusive, perpetual licence to use the submission
  (`RULES-WATCH.md`, IP rows, citing the waiver read 2026-10-23). Nothing read so far requires an open source licence
  here; item 2 requires a public repository and a README and a licence at the root.

## The three options

| # | Licence | What it allows, in one line | What it costs |
| --- | --- | --- | --- |
| A | MIT for the code, all rights reserved for the art, audio and story | Anyone may use, copy, modify, publish and sell the code as long as they keep the copyright notice; the art, music and story stay Nayil's alone | It is two grants in two files, so the root needs a second short notice (for example `LICENSE-ART`) or a judge reading one `LICENSE` will assume the art is MIT too |
| B | Apache 2.0 for the whole repository | Anyone may do the same as MIT, plus they get an explicit patent grant from Nayil and the trademark clause that goes with it | The notice file and the change statements are machinery a hackathon judge will not read, and applying it to the art and the story as well is probably not what Nayil wants |
| C | Source available, all rights reserved (the position today) | Anyone may read, clone and run it, which is what judging needs; nobody may reuse, redistribute or sell it | Nothing to write: `LICENCE` already says exactly this, and it keeps the commercial release and any future art or music licensing open |

Two combinations worth naming, because they are not on the list: adding an open source licence only so the
submission looks open, and dual licensing the art under a non commercial Creative Commons licence, both of which
change what a future commercial release may do and neither of which the rules ask for.

## What happens when Nayil picks

1. Section 2 of `LICENCE` is replaced in full by the chosen licence's own text, or a `LICENSE` file is added and
   `LICENCE` is renamed, and section 2 becomes the pointer between them.
2. `README.md` carries the same one line in its licence section, instead of the sentence that points here.
3. Sections 3 to 6 of `LICENCE` stay as they are: third party material, the obligations, where they are recorded, and
   the record of the decision. A grant cannot speak for ODbL or for the font.
4. `CREDITS.md` does not change. It already lists one row per attribution obligation.

Nothing in this file was published, uploaded or submitted. The repository stays private and nothing was pushed.

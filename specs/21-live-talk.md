# Spec 21: the live TALK entry (SAY IT YOURSELF)

Status: spec, 2026-10-26. Code exists (card t_ee178652, lane W2 of WIN-PLAN-2026-10-26). Numbers are DECISIONS.
Reads with spec 16 (the TALK command and the mercy meter) and spec 19 (the baked talk path). Where this spec and
spec 16 differ, this one wins for the fifth entry only.

Goal: in the first fight the player stops picking from three written lines and writes one. A typed line, a line built
on an NES letter grid with the d-pad, or a spoken line the player edits as a transcript. It goes to the local AI
bridge, a model judges it in character, the sailor answers in the same text box every other reply uses, and his WILL
bar moves (it reads MERCY on screen, for the reason in section 0 item 3). The fight can always end, with the network off or on.

## 0. What this changes in the existing specs

1. Spec 16 section 1 step 1 lists four context options plus a fifth fixed entry SAY IT YOURSELF. The panel therefore
   draws **four rows**, and this spec owns the geometry change: pitch 13 from `PP_MENU_TOP + 8` (176, 189, 202, 215,
   last glyph bottom at 223, inside the band's border at 232) with a one pixel rule above the fifth row. At spec 16's
   16 pixel pitch a fourth row lands on 234 and prints over the border, which is why the number moved.
2. Spec 16 section 1 step 2 describes a keyboard only input row with a 120 character cap. This spec keeps the cap and
   the cap's arithmetic and adds two more ways to reach the same line (the grid, the microphone) and one more window
   (the battle's own message window, x 0 to 256, y 0 to 48), because the fight's window is where every other reply
   already goes and a second box would be a second renderer.
3. The meter is spec 16 section 2's `talk_mercy`, shown on screen as the enemy's WILL bar. Renaming the numbers
   would break spec 07's spare gate, so the field stays `talk_mercy`. The name on screen is **MERCY**, not WILL,
   because the player's own WILL is already printed on the same screen at y 156 and two things called WILL is one
   thing too many: `data/talk_live.json`'s `will.label` carries the word the bar draws, and this spec follows it.
4. Spec 05 gains one sentence: the box uses the sheet's 77 glyph alphabet and nothing else, so a line is filtered to
   it and a mark the sheet lacks is never drawn. Spec 06 gains one sentence: a scene may not open the box, because a
   cutscene cannot wait on a player's typing.

## 1. The three input paths, one line

One buffer, `battle.live_text`, and three ways to fill it. A player can mix them inside one line, which is the point:
speak, then fix a word with the keyboard, then tap in a full stop on the grid.

| Path | Keys | Rules |
| --- | --- | --- |
| Keyboard | letters, digits, the marks the sheet has, space; SHIFT for the marks above the digits; BACKSPACE deletes; ENTER sends; ESC puts the box down | typed characters go through the sheet's alphabet filter; the reader lives in pp_input, the only module that reads a key (spec 02 rule 1), and publishes one character per step |
| Grid | d-pad or stick moves, A (confirm) types the highlighted cell, B (cancel) deletes, START (menu) sends, HELD cancel returns to the keyboard | 4 rows x 11 columns = 44 cells in the classic order: A to Z, 0 to 9, space, `.` `,` `!` `?` `'`, then DEL and END |
| Voice | hold F5 or the left shoulder while the box is open | a recording shorter than 15 steps (0.25 s) is refused with the low blip rather than transcribed; the transcript fills the same buffer the keyboard fills, so it can be edited before it is sent |

Rules
1. The grid is entered by pressing a direction. A printed character on the keyboard while the grid is up types and
   returns the box to keyboard mode. No player is trapped in either mode, and the held cancel is the pad only exit.
2. Every buffer change plays a blip. A refused character (a glyph the sheet lacks) plays the lower one.
3. The cursor is six pixels of rule under the next character's cell, blinking 30 steps on and 30 off. The sheet has
   no underscore glyph, which is why spec 16 says six pixels and not "an underscore".
4. The box shows the last 60 characters in two rows of 28, scrolled to the end, cut at a space. The buffer holds 120.
5. The prompt row carries `* SAY IT YOURSELF` at the left and the tries left as `2/3` at the right.
6. Nothing in the box reads a key inside pp_talk_live: the box asks pp_input for a character, exactly as every other
   feature asks it for a press.

## 2. Sending, and the thinking beat

1. SEND is refused on an empty line with `Say something first.` and the box stays open. An empty line is not a turn.
2. On a send the box closes, `live_tries` goes up by one, the stage becomes `wait`, and the message window shows
   `* .`, `* . .`, `* . . .` one dot per 15 steps and no more than three. Not a spinner: a spinner at 60 steps a
   second says the game is busy, three dots say the game is waiting.
3. The budget is 780 steps (13 s). It must exceed `tools/ai_bridge.py`'s own rung deadline (6 s, or 12 s when a Meta
   key is present, which is the budget muse-spark-1.3 needs), or the game would cut answers the bridge was about to
   deliver. At 781 with nothing in hand the fallback answers, the turn continues, and a late answer is discarded by
   the id check in the async handler.
4. One request in flight, always. A second send while one is out is refused and logged.
5. The battle clock never pauses for the request, and talking never costs the player a hit.

## 3. The protocol

The bridge is `tools/ai_bridge.py`, loopback only (127.0.0.1:8791 by default), started by `tools/run.ps1`. This spec
does not own that file; it consumes its documented contract.

Request, POST /talk:

```
{"encounter_id": "tutorial_sailors", "npc": "navy_sailor", "player_text": "...",
 "history": [{"player_text": "", "reply": ["..."], "verdict": "persuaded"}],
 "will": 20, "mood": "guarded"}
```

Answer:

```
{"verdict": "persuaded" | "unmoved" | "angered",
 "will_delta": -10 | 0 | 5 | 20,
 "reply": ["TWENTY TWO YEARS", "OF THIS. GO ON,"],
 "source": "meta" | "open-weights" | "replay" | "fallback",
 "mood": "guarded", "cached": true, "latency_ms": 412, "origin": "meta"}
```

Voice, POST /hear: raw 16000 Hz mono 16 bit PCM wav bytes, answer `{"transcript": "..."}`. The engine does not expose
its recording device's rate, so the wav is written at `voice.sample_rate` from data and that field is the one place to
change it.

Rules
1. The game sends no key, no save, no flag, no exact hp, and never the player's earlier lines: `history` carries the
   reply and the verdict only, which is what spec 19 section 3 already decided.
2. `will_delta` is the ONLY number from an answer that reaches the game, and it is clamped to -20..+20 and then the
   meter to 0..100. No answer can move the bar further than an authored option could.
3. `source` is printed on every answer's debug line and in the capture. "The WILL bar moved" is not evidence until the
   run says where the words came from.
4. The address is assembled at call time from `bridge.host`, `bridge.port` and the two paths in
   `data/talk_live.json`. No address string is written in GML, and a host that is not `127.0.0.1` or `localhost` is
   replaced with the loopback default and logged. The text of a player's line never leaves this machine.
5. The async answer arrives in the object's HTTP event (`Other_69.gml`, and `Other_62.gml` for the older slot name).
   The handler matches `async_load`'s `id` against the request the fight started, so an unrelated transfer is never
   applied to a turn.

## 4. The answer, and what the player sees

1. Validation, in order: the answer must be a JSON object with a numeric `will_delta`; `verdict` must be one of the
   three or it becomes `unmoved`; `mood` must be one of spec 19's five or it is derived from the verdict; every reply
   line must be drawable by the sheet, is cut to 28 at a space, and at most three lines are kept. An answer with no
   usable line keeps its delta and shows the encounter's fallback line, labelled `fallback`.
2. The reply draws in the battle's own message window at spec 19's 8 pixel pitch with the `* ` marker code adds, and
   the enemy's turn follows the words exactly as it follows a FIGHT or an authored option.
3. The enemy's MERCY bar is 4 pixels tall under the health bar: the label on the row above, then a 64 pixel track
   and its fill, which is the full width of the health bar's own track. No value is printed beside it: at 64 pixels
   the digits left a 12 pixel fill, and a bar a judge cannot see move is not evidence of anything. It moves on the
   same step the reply appears.

## 5. Three tries, and the floor under the fight

1. `tries_max` is 3. The fourth free text try is refused: the fifth entry stays on the panel, the press plays the low
   blip and the note `That is enough talking.` appears under the panel, so the player sees why rather than a row that
   vanished (spec 07 rule 1).
2. After that the three authored options carry the fight. One authored option is worth the encounter's own
   `mercy_per_option` (20), three of them reach `mercy_to_spare` (60), and the SPARE gate opens exactly as spec 07 and
   spec 19 already promised. The live path can therefore never make a fight unwinnable or stuck, with or without a
   model, with or without a network.
3. A timeout, a transport error, a refused answer or a dead bridge are all the same event to the player: the fallback
   answers this turn and the fight continues on the same turn.

## 6. Replay, the demo's mode

1. `PP_TALK_LIVE_MODE` is `"replay"` in `pp_config.gml` and F6 flips it at run time. Replay is the DEFAULT and the
   demo's mode.
2. In replay the answer comes from `data/talk_live_tape.json`: an exchange keyed by enemy and normalised line, the two
   voice transcripts, and a miss row that answers a line nobody recorded. An answer is byte shaped like a live one,
   because a replay that is a different shape is a second code path.
3. The thinking beat is deferred by the recorded `latency_ms`, so the replay's timing is the live timing (see check 4).
4. Replay opens no socket. Nothing in the shipped build reaches the network with the mode at its default.
5. The tape records what it was captured against (`recorded_against`). A data version bump means re-record, not edit.

## 7. NES legality

1. Every glyph the box draws is a frame of `spr_pp_font8`. The alphabet is 77 characters, and a character outside it is
   filtered before it can reach the buffer, so no line can draw a hole.
2. The box spends four roles the deck's own palette set declares: `ink`, `paper`, `dim`, `text`. No tint, no blend, no
   colour literal. The cursor, the grid marker and the WILL fill are the `text` role, the brightest the sets share.
3. Every coordinate is a whole pixel inside the throwaway margins the audit already measures: the message window is
   x 0 to 256, y 0 to 48; grid rows land on 16, 24, 32, 40 with the last glyph bottom at 48; the panel rows are 176,
   189, 202, 215 with the last bottom at 223 inside the band's border at 232.
4. The box adds no sprite, no tile and no colour to the frame.

## 8. Data

`data/talk_live.json` (this spec's numbers, strings and letter grid), `data/talk_live_tape.json` (the demo's recorded
exchanges and transcripts). Both ship, both are read through `pp_data_json` like every other data file, and both are
mirrored into `game/datafiles/` by `tools/sync_data.py`. A missing or unreadable `talk_live.json` leaves the GML's own
defaults in place and the box still opens, because a data file that can stop the signature moment of the demo is a data
file in the wrong place.

## 9. Checks, all measurable

Run through `python -m pytest tests/test_talk_live.py -q` (38 checks) and `python -m pytest
tests/test_no_network_in_build.py -q` (13 checks).

1. Data: every string and every grid cell is drawable by the sheet, every string fits 28 columns, the grid is 44 cells
   with DEL and END last.
2. Tape: every recorded delta is a delta the judge's own effect map can produce for that verdict, every reply line is
   1 to 28 characters and drawable, the three demo lines are recorded, the miss row is labelled `fallback`.
3. Line: typing, the sheet filter, delete, the 120 cap, the two row window and the empty submit.
4. Replay timing: the deferred answer lands at the recorded latency, and the timeout's fallback lands at exactly 780
   steps, once, with the box out of the way.
5. Meter: +20 on 95 leaves 100 and the delta printed is 5; no answer moves the meter outside 0..100.
6. Three tries: the fourth is refused with the note, and the authored options still reach the spare threshold after.
7. Demo arc: the WILL bar reads 0 -> 20 -> 40 -> 40, and the third line is labelled `replay`.
8. Network: the only file under `game/` that names a network function is `pp_talk_live.gml`, exactly two call sites,
   both `http_request`, the address assembled from data, no non loopback literal in the code, and replay opens
   nothing.
9. GML and mirror agree on the stage names, the two macros and the two defaults.
10. The text reader is in pp_input and nowhere else, and the two actions it adds steal no key from another action.
11. Capture: `python tools/capture_talk_live.py --check` renders the seven frames and every one passes
    `tools/nes_composite_check.py`'s frame audit on a 256x240 canvas: 0 off-palette pixels, at most four background
    palettes, at most 25 colours on screen. The suite audits the same pixels through the tool's `prepare()`, so the
    picture a judge is handed and the picture a test measures cannot drift apart. The roles are resolved through
    `data/palette_ppu.json` the way `pp_data_palette_rgb` resolves them; the first run of this audit is what caught the
    tool drawing the design hexes, and 0 of the 54 design colours is a 2C02 output.
12. The three paths are three pictures: `entry_keys`, `entry_grid`, `listen` (the microphone open, `hint_voice` printed
    where the line goes) and `entry_voice` (the transcript landed in the same buffer) are separate frames with separate
    debug lines, and the answer's frame is the first one that draws the WILL fill, at the meter's own share of the track.

## 10. Out of scope

Voice activity detection (the player holds the key), a second language, editing the tape in game, a model choosing the
bullet pattern, the box inside a cutscene, and any use of the live path outside a battle.

## 11. Personas, the same door outside a fight (card t_acae7c0a)

Status: spec, 2026-10-26. Code exists. This section extends the live path from the one fight to the three scenes a
judge walks through, and it changes nothing about section 2's budget, section 3's protocol or section 6's replay.

Why. The live box was felt in one scene out of four. A judge who meets Konrad at the door, Urien in the rain and a
bystander on Town Quay should be able to type at all three and get an answer in character, through the same door,
the same rungs and the same cache. `data/talk_personas.json` is that, and `tools/bake_personas.py` records it.

1. Three cards, one per scene, from `knowledge/SCENES-S1-S3.md`: `konrad` (S1, Wessex Lane Halls, polite and
   cutting and never loud), `urien` (S2, Southampton High Street, jovial weather talk, and he never says who he
   used to be) and `quay_townsperson` (S3, Town Quay, panicking and unable to calm down inside one answer).
   A card carries the voice, the wants, the fears, the topic lists, the lore limits, the guards and fifteen bake
   lines. The file is bridge input, not bundle input: it is listed in `sync_data.NOT_RUNTIME` beside
   `talk_profanity.json`, and the test names both halves so the day a GML module reads it the line fails.
2. A persona request is a chat, not a fight. It is built with scene `npc`, the effects `none` and `end`, no
   encounter id needed, and the persona's own place in the scene block. The meter is not touched, so a persona
   can never make a fight winnable or unwinnable, and section 5's floor is unchanged.
3. The answer cap is two sentences drawn as at most two box lines of 28 characters. The cleaning cuts at the
   second sentence end and labels `capped_sentences`; it does not throw the answer away.
4. The guards live on this side of the wire. `banned_words`, `banned_marks` and `mood_allowed` are read by the
   bridge and are never put in a prompt, because a prompt that lists the word it must not say is a prompt that
   puts the word in the model's mouth. The lore limit reaches the model as `knows` and `cannot_say`, both
   written as categories. A reply carrying a banned word is refused (the next rung answers); a banned mark, a
   third sentence and an out of character mood are repaired and labelled, because those can be fixed without
   changing what the character said. Konrad bans the exclamation mark: he never raises his voice, and that is a
   punctuation rule before it is a tone rule. The bystander allows only `rattled` and `angry`.
5. The shared guards still run first. A persona adds to `data/talk_profanity.json`, never replaces it, and the
   same refusal phrases, links and digit runs apply.
6. The deadline is section 2's 6 seconds, the rungs are section 3's, and the cache is section 6's. A persona
   answer is keyed on the judge version, the persona block, the persona's version, the two limits and the
   player's line, so a card edit invalidates exactly its own rows.
7. The bake is fifteen lines per persona, written by `tools/bake_personas.py` through the Meta rung only, and
   reported in `data/talk_personas_bake.json` with `calls_attempted`, `answered`, `fallback`, `model` and the
   cache key of every live row. `--check` refuses a row that breaks character, a live row whose cache file is
   missing or holds different words, and a bake block that claims more than its rows did. Replay with no key
   and no network answers all three: cache first, then the persona's own `fallback_pool`.
8. Checks: `python -m pytest tests/test_talk_personas.py -q`, and `python tools/bake_personas.py --check`.

Out of scope here, and owed to the card that wires the scenes: a GML trigger that opens the box at S1, S2 and
S3, a second persona in one scene, voice input for a persona, and moving `data/talk_personas.json` out of
`NOT_RUNTIME` into the bundle. Until that card lands, the personas are proved through the bridge and the tests,
not through a GameMaker run.

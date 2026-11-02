# MUSIC COVERAGE, 2026-11-02 (card t_74fee92b)

Nayil reported no music in Town Quay, in battle and in Percy's fight. This document is the static half of that
question: for every room and every fight, which cue is asked for, which OGG answers it, whether that OGG is in
the source tree, in the mirror and in the build the player runs, whether it loops, and how loud it is measured
with ffmpeg. The runtime half belongs to the MUSIC-REAL card, which owns `game/scripts/pp_audio` and the audio
calls in `pp_overworld`, `pp_scene` and `pp_app`; nothing in this card edited a GML file.

Verdict of the static audit: **every room and every fight resolves to an OGG that exists, ships, loops and
measures between -11.3 and -17.9 dB mean.** None of the three failure kinds the card names fires. The silence
Nayil reports is therefore not a missing cue, a missing file, or a silent file, and the static material below is
not the place the fix goes.

## How the numbers were taken

    cd "<repo>"
    python -m pytest tests/test_music_coverage.py -q      # 6 passed in 3.69s
    python tests/test_music_coverage.py                   # prints the table below

`tests/test_music_coverage.py` resolves each cue the way `pp_audio_music_paths` resolves it: the basename of the
row's `delivered_file` first, then `<asset>.ogg`, each tried in `streams/` and `datafiles/streams/` beside the
running game. A row whose own file is absent follows its `fallback` chain, up to the 8 hops
`pp_audio_cue_resolve` walks. The mean level is ffmpeg's own `volumedetect` mean, through
`tools/play_demo.py`'s `ffmpeg_path()`, on the mirror bytes the game opens.

## Every room

| room id | cue asked | cue resolved | ogg that plays | in assets/audio | in datafiles/streams | loop | mean dB |
|---|---|---|---|---|---|---|---|
| ship_small | PP-05 | PP-05 | pp_05_small_ship.ogg | yes | yes | yes | -17.9 |
| ship_cabin | PP-05 | PP-05 | pp_05_small_ship.ogg | yes | yes | yes | -17.9 |
| southampton_town_quay | PP-03 | PP-03 | pp_03_harbor_master1.ogg | yes | yes | yes | -13.2 |
| quay_dock_office | PP-03 | PP-03 | pp_03_harbor_master1.ogg | yes | yes | yes | -13.2 |
| drive_m4_corridor | PP-02 | PP-02 | pp_drive_master1.ogg | yes | yes | yes | -12.5 |
| wessex_lane_montefiore | PP-05 | PP-05 | pp_05_small_ship.ogg | yes | yes | yes | -17.9 |
| southampton_high_street | PP-05 | PP-05 | pp_05_small_ship.ogg | yes | yes | yes | -17.9 |
| ship_sample | PP-05 | PP-05 | pp_05_small_ship.ogg | yes | yes | yes | -17.9 |

Eight rooms: the seven rows of `data/maps/all.json` plus `ship_sample` from `data/maps/ship_sample.json`, which
`pp_data.gml` appends to the runtime registry, so it is a room the game can load and not a fixture.

Town Quay is `southampton_town_quay`, cue PP-03, and the file it asks for is `pp_03_harbor_master1.ogg`, the
3:45 master at -13.2 dB mean. The dock office next door asks the same cue and does not restart it, because
`pp_audio_music` returns early when the resolved cue is already playing.

## Every fight

| encounter id | cue asked | cue resolved | ogg that plays | in assets/audio | in datafiles/streams | loop | mean dB |
|---|---|---|---|---|---|---|---|
| tutorial_sailors | PP-04 | PP-04 | pp_04_navy_sailors_master1.ogg | yes | yes | yes | -11.3 |
| deck_hound | PP-04 | PP-04 | pp_04_navy_sailors_master1.ogg | yes | yes | yes | -11.3 |
| deck_collapse | PP-06 | PP-06 | percy_theme.ogg | yes | yes | yes | -16.6 |
| percy | PP-06 | PP-06 | percy_theme.ogg | yes | yes | yes | -16.6 |
| morgan_gate | PP-04 | PP-04 | pp_04_navy_sailors_master1.ogg | yes | yes | yes | -11.3 |

Percy's fight is encounter `percy`, cue PP-06, `percy_theme.ogg`, the G minor tyrant waltz at -16.6 dB mean. The
row is the boss one, so `pp_audio_music` gives it `PP_AUDIO_PRI_BOSS` (12) rather than the music priority.

Which fights are live: `tutorial_sailors` is the trigger on `ship_small` (`kind: battle`), `percy` is the
`battle` command in the scenes `percy_lore_stop` and `percy_rematch` (the `ship_cabin` triggers), and
`morgan_gate` is the `battle` command in `quay_gate_truth`, `quay_gate_bluff` and `quay_gate_authority`.
`deck_hound` and `deck_collapse` are named by no trigger in the live maps or scenes; today's slice cannot reach
either, and a comment in `pp_battle_director.gml:335` says so for `deck_collapse`. Both rows still carry a cue,
so the day a trigger points at one of them the music is already there. All five rows are audited above because
"live" is a moving fact and the cue table is not.

## The pending cues and the fallback each one uses

Eleven cues have no render of their own and reach the speaker through `fallback`, the same chain
`pp_audio_cue_resolve` walks at runtime. Every chain terminates at a landed cue in one hop.

| pending cue | fallback it names | resolved | ogg that plays |
|---|---|---|---|
| PP-07 Prometheus Explains | PP-05 | PP-05 | pp_05_small_ship.ogg |
| PP-08 Dead Rising | PP-03 | PP-03 | pp_03_harbor_master1.ogg |
| PP-09 The Data Center | PP-03 | PP-03 | pp_03_harbor_master1.ogg |
| PP-10 Hector | PP-06 | PP-06 | percy_theme.ogg |
| PP-11 Rush to Prison | PP-02 | PP-02 | pp_drive_master1.ogg |
| PP-12 One North Quay | PP-03 | PP-03 | pp_03_harbor_master1.ogg |
| PP-13 Titan Employees | PP-03 | PP-03 | pp_03_harbor_master1.ogg |
| PP-14 Kronos | PP-06 | PP-06 | percy_theme.ogg |
| PP-15a Entropy | PP-01 | PP-01 | pp_01_title.ogg |
| PP-15b Mercy | PP-01 | PP-01 | pp_01_title.ogg |
| PP-16 Ouranos | PP-01 | PP-01 | pp_01_title.ogg |

No room and no fight asks for a pending cue today; the only pending cue a scene asks for is PP-07, in
`prometheus_interrupt`. The chain still matters, because a data edit that points a room at PP-12 is silent only
if the fallback breaks.

## The bundle the player actually runs

The test checks the mirror and the committed project file. A third check was run by hand, because the build
folder is generated and cannot be asserted from the repository: the seven OGGs the bus can ask for are present
in `output/PrimordialParadox/streams/`, byte identical (sha256) to `game/datafiles/streams/`, beside the
`PrimordialParadox.exe` and the `.win` rebuilt today at 14:56. GameMaker flattens an Included File whose
`filePath` is `datafiles/streams` to `streams/` next to the executable, which is the first path
`pp_audio_music_paths` tries, so the first candidate the bus opens is the file that is really there.

## Gaps this audit found

1. No coverage gap. Every room and every fight resolves to a file that exists, ships, loops and is above the
   -40 dBFS floor by at least 22 dB. The three failure kinds the card names do not fire on this tree.
2. Two rooms still play a stand-in: `wessex_lane_montefiore` and `southampton_high_street` ask PP-05 (small ship)
   because they have no cue of their own. No door leads to either room yet, so nothing is heard wrong today. This
   was already recorded on the MUSIC-EVERYWHERE card and is a musician delivery, not a wiring bug.
3. Nothing static explains silence in Town Quay, battle or Percy. The cue row, the file, the mirror, the project
   file, the build folder and the level are each proved above, and the runtime tour of 2026-11-01 logged
   `stream yes` on all 12 stops. Whatever removes the sound happens after the stream opens: the runtime owner's
   card is the place for it, and the one number worth handing them is that the fight cue is the loudest thing in
   the game (-11.3 dB) while the ship cue, the room Nayil stands in first, is the quietest (-17.9 dB).

## What this does not prove

- No speaker was involved. Nothing here opens a GameMaker window or plays a sample; a green run means the
  material is right, not that Nayil hears it.
- A launch through `tools/pp_launch.py` is muted on purpose (`PP_MUTE=1`, master gain 0) unless `--sound` is
  passed, so a capture or proof run cannot be used to judge audibility. `tools/run.ps1` and `tools/run.vbs`, the
  double click path, start the game unmuted; that is the launcher a report about what Nayil hears refers to.
- The mirror row proves that `tools/sync_art.py` copies this file, because the conftest session fixture rebuilds
  the mirror from `assets/audio` on every run. It does not prove that an older build folder held a fresh copy;
  the hand check in the section above covers today's build only.
- The volume row needs ffmpeg and is marked `windows_only`, because `tools/play_demo.py` binds a Win32 API at
  import. Off this Windows host the row skips with that reason and the dB column is unmeasured there.

## The proof that the test can fail

The assertions were mutation tested on scratch copies, with no repository file touched
(`profiles/musician/cache/scratch/mutate_coverage.py`), and each mutation was caught with a message naming the
room or the fight:

    A room without a cue        FAILED: room southampton_town_quay (maps/all.json) names no music cue at all
    Cue file missing from mirror FAILED: room southampton_town_quay plays cue PP-03 (pp_03_harbor_master1.ogg)
                                       and it is absent from game/datafiles/streams/pp_03_harbor_master1.ogg
    Cue below the -40 dB floor  FAILED: percy_theme.ogg measures -91.0 dB mean, below the -40 dB floor, and it is
                                       what fight deck_collapse, fight percy play
    Pending cue with a dead chain FAILED: pending cue PP-10 does not reach a landed cue: chain PP-10 -> PP-99

## Reproduce

    cd "<repo>"
    set TEMP=D:\Temp\hermes-tmp
    set TMP=D:\Temp\hermes-tmp
    python -m pytest tests/test_music_coverage.py -q
    python tests/test_music_coverage.py

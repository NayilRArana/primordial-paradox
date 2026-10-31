# PINE-HONEST: two Pine cards of every three were measuring an import failure

Card t_84fe63ff, 2026-10-24. gamedev.

## The defect

`tools/play_demo.py` imported `capture_title` at module level, and `capture_title.py:39` imported
`ctypes.wintypes`. `pp_launch.py:41` imported it too. Off Windows that import fails, so on Pine the
demonstration tools could not be imported at all, and every red that the suite produced there was
classified in the shadow of that failure.

Measured on 2026-10-24: 21 Pine reds, 19 of which pass on Windows.

Worse than a broken import: it is a broken import that produced a plausible verdict. A reader saw
21 failures and a classification note, not a traceback.

## The fix

Two guarded imports, one refusal each:

- `tools/capture_title.py`: `WINDOW_PRIMITIVES = sys.platform == "win32"`, with `ctypes.wintypes`
  imported only when true, and the module-level `ctypes.windll.user32`, the DPI block and
  `ctypes.WINFUNCTYPE` now behind the same guard. Off Windows `user32` and `EnumWindowsProc` are None.
- `tools/pp_launch.py`: the same guard on the same import.
- `tools/play_demo.py` `run_demo`: refuses with the message `play_demo: unavailable on this platform`
  and returns `pp_launch.EXIT_REFUSED`, which is 4.
- `tools/capture_title.py` `main`: refuses the same way.

Exit 4 is not a new convention. `tools/idle_check.py:48` defines `EXIT_REFUSED = 4` and its header
explains it is 4 and not 3 because 3 is the watchdog's code in this harness.

The refusal lives in `run_demo` and not at import on purpose: `--check` and `--dry-run` inspect an
existing file and must keep working on a machine that cannot show a game.

## Proof, both directions

Probe at `profiles/gamedev/cache/scratch/probe_pine_honest.py`:

```
branch 1, this machine
  sys.platform        : win32
  capture_title flag  : True
  pp_launch flag      : True
  user32 object       : WinDLL
branch 2, primitives absent
  import succeeded    : yes, which is the fix
  capture_title flag  : False
  pp_launch flag      : False
  user32 object       : NoneType
  play_demo run_demo  : returned 4 | play_demo: unavailable on this platform
  capture_title main  : returned 4 | capture_title: unavailable on this platform
  refused, not passed : True
```

Windows behaviour unchanged: 129 passed across `test_capture_title.py`, `test_play_demo.py`,
`test_capture_quiet.py`, `test_capture_quiet_impl.py`, `test_first_fight_capture.py`,
`test_talk_fight_capture.py`.

## The cards whose verdicts were never measured

These closed on Pine numbers that this defect was producing. Their verdicts are UNMEASURED and must be
re-run, not inherited. Named as the card requires:

- t_cb1f931b TEST-TRIAGE-PINE, testing. It sorted 49 Pine failures into windows-only, zip gaps and
  real regressions. Its windows-only bucket was very likely right in substance and cannot be trusted in
  detail until re-run against this fix.
- t_fa895ddf PINE-CHECKS, testing. Palette and NES checks over every frame through Pine.
- t_dacb50c7, t_1ed727b8, t_37657207, t_e7c9dcc2, t_9a18f2e9, t_1649d513, t_f6f73680, AUTO-GATE-GREEN,
  testing. Seven cards, each of which classified Pine failures and raised fix cards for the ones it
  called real.
- t_e87e71e6, t_d8f13f33, t_64d39815, AUTO-PINE-CHECKS, testing. Three cards, same exposure.
- t_a14fbdd3 MUS-V5, musician. Used Pine side checks on the title theme; its audio verdicts stand on the
  rendered files, but its Pine column does not.

Not affected, checked and named so nobody re-opens them: t_429b26d4 PINE-SKILL and t_7e5ece0f
PINE-RESEARCH are client and research cards with no suite verdict, and t_753fb388 PINE-PLACES-DIGEST
is a research digest.

## What to do with a not-measured result

Do not treat 4 as a pass and do not treat it as a failure. Re-run on Windows, or record the row as not
measured. The one thing this project must not do again is convert "I could not measure" into a green.

## The re-measurement, card t_ae84da65, 2026-10-24 17:34 to 17:52

All thirteen cards were re-run against the fixed tree. Every one is `measured`; none is `refused` and
none is `failed` at card level. The only reds are the two drive rows, which that defect never touched
and which a builder card owns.

### The tree this measured

- `33c2cb4` at 16:56 and its follow-up `d87980c` at 17:12, both ancestors of the tree the runs zipped.
  `d87980c` is not optional: at `33c2cb4` alone `run_demo` read a module level `FFMPEG` that only
  `ffmpeg_path()` fills, so every recording run printed `ffmpeg was not found` and returned 1, and this
  re-measure would have reported a red that was a second defect (`git show d87980c`).
- The measurement is of the working tree, not of a commit. The last commit touching this project is
  `d87980c`; at 17:52 the project held 55 modified and 249 untracked paths, so the rows below also
  cover other lanes' unfinished work (`git status --porcelain -- projects/primordial-paradox`).
- Runner: `<home>/AppData/Local/Python/bin/python.exe pine_offload.py`, working directory
  `<workspace>\Shared\projects\arananet\pine`, zip built at 17:34:37.

### The jobs, one line each

| job | command | window | the line it prints | result file |
| --- | --- | --- | --- | --- |
| `pinem` | `pine_offload.py --shards 3 --name pinem` | 17:34:37 to 17:38:53 | `432 passed, 7 skipped` and `529 passed, 2 failed, 34 skipped` and `369 passed, 9 skipped, 3 deselected`; SUMMARY 432/0, 529/2, 369/0 | `data/results/offload-pinem-0.json`, `-1.json`, `-2.json` |
| `pinem-pal2` | `--cmd "cd projects/primordial-paradox && python tools/palette_synergy.py --gate --out output/ps_pinem.json"` | 17:41:36 to 17:43:37 | `palette_synergy: 6 entry(ies), 0 gated failure(s), 6 advisory failure(s)` then `EXIT=0` | `data/results/offload-pinem-pal2-0.json` |
| `pinem-audit3` | `--cmd "cd projects/primordial-paradox && python tools/nes_audit_all.py --no-write"` | 17:41:37 to 17:44:55 | `nes_audit_all: FAIL 184 file(s), 34 failing, 0 unmeasured` then `exit: 1` | `data/results/offload-pinem-audit3-0.json` |
| `pinem-comp` | `--cmd` loop over `output/nes_title_frame.png`, `output/bg_battle_deck_night_frame.png`, `output/bg_battle_corridor_frame.png` and `output/ship_dialogue.png` through `tools/nes_composite_check.py <frame> --quiet` | 17:49:02 to 17:50:31 | exits 0, 0, 0, 1; `ship_dialogue` reports `FAIL: 70 block(s) violate the background rules` and `407 colours` | `data/results/offload-pinem-comp-0.json` |
| `pinem-hook` | `--cmd "cd projects/primordial-paradox && python tools/hook_score.py assets/audio/title_theme_v5/title_theme_v5.mid"` | 17:42:30 to 17:43:58 | `melody track 'vrc6 pulse a', 52 bars, 137 notes, score 73 / 100` then `EXIT=0` | `data/results/offload-pinem-hook-0.json` |
| `pinem-refuse` | `--cmd "cd projects/primordial-paradox && { python tools/play_demo.py; echo PLAY_EXIT=$?; python tools/capture_title.py; echo CAPTURE_EXIT=$?; python tools/play_demo.py --dry-run; echo DRYRUN_EXIT=$?; }"` | 17:44:40 to 17:46:36 | `play_demo: unavailable on this platform` `PLAY_EXIT=4`; `capture_title: unavailable on this platform` `CAPTURE_EXIT=4`; `run_001: 19 events, 71.0 s, 60 fps` `DRYRUN_EXIT=0` | `data/results/offload-pinem-refuse-0.json` |

Suite arithmetic: 432 + 529 + 369 = 1330 passed, 2 failed, 7 + 34 + 9 = 50 skipped, 3 deselected,
0 error rows, 1385 collected rows, 1330 of the 1332 graded rows passing, 99.85%
(`data/results/offload-pinem-0.json`, `-1.json`, `-2.json`).

The refusal row is what makes the rest readable. On the real Pine host the demo launcher now answers 4
with its own line and the read-only path still runs, so a Pine reader sees "not measured" where the
old runs showed a red (`data/results/offload-pinem-refuse-0.json`, `tools/play_demo.py:838`).

### Windows cross-check of the rows Pine cannot carry

| command, run on this PC at 17:46 | output |
| --- | --- |
| `python -m pytest tests/test_project.py tests/test_build_inputs.py tests/test_test_inputs.py tests/test_sync_art.py tests/test_mix_check_v3.py tests/test_slice_route.py tests/test_make_characters_v2.py -q` | `2 failed, 90 passed in 10.73s`; both failures are the two drive rows at `tests/test_slice_route.py:498` and `tests/test_slice_route.py:528` |
| `python -m pytest tests/test_audio.py -q` | `24 passed in 2.28s` |
| `python tools/nes_audit_all.py --no-write --quiet` | `nes_audit_all: FAIL, 184 file(s), 34 failing (10 gated), 0 unmeasured, exit 1` |
| `python tools/palette_synergy.py --gate --out <workspace>/ps_pinem_local.json` | 6 entries, 0 gated, 6 advisory; 152, 16, 211, 242, 163 and 3 problems, 787 in total |

The Pine audit tail names the same failing rows as the local run, and every one of the 34 sits under
`output/`: of the 184 audited rows, 130 are game assets and all 130 pass, while 34 of the 54 output
previews, sheets and captures fail (`data/results/offload-pinem-audit3-0.json`,
`python tools/nes_audit_all.py --list`).

### Per card

| card | what its Pine verdict rested on | verdict | what the fresh run returns |
| --- | --- | --- | --- |
| `t_cb1f931b` TEST-TRIAGE-PINE | 49 failures sorted 8 windows-only, 34 zip gaps, 7 real; rerun 725 passed, 24 failed | `measured` | `pinem`: 1330 passed, 2 failed, 50 skipped, 3 deselected. All 24 of its rerun reds (game window, Pillow byte, map data, one audio row) are green; the 2 reds left are the drive rows, which its list did not carry. No red is windows-only now. |
| `t_fa895ddf` PINE-CHECKS | palette 6 pairs all FAIL, 0 gated; audit 160 files, 25 failing; composite 3 of 4 frames PASS | `measured` | `pinem-pal2` 6 pairs, 6 advisory, 0 gated, exit 0; `pinem-audit3` 184 files, 34 failing, exit 1; `pinem-comp` exits 0, 0, 0, 1. |
| `t_dacb50c7` gate at 18:56 | 857 passed, 36 failed; 15 windows-only, 19 real, 2 unproven | `measured` | `pinem`: 1330 passed, 2 failed. Every capture and demo row it called windows-only now skips by its marker or passes, and the title art cluster it raised is green. |
| `t_1ed727b8` gate23 | 1281 passed, 8 failed, all real | `measured` | The other 6 of its 8 pass in the fresh run and the PC agrees (`tests/test_audio.py` 24 passed, the project rows inside the 90 passed set). Only the 2 drive rows are still red. |
| `t_37657207` gate24 | 1325 passed, 11 failed; 7 windows-only, 4 real | `measured` | The 7 first-fight-capture rows skip by their marker (the 7 skips in shard 0), the 2 yyp rows pass on Windows, the 2 drive rows are still red. |
| `t_e7c9dcc2` gate25 | 1325 passed, 4 failed; 2 yyp, 2 drive | `measured` | Drive rows red. The yyp rows have been deselected on Pine by design since 23:01 and pass in the Windows set. |
| `t_9a18f2e9` gate26 | 1325 passed, 4 failed, the same four | `measured` | Same as gate25: drive red, yyp green on Windows. |
| `t_1649d513` gate28 | 1325 passed, 2 failed, both drive | `measured` | Unchanged in substance: 1330 passed, the same 2 drive rows red. |
| `t_f6f73680` gate29 | 1324 passed, 3 failed; 2 drive, 1 sailor | `measured` | The sailor row passes now (`tests/test_make_characters_v2.py` is in the 90 passed set); the 2 drive rows are still red. |
| `t_e87e71e6` AUTO-PINE-CHECKS 1 | 6 pairs, 658 problems; audit 160 files, 25 failing, exit 0 | `measured` | 6 pairs, 787 problems, 0 gated, exit 0; audit 184 files, 34 failing, 10 gated, exit 1. |
| `t_d8f13f33` AUTO-PINE-CHECKS 2 | 6 pairs, 706 problems; audit 25 failing, all under `output/` | `measured` | 787 problems; 34 failing, all under `output/`. |
| `t_64d39815` AUTO-PINE-CHECKS 3 | 181 files, 777 problems, 10 gated, audit exit 1 | `measured` | 184 files, 787 problems, the same 10 gated, audit exit 1. |
| `t_a14fbdd3` MUS-V5 | 143 pytest checks on Pine and hook_score 68/100 | `measured` | Its music files ran green inside `pinem` (`test_arrange.py`, `test_arrange_v3.py`, `test_ear_critic.py`, `test_hook_score.py`, `test_dissonance_rules.py`, `test_humanize.py`, `test_cue_cut_v3.py`, `test_audio.py`, `test_mix_check_v3.py`); `pinem-hook` returns 73/100. |

Two of the older figures moved because the tree moved, not because the check changed: card
`t_64d39815` measured 777 problems and the same command now reports 787, per pair 152, 16, 211, 242,
163 and 3 against that card's 238, 27, 192, 258, 51 and 11 (`ps_pinem_local.json` in the card
workspace). Card `t_a14fbdd3` measured 68 and the same tool on the same MIDI now reports 73
(`data/results/offload-pinem-hook-0.json`).

Each of the thirteen closed on numbers this defect was producing, so its old count is superseded
rather than confirmed. The column that carries the verdict is the last one, and every row in it is a
fresh Pine output line (`data/results/offload-pinem-*.json`).

### What is still red, and whose

- The two drive rows, `tests/test_slice_route.py::test_a_step_resolves_the_one_id_it_names[drive]` and
  `tests/test_slice_route.py::test_a_scene_step_reaches_end_with_only_known_commands[drive]`. They fail
  on Pine and on this PC for the same reason, the scene `drive_to_southampton` is absent from
  `data/scenes/all.json`, and builder card t_c27552e3 owns them (`tests/test_slice_route.py:498`).
- The NES audit, 34 failing and 10 gated, every row under `output/` (previews, sheets, captures), so
  the exit is 1 while no game asset fails (`tools/nes_audit_all.py:919`).
- The palette gate reports 6 pairs, 6 advisory failures and 0 gated, so RULE 0 blocks nothing until an
  entry in `data/scene_palettes.json` carries `gate: true` (`tools/palette_synergy.py:783`).

### Retries, gaps, cost

- Ten result files, 0.0478 USD of estimated Computer time (`data/results/offload-pinem-*.json`).
- `pinem-audit` at 17:39:40 died on the documented upload reset,
  `ConnectionError: [Errno 10054] An existing connection was forcibly closed`; it was retried once as
  `pinem-audit3`, which completed (`data/results/offload-pinem-audit-0.json`).
- `pinem-pal` at 17:39:40 ran from `~/repo` and could not find `tools/palette_synergy.py`, so it was
  redone as `pinem-pal2` with a `cd` first (`data/results/offload-pinem-pal-0.json`).
- A third attempt, `pinem-audit2`, was stopped by me after the same working-directory mistake and
  produced no verdict and no cost line.
- Never on Pine, by design: `tests/test_build_inputs.py`, `tests/test_test_inputs.py`,
  `tests/test_sync_art.py`, and the three deselected nodes
  `tests/test_mix_check_v3.py::test_the_script_still_runs_on_a_slice`,
  `tests/test_project.py::test_project_graph_matches_disk` and
  `tests/test_project.py::test_generated_project_files_are_current`. They were measured on this PC
  above (`pine_offload.py:79`, `:88`, `:102`, `:123`).
- The zip was between 39,983,422 and 39,984,745 bytes across the nine builds, against the 40,000,000
  ceiling that has refused uploads before, and one job lost its upload to that margin: the first audit
  attempt (`OFFLOAD.md:73`, `data/results/offload-pinem-audit-0.json`).

### Observations

1. `--cmd` starts in `~/repo`, where the zip unpacks, and the project is one level down at
   `~/repo/projects/primordial-paradox`. A `--cmd` that does not start with `cd projects/primordial-paradox &&`
   fails with `can't open file`, exit 2. Written into `OFFLOAD.md` under Use.
2. `tools/play_demo.py:43` raises `SyntaxWarning: invalid escape sequence '\i'` when the tool is
   imported under Python 3.14 on Pine. Cosmetic, it changes no verdict, and it is gamedev's file
   (`data/results/offload-pinem-refuse-0.json`).
3. The two fix commits disagree on how many old reds the defect caused: `33c2cb4` says 21 reds, 19 of
   them passing on Windows, while `d87980c` says 16 are one import chain and 3 are host byte
   differences. Unverified which is right, and no verdict above depends on it, because the row that
   counts is the fresh one (`git show 33c2cb4`, `git show d87980c`).
4. gate30, card t_773e368b, is not one of the thirteen but ran from 16:49 to 16:54, before `33c2cb4`
   landed at 16:56, so its 1329 passed and 3 failed has the same exposure. The `pinem` run here is its
   measurement too: 1330 passed, 2 failed, the third red having gone green in between
   (`data/results/offload-gate30-0.json`, `data/results/offload-pinem-0.json`).

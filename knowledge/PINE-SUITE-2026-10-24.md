# PINE-SUITE: the gamedev suite run 3 ways on Pine, 2026-10-23

Card `t_64d6e959` (PINE-SUITE), owner testing, created by gamedev. Goal: the full suite sharded 3 ways onto Pine
through the offload helper, merged into one honest count. Tree measured: `git rev-parse --short HEAD` answers
`69abae0`, and `git status --porcelain | wc -l` answers 654, so other lanes held the tree while this run went out
(`<repo>`).

Follow-up card `t_572d611d` (PINE-SUITE-2) closed the third shard and the zip size at 03:18 to 03:45 on 2026-10-23.
Its three tree readings, taken while other lanes wrote: `HEAD c464edd` with 657 dirty entries at 03:18:40 (the zip
measurement), `HEAD 41ce9b2` with 670 at 03:37:20 (the zip the shard 2 run shipped), `HEAD 09c99ec` with 680 at
03:42:04 (the Windows rerun of shard 2's failures). Sections 4, 5b and 6 carry that work.

## 1. The command, and one correction to the card's INPUTS line

The card names `tools/pine_offload.py`. There is no such file: `ls tools/` in the repo lists 68 entries and none is
`pine_offload.py` (`<repo>\tools`). The helper the card means is
`<workspace>\Shared\projects\arananet\pine\pine_offload.py`, whose `REPO` is
`HERE.parent.parent / "primordial-paradox"`, that is the tree measured above.

- Interpreter: `<home>\AppData\Local\Python\bin\python.exe`, 3.14.7, the only one that imports `pinesandbox`
  (`pine_offload.py` lines 15 to 16 say the Hermes venv python cannot import it).
- Tests offloaded: 66 of the 68 `tests/test_*.py` files. The tool refuses two by name before sharding:
  `not offloaded (checks need git history, they run on the Windows suite): tests/test_build_inputs.py,
  tests/test_test_inputs.py` (`GIT_TESTS`, `pine_offload.py`). Card `t_572d611d` added a third
  (`tests/test_sync_art.py`, section 6), so a run from 03:38 on offloads 65.
- Zip: 54,038,076 bytes for the 3-way attempt (`offload-gamedev-daily-0-timeout.json` has no field for it; the number
  is the tool's own `zip bytes 54038076 files 66 shards 3` line on stdout, run start 02:30:32). After the fix it is
  `zip bytes 24242661 files 22 shards 1` for the shard 2 run (section 6).
- Key handling: `PINE_SANDBOX_API_KEY` was present in the environment (48 chars) and was never printed; the tool reads
  it itself (`<workspace>\Shared\projects\arananet\pine\OFFLOAD.md` line 22).

## 2. The 3-way run, and the transport failure on all three shards

`python pine_offload.py --shards 3 --name gamedev-daily` at 02:30:32 did not complete: all three shards ended
`status: error` at the upload step, `PUT /v1/sessions/main/files`, within 52 seconds.

| Shard | Error kind | Error text (verbatim, truncated) | Evidence file |
|---|---|---|---|
| gamedev-daily-0 | timeout | `PineCallError: pine write_file failed: TimeoutError: pinesandbox: request timed out: deadline exceeded ... op=PUT /v1/sessions/main/files` | `pine/data/results/offload-gamedev-daily-0-timeout.json` |
| gamedev-daily-1 | timeout | same `TimeoutError ... deadline exceeded` on the same PUT operation | `pine/data/results/offload-gamedev-daily-1-timeout.json` |
| gamedev-daily-2 | connection reset | `PineCallError: pine write_file failed: ConnectionError: pinesandbox: connection failed: [Errno 10054] An existing connection was forcibly closed by the remote host` | `pine/data/results/offload-gamedev-daily-2-timeout.json` |

The error records were copied to the `-timeout.json` names before the retries so the evidence survives the retry
overwriting the shard file (copy at 02:37, `ls -la pine/data/results/offload-gamedev-daily*`).

Cause: the zip is 54 MB, and `OFFLOAD.md` line 32 records that a zip over about 38 MB starts failing the upload with
`ConnectionError: [Errno 10054]`, and that a 66 MB zip timed out on all three shards on 2026-10-22
(`<workspace>\Shared\projects\arananet\pine\OFFLOAD.md`).

## 3. The retry, one Computer per shard, in the card's rule

The card says a transport error on one shard is retried once by name. Each shard was retried once, alone, with its own
22 files from the failed shards' `files` lists (`--shards 1 --files <that shard's 22 files>`), which is the same
partition the 3-way run made (`pine_offload.py` line 163, `files[i :: a.shards]`).

| Shard | Retry start, end | Wall | Status | Result file |
|---|---|---|---|---|
| gamedev-daily-0 | 02:39:03 to 02:43:27 | 229.7 s | completed | `pine/data/results/offload-gamedev-daily-0.json` |
| gamedev-daily-1 | 02:44:14 to 02:46:32 | 95.3 s | completed | `pine/data/results/offload-gamedev-daily-1-0.json` |
| gamedev-daily-2 | 02:48:06 to 02:48:41 | 35 s | error, retry spent | `pine/data/results/offload-gamedev-daily-2-0.json` |

Shard 2's retry failed on the same upload with `ConnectionError: pinesandbox: connection failed: [Errno 10053] An
established connection was aborted by the software in your host machine ... op=PUT /v1/sessions/main/files`, so under
the card's rule it is recorded as unknown and contributes nothing to any count (
`pine/data/results/offload-gamedev-daily-2-0.json`). The retry naming is the tool's own: `"%s-%d" % (name, i)` with
`i = 0` for a one-shard run, hence `-1-0` and `-2-0` (`pine_offload.py` line 166).

## 4. The merged count

Every number below is read out of the `pytest` summary line inside `results_txt`, which is the tool's own captured
output, not the remote agent's `SUMMARY` prose, as `OFFLOAD.md` requires. All three rows that exist had a pytest line,
and each one agrees with the agent's own `SUMMARY` line, which is why that prose is redundant here and not a source.

| Shard | Files | `pytest` summary line (verbatim) | passed | skipped | failed | Rows |
|---|---|---|---|---|---|---|
| gamedev-daily-0 | 22 | `3 failed, 385 passed, 1 skipped, 80 warnings in 161.28s` | 385 | 1 | 3 | 389 |
| gamedev-daily-1 | 22 | `406 passed, 14 skipped, 3 warnings in 11.04s` | 406 | 14 | 0 | 420 |
| gamedev-daily-2 | 22 | `9 failed, 409 passed, 6 skipped, 20 warnings in 36.65s` | 409 | 6 | 9 | 424 |
| total | 66 | three pytest lines, quoted above | 1200 | 21 | 12 | 1233 |

Rows: 389 + 420 + 424 = 1233, and 1200 + 21 + 12 = 1233, so the row count closes against the counts on the
three lines. Shard 1's 14 skips are visible as fourteen `s` marks in its progress output (5 in the 34% block, 2
and 7 in the 85% block), which is the 5 `windows_only` tests of `tests/test_capture_title.py` and the 8 of
`tests/test_play_demo.py` plus 1 more (`pine/data/results/offload-gamedev-daily-1-0.json`, `results_txt`).

The third row is card `t_572d611d` (PINE-SUITE-2) and not this card's run: shard 2's 22 files were run once, by
name, on 2026-10-23 at 03:38:03 to 03:40:18 after the zip was brought under the upload ceiling (section 6). Its
line is `9 failed, 409 passed, 6 skipped, 20 warnings in 36.65s`, read out of the `results_txt` of
`pine/data/results/offload-gamedev-daily-2-0.json`, and the remote agent's own `SUMMARY passed=409 failed=9`
agrees with it. Nothing here is counted from that prose. The three shard rows now cover all 66 offloaded files,
so 1200 passed, 21 skipped, 12 failed is the suite's own count and no longer a floor.

Three test files are not offloaded at all, by the tool's own rules: `tests/test_build_inputs.py` and
`tests/test_test_inputs.py` need a git checkout, and from card `t_572d611d` on `tests/test_sync_art.py`
needs the 34 MB stream mirror the upload ceiling cannot carry. All three run on the Windows suite
(`pine_offload.py`, `GIT_TESTS` and `ASSET_TESTS`). The three rows above still cover 66 files, because
shard 1 ran before that rule landed.

## 5. The three failures, checked on the Windows host

The card does not edit a test, and `pine`-only reds can mean the zip lacked a file (`OFFLOAD.md` lines 17 to 20), so
the three were rerun on the PC before being called red:

    python -m pytest <the three ids> -q -p no:cacheprovider --tb=short   ->   3 failed in 6.69s

| Test | What the assertion says | Verdict |
|---|---|---|
| `tests/test_audio.py::test_unreferenced_cue_rows_are_the_recorded_debt_list` | `['PP-01', 'PP...` != `['PP-01', 'PP...`; `At index 2 diff: 'PP-08' != 'PP-03'`, `Right contains one more item: 'PP-16'`: the debt list in the test and the cue rows in `data/` disagree | red on both hosts, real; no card id assigned by this card (unverified which lane owns it) |
| `tests/test_no_network_in_build.py::test_the_build_holds_no_endpoint_no_key_and_no_live_call` | `12 finding(s)`, all `REFUSED ...: URL in a data file that declares no citation and no third party provenance`, 6 in `game/datafiles/credits.json` and `game/datafiles/tile_classes_drive.json`, 6 in `data/credits.json` and `data/tile_classes_drive.json` | red on both hosts, real; the exemption block the checker wants is missing from those two data files (unverified which lane owns it) |
| `tests/test_slice_story.py::test_every_gate_the_data_names_is_a_flag` | `flag 'gate_passed' gates content but nothing the slice reaches ever sets it` | red on both hosts, real; the gate flag is set nowhere the slice reaches (unverified which lane owns it) |

None of the three is in `knowledge/TEST-CLASSIFY-2026-10-23.md`, neither its table of 33 (section 3) nor its list of
later reds (section 4), so all three are new since that page was written.

Host difference worth naming: the local rerun scans 624 files (40 GML, 232 JSON) and 304 URLs, while
`knowledge/TEST-CLASSIFY-2026-10-23.md` section 6 records 604 files (36 GML, 226 JSON) and 292 URLs, because the tree
grew between 01:44 and 02:58.

## 5b. The nine failures shard 2 landed, and how each was checked

Shard 2's `results_txt` names nine FAILED lines. The remote tail keeps only the last 80 lines, so the
first two failures' own text is cut; the rest is quoted where it appears. Each one was rerun on the
Windows host at 03:42 on `HEAD 09c99ec` with 680 dirty entries: `8 failed, 10 passed in 4.02s` for the ids
that still exist, which is the honest way to tell a real red from a zip gap (`OFFLOAD.md` lines 17 to 20).

| Test | Pine verdict and text | Windows rerun | Verdict |
|---|---|---|---|
| `tests/test_dialogue_v2.py::test_the_checker_refuses_a_31_character_page_line` | failed; its text is above the kept tail | that name does not exist in the tree any more: the test was renamed `test_the_checker_refuses_a_page_line_one_character_too_long` (`tests/test_dialogue_v2.py` line 200) and that one passes on the host | tree moved under the run between 03:38 and 03:42; the snapshot's red cannot be reproduced by name (unverified whether it was real at 03:38) |
| `tests/test_mix_check_v3.py::test_the_script_still_runs_on_a_slice` | `FileNotFoundError` | `OSError: [WinError 6] The handle is invalid` at `subprocess.run` | zip gap on Pine, not a regression: the 30 second slice reads `assets/audio/pp_drive/pp_drive_v3_humanized.wav` (15,748,192 bytes, `assets/audio/pp_drive/mix_check_v3.py` lines 5 and 168), which the zip never carried because `.wav` outside `AUDIO_PREFIXES` is skipped. The host red is a different cause in this shell, so this test is not measured on either host. **Resolved the same night by card t_cd466fd4:** the render does not fit (the two renders are 16,752,241 bytes of deflate and put the zip at 41,216,180 against the 40,000,000 ceiling), so the node is in `RENDER_NODES` in `pine_offload.py` and Pine now deselects it: `--files tests/test_mix_check_v3.py --shards 1 --name mixnode` returned `4 passed, 1 deselected in 0.20s` (`arananet/pine/data/results/offload-mixnode-0.json`). The host `[WinError 6]` did not reproduce: the same node passed 4 times in a row and the whole file was `5 passed in 3.10s` on the host, so it was that shell, not a real red |
| `tests/test_project.py::test_project_graph_matches_disk` | `AssertionError` | same assertion, `assert check_project.check(ROOT) == []` | red on both hosts: `PrimordialParadox.yyp: game/datafiles/tile_classes_ship.json is not listed as an Included File` |
| `tests/test_project.py::test_generated_project_files_are_current` | `AssertionError` | `assert 1 == 0`, `gen_project.main()` returns 1 | red on both hosts: the generated project files are stale against the tree |
| `tests/test_project.py::test_gml_uses_only_defined_macros_and_enums` | `AssertionError` | `used but never defined: ['PP_PORTRAIT_']` (`tests/test_project.py` line 277) | red on both hosts |
| `tests/test_slice_route.py::test_a_step_resolves_the_one_id_it_names[drive]` and `[save]` | `step drive: the scene 'drive_to_southampton' is not in data/scenes/all.json, so its commands cannot be read`; `step save: the row names no trigger` | identical text at `tests/test_slice_route.py` lines 498, 528 and 607 | red on both hosts |
| `tests/test_slice_route.py::test_a_scene_step_reaches_end_with_only_known_commands[drive]` | same `drive_to_southampton` assertion | identical | red on both hosts |
| `tests/test_slice_route.py::test_the_save_step_names_a_trigger_that_exists_on_its_map` | `step save: the row names no trigger` | identical | red on both hosts |

Seven of the nine are real and reproduce on the host with the same assertion. One is a zip gap by the tool's own
`.wav` rule, which predates this card, and one cannot be reproduced because its test was renamed while the run was
in flight.

### The far-side tree, put on trial locally

A red on Pine can also mean "the zip lacked a file", so the zip was unzipped into a scratch
`shared/` root (`make_farside.py`, `zip bytes 24339306`) and `tests/test_project.py` plus
`tests/test_sync_art.py` were run against exactly what a Computer receives. That tree has no
`game/datafiles/streams` at all, by the rule above, and it answers the question the grep cannot:
one check does read the mirror besides `tests/test_sync_art.py`.

    PrimordialParadox.yyp: game/datafiles/tile_classes_ship.json is not listed as an Included File
    PrimordialParadox.yyp: lists Included File streams/percy_theme.ogg which is not in game/datafiles
    ... 23 more, one per stream the zip cannot carry

So on the far side `check_project.check(ROOT)` returns 25 items where the live tree returns 1: the
`tile_classes_ship.json` red is the live one, and the other 24 are the `.yyp`'s stream entries whose
mirror the cut removed. That half of `test_project_graph_matches_disk` is therefore Windows-only from now
on, and its verdict on Pine does not change, because the item that made it red is the same one that makes
it red on the host. It is named here so no later run reads that test's Pine line as covering streams.

The streams cannot be paid for at any size: 34,229,523 bytes of streams plus 12.5 MB of tests, tools, data,
specs and knowledge is 46.7 MB, so a zip carrying the mirror is over the ceiling before `output/` and
`assets/audio` are added at all. That is why the fix is a smaller zip and not a wider ceiling.

## 6. Why the upload failed, stated as a number, and the fix that closed it

The zip is 54 MB because the tree's audio and recorded output grew. Measured from the tool's own include rules
(`probe_zip.py` over `INCLUDE`, `AUDIO_PREFIXES`, `EXCLUDE_PREFIXES`, run at 02:34):

| Part | Raw size |
|---|---|
| `game/datafiles/streams/` (46 files) | 34.2 MB |
| `output/` (demo audio, `nes_audit` json) | 18.8 MB |
| `assets/audio/title_theme/` (6 files, `title_theme.wav` is 6.05 MB) | 8.5 MB |
| everything else (knowledge, game, tools, data, assets, tests, specs) | 12.5 MB |

Three parallel 54 MB uploads failed; one 54 MB upload at a time succeeded twice in a row (shard 0 and shard 1 above).

Card `t_572d611d` fixed it in the helper, not by editing a test. Re-measured at 03:20 on 2026-10-23 with the same
rule set, the zip had grown to 58,270,033 bytes, and the streams were carried TWICE: once as
`game/datafiles/streams/*.ogg` (34,229,523 bytes, 46 files) and once as their sources under `assets/audio/`. The
mirror is generated, not authored: `tools/sync_art.py` `mirror_streams()` copies every `.ogg` under
`assets/audio/<name>/` into it, and `tests/conftest.py` runs `sync_art.main()` as a session fixture before any test
measures anything (`tests/conftest.py` lines 18 to 52), so the copy is rebuilt on the far side.

Measured before the change, by `streams_check.py`: 46 streams in the mirror and 46 `.ogg` sources under
`assets/audio/`, 34,229,523 bytes on each side, no basename present on only one side, and the committed
`game/PrimordialParadox.yyp` lists all 46. The mirror copy is therefore in `GENERATED_MIRRORS` and is no longer
zipped; the sources stay, because `mirror_streams()` reads them.

Result: `zip bytes 24242661 files 22 shards 1` was the tool's own line for the shard 2 run at 03:38:03, that is
24.24 MB against the 38 MB ceiling, and the upload completed on the first attempt (`shard2-run.log` line 1,
`pine/data/results/offload-gamedev-daily-2-0.json`).

The grep that had to come before the cut, on the tree at 03:20:

    $ grep -rn "datafiles/streams\|streams/title_theme" tests/ --include=*.py
    tests/test_build_inputs.py:49:    assert "datafiles/streams/title_theme_v3.ogg" in included
    tests/test_build_inputs.py:58:    bogus = "datafiles/streams/theme_that_was_never_committed.ogg"
    tests/test_build_inputs.py:68:    assert module.unresolved(["datafiles/streams/title_theme_v3.ogg"], tracked, repo) == []
    tests/test_sync_art.py:9:streams/title_theme.ogg which is not in game/datafiles".
    tests/test_sync_art.py:86:    listed = _listed_included_files("datafiles/streams")
    tests/test_sync_art.py:87:    assert "datafiles/streams/title_theme.ogg" in listed, f"unexpected stream entries: {listed}"

    $ grep -rn "assets.*audio.*ogg" tools/sync_art.py tools/check_build_inputs.py
    tools/sync_art.py:282:            if not fname.endswith(".ogg"):
    tools/check_build_inputs.py:106:                # .ogg also lands in datafiles/streams and has a source here.

Two files read the mirror, and only one of them was offloaded. `tests/test_build_inputs.py` is already a host-only
file (`GIT_TESTS`). `tests/test_sync_art.py` walks the `.yyp`'s 46 `datafiles/streams` entries and requires every
one on disk, and the zip can only rebuild the 22 whose source folder is under `AUDIO_PREFIXES`; carrying the other
24 costs the same 34 MB the ceiling cannot take (24.2 MB of the rest plus 34 MB of streams is 58 MB again). So it
joined the host-only list as `ASSET_TESTS`, with its reason printed by the tool:

    not offloaded (reads the theme streams, which no zip under the upload ceiling carries, it runs on the Windows suite): tests/test_sync_art.py

That is a coverage move on Pine, not a weakened or edited test: it runs on the Windows suite, and on this host it
is green, measured at 03:33 with `python -m pytest tests/test_sync_art.py -q -p no:cacheprovider` -> `4 passed in
4.04s`, so the move is not hiding a red.

Asked and answered: the SDK has no call that shares one uploaded file across Computers.
`pine_client.py` exposes `put_file` (line 981) and `get_file` (line 987) per session, and the only reuse
primitive is `create_or_resume_computer` (line 497), which reuses one Computer by name. Uploading once and running
three shards there means three shards in sequence on one Computer, and the single 54 MB PUT still has to win: it
lost once at 02:48 with `[Errno 10053]`. The size cut is the fix; sharing would only have removed the parallelism.

ZIP-STATE per run: the 22 files of shard 2 were zipped from `HEAD 41ce9b2` with 670 entries in `git status
--porcelain` at 03:37:20, so other lanes held the tree while it went out exactly as they did for shards 0 and 1.

## 7. The result files, pasted

The three shard result files this card produced:

    pine/data/results/offload-gamedev-daily-0.json
    pine/data/results/offload-gamedev-daily-1-0.json
    pine/data/results/offload-gamedev-daily-2-0.json

The three that record the failed 3-way attempt, kept as evidence:

    pine/data/results/offload-gamedev-daily-0-timeout.json
    pine/data/results/offload-gamedev-daily-1-timeout.json
    pine/data/results/offload-gamedev-daily-2-timeout.json

And the one that records shard 2's second failed upload, which the shard 2 rerun would otherwise have
overwritten (copied at 03:36, before the run):

    pine/data/results/offload-gamedev-daily-2-0-failed-upload.json

Cost of the attempts: shard 0 0.0115 USD, shard 1 0.0048 USD and shard 2 0.0053 USD of Computer time, from the
`est_computer_usd` field of their result files; the four failed attempts ran a Computer for under a minute each and
the tool recorded no figure for them, so the total is 0.0216 USD measured and roughly 0.012 USD more unrecorded
(`pine/data/results/offload-gamedev-daily-0.json`, `offload-gamedev-daily-1-0.json`,
`offload-gamedev-daily-2-0.json`). The 22 file run that finally landed shard 2 is the one that matters: it cost one
Computer for 135 seconds and shipped 24.2 MB, where three parallel 54 MB uploads had failed twice.

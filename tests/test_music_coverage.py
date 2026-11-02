"""Coverage test for music: every room and every fight reaches an audible cue, or this file says which one does not.

What is pinned here, and why each pin earns its place. Nayil reported no music in Town Quay, in battle and in
Percy's fight while the runtime owner reworked the bus, so this file answers one question with numbers: is
there a room or a fight that has no cue, no OGG, or an OGG too quiet to hear? The three failure kinds the card
names are the three groups below.

  1. COVERAGE. Every map row in data\\maps\\all.json and data\\maps\\ship_sample.json (pp_data appends the
     sample map to the runtime registry) names a cue in its own `music` field, that cue is a row in
     data\\audio.json, and the row lands on a file, either its own or one down its `fallback` chain. Every
     encounter row in data\\encounters\\all.json does the same, and a row that names no cue is covered by
     PP_AUDIO_FIGHT_CUE, the macro the module uses for exactly that case.
  2. THE FILE IS IN THE BUILD, not only in the ledger. The name the bus opens is resolved the way
     pp_audio_music_paths resolves it (the delivered_file basename first, then <asset>.ogg), and that name
     must exist under assets\\audio, in the generated mirror game\\datafiles\\streams (sync_art copies every
     .ogg there, and the conftest session fixture builds that mirror before any test measures it), and as an
     Included File in game\\PrimordialParadox.yyp. A stream in the mirror that the project file does not list
     is a cue the build does not ship.
  3. IT IS AUDIBLE. ffmpeg's own volumedetect mean for that OGG must be above -40 dBFS. This is the number
     the card asks for, and it catches the failure a file-exists check cannot see: an OGG of digital silence.

Honest limits, so no reader takes more from a green run than it says.
  - A green run does NOT say music was heard. Nothing here opens a GameMaker window or touches a speaker; the
    last inch is the runtime owner's card and the tour log it produced (knowledge\\MUSIC-COVERAGE-2026-11-02.md
    quotes it). What is proved is data, file, mirror, project membership and level.
  - The mirror row proves that sync_art copies this file, because the mirror is regenerated from assets\\audio by
    the conftest fixture during every run. It does not prove that some earlier build folder still held a stale copy.
  - The volume row needs ffmpeg, and it is found the way this project finds it (tools\\play_demo.py
    ffmpeg_path(), which binds a Win32 API through ctypes at import, so the row is marked windows_only and says
    so rather than failing off the Windows host).
  - The bus wiring itself (pp_audio_room reading the map field, pp_audio_battle reading the encounter field) is
    pinned by tests\\test_music_everywhere.py, which belongs to that card. This file measures the material those
    functions read, not their code.

Run `python tests/test_music_coverage.py` to print the coverage table that knowledge\\MUSIC-COVERAGE-2026-11-02.md
carries, from the same functions the assertions use, so the document and the test cannot drift.
"""

from __future__ import annotations

import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
for _path in (ROOT, TOOLS):
    if _path not in sys.path:
        sys.path.insert(0, _path)

DATA = os.path.join(ROOT, "data")
AUDIO = os.path.join(ROOT, "assets", "audio")
STREAMS = os.path.join(ROOT, "game", "datafiles", "streams")
PROJECT = os.path.join(ROOT, "game", "PrimordialParadox.yyp")
AUDIO_JSON = os.path.join(DATA, "audio.json")
MAPS_JSON = os.path.join(DATA, "maps", "all.json")
SHIP_JSON = os.path.join(DATA, "maps", "ship_sample.json")
ENCOUNTERS_JSON = os.path.join(DATA, "encounters", "all.json")

# pp_audio_cue_resolve walks the fallback chain with `for (var hop = 0; hop < 8; hop += 1)`, so a chain longer than
# this is a chain the game itself would abandon. The number is copied, not chosen: a test with a longer bound would
# pass a chain the runtime cannot follow.
FALLBACK_HOPS = 8

# The card's audibility floor, in dBFS, read from ffmpeg's own volumedetect mean.
AUDIBLE_DB = -40.0

# Per-process caches: the audio index, the project's Included Files and the ffmpeg measurement are read once by the
# assertions and once by the table printer, and a second decode of the same 3:45 OGG buys nothing.
_AUDIO_INDEX = None
_PROJECT_STREAMS = None


def _read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def cue_rows():
    """The cue table from data\\audio.json, as {id: row}. Duplicate ids are a finding, not something to merge."""
    rows = _read(AUDIO_JSON).get("cues") or []
    out = {}
    for row in rows:
        cue_id = row.get("id")
        assert cue_id, "a cue row in data/audio.json has no id"
        assert cue_id not in out, "data/audio.json has two rows for cue %s" % cue_id
        out[cue_id] = row
    return out


def rooms():
    """Every map the runtime registry holds, from both map files, as (room id, cue id, source file).

    pp_data.gml appends data\\maps\\ship_sample.json to the registry, so a room in the sample is a room the game
    can load and a room this coverage answer has to include.
    """
    out = []
    for path, label in ((MAPS_JSON, "maps/all.json"), (SHIP_JSON, "maps/ship_sample.json")):
        for row in _read(path).get("maps") or []:
            out.append((str(row.get("id")), row.get("music"), label))
    return out


def encounters():
    """Every encounter row, as (encounter id, cue id or None)."""
    return [(str(row.get("id")), row.get("music")) for row in _read(ENCOUNTERS_JSON).get("encounters") or []]


def fight_fallback_cue():
    """The cue pp_audio_battle uses when an encounter row names none, read from the module's own macro.

    Read from the source rather than written in: a test that hard-coded PP-04 would keep passing after the module
    changed its default, and the encounter rows with no music field are covered only by that macro.
    """
    path = os.path.join(ROOT, "game", "scripts", "pp_audio", "pp_audio.gml")
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    found = re.search(r'#macro\s+PP_AUDIO_FIGHT_CUE\s+"([^"]+)"', text)
    assert found, "pp_audio.gml no longer defines PP_AUDIO_FIGHT_CUE, so a fight with no music row has no cue"
    return found.group(1)


def music_file_name(entry):
    """The file name the bus opens for a cue row, no folder. Mirrors pp_audio_music_file_name."""
    declared = entry.get("delivered_file") or ""
    if declared:
        declared = str(declared).replace("\\", "/").rsplit("/", 1)[-1]
    if declared:
        return declared
    return "%s.ogg" % entry.get("asset")


def candidate_names(entry):
    """The names the bus tries for a cue row, in order. Mirrors pp_audio_music_paths."""
    names = [music_file_name(entry)]
    asset_name = "%s.ogg" % entry.get("asset")
    if asset_name != names[0]:
        names.append(asset_name)
    return names


def audio_index():
    """Basename to the paths that hold it under assets\\audio, built once per process."""
    global _AUDIO_INDEX
    if _AUDIO_INDEX is not None:
        return _AUDIO_INDEX
    index = {}
    for folder, _dirs, files in os.walk(AUDIO):
        for name in files:
            index.setdefault(name, []).append(os.path.join(folder, name))
    _AUDIO_INDEX = index
    return _AUDIO_INDEX


def project_streams():
    """The stream names game\\PrimordialParadox.yyp ships as Included Files, keyed by name."""
    global _PROJECT_STREAMS
    if _PROJECT_STREAMS is not None:
        return _PROJECT_STREAMS
    names = set()
    for row in _read(PROJECT).get("IncludedFiles") or []:
        folder = str(row.get("filePath") or "").replace("\\", "/").rstrip("/")
        name = row.get("name") or row.get("%Name")
        if not name:
            continue
        if folder.rsplit("/", 1)[-1] == "streams":
            names.add(name)
    _PROJECT_STREAMS = names
    return _PROJECT_STREAMS



def landed_name(entry):
    """The name the bus opens for a row, the first candidate that is on disk under assets\\audio, or '' when none is."""
    index = audio_index()
    for name in candidate_names(entry):
        if name in index:
            return name
    return ""


def resolve(cue_id, table=None):
    """The cue that actually plays, and the chain walked to it, following pp_audio_cue_resolve.

    Returns (resolved id or None, chain of ids asked). None means the chain ran out of hops, named a row that is
    not in the table, or reached a row with nothing on disk and no fallback: the three ways a room goes silent.
    """
    table = cue_rows() if table is None else table
    chain = [cue_id]
    current = cue_id
    for _hop in range(FALLBACK_HOPS):
        entry = table.get(current)
        if entry is None:
            return None, chain
        if landed_name(entry):
            return current, chain
        fallback = entry.get("fallback")
        if not isinstance(fallback, str) or fallback == "":
            return None, chain
        current = fallback
        chain.append(current)
    return None, chain


def coverage_rows():
    """One row per room and per fight, the table this file prints and the document carries."""
    table = cue_rows()
    ship = project_streams()
    index = audio_index()
    rows = []
    for kind, items in (("room", rooms()), ("fight", encounters())):
        for item in items:
            item_id, cue = item[0], item[1]
            asked = cue if (isinstance(cue, str) and cue) else fight_fallback_cue()
            resolved, chain = resolve(asked, table)
            names = candidate_names(table[resolved]) if resolved else []
            opened = landed_name(table[resolved]) if resolved else ""
            rows.append({
                "kind": kind,
                "id": item_id,
                "asked": asked,
                "resolved": resolved,
                "chain": chain,
                "ogg": opened,
                "in_assets": bool(opened) and opened in index,
                "in_streams": bool(opened) and os.path.isfile(os.path.join(STREAMS, opened)),
                "in_project": bool(opened) and opened in ship,
                "loop": table[resolved].get("loop") if resolved else None,
                "candidates": names,
            })
    return rows


_VOLUME_CACHE = {}


def mean_volume_db(name):
    """ffmpeg's volumedetect mean for one stream, measured once per process.

    The path is the mirror file, because that is the bytes the game opens. ffmpeg is found through
    tools\\play_demo.py, the project's own lookup, so this row cannot measure with a different binary than the
    rest of the tree.
    """
    if name in _VOLUME_CACHE:
        return _VOLUME_CACHE[name]
    import play_demo

    path = os.path.join(STREAMS, name)
    value = play_demo.mean_volume_db(path)
    _VOLUME_CACHE[name] = value
    return value


# ---------------------------------------------------------------------------------------------------------------
# The three failure kinds the card names.


def test_every_room_names_a_cue_that_lands():
    """A room with no cue, an unregistered cue id, or a chain that lands nothing is a silent room."""
    table = cue_rows()
    problems = []
    for room_id, cue, source in rooms():
        if not isinstance(cue, str) or cue == "":
            problems.append("room %s (%s) names no music cue at all" % (room_id, source))
            continue
        if cue not in table:
            problems.append("room %s (%s) asks cue %s, which is not a row in data/audio.json" % (room_id, source, cue))
            continue
        resolved, chain = resolve(cue, table)
        if resolved is None:
            problems.append("room %s (%s) asks cue %s, and the chain %s lands on no OGG"
                            % (room_id, source, cue, " -> ".join(chain)))
    assert not problems, "\n".join(problems)


def test_every_fight_names_a_cue_that_lands():
    """The same for fights, including a row that names none, which the module covers with PP_AUDIO_FIGHT_CUE."""
    table = cue_rows()
    default = fight_fallback_cue()
    assert default in table, "PP_AUDIO_FIGHT_CUE is %s, which is not a row in data/audio.json" % default
    problems = []
    for enc_id, cue in encounters():
        asked = cue if (isinstance(cue, str) and cue) else default
        if asked not in table:
            problems.append("fight %s asks cue %s, which is not a row in data/audio.json" % (enc_id, asked))
            continue
        resolved, chain = resolve(asked, table)
        if resolved is None:
            problems.append("fight %s asks cue %s, and the chain %s lands on no OGG"
                            % (enc_id, asked, " -> ".join(chain)))
    assert not problems, "\n".join(problems)


def test_every_resolved_cue_file_exists_in_assets_the_mirror_and_the_project():
    """A cue whose OGG is missing from any of the three places is a room that goes silent for that reason alone."""
    problems = []
    ship = project_streams()
    for row in coverage_rows():
        if row["resolved"] is None:
            problems.append("%s %s resolves to no cue, so there is no file to check" % (row["kind"], row["id"]))
            continue
        missing = []
        if not row["in_assets"]:
            missing.append("assets/audio (tried %s)" % ", ".join(row["candidates"]))
        if not row["in_streams"]:
            missing.append("game/datafiles/streams/%s" % row["ogg"])
        if not row["in_project"]:
            missing.append("game/PrimordialParadox.yyp Included Files (datafiles/streams/%s)" % row["ogg"])
        if missing:
            problems.append("%s %s plays cue %s (%s) and it is absent from %s"
                            % (row["kind"], row["id"], row["resolved"], row["ogg"], "; ".join(missing)))
    assert not problems, "\n".join(problems)


@pytest.mark.windows_only
def test_every_cue_a_room_or_fight_plays_is_above_the_audibility_floor():
    """A file that exists and measures below -40 dBFS mean is silence with a file name, which is the third failure."""
    import play_demo

    if not play_demo.ffmpeg_path():
        pytest.skip("ffmpeg is not installed on this host, so the mean volume column is unmeasured here "
                    "(tools/play_demo.py ffmpeg_path() answered empty)")

    quiet = {}
    for row in coverage_rows():
        if row["resolved"] is None:
            continue
        name = row["ogg"]
        value = mean_volume_db(name)
        assert value is not None, "ffmpeg could not measure game/datafiles/streams/%s, so its level is unknown" % name
        quiet.setdefault(name, []).append((row["kind"], row["id"], value))
    problems = []
    for name, users in sorted(quiet.items()):
        value = users[0][2]
        if value < AUDIBLE_DB:
            who = ", ".join("%s %s" % (kind, item) for kind, item, _v in users)
            problems.append("%s measures %.1f dB mean, below the %.0f dB floor, and it is what %s play"
                            % (name, value, AUDIBLE_DB, who))
    assert not problems, "\n".join(problems)


test_every_cue_a_room_or_fight_plays_is_above_the_audibility_floor = pytest.mark.windows_only(
    test_every_cue_a_room_or_fight_plays_is_above_the_audibility_floor)


# ---------------------------------------------------------------------------------------------------------------
# The pending rows: a cue with no render of its own is covered only by its fallback chain.


def test_every_pending_cue_falls_back_to_a_landed_cue():
    """A pending cue is a promise that its `fallback` chain reaches a landed row; a broken chain is a silent room."""
    table = cue_rows()
    problems = []
    for cue_id, entry in sorted(table.items()):
        resolved, chain = resolve(cue_id, table)
        if entry.get("pending"):
            if resolved is None:
                problems.append("pending cue %s does not reach a landed cue: chain %s" % (cue_id, " -> ".join(chain)))
            elif resolved == cue_id:
                problems.append("pending cue %s has no delivered_file but resolves to itself, which cannot play"
                                % cue_id)
            elif entry.get("delivered_file"):
                problems.append("pending cue %s names a delivered_file, so pending and delivered disagree" % cue_id)
            elif len(chain) > FALLBACK_HOPS:
                problems.append("pending cue %s needs %d hops, past the %d the bus walks"
                                % (cue_id, len(chain), FALLBACK_HOPS))
        else:
            if not entry.get("delivered_file"):
                problems.append("cue %s is not pending, so it should name a delivered_file, and it does not" % cue_id)
            if resolved != cue_id:
                problems.append("cue %s is landed but resolves to %s, so its own OGG is not where the bus looks"
                                % (cue_id, resolved))
    assert not problems, "\n".join(problems)


def test_the_fight_default_cue_is_a_landed_cue():
    """PP_AUDIO_FIGHT_CUE is the cue a fight with no music row plays, so it must resolve without a row's help."""
    default = fight_fallback_cue()
    table = cue_rows()
    assert default in table, "PP_AUDIO_FIGHT_CUE %s is not in data/audio.json" % default
    resolved, chain = resolve(default, table)
    assert resolved is not None, "PP_AUDIO_FIGHT_CUE %s lands on no OGG: chain %s" % (default, " -> ".join(chain))


# ---------------------------------------------------------------------------------------------------------------
# The table the document carries.


def table_rows():
    """The coverage table as markdown lines, from the same resolvers the assertions use."""
    lines = []
    for row in coverage_rows():
        volume = mean_volume_db(row["ogg"]) if row["ogg"] else None
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            row["kind"],
            row["id"],
            row["asked"],
            row["resolved"] or "NONE",
            row["ogg"] or "NONE",
            "yes" if row["in_assets"] else "no",
            "yes" if row["in_streams"] else "no",
            "yes" if row["loop"] else "no",
            ("%.1f" % volume) if volume is not None else "unmeasured",
        ))
    return lines


def main(argv=None):
    """Print the coverage table. `python tests/test_music_coverage.py` is how the document's table is made."""
    print("| kind | id | cue asked | cue resolved | ogg | assets/audio | streams | loop | mean dB |")
    print("|---|---|---|---|---|---|---|---|---|")
    for line in table_rows():
        print(line)
    pending = [(cue_id, resolve(cue_id)[1]) for cue_id, entry in sorted(cue_rows().items()) if entry.get("pending")]
    print("")
    print("pending cue chains: %d" % len(pending))
    for cue_id, chain in pending:
        print("  %s -> %s" % (" -> ".join(chain), chain[-1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

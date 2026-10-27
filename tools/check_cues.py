"""Resolve every music cue the vertical slice names to a file or to an honest pending row (card R36).

The question this answers, in one line: for each cue id a map, a scene or an encounter asks for, is there
an OGG behind it, and when there is not, does the data say so and name the cue the bus should play instead?

It reads only:
  data/audio.json                 the cue table this card owns
  data/slice.json                 the slice's map, scene and encounter
  data/maps/all.json, data/maps/ship_sample.json, data/scenes/all.json, data/encounters/all.json
  assets/audio/<asset>/<asset>.ogg   the file each landed cue claims
  game/scripts/pp_audio/pp_audio.gml  read only, for the crossfade macro the data mirrors

It does not render, write, or play anything. Exit code 0 means every check passed.

Usage:
    python tools/check_cues.py
    python tools/check_cues.py --root .
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

MUSIC_VOLUME = 0.7
SFX_VOLUME = 0.9
CROSSFADE = 30
CUE_RE = re.compile(r"^PP-[0-9]{2}[ab]?$")
# The two stingers the slice plays, which are effects rather than music cues, so they live in sounds.
STINGER_SOUNDS = ("game_over", "save_jingle")


def load(root, rel):
    with open(os.path.join(root, rel), "r", encoding="utf-8") as handle:
        return json.load(handle)


def music_refs(root):
    """Every music reference the data holds, as (file, field, id). Cue shaped ids only."""
    refs = []
    for rel in ("data/maps/all.json", "data/maps/ship_sample.json"):
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        for index, row in enumerate(load(root, rel).get("maps", [])):
            name = row.get("music")
            if isinstance(name, str) and name:
                refs.append((rel, "maps[%d].music" % index, name))
    for index, row in enumerate(load(root, "data/encounters/all.json").get("encounters", [])):
        name = row.get("music")
        if isinstance(name, str) and name:
            refs.append(("data/encounters/all.json", "encounters[%d].music" % index, name))
    for index, scene in enumerate(load(root, "data/scenes/all.json").get("scenes", [])):
        for step, command in enumerate(scene.get("commands", [])):
            if isinstance(command, dict) and command.get("cmd") == "music":
                refs.append(("data/scenes/all.json", "scenes[%d].commands[%d].id" % (index, step),
                             command.get("id")))
    return [ref for ref in refs if isinstance(ref[2], str) and CUE_RE.match(ref[2])]


def slice_refs(root):
    """The cues the slice itself plays, followed through its own map, scene and encounter."""
    slice_ = load(root, "data/slice.json")
    refs = set()
    for row in load(root, "data/maps/all.json").get("maps", []):
        if row.get("id") == slice_.get("map") and isinstance(row.get("music"), str):
            refs.add(row["music"])
    for row in load(root, "data/scenes/all.json").get("scenes", []):
        if row.get("id") == slice_.get("scene"):
            for command in row.get("commands", []):
                if isinstance(command, dict) and command.get("cmd") == "music":
                    refs.add(command.get("id"))
    for row in load(root, "data/encounters/all.json").get("encounters", []):
        if row.get("id") == slice_.get("encounter") and isinstance(row.get("music"), str):
            refs.add(row["music"])
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = parser.parse_args()
    root = args.root
    problems: list[str] = []

    audio = load(root, "data/audio.json")
    cues = audio.get("cues", [])
    rows = {row.get("id"): row for row in cues}
    sounds = {row.get("id"): row for row in audio.get("sounds", [])}

    # --- the table itself ---------------------------------------------------------------------------------------
    if len(rows) != len(cues):
        problems.append("data/audio.json: cues: duplicate cue id")
    assets = [row.get("asset") for row in cues]
    if len(set(assets)) != len(assets):
        problems.append("data/audio.json: cues: two cues share one asset, so one file cannot be told from the other")

    landed = {}
    for cue_id, row in rows.items():
        asset = row.get("asset") or ""
        path = os.path.join(root, "assets", "audio", asset, asset + ".ogg")
        present = os.path.isfile(path)
        landed[cue_id] = present
        declared = row.get("delivered_file")
        pending = row.get("pending")
        if not isinstance(pending, bool):
            problems.append("data/audio.json: %s: pending must be true or false" % cue_id)
            continue
        if row.get("volume") != MUSIC_VOLUME:
            problems.append("data/audio.json: %s: volume is %r, spec 12 sets music at %s"
                            % (cue_id, row.get("volume"), MUSIC_VOLUME))
        if row.get("loop") is not True:
            problems.append("data/audio.json: %s: loop is %r, spec 12 rule 1 plays music looped"
                            % (cue_id, row.get("loop")))
        if pending and present:
            problems.append("data/audio.json: %s: marked pending but %s exists" % (cue_id, path))
        if not pending and not present:
            problems.append("data/audio.json: %s: not pending but %s is missing" % (cue_id, path))
        if present and declared != "assets/audio/%s/%s.ogg" % (asset, asset):
            problems.append("data/audio.json: %s: delivered_file %r does not name %s"
                            % (cue_id, declared, "assets/audio/%s/%s.ogg" % (asset, asset)))
        if not present and declared is not None:
            problems.append("data/audio.json: %s: delivered_file is set but the file is missing" % cue_id)

    # --- the fallback chain must terminate at a file, with no cycle ---------------------------------------------
    def resolve(cue_id, trail):
        if cue_id not in rows:
            return None, "fallback %r is not a cue row" % cue_id
        if landed.get(cue_id):
            return cue_id, ""
        fallback = rows[cue_id].get("fallback")
        if not isinstance(fallback, str) or not fallback:
            return None, "%s is pending with no fallback, so the bus would stay silent" % cue_id
        if fallback in trail:
            return None, "fallback cycle: %s" % " -> ".join(trail + [fallback])
        if not rows[fallback].get("pending"):
            return fallback, ""
        return resolve(fallback, trail + [fallback])

    for cue_id, row in rows.items():
        if landed.get(cue_id):
            continue
        target, why = resolve(cue_id, [cue_id])
        if target is None:
            problems.append("data/audio.json: %s: %s" % (cue_id, why))
        elif row.get("fallback") != target:
            problems.append("data/audio.json: %s: fallback is %r, the chain ends at %r"
                            % (cue_id, row.get("fallback"), target))

    # --- every cue the data asks for ----------------------------------------------------------------------------
    refs = music_refs(root)
    if len(refs) < 5:
        problems.append("the reference walk found %d music references, so the check would be vacuous" % len(refs))
    for rel, field, cue_id in refs:
        if cue_id not in rows:
            problems.append("%s: %s: cue %r is not in data/audio.json" % (rel, field, cue_id))
            continue
        target, why = resolve(cue_id, [cue_id])
        if target is None:
            problems.append("%s: %s: cue %r does not resolve to a file: %s" % (rel, field, cue_id, why))

    # --- the slice's own cues -----------------------------------------------------------------------------------
    slice_cues = sorted(slice_refs(root))
    for cue_id in slice_cues:
        if cue_id not in rows:
            problems.append("data/slice.json: cue %r is not in data/audio.json" % cue_id)
            continue
        target, why = resolve(cue_id, [cue_id])
        if target is None:
            problems.append("data/slice.json: cue %r does not resolve to a file: %s" % (cue_id, why))

    # --- the two stingers do not loop ---------------------------------------------------------------------------
    for name in STINGER_SOUNDS:
        row = sounds.get(name)
        if row is None:
            problems.append("data/audio.json: sounds: the stinger %r is not registered" % name)
            continue
        if row.get("loop") is not False:
            problems.append("data/audio.json: sounds.%s: loop is %r, a stinger must play once"
                            % (name, row.get("loop")))
        if row.get("volume") != SFX_VOLUME:
            problems.append("data/audio.json: sounds.%s: volume is %r, spec 12 sets effects at %s"
                            % (name, row.get("volume"), SFX_VOLUME))
        declared = row.get("delivered_file")
        if declared and not os.path.isfile(os.path.join(root, declared)):
            problems.append("data/audio.json: sounds.%s: delivered_file %r is missing" % (name, declared))

    # --- the crossfade the data mirrors -------------------------------------------------------------------------
    module = os.path.join(root, "game", "scripts", "pp_audio", "pp_audio.gml")
    macro = None
    if os.path.isfile(module):
        with open(module, "r", encoding="utf-8") as handle:
            match = re.search(r"^#macro\s+PP_AUDIO_FADE_STEPS\s+(\S+)", handle.read(), re.MULTILINE)
        macro = int(match.group(1)) if match else None
    if macro != CROSSFADE:
        problems.append("game/scripts/pp_audio/pp_audio.gml: PP_AUDIO_FADE_STEPS is %r, spec 12 rule 4 says %d"
                        % (macro, CROSSFADE))
    if audio.get("crossfade_steps") != CROSSFADE:
        problems.append("data/audio.json: crossfade_steps is %r, spec 12 rule 4 says %d"
                        % (audio.get("crossfade_steps"), CROSSFADE))

    # --- report -------------------------------------------------------------------------------------------------
    print("%-6s %-34s %-28s %-7s %s" % ("cue", "asset", "file", "state", "fallback"))
    for cue_id, row in rows.items():
        asset = row.get("asset") or ""
        state = "landed" if landed.get(cue_id) else "pending"
        print("%-6s %-34s %-28s %-7s %s"
              % (cue_id, asset, "%s.ogg" % asset if landed.get(cue_id) else "-", state,
                 row.get("fallback") or "-"))
    print("")
    print("references walked: %d from maps, scenes and encounters; slice cues: %s"
          % (len(refs), ", ".join(slice_cues) or "none"))
    print("landed %d, pending %d" % (sum(1 for v in landed.values() if v), sum(1 for v in landed.values() if not v)))
    if problems:
        for problem in problems:
            print("FAIL " + problem)
        print("\n%d problem(s)" % len(problems))
        return 1
    print("check_cues: every cue the slice names resolves to a file or to a pending row with a landed fallback")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Check data/dissonance_rules.json against data/schemas/dissonance_rules.schema.json
and against the rules of card t_baafc947 (MUS-DISSONANCE).

Checks
  C1  the JSON parses and validates against the schema written for it (jsonschema when
      installed, otherwise the small resolver below, which implements every keyword the
      schema actually uses)
  C2  exactly 30 devices, ids DIS-01 to DIS-30, no duplicates, no gaps
  C3  every device has a resolution block with a target, a direction and a finite window
  C4  every forbidden id and every source id a device cites exists (sources may live in
      this JSON or in the source tables of knowledge/MUSIC-STYLE-BIBLE.md and
      knowledge/MUSIC-HOOK-GRAMMAR.md)
  C5  the rate policy is arithmetically consistent with the note counts it states, and no
      device exceeds its risk cap
  C6  no em dash, no en dash and no long dash in the JSON, the schema or the markdown
  C7  knowledge/MUSIC-DISSONANCE.md names all 30 device ids, every forbidden id, and the
      resolution rule for each device family

Usage:
    python tools/check_dissonance_rules.py
    python tools/check_dissonance_rules.py --root .

Exit code 0 means every check passed. Every message names the file and the JSON path.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

JSON_REL = os.path.join("data", "dissonance_rules.json")
SCHEMA_REL = os.path.join("data", "schemas", "dissonance_rules.schema.json")
MD_REL = "knowledge/MUSIC-DISSONANCE.md"
BIBLE_REL = "knowledge/MUSIC-STYLE-BIBLE.md"
HOOK_REL = "knowledge/MUSIC-HOOK-GRAMMAR.md"

LONG_DASHES = ("\u2014", "\u2013", "\u2015", "\u2212")

DEVICE_COUNT = 30


# ----------------------------------------------------------------------------------------------
# Loading and a minimal JSON Schema resolver for the keywords this project's schemas use.

def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def read_text(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def resolve_ref(schema, ref):
    if not ref.startswith("#/"):
        raise ValueError("only local refs are supported: %s" % ref)
    node = schema
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def type_ok(value, expected):
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate(value, schema, root, path, errors):
    """Validate one node. Supports the keywords used by this repository's schemas."""
    if "$ref" in schema:
        validate(value, resolve_ref(root, schema["$ref"]), root, path, errors)
        return

    if "const" in schema and value != schema["const"]:
        errors.append("%s: expected const %r, found %r" % (path, schema["const"], value))
    if "enum" in schema and value not in schema["enum"]:
        errors.append("%s: %r is not one of %r" % (path, value, schema["enum"]))

    if "type" in schema:
        expected = schema["type"]
        options = expected if isinstance(expected, list) else [expected]
        if not any(type_ok(value, option) for option in options):
            errors.append("%s: expected type %s, found %s" % (path, expected, type(value).__name__))
            return

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append("%s: string shorter than %d" % (path, schema["minLength"]))
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append("%s: %r does not match %s" % (path, value, schema["pattern"]))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append("%s: %r below minimum %r" % (path, value, schema["minimum"]))
        if "maximum" in schema and value > schema["maximum"]:
            errors.append("%s: %r above maximum %r" % (path, value, schema["maximum"]))
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append("%s: %r not above exclusive minimum %r" % (path, value, schema["exclusiveMinimum"]))
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            errors.append("%s: %r not below exclusive maximum %r" % (path, value, schema["exclusiveMaximum"]))

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append("%s: %d items, at least %d required" % (path, len(value), schema["minItems"]))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append("%s: %d items, at most %d allowed" % (path, len(value), schema["maxItems"]))
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                validate(item, item_schema, root, "%s[%d]" % (path, index), errors)

    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append("%s: missing required field %r" % (path, key))
        properties = schema.get("properties", {})
        pattern_properties = schema.get("patternProperties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            matched = False
            if key in properties:
                matched = True
                validate(item, properties[key], root, "%s.%s" % (path, key), errors)
            for pattern, sub_schema in pattern_properties.items():
                if re.search(pattern, key):
                    matched = True
                    validate(item, sub_schema, root, "%s.%s" % (path, key), errors)
            if not matched and additional is False:
                errors.append("%s: field %r is not allowed" % (path, key))
        if "minProperties" in schema and len(value) < schema["minProperties"]:
            errors.append("%s: %d keys, at least %d required" % (path, len(value), schema["minProperties"]))


# ----------------------------------------------------------------------------------------------

def bible_source_ids(root):
    """Source ids already published in the style bible and the hook grammar tables."""
    found = set()
    for rel in (BIBLE_REL, HOOK_REL):
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        for line in read_text(path).splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            first = line.split("|")[1].strip()
            if re.fullmatch(r"S[0-9]+", first):
                found.add(first)
    return found


def check(root):
    errors = []
    json_path = os.path.join(root, JSON_REL)
    schema_path = os.path.join(root, SCHEMA_REL)
    md_path = os.path.join(root, MD_REL)

    for path in (json_path, schema_path, md_path):
        if not os.path.isfile(path):
            errors.append("%s: missing" % os.path.relpath(path, root).replace("\\", "/"))
    if errors:
        return errors

    data = load_json(json_path)
    schema = load_json(schema_path)

    # C1 schema
    try:
        import jsonschema  # noqa: F401
        validator = jsonschema.Draft202012Validator(schema)
        for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            errors.append("%s: schema %s: %s" % (JSON_REL, ".".join(str(p) for p in error.path) or "(root)",
                                                 error.message))
        engine = "jsonschema"
    except ImportError:
        validate(data, schema, schema, "$", errors)
        engine = "built in resolver"

    rules = data["rules"]

    # C2 count and ids
    if len(rules) != DEVICE_COUNT:
        errors.append("%s: %d devices, exactly %d required" % (JSON_REL, len(rules), DEVICE_COUNT))
    ids = [rule["id"] for rule in rules]
    expected = ["DIS-%02d" % number for number in range(1, DEVICE_COUNT + 1)]
    if sorted(ids) != expected:
        missing = [i for i in expected if i not in ids]
        extra = [i for i in ids if i not in expected]
        errors.append("%s: device ids do not run DIS-01 to DIS-%02d (missing %r, extra %r)"
                      % (JSON_REL, DEVICE_COUNT, missing, extra))

    # C3 every device resolves
    for rule in rules:
        path = "rules.%s" % rule["id"]
        resolution = rule.get("resolution", {})
        for field in ("target", "direction", "within_beats_max"):
            if field not in resolution:
                errors.append("%s.resolution: missing %r" % (path, field))
        if resolution.get("within_beats_max", 0) <= 0:
            errors.append("%s.resolution: within_beats_max must be a positive number of beats" % path)
        if rule["duration_beats"]["max"] < rule["duration_beats"]["min"]:
            errors.append("%s.duration_beats: max below min" % path)

    # C4 references
    forbidden_ids = {row["id"] for row in data["forbidden"]}
    local_sources = set(data["sources"].keys())
    known_sources = local_sources | bible_source_ids(root)
    for rule in rules:
        path = "rules.%s" % rule["id"]
        for ref in rule["forbidden"]:
            if ref not in forbidden_ids:
                errors.append("%s.forbidden: %r is not in the top level forbidden list" % (path, ref))
        if not rule["sources"]:
            errors.append("%s.sources: no source" % path)
        for ref in rule["sources"]:
            if ref not in known_sources:
                errors.append("%s.sources: %r is not in this file's sources and not in the style bible or "
                              "hook grammar tables" % (path, ref))
    for rule in rules:
        if "F1" not in rule["forbidden"] or "F2" not in rule["forbidden"]:
            errors.append("rules.%s.forbidden: must carry F1 (no leitmotif ends) and F2 (no cadence bar)"
                          % rule["id"])

    # C5 rate policy arithmetic and risk caps
    policy = data["rate_policy"]
    lo = policy["device_rate_min_percent"] / 100.0
    hi = policy["device_rate_max_percent"] / 100.0
    # The device budget is stated in whole devices, so a quarter of a device of rounding is allowed:
    # 3 percent of 27 notes is 0.81 devices, which a score can only spend as 1 device.
    tolerance = 0.25
    for key, notes in (("note_count_per_8_bars_3_4", policy["note_count_per_8_bars_3_4"]),
                       ("note_count_per_8_bars_4_4", policy["note_count_per_8_bars_4_4"])):
        low_devices = notes * lo
        high_devices = notes * hi
        if policy["devices_per_8_bars_min"] > low_devices + tolerance:
            errors.append("%s.%s: %.2f devices per 8 bars is above the %.2f the minimum rate gives"
                          % (JSON_REL, key, policy["devices_per_8_bars_min"], low_devices))
        if policy["devices_per_8_bars_max"] + tolerance < high_devices:
            errors.append("%s.%s: %.2f devices per 8 bars cannot hold the %.2f the maximum rate gives"
                          % (JSON_REL, key, policy["devices_per_8_bars_max"], high_devices))
    if policy["device_rate_min_percent"] >= policy["device_rate_max_percent"]:
        errors.append("%s.rate_policy: the rate band is empty" % JSON_REL)
    if policy["strong_clash_max_per_8_bars"] > 1:
        errors.append("%s.rate_policy: strong_clash_max_per_8_bars above 1 lets the piece shout twice in a "
                      "phrase" % JSON_REL)
    risk_caps = {int(level): row["max_per_8_bars"] for level, row in data["risk_levels"].items()}
    for rule in rules:
        cap = risk_caps[rule["risk"]]
        if rule["rate_per_8_bars"]["max"] > cap:
            errors.append("rules.%s.rate_per_8_bars: max %.2f exceeds the risk %d cap of %d per 8 bars"
                          % (rule["id"], rule["rate_per_8_bars"]["max"], rule["risk"], cap))
        if rule["rate_per_8_bars"]["min"] > rule["rate_per_8_bars"]["max"]:
            errors.append("rules.%s.rate_per_8_bars: min above max" % rule["id"])
    total_min = sum(rule["rate_per_8_bars"]["min"] for rule in rules)
    if total_min <= 0:
        errors.append("%s.rules: no device has a positive minimum rate, so nothing would ever fire" % JSON_REL)
    if math.isclose(policy["devices_per_8_bars_min"], 0.0):
        errors.append("%s.rate_policy: the minimum devices per 8 bars is zero" % JSON_REL)

    # C6 dashes
    for path in (json_path, schema_path, md_path):
        text = read_text(path)
        rel = os.path.relpath(path, root).replace("\\", "/")
        for dash in LONG_DASHES:
            if dash in text:
                index = text.index(dash)
                line = text.count("\n", 0, index) + 1
                errors.append("%s:%d: contains a long dash character U+%04X" % (rel, line, ord(dash)))

    # C7 the markdown carries the same catalogue
    md = read_text(md_path)
    for device_id in expected:
        if device_id not in md:
            errors.append("%s: does not name %s" % (MD_REL, device_id))
    for forbidden_id in sorted(forbidden_ids):
        if forbidden_id not in md:
            errors.append("%s: does not name forbidden rule %s" % (MD_REL, forbidden_id))
    for phrase in ("preparation", "resolution", "risk level", "rate target", "injector"):
        if phrase not in md.lower():
            errors.append("%s: does not discuss %r" % (MD_REL, phrase))

    # C8 every device names its preparation and its resolution (card t_aa3ab04e)
    errors.extend(check_preparations(data))

    # C9 the injector refuses a device whose rule names neither
    errors.extend(check_injector_refuses(data))

    print("check_dissonance_rules: %d devices, %d forbidden rules, %d local sources, %d known sources, "
          "schema engine %s" % (len(rules), len(forbidden_ids), len(local_sources), len(known_sources), engine))
    return errors


def check_preparations(data):
    """C8: a device that cannot say how the ear is made ready for it is not a device, it is a stab."""
    errors = []
    for rule in data["rules"]:
        path = "rules.%s" % rule["id"]
        preparation = rule.get("preparation")
        if not isinstance(preparation, dict):
            errors.append("%s.preparation: missing, so the device cannot say how it is prepared"
                          % path)
        else:
            for field in ("kind", "requires", "verdict_if_missing"):
                if field not in preparation:
                    errors.append("%s.preparation: missing %r" % (path, field))
            kinds = ("held_chord_tone", "previous_chord_member", "step_from_consonance",
                     "bass_step_approach", "scale_approach", "none_needed")
            if preparation.get("kind") not in kinds:
                errors.append("%s.preparation.kind: %r is not one of %s"
                              % (path, preparation.get("kind"), ", ".join(kinds)))
            if len(str(preparation.get("requires") or "").strip()) < 20:
                errors.append("%s.preparation.requires: too short to say what must sound first, "
                              "or why nothing is owed" % path)
            if preparation.get("verdict_if_missing") not in ("reject", "warn"):
                errors.append("%s.preparation.verdict_if_missing: %r"
                              % (path, preparation.get("verdict_if_missing")))
        resolution = rule.get("resolution") or {}
        if not str(resolution.get("target") or "").strip():
            errors.append("%s.resolution.target: empty, so the device owes nothing in particular"
                          % path)
    return errors


def check_injector_refuses(data):
    """C9: the injector's own gate accepts every device it writes, and refuses a stripped rule."""
    import copy

    try:
        import spice
    except (ImportError, AttributeError) as error:  # noqa: BLE001 - reported, never skipped
        return ["tools/spice.py: the injector could not be loaded, so its refusal is unproven: %s"
                % error]
    errors = []
    allowed, refused = spice.device_gate(data)
    for device in sorted(refused):
        errors.append("tools/spice.py: the injector refuses %s, %s. Every device it writes needs a "
                      "preparation and a resolution in this file" % (device, refused[device]))
    for device in sorted(spice.DEVICE_RULES):
        if device not in allowed and device not in refused:
            errors.append("tools/spice.py: %s is in DEVICE_RULES and the gate says nothing about it"
                          % device)
    # The refusal has to be exercised, not just declared: strip one accepted device's rule of both
    # blocks and require that the injector now refuses it.
    probe = copy.deepcopy(data)
    picked = next((name for name in sorted(allowed) if name in spice.DEVICE_RULES), None)
    if picked:
        rule_id = spice.DEVICE_RULES[picked][0]
        for rule in probe["rules"]:
            if rule["id"] == rule_id:
                rule.pop("preparation", None)
                rule.pop("resolution", None)
        _allowed, refused_probe = spice.device_gate(probe)
        if picked not in refused_probe:
            errors.append("tools/spice.py: the injector would still write %s after its rule lost "
                          "both its preparation and its resolution" % picked)
    elif allowed:
        errors.append("tools/spice.py: no accepted device matched DEVICE_RULES, so the refusal "
                      "could not be exercised")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = parser.parse_args()

    errors = check(args.root)
    if errors:
        for line in errors[:60]:
            print("FAIL " + line)
        if len(errors) > 60:
            print("... and %d more" % (len(errors) - 60))
        print("\n%d dissonance rule problem(s)" % len(errors))
        return 1
    print("check_dissonance_rules: 30 devices, every rule resolves, every reference exists, no long dash")
    return 0


if __name__ == "__main__":
    sys.exit(main())

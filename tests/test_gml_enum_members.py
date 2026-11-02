"""Every enum member the GML names must be defined by an enum in the GML.

Why this file exists (2026-11-01): HEAD cb6fcf63 did not compile because pp_app.gml and pp_overworld.gml used
PPMode.talk_persona while only an uncommitted pp_config.gml defined it (Igor: enum reference 'talk_persona' does not exist
in 'PPMode'). test_gml_calls_only_defined_pp_functions checks calls, not enum members, so nothing caught it before the
public repo carried a build that cannot compile. This test reads the committed GML only, so it fails on a checkout that
is missing the enum, with no compiler needed.
"""
import re
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
GAME = PP / "game"

ENUM_RX = re.compile(r"\benum\s+(PP[A-Za-z0-9_]*)\s*\{(.*?)\}", re.S)
REF_RX = re.compile(r"\b(PP[A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b")
COMMENT_RX = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
STRING_RX = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def gml_files():
    for path in sorted(GAME.rglob("*.gml")):
        if "datafiles" in path.parts or "node_modules" in path.parts:
            continue
        yield path


def strip(text):
    """Comments and string literals removed, so a word in prose or a message is never read as a reference."""
    return STRING_RX.sub('""', COMMENT_RX.sub("", text))


def defined_enums():
    enums = {}
    for path in gml_files():
        body = strip(path.read_text(encoding="utf-8", errors="replace"))
        for match in ENUM_RX.finditer(body):
            members = set()
            for item in match.group(2).split(","):
                name = item.split("=", 1)[0].strip()
                if name:
                    members.add(name)
            enums.setdefault(match.group(1), set()).update(members)
    return enums


def test_the_enums_are_found():
    enums = defined_enums()
    assert "PPMode" in enums and "overworld" in enums["PPMode"], "the scan did not find PPMode in pp_config.gml"
    assert len(enums) >= 3, "expected several PP enums, found %s" % sorted(enums)


def test_every_enum_member_the_gml_names_is_defined():
    enums = defined_enums()
    missing = []
    for path in gml_files():
        body = strip(path.read_text(encoding="utf-8", errors="replace"))
        for number, line in enumerate(body.splitlines(), 1):
            for match in REF_RX.finditer(line):
                enum, member = match.group(1), match.group(2)
                if enum in enums and member not in enums[enum]:
                    missing.append("%s:%d %s.%s" % (path.relative_to(PP).as_posix(), number, enum, member))
    assert not missing, "enum members used but not defined (the build would fail): " + "; ".join(missing[:12])

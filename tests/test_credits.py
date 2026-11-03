"""The credits roll (card CREDITS): data parses, fits the font, both variants run, the GML door and log lines exist."""
import filecmp
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import check_credits  # noqa: E402

GML = os.path.join(ROOT, "game", "scripts", "pp_credits", "pp_credits.gml")


def gml():
    with open(GML, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def test_credits_data_checks_clean():
    assert check_credits.check() == []


def test_both_variants_lay_out_and_end():
    data = check_credits.load()
    for variant in ("spare", "kill"):
        rows, height = check_credits.layout(data, variant)
        end, total = check_credits.timing(data, variant)
        assert rows[0][1] == "PRIMORDIAL PARADOX" and rows[-1][1] == "THANK YOU FOR PLAYING"
        assert 0 < end < height + check_credits.FRAME_H and total > 0


def test_the_variants_differ_only_in_the_closing_and_the_cue():
    data = check_credits.load()["roll"]["variants"]
    assert data["spare"]["closing"] != data["kill"]["closing"]
    assert data["spare"]["music_cue"] != data["kill"]["music_cue"]


def test_the_licence_notices_still_travel_in_the_file():
    data = check_credits.load()
    ids = {row["id"] for row in data["licences"]}
    assert {"ofl_pressstart2p", "odbl_openstreetmap"} <= ids
    assert "openstreetmap.org/copyright" in open(check_credits.CREDITS, encoding="utf-8").read()


def test_the_build_copy_matches_the_data():
    assert filecmp.cmp(check_credits.CREDITS, os.path.join(ROOT, "game", "datafiles", "credits.json"), shallow=False)


def test_the_gml_door_and_the_contract_log_lines():
    code = gml()
    assert "function pp_credits_start(_variant)" in code
    assert 'show_debug_message("PP: credits start spare")' in code
    assert 'show_debug_message("PP: credits start kill")' in code
    assert "pp_app_request(PPMode.credits" in code
    assert "pp_app_enter_room(PPMode.title, {}, rm_pp_title)" in code
    assert re.search(r"credits = 7", open(os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml")).read())


def test_the_gml_reads_no_key_and_no_colour_literal():
    code = "\n".join(line.split("//")[0] for line in gml().splitlines())
    assert not re.search(r"keyboard_check|gamepad_button_check|\bc_[a-z]+\b|make_colou?r_rgb|draw_text", code)


def test_the_skip_is_the_held_cancel_action():
    code = gml()
    assert 'pp_action("cancel")' in code and "PP_CREDITS_SKIP_HOLD" in code

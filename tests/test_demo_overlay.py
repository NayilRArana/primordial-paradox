"""The S5 overlay, measured: the bake row is in the pixels, and the words are the file's own.

What these tests hold down, and why each one earns its place:
  1. THE WORDS ARE NOT TYPED HERE. Every model, time, mode and hash drawn on screen is read back out of
     the bake file at test time and compared with what the tool put in the line. A rename or a re-bake
     that changes those values changes the drawing, and a value the file does not hold cannot appear;
  2. A MISSING ROW OR FIELD STOPS THE SHOT. Section 4 rule 1 of knowledge/DEMO-SCRIPT.md says a row that
     is missing means the shot is not recordable, so the four ways a row can be wrong are all refused
     rather than drawn;
  3. A FALLBACK ROW IS NOT A RECEIPT. fight/morgan/1 to 3 are hand written fallbacks in the bake file as
     it stands, so the plate for the shot's three receipt windows cannot be drawn at all today, and the
     tool says which row stopped it. That is the shipped state, not a test fixture: see test 3b, which
     asks the real file and passes in either state;
  4. THE FRAME TEST FINDS THE ROW. `check_frame` is run on a real render of the shot and every check it
     makes has to pass: plate pixels, ink on each bake line, far less ink when the lines are blanked,
     no ink outside a line box, and a badge;
  5. THE TEXT BOXES STAY THE GAME'S OWN PIXELS. The dialogue box at (8, 168) 240x64 is compared byte for
     byte against the source frame, and the plate is asked to refuse a layout that would touch it;
  6. THE DEAD BADGE IS ONLY DRAWN WHEN THE FILE SAYS DEAD, and the network line says the same thing the
     file's own `offline` and `network` fields say, in both states;
  7. THE NES TALK BOX IS THE RECORD AND NOTHING ELSE. Its reply lines are the bake row's own `text`, its
     verdict is the judge map's word for that row's effect, and the id it prints is looked up in
     data/receipts/meta_receipts.jsonl, so a row whose verdict receipt was never logged refuses rather
     than printing a made up id. On the rewritten S5 the box has nothing it can honestly draw: the three
     Morgan rows are fallback, and none of them has a logged verdict receipt. Tests 7a and 7b pin both
     refusals; the box's own line building is still measured on synthetic rows.

What this module no longer covers, and why: S6 draws nothing. The rewrite moved the fight shot to
Percy's encounter, which carries no `talk` block, so no bake row answers in it and the six `fight/percy`
rows are never read (knowledge/DEMO-SCRIPT.md section 4). The S6 plate, the S6 talk box and their frame
tests went with the shot table that named the deck watch.

Run: python -m pytest tests/test_demo_overlay.py -q
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os

import pytest

from PIL import Image, ImageChops, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
SCRIPT = os.path.join(ROOT, "knowledge", "DEMO-SCRIPT.md")
BAKE = os.path.join(ROOT, "data", "meta_bake.json")
LONG_DASHES = ("\u2014", "\u2013", "\u2012", "\u2015")
TALK_ROWS = ("fight/morgan/1", "fight/morgan/2", "fight/morgan/3")


def load_tool(name: str):
    path = os.path.join(TOOLS, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def overlay():
    return load_tool("demo_overlay")


def real_bake():
    with open(BAKE, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def script_text():
    with open(SCRIPT, "r", encoding="utf-8") as handle:
        return handle.read()


def write_bake(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1)
    return path


@pytest.fixture()
def live_bake_file(tmp_path, overlay):
    """The real bake file, with the three TALK rows marked live, in a throwaway directory.

    This is a test fixture and it never touches data/meta_bake.json: it exists so the S6 drawing and the
    frame test can be measured on a bake that holds three live answers. The tool's own refusal of a
    fallback row is pinned separately, against the file's real state.
    """
    data = copy.deepcopy(real_bake())
    for row in data["rows"]:
        if row["id"] in TALK_ROWS:
            row["source"] = "live"
            row["network"] = True
            row["reason"] = ""
    # The header is set to match the rows this fixture just made live. It used to be inherited from
    # the committed file, which only worked while that file happened to be a live, networked bake;
    # the card t_2c698fe6 rebake is a replay read from data/ai_cache (network false), so the fixture
    # now states its own header the way the offline fixture below already does.
    data["bake"]["mode"] = "live"
    data["bake"]["offline"] = False
    data["bake"]["network"] = True
    return write_bake(tmp_path / "live_bake.json", data)


@pytest.fixture()
def offline_bake_file(tmp_path, live_bake_file, overlay):
    data = real_bake()
    for row in data["rows"]:
        if row["id"] in TALK_ROWS:
            row["source"] = "live"
            row["network"] = True
            row["reason"] = ""
    data["bake"]["offline"] = True
    data["bake"]["network"] = False
    return write_bake(tmp_path / "offline_bake.json", data)


@pytest.fixture()
def frame_file(tmp_path, overlay):
    """A 768x720 frame with a few blocks of colour, so a plate drawn on it is measurable."""
    image = Image.new("RGB", (overlay.FRAME_W, overlay.FRAME_H), (26, 111, 130))
    draw = ImageDraw.Draw(image)
    for step in range(12):
        draw.rectangle((8, 20 + step * 40, 760, 40 + step * 40), fill=(13, 43, 58))
        draw.rectangle((40 + step * 56, 60 + step * 40, 60 + step * 56, 90 + step * 40), fill=(216, 165, 92))
    path = tmp_path / "frame.png"
    image.save(path)
    return str(path)


def render_shot(overlay, shot, bake_path, frame_path, out_path, **kwargs):
    bake, index = overlay.load_bake(bake_path)
    image, layout = overlay.render(frame_path, shot, bake, index, **kwargs)
    image.save(out_path)
    return layout


# 1. The words are the file's own


def test_caption_is_read_from_the_script(overlay):
    text = script_text()
    for shot in ("S5", "S6"):
        caption = overlay.shot_caption(shot)
        assert caption in text, "the %s caption the tool draws is not in DEMO-SCRIPT.md" % shot
        assert overlay.shot_caption(shot) == caption


def test_every_drawn_value_comes_out_of_the_bake_file(overlay, live_bake_file):
    bake, index = overlay.load_bake(live_bake_file)
    block = bake["bake"]
    hashes = {row["request_hash"] for row in bake["rows"]}
    for shot in ("S5",):
        lines = overlay.overlay_lines(shot, bake, index)
        text = "\n".join(line for _, line in lines)
        assert block["model"] in text, "%s does not print the model the file records" % shot
        assert block["created_at"] in text, "%s does not print the time the file records" % shot
        assert "MODE %s" % block["mode"] in text
        printed = [line.split(" ", 1)[1] for tier, line in lines if tier == "hash"]
        for line in printed:
            value = line.split(" ", 1)[1] if line.startswith(("T1", "T2", "T3")) else line.replace("HASH ", "")
            assert value in hashes, "the drawn hash %r is not a request_hash in the bake file" % value


def test_no_long_dash_in_any_drawn_line_or_in_the_tool(overlay, live_bake_file):
    bake, index = overlay.load_bake(live_bake_file)
    for shot in ("S5",):
        for _, text in overlay.overlay_lines(shot, bake, index):
            for dash in LONG_DASHES:
                assert dash not in text
    with open(os.path.join(TOOLS, "demo_overlay.py"), "r", encoding="utf-8") as handle:
        source = handle.read()
    for dash in LONG_DASHES:
        assert dash not in source, "tools/demo_overlay.py carries a long dash"


# 2. A missing row or field stops the shot


def test_a_row_the_file_does_not_hold_is_refused(overlay, tmp_path):
    data = real_bake()
    data["rows"] = [row for row in data["rows"] if row["id"] != "fight/morgan/1"]
    path = write_bake(tmp_path / "no_morgan.json", data)
    bake, index = overlay.load_bake(path)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.overlay_lines("S5", bake, index)
    assert "fight/morgan/1" in str(error.value)


@pytest.mark.parametrize("field", ("model", "created_at", "request_hash", "source", "network"))
def test_a_row_field_that_is_missing_is_refused(overlay, tmp_path, field):
    data = real_bake()
    for row in data["rows"]:
        if row["id"] == "fight/morgan/1":
            row.pop(field, None)
    path = write_bake(tmp_path / ("no_%s.json" % field), data)
    bake, index = overlay.load_bake(path)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.overlay_lines("S5", bake, index)
    assert field in str(error.value)


def test_a_bake_with_no_bake_block_is_refused(overlay, tmp_path):
    data = real_bake()
    data.pop("bake", None)
    path = write_bake(tmp_path / "no_block.json", data)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.load_bake(path)
    assert "bake block" in str(error.value)


# 3. A fallback row is not a receipt


def test_a_fallback_row_is_refused_unless_it_is_labelled(overlay):
    """The shipped state, asked of the real file: the Morgan rows are fallback, so the plate refuses.

    `allow_fallback` still draws one, and the label's exact words are pinned here: a fallback drawn as
    a bare receipt would claim a model answered, and a labelled one says what it is.
    """
    bake, index = overlay.load_bake(BAKE)
    fallback = [row["id"] for row in bake["rows"]
                if row["id"] in TALK_ROWS and (row["source"] != "live" or row["network"] is not True)]
    if fallback:
        with pytest.raises(overlay.OverlayError) as error:
            overlay.overlay_lines("S5", bake, index)
        assert "not a live Meta answer" in str(error.value)
        assert fallback[0] in str(error.value)
    lines = overlay.overlay_lines("S5", bake, index, allow_fallback=True, rows=("fight/morgan/1",))
    text = "\n".join(line for _, line in lines)
    assert "ROW fight/morgan/1 IS SOURCE fallback, NOT A LIVE ANSWER" in text


def test_the_real_bake_file_is_asked_for_a_live_answer_on_the_talk_shot(overlay):
    """S5 draws its plate only if the file holds live answers for Morgan's three TALK rows.

    This is the honest state check: if the current bake has a fallback row, the tool must refuse and
    the reason must name that row. When the bake is redone with live answers (Q1) the same call renders,
    so the test asserts the behaviour and the file's own values, not one fixed outcome.
    """
    bake, index = overlay.load_bake(BAKE)
    live = [row["id"] for row in bake["rows"] if row["id"] in TALK_ROWS and row["source"] == "live" and row["network"] is True]
    if len(live) == len(TALK_ROWS):
        lines = overlay.overlay_lines("S5", bake, index, rows=("fight/morgan/1",))
        assert any(tier == "hash" for tier, _ in lines)
        assert any(tier == "badge" for tier, _ in lines)
    else:
        with pytest.raises(overlay.OverlayError) as error:
            overlay.overlay_lines("S5", bake, index)
        assert "not a live Meta answer" in str(error.value)


# 4 and 5. The frame test, and the text boxes


def test_s5_frame_test_passes_and_the_dialogue_box_is_untouched(overlay, live_bake_file, frame_file, tmp_path):
    out = str(tmp_path / "s5.png")
    rows = ("fight/morgan/1",)
    layout = render_shot(overlay, "S5", live_bake_file, frame_file, out, rows=rows)
    bake, index = overlay.load_bake(live_bake_file)
    report = overlay.check_frame(frame_file, out, "S5", bake, index, rows=rows)
    assert report["ok"], [item for item in report["checks"] if not item["ok"]]
    source = Image.open(frame_file).convert("RGB")
    rendered = Image.open(out).convert("RGB")
    box = overlay.scale_rect(overlay.DIALOGUE_BOX)
    assert ImageChops.difference(source.crop(box), rendered.crop(box)).getbbox() is None
    assert not overlay.intersects(layout["plate"], box)
    inked = [item for item in report["checks"] if item["name"].startswith("ink on the bake line")]
    assert len(inked) == 6, ("one reply's window draws six bake lines: model, time, row, source, hash, "
                             "and the line that says where the replies came from")



def test_a_receipt_window_carries_its_own_row_and_no_other(overlay, live_bake_file):
    """Each of the three clocks draws its own row, which is what makes three windows three receipts."""
    bake, index = overlay.load_bake(live_bake_file)
    hashes = {}
    for row_id in TALK_ROWS:
        lines = overlay.overlay_lines("S5", bake, index, rows=(row_id,))
        texts = [text for _, text in lines]
        assert any(text.startswith("ROW %s " % row_id) for text in texts), row_id
        hashes[row_id] = [text for text in texts if text.startswith("HASH ")]
        others = [other for other in TALK_ROWS if other != row_id]
        for other in others:
            assert not any(other in text for text in texts), "one window printed another row"
    found = [values[0] for values in hashes.values()]
    assert len(set(found)) == len(found), "three windows, three different hashes"


def test_a_plate_that_would_cover_a_text_box_is_refused(overlay):
    tall = [overlay.line_height("detail")] * 60
    with pytest.raises(overlay.OverlayError) as error:
        overlay.plate_rect("S5", tall, below=False)
    assert "does not fit" in str(error.value) or "would cover" in str(error.value)


def test_a_frame_that_is_not_the_three_x_screen_is_refused(overlay, tmp_path):
    small = Image.new("RGB", (256, 240), (0, 0, 0))
    path = str(tmp_path / "small.png")
    small.save(path)
    bake, index = overlay.load_bake(BAKE)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.render(path, "S5", bake, index)
    assert "768x720" in str(error.value)


# 6. The network line follows the file


def test_the_badge_and_the_network_line_follow_the_file(overlay, live_bake_file, offline_bake_file, frame_file, tmp_path):
    live_bake, live_index = overlay.load_bake(live_bake_file)
    offline_bake, offline_index = overlay.load_bake(offline_bake_file)
    # The network window carries no bake row: its words come from the file's own two flags.
    live_lines = overlay.overlay_lines("S5", live_bake, live_index, rows=())
    offline_lines = overlay.overlay_lines("S5", offline_bake, offline_index, rows=())
    live_text = " ".join(text for _, text in live_lines)
    offline_text = " ".join(text for _, text in offline_lines)
    assert "NETWORK LIVE" in live_text and "NETWORK OFF" not in live_text
    assert "NETWORK OFF" in offline_text and "NETWORK LIVE" not in offline_text
    assert "NETWORK UP AT BAKE TIME." in live_text
    assert "NETWORK DEAD SINCE THE FIRST FRAME." in offline_text
    assert not any(tier == "hash" for tier, _ in live_lines), "the network window draws no receipt"

    colours = overlay.load_palette()
    live_out = str(tmp_path / "live.png")
    offline_out = str(tmp_path / "offline.png")
    live_layout = render_shot(overlay, "S5", live_bake_file, frame_file, live_out, rows=())
    offline_layout = render_shot(overlay, "S5", offline_bake_file, frame_file, offline_out, rows=())
    live_image = Image.open(live_out).convert("RGB")
    offline_image = Image.open(offline_out).convert("RGB")
    assert overlay.count_colour(live_image, live_layout["badge"]["rect"], colours["warn"]) > 100
    assert overlay.count_colour(live_image, live_layout["badge"]["rect"], colours["hazard"]) == 0
    assert overlay.count_colour(offline_image, offline_layout["badge"]["rect"], colours["hazard"]) > 100


def test_the_runs_below_the_frame_leave_the_frame_alone(overlay, live_bake_file, frame_file, tmp_path):
    out = str(tmp_path / "below.png")
    render_shot(overlay, "S5", live_bake_file, frame_file, out, below=True, rows=("fight/morgan/1",))
    source = Image.open(frame_file).convert("RGB")
    rendered = Image.open(out).convert("RGB")

    assert rendered.size[0] == overlay.FRAME_W
    assert rendered.size[1] > overlay.FRAME_H
    top = rendered.crop((0, 0, overlay.FRAME_W, overlay.FRAME_H))
    assert ImageChops.difference(source, top).getbbox() is None


# The clocks


def test_the_clocks_match_the_script(overlay):
    """The rewrite moved the receipt and network clocks; this pins the tool to the script's own words."""
    text = script_text()
    assert "1:23.4 to 1:27.4" in text
    assert "1:31.0 to 1:35.0" in text
    assert "1:38.0 to 1:41.0" in text
    assert "1:41.00 to 1:44.00" in text
    assert overlay.SHOT_WINDOWS["S5"]["bake"] == ((83.4, 87.4), (91.0, 95.0), (98.0, 101.0))
    assert overlay.SHOT_WINDOWS["S5"]["network"] == ((101.0, 104.0),)
    assert "S6" not in overlay.SHOT_WINDOWS, "Percy's fight reads no bake, so S6 has no overlay clock"
    assert "S6" not in overlay.SHOT_ROWS, "and no row to draw"
    assert overlay.SHOT_ROWS["S5"] == ("fight/morgan/1", "fight/morgan/2", "fight/morgan/3")



def test_the_cli_prints_the_rows_and_exits_zero(overlay, capsys):
    # The real file's Morgan rows are fallback, so the CLI needs the labelled path to print them.
    assert overlay.main(["--shot", "S5", "--rows", "--allow-fallback"]) == 0
    printed = capsys.readouterr().out
    payload = json.loads(printed)
    assert payload["shot"] == "S5"
    assert payload["rows"] == list(overlay.SHOT_ROWS["S5"])
    assert any(line["tier"] == "hash" for line in payload["lines"])
    assert any("NOT A LIVE ANSWER" in line["text"] for line in payload["lines"])


def test_the_cli_refuses_the_plate_the_script_says_is_not_recordable(overlay, capsys):
    """The shipped state: `--rows` without the label refuses, and says which row stopped it."""
    assert overlay.main(["--shot", "S5", "--rows"]) == 1
    printed = capsys.readouterr().out
    assert "REFUSED" in printed and "fight/morgan/1" in printed


def test_the_cli_prints_the_network_window_with_no_row(overlay, capsys):
    assert overlay.main(["--shot", "S5", "--rows", "--only", ""]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["rows"] == []
    text = " ".join(line["text"] for line in payload["lines"])
    assert "NETWORK OFF" in text
    assert not any(line["tier"] == "hash" for line in payload["lines"])


# 7. The NES talk box: the row's words, its verdict, and the receipt that backs it
#
# The box draws a judging record, and everything in it is the record's own: the line the player typed, the
# reply the model sent back, the verdict the effect table gives, and the id of the receipt that backs all
# three. Since card t_892cc851 moved S5 to Captain Morgan's three `fight` rows, data/meta_bake.json holds
# neither a live answer nor a logged verdict receipt for them, so the box refuses in the shipped state and
# both refusals are pinned here. The box's own drawing is measured on a row the ledger does hold, patched
# into S5's row list for the length of the test: that measures the contract, not the shipped picture.

# The box's contract is measured on fight/navy_sailor/1: the real file holds it as a live answer and the
# ledger holds its verdict receipt, so the box can be drawn and measured. It is borrowed into S5's row list
# for the length of a test and is never what the cut ships: S5's own rows (Morgan's) have no live answer yet.
BOX_ROW = "fight/navy_sailor/1"



def borrowed_box_row(overlay, monkeypatch):
    """Point S5's row list at a row the ledger holds, so the box's contract can be measured."""
    monkeypatch.setitem(overlay.SHOT_ROWS, "S5", (BOX_ROW,))
    return BOX_ROW


def test_the_shipped_state_draws_no_box_because_the_row_is_not_a_live_answer(overlay):
    bake, index = overlay.load_bake(BAKE)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.plan("S5", bake, index, talk_box=True)
    assert "not a live Meta answer" in str(error.value)
    assert "fight/morgan/1" in str(error.value)


def test_the_box_refuses_a_row_with_no_logged_receipt(overlay, live_bake_file, monkeypatch):
    """A live row is step one; step two is a receipt in the ledger, and the refusal names the fix."""
    borrowed_box_row(overlay, monkeypatch)
    bake, index = overlay.load_bake(live_bake_file)
    monkeypatch.setattr(overlay, "load_ledger", lambda *args, **kwargs: {})
    with pytest.raises(overlay.OverlayError) as error:
        overlay.plan("S5", bake, index, talk_box=True)
    assert "tools\\receipts.py --row %s" % BOX_ROW in str(error.value)


def test_the_box_draws_the_rows_own_words_verdict_and_receipt(overlay, live_bake_file, monkeypatch):
    row_id = borrowed_box_row(overlay, monkeypatch)
    bake, index = overlay.load_bake(live_bake_file)
    layout = overlay.plan("S5", bake, index, talk_box=True)
    talk = layout["talk_box"]
    row = [item for item in bake["rows"] if item["id"] == row_id][0]
    verdicts = overlay.load_verdicts()
    entry = verdicts[row["effect"]]
    texts = [line["source_text"] for line in talk["lines"]]
    assert texts[1] == row["player_line"], "the box prints the line the player typed, as recorded"
    assert texts[2:2 + len(row["text"])] == row["text"], "and then the row's own reply lines"
    assert texts[2 + len(row["text"])] == "VERDICT %s, WILL %s%s" % (
        entry["verdict"].upper(), "+" if entry["will_delta"] > 0 else "", entry["will_delta"])
    assert talk["verdict"] == entry["verdict"]
    assert talk["receipt"] in overlay.load_ledger(), "the id the box prints is a logged receipt"
    assert any(talk["receipt"] in piece for piece in texts)
    assert not any("NOT A LIVE ANSWER" in piece for piece in texts), "an unlabelled draw claims a live answer"



def test_a_verdict_whose_receipt_is_not_logged_is_refused(overlay):
    with pytest.raises(overlay.OverlayError) as error:
        overlay.row_receipt_id({"id": BOX_ROW}, ledger={})
    assert "tools\\receipts.py --row %s" % BOX_ROW in str(error.value)


def test_the_talk_box_refuses_a_row_the_verdict_map_does_not_hold(overlay):
    verdicts = overlay.load_verdicts()
    row = {"id": "x/y/1", "text": ["ONE LINE."], "effect": "tickle", "source": "live", "network": True}
    with pytest.raises(overlay.OverlayError) as error:
        overlay.talk_box_lines("S5", row, verdicts, "rcpt-0000000000000000")
    assert "no entry" in str(error.value)


def test_the_talk_box_labels_a_fallback_row_and_refuses_it_unlabelled(overlay):
    verdicts = overlay.load_verdicts()
    row = {"id": "x/y/1", "text": ["ONE LINE."], "effect": "none", "source": "fallback", "network": False}
    with pytest.raises(overlay.OverlayError) as error:
        overlay.talk_box_lines("S5", row, verdicts, "rcpt-0000000000000000")
    assert "not a live answer" in str(error.value)
    lines = overlay.talk_box_lines("S5", row, verdicts, "rcpt-0000000000000000", allow_fallback=True)
    texts = [piece for _tier, piece, _role in lines]
    assert "FALLBACK, NOT A LIVE ANSWER" in texts
    assert texts[-1].endswith("FALLBACK")


def test_the_talk_box_is_refused_on_a_shot_whose_claim_is_not_the_box(overlay, monkeypatch):
    """A shot draws the box only if the box is what that shot claims to show.

    Card t_892cc851 leaves one such shot, S5, so the test sets the list to a different shot and asks S5:
    it must refuse and say which shots it will draw.
    """
    verdicts = overlay.load_verdicts()
    row = {"id": "x/y/1", "text": ["ONE LINE."], "effect": "none", "source": "live", "network": True}
    monkeypatch.setattr(overlay, "TALK_BOX_SHOTS", ("S6",))
    with pytest.raises(overlay.OverlayError) as error:
        overlay.talk_box_lines("S5", row, verdicts, "rcpt-0000000000000000")
    assert "S6" in str(error.value)
    monkeypatch.undo()
    assert overlay.TALK_BOX_SHOTS == ("S5",), "the shot that draws the box is the one whose claim it is"


def test_a_system_prompt_that_two_sources_disagree_on_is_refused(overlay, monkeypatch, tmp_path):
    borrowed_box_row(overlay, monkeypatch)
    data = real_bake()
    for row in data["rows"]:
        if row["id"] == BOX_ROW:
            row["request"]["system_chars"] = 2407
    path = write_bake(tmp_path / "mismatch.json", data)
    bake, index = overlay.load_bake(path)
    with pytest.raises(overlay.OverlayError) as error:
        overlay.plan("S5", bake, index, talk_box=True)
    assert "do not describe one prompt" in str(error.value)



def test_a_ledger_receipt_for_another_number_is_refused(overlay):
    with pytest.raises(overlay.OverlayError) as error:
        overlay.ledger_number("meta.model_calls", 22)
    assert "do not back the same number" in str(error.value)
    with pytest.raises(overlay.OverlayError) as missing:
        overlay.ledger_number("meta.no_such_number", 1)
    assert "holds no" in str(missing.value)


def test_the_box_frame_test_passes_and_the_dialogue_box_is_untouched(overlay, monkeypatch, live_bake_file, frame_file, tmp_path):
    row_id = borrowed_box_row(overlay, monkeypatch)
    out = str(tmp_path / "box.png")
    render_shot(overlay, "S5", live_bake_file, frame_file, out, talk_box=True)
    bake, index = overlay.load_bake(live_bake_file)
    report = overlay.check_frame(frame_file, out, "S5", bake, index, talk_box=True)
    assert report["ok"], [item for item in report["checks"] if not item["ok"]]
    source = Image.open(frame_file).convert("RGB")
    rendered = Image.open(out).convert("RGB")
    dialogue = overlay.scale_rect(overlay.DIALOGUE_BOX)
    assert ImageChops.difference(source.crop(dialogue), rendered.crop(dialogue)).getbbox() is None
    assert report["talk_box"] is not None
    assert report["talk_box"]["row"] == row_id
    assert not overlay.intersects(report["talk_box"]["rect"], dialogue)
    assert not overlay.intersects(report["talk_box"]["rect"], report["plate"])
    named = [item["name"] for item in report["checks"]]
    assert any(name.startswith("ink on the box line") for name in named)
    assert any(name.startswith("the receipt id is printed") for name in named)
    assert "no box text outside the lines' reserved band" in named


def test_every_box_line_fits_the_window_and_the_band(overlay, monkeypatch, live_bake_file):
    row_id = borrowed_box_row(overlay, monkeypatch)
    bake, index = overlay.load_bake(live_bake_file)
    layout = overlay.plan("S5", bake, index, talk_box=True)
    talk = layout["talk_box"]
    row = [item for item in bake["rows"] if item["id"] == row_id][0]
    # The 28 column rule is the NES box's rule and it is held to the words the player and Nye say: the
    # reply lines and the player's own line. The receipt lines are the small print under them, held to the
    # width of the window in pixels instead.
    columns = [line["source_text"] for line in talk["lines"]
               if line["source_text"] == row["player_line"] or line["source_text"] in row["text"]]
    assert columns, "the player's line and the reply are in the box"
    for piece in columns:
        assert len(piece) <= overlay.TALK_COLS, piece
    usable = overlay.TALK_BOX_W * overlay.SCALE - 2 * overlay.PLATE_PAD
    for line in talk["lines"]:
        assert len(line["source_text"]) * line["size"] <= usable, line["source_text"]
    rect = talk["rect"]
    assert rect[0] >= 0 and rect[2] <= overlay.FRAME_W
    assert not overlay.intersects(rect, layout["plate"]), "the box is stacked, never on the plate"


def test_the_talk_box_cli_refuses_in_the_shipped_state_and_says_which_row(overlay, capsys):
    assert overlay.main(["--shot", "S5", "--rows", "--talk-box"]) == 1
    printed = capsys.readouterr().out
    assert "REFUSED" in printed
    assert "fight/morgan/1" in printed and "not a live Meta answer" in printed


def test_the_talk_box_cli_prints_the_box_and_exits_zero(overlay, monkeypatch, live_bake_file, capsys):
    borrowed_box_row(overlay, monkeypatch)
    assert overlay.main(["--shot", "S5", "--rows", "--talk-box", "--bake", str(live_bake_file)]) == 0
    payload = json.loads(capsys.readouterr().out)
    talk = payload["talk_box"]
    assert talk["receipt"] in overlay.load_ledger()
    verdicts = overlay.load_verdicts()
    assert talk["verdict"] in [entry["verdict"] for entry in verdicts.values()]
    assert any(talk["receipt"] in line["text"] for line in talk["lines"])

"""The rules of knowledge/MAP-STYLE-GUIDE.md that a script can check, on the Town Quay v2 room (card LD-4, 2026-10-27).

What a script cannot settle (hue, value, whether it looks designed) is judged on the renders in
output/level_pass_2026-10-27/v2 and recorded in that folder's PROGRESS.md (Part E, 15 questions). This file pins the rest:

  buildings   rectangle or L, 3 to 9 wide, 4 to 6 deep (one 3 x 8 tower), roof over wall, one door group on the bottom row,
              a free reachable 2 x 2 apron under every door
  streets     the arrival street 4 wide, the north lane 3 wide, the gate passage and the alleys 4 wide, each constant;
              no 1 tile pinch except door niches
  runs        B6: wall 4, roof 6, paving 8, freestanding props 2, fence series 8, water 8 in a row
  density     B6: building share 10 to 25 percent, walkable 35 to 60 percent of the room and 45 to 65 percent of the dry land,
              banded core > working quay > waterfront
  shore       one straight quay wall face of 8 or more, bollards on the coping, openings only for steps and the pier
  pier        3 planks wide, 8 rows, rails both sides, bollard pairs, lamp pair at the head, gangway to the ship
  edges       no walkable tile on the map edge except the 4 wide arrival street; the anchors of the brief are all present

Sources: data/maps/all.json (committed room), tools/quay_town_layout.txt (the design), tools/make_quay_town.py.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_quay_town as mq  # noqa: E402
import map_audit as audit  # noqa: E402

PAVING = set(":,;")


@pytest.fixture(scope="module")
def built():
    return mq.build_all()


@pytest.fixture(scope="module")
def room():
    return [m for m in audit.load_maps() if m["id"] == mq.ROOM_ID][0]


@pytest.fixture(scope="module")
def grid(built):
    return built["grid"]


@pytest.fixture(scope="module")
def blds(grid):
    return mq.buildings(grid)


def runs(lines, glyphs):
    """(glyph, length, x_or_y, line_index) of every maximal run of one glyph in `glyphs`."""
    out = []
    for i, line in enumerate(lines):
        j = 0
        while j < len(line):
            k = j
            while k < len(line) and line[k] == line[j]:
                k += 1
            if line[j] in glyphs:
                out.append((line[j], k - j, j, i))
            j = k
    return out


def columns(tiles):
    return ["".join(row[x] for row in tiles) for x in range(len(tiles[0]))]


# --------------------------------------------------------------------------- the room is the design

def test_the_committed_room_is_a_fresh_build_of_the_layout(room, built):
    fresh = built["room"]
    for key in ("width", "height", "tile_legend", "tiles", "collision", "spawns", "triggers", "actors"):
        assert room[key] == fresh[key], "%s differs: run python tools/make_quay_town.py" % key
    assert built["problems"] == []


def test_the_room_is_3_by_3_screens(room):
    assert (room["width"], room["height"]) == (48, 45)
    assert all(len(r) == 48 for r in room["tiles"]) and len(room["tiles"]) == 45


def test_every_glyph_is_in_the_tile_class_file_and_the_legend(room, built):
    used = set("".join(room["tiles"]))
    assert used <= set(built["classes"]), sorted(used - set(built["classes"]))
    assert used <= set(room["tile_legend"])
    assert len(used) >= 40, "the room uses %d glyphs; the vocabulary has %d" % (len(used), len(built["classes"]))


# --------------------------------------------------------------------------- buildings

def _is_rect_or_l(b):
    cells = {(x, y) for (x, y) in b["cells"]}
    w, h = b["x1"] - b["x0"] + 1, b["y1"] - b["y0"] + 1
    box = {(x, y) for x in range(b["x0"], b["x1"] + 1) for y in range(b["y0"], b["y1"] + 1)}
    missing = box - cells
    if not missing:
        return True
    xs = sorted({x for x, _ in missing})
    ys = sorted({y for _, y in missing})
    mx0, mx1, my0, my1 = xs[0], xs[-1], ys[0], ys[-1]
    if len(missing) != (mx1 - mx0 + 1) * (my1 - my0 + 1):
        return False
    touches_corner = (mx0 in (b["x0"], ) or mx1 == b["x1"]) and (my0 == b["y0"] or my1 == b["y1"])
    arms = (w - (mx1 - mx0 + 1) >= 3) and (h - (my1 - my0 + 1) >= 3) and (mx1 - mx0 + 1) >= 3 and (my1 - my0 + 1) >= 3
    return touches_corner and arms


def test_there_are_buildings_at_all(blds):
    assert len(blds) == 14, [(b["x0"], b["y0"]) for b in blds]


def test_every_building_is_a_rectangle_or_an_L(blds):
    bad = [(b["x0"], b["y0"]) for b in blds if not _is_rect_or_l(b)]
    assert bad == [], "buildings that are neither a rectangle nor an L: %s" % bad


def test_every_building_is_3_to_9_wide_and_4_to_6_deep_with_one_tower_at_most(blds):
    towers = []
    for b in blds:
        w, h = b["x1"] - b["x0"] + 1, b["y1"] - b["y0"] + 1
        assert 3 <= w <= 9, "building at (%d,%d) is %d wide" % (b["x0"], b["y0"], w)
        if h == 8:
            towers.append((b["x0"], b["y0"], w))
            assert w == 3, "only the 3 x 8 tower may be 8 deep"
        else:
            assert 4 <= h <= 6, "building at (%d,%d) is %d deep" % (b["x0"], b["y0"], h)
    assert len(towers) <= 1, towers


def test_roof_sits_over_wall_with_one_door_group_on_the_bottom_row(grid, blds):
    for b in blds:
        x0, x1, y0, y1 = b["x0"], b["x1"], b["y0"], b["y1"]
        ridge = grid[y0][x0:x1 + 1]
        eave = grid[y0 + 1][x0:x1 + 1]
        assert set(ridge) <= mq.ROOF_GLYPHS, "no ridge row at (%d,%d): %r" % (x0, y0, ridge)
        assert set(eave) <= (mq.ROOF_GLYPHS | set("GS")), "no eave row at (%d,%d): %r" % (x0, y0, eave)
        wall_rows = [grid[y][x0:x1 + 1] for y in range(y0 + 2, y1 + 1)]
        assert wall_rows and all(set(r) & mq.WALL_GLYPHS for r in wall_rows), "no wall under the roof at (%d,%d)" % (x0, y0)
        doors = [(x, y) for (x, y) in b["cells"] if grid[y][x] == "D"]
        assert doors, "building at (%d,%d) has no door" % (x0, y0)
        assert all(y == y1 for (_, y) in doors), "a door above the bottom row at (%d,%d)" % (x0, y0)
        xs = sorted(x for x, _ in doors)
        assert xs == list(range(xs[0], xs[-1] + 1)) and 1 <= len(xs) <= 3, "door group at (%d,%d) is %s" % (x0, y0, xs)


def test_every_door_has_a_free_reachable_2_by_2_apron(room, grid, blds):
    walk = audit.room_walkables(room)
    reach = audit.reachable_set(room)
    blocked = {(t["x"], t["y"]) for t in room["triggers"]} | {(a["x"], a["y"]) for a in room["actors"]}
    bad = []
    for b in blds:
        doors = sorted((x, y) for (x, y) in b["cells"] if grid[y][x] == "D")
        dx0, dx1, dy = doors[0][0], doors[-1][0], doors[0][1]
        ok = False
        for c in range(dx0 - 1, dx1 + 1):
            block = [(c + i, dy + 1 + j) for i in (0, 1) for j in (0, 1)]
            covers = any(dx0 <= x <= dx1 for (x, _) in block)
            if covers and all(t in walk and t in reach and t not in blocked for t in block):
                ok = True
                break
        if not ok:
            bad.append((dx0, dy))
    assert bad == [], "doors without a free 2 x 2 apron: %s" % bad


def test_public_doors_carry_a_sign_one_or_two_tiles_right_on_the_door_row(grid, blds):
    # shops, pubs, the terminal, the dock office and the hut (Telephone House) are public; the chapel, the tower, the
    # warehouse and plain houses need none (guide Part E question 5)
    signed = 0
    for b in blds:
        doors = sorted((x, y) for (x, y) in b["cells"] if grid[y][x] == "D")
        dx1, dy = doors[-1]
        near = grid[dy][dx1 + 1:dx1 + 3]
        if "S" in near:
            signed += 1
    assert signed >= 7, "only %d buildings carry a door sign" % signed


# --------------------------------------------------------------------------- streets and pinches

def _run_len(line, x):
    lo = hi = x
    while lo > 0 and line[lo - 1] in PAVING:
        lo -= 1
    while hi + 1 < len(line) and line[hi + 1] in PAVING:
        hi += 1
    return hi - lo + 1


def test_the_arrival_street_is_4_wide_along_its_whole_length(grid):
    widths = {_run_len(grid[y], 24) for y in range(0, 8)}
    assert widths == {4}, widths


def test_the_north_lane_is_3_wide_between_its_junctions(grid):
    cols = columns(grid)
    junctions = set(range(22, 26)) | set(range(8, 12)) | set(range(15, 19)) | set(range(28, 32))
    widths = {x: _run_len(cols[x], 9) for x in range(3, 45) if x not in junctions}
    assert set(widths.values()) == {3}, {x: w for x, w in widths.items() if w != 3}


def test_the_gate_passage_and_both_alleys_are_4_wide(grid):
    for x in (9, 16, 29):
        assert {_run_len(grid[y], x) for y in range(11, 15)} == {4}, x


def test_the_quay_road_and_forecourt_are_at_least_4_deep_everywhere(grid):
    cols = columns(grid)
    thin = [x for x in range(3, 45) if _run_len(cols[x], 18) < 4]
    assert thin == [], thin


def test_no_one_tile_pinch_except_door_niches(room):
    legend = room["tile_legend"]
    doors = {(x, y) for y, row in enumerate(room["tiles"]) for x, ch in enumerate(row) if legend[ch] == "door"}
    pinch = {tuple(p) for p in audit.check_pinches(room)["pinch"]}
    assert sorted(pinch - doors) == [], "1 tile pinches outside door niches: %s" % sorted(pinch - doors)


def test_the_audit_is_clean_for_the_quay(room):
    rooms = {m["id"]: m for m in audit.load_maps()}
    findings = audit.audit_room(room, rooms)
    by_kind = {}
    for f in findings:
        by_kind.setdefault(f["kind"], []).append(f)
    assert by_kind["reachability"][0]["unreachable_count"] == 0
    assert by_kind["snag"][0]["snag_count"] == 0
    assert by_kind["dead_end"][0]["unrewarded_dead_ends"] == []
    assert by_kind["readability"][0]["phantom_wall"] == [] and by_kind["readability"][0]["blocked_floor"] == []
    problems = [f for f in findings if f["kind"] in ("dangling_door", "missing_spawn", "landing_blocked", "landing_boxed",
                                                     "asymmetric_door", "one_way_door")]
    assert problems == [], problems


# --------------------------------------------------------------------------- runs (B6)

def test_runs_stay_inside_the_guide_limits(room):
    tiles = room["tiles"]
    cols = columns(tiles)
    limits = [("walls (4)", set("WVPwx"), 4, tiles), ("roofs (6)", set("^rQq"), 6, tiles),
              ("paving (8)", set(":,"), 8, tiles + cols), ("props (2)", set("LhoOnT*YZ"), 2, tiles + cols),
              ("fence (8)", set("f"), 8, tiles + cols), ("bollards (2)", set("b"), 2, tiles + cols),
              ("water (8)", set("~_"), 8, tiles + cols), ("containers (3)", set("X"), 3, tiles + cols)]
    for label, glyphs, limit, lines in limits:
        long_runs = [(g, n, pos, line) for (g, n, pos, line) in runs(lines, glyphs) if n > limit]
        assert long_runs == [], "%s: %s" % (label, long_runs[:6])


# --------------------------------------------------------------------------- density bands (B6)

def test_density_is_banded_and_inside_the_guides_numbers(room, grid, blds):
    total = room["width"] * room["height"]
    building = {c for b in blds for c in b["cells"]}
    walk = audit.room_walkables(room)
    water = sum(1 for row in room["tiles"] for ch in row if room["tile_legend"][ch] == "water")
    share = len(building) / total
    assert 0.10 <= share <= 0.25, "building share %.3f" % share
    assert 0.35 <= len(walk) / total <= 0.60, "walkable share %.3f" % (len(walk) / total)
    assert 0.45 <= len(walk) / (total - water) <= 0.65, "walkable share of dry land %.3f" % (len(walk) / (total - water))

    def zone(y0, y1):
        area = room["width"] * (y1 - y0 + 1)
        return len([c for c in building if y0 <= c[1] <= y1]) / area
    core, working, front = zone(0, 20), zone(21, 30), zone(31, 44)
    assert front <= 0.10, front
    assert 0.10 <= working <= 0.20, working
    assert core > working > front, (core, working, front)


# --------------------------------------------------------------------------- shore and pier

def test_the_shore_is_one_straight_quay_face_with_bollards_and_only_purposeful_openings(grid):
    face_rows = [y for y, row in enumerate(grid) if row.count("#") >= 8]
    assert len(face_rows) == 1, face_rows
    fy = face_rows[0]
    assert max(n for (g, n, _, i) in runs([grid[fy]], "#")) >= 8
    coping = grid[fy - 1]
    assert coping.count("b") >= 6, "bollards on the coping: %d" % coping.count("b")
    gaps = [n for (g, n, _, _) in runs([coping], "=")]
    assert all(2 <= n <= 6 for n in gaps), gaps                     # no 1 tile nub, no long bare coping
    openings = [x for x, ch in enumerate(grid[fy]) if ch != "#"]
    steps = [x for x in openings if grid[fy][x] == "s"]
    pier = [x for x in openings if grid[fy][x] in "p|"]
    assert steps == [6, 7, 8] and pier == [21, 22, 23, 24, 25] and sorted(steps + pier) == openings, openings


def test_the_pier_is_3_planks_wide_8_rows_long_with_rails_bollards_lamps_and_a_ship(grid):
    rows = [y for y, row in enumerate(grid) if row[22:25] == "ppp"]
    assert rows == list(range(31, 39)), rows
    for y in rows[1:]:
        assert grid[y][21] in "|bL" and grid[y][25] in "|bL", y
    for y in rows[2:]:
        assert grid[y][20] == "~" and grid[y][26] == "~", "plank row %d is wider than 3" % y
    assert [y for y in rows if grid[y][21] == "b" and grid[y][25] == "b"] == [33, 36]
    assert grid[38][21] == "L" and grid[38][25] == "L"
    assert grid[39][23:25] == "gg" and grid[40][23:25] == "gg"
    assert grid[41][23] == "d" and grid[42][23] == "H", "the ship lies at the end of the pier axis"


def test_vessels_are_sized_and_ordered_as_the_guide_says(grid):
    hull_rows = {y: "".join(row) for y, row in enumerate(grid) if "H" in row}
    ship = [len(r.strip("~")) for y, r in hull_rows.items() if y == 42][0]
    assert ship == 12, "the ship is 12 tiles long"
    assert sum(row.count(">") for row in grid) == 4, "two dinghies, the fishing boat and the ship, bow right"


# --------------------------------------------------------------------------- edges and anchors

def test_no_walkable_tile_on_the_map_edge_except_the_arrival_street(room):
    walk = audit.room_walkables(room)
    edge = sorted(t for t in walk if t[0] in (0, 47) or t[1] in (0, 44))
    assert edge == [(x, 0) for x in range(22, 26)], edge


def test_the_anchors_of_the_brief_are_all_there(room, built):
    sp, trig = room["spawns"], {(t["id"], t["x"], t["y"]): t for t in room["triggers"]}
    assert set(sp) == {"start", "from_gate", "from_office", "from_pier"}
    assert sp["start"]["y"] <= 2 and 22 <= sp["start"]["x"] <= 25, "the arrival tile is top centre"
    office = [t for t in room["triggers"] if t["id"] == "quay_dock_office"]
    assert len(office) == 1 and office[0]["kind"] == "map" and office[0]["spawn"] == "from_quay"
    assert room["tiles"][office[0]["y"]][office[0]["x"]] == "D"
    assert (sp["from_office"]["x"], sp["from_office"]["y"]) == (office[0]["x"], office[0]["y"] + 1)
    boarding = [t for t in room["triggers"] if t["id"] == "ship_small"]
    assert boarding and all(t["kind"] == "map" and t["spawn"] == "start" for t in boarding)
    assert all(room["tiles"][t["y"]][t["x"]] == "g" for t in boarding), "boarding triggers stand on gangway tiles"
    assert min(max(abs(sp["from_pier"]["x"] - t["x"]), abs(sp["from_pier"]["y"] - t["y"])) for t in boarding) <= 1
    assert ("quay_gate_checkpoint", 8, 10) in trig and ("quay_yard_walk", 8, 12) in trig
    walk = audit.room_walkables(room)
    yard = [(8, 10), (8, 11), (8, 12), (9, 12), (10, 12), (11, 12)]
    assert [t for t in yard if t not in walk and t != (8, 11)] == [], "the scripted yard walk needs these tiles"
    spots = built["directives"]["fightspots"]
    assert spots and spots[0]["id"] == "morgan_gate"
    fx, fy = spots[0]["x"], spots[0]["y"]
    # 2026-11-01 (three battles): the one fight spot is Morgan's, met at the gate, so it stands within two tiles of
    # the gate checkpoint trigger (8,10); it used to be the dock office door, which the old petty officer guarded.
    assert (fx, fy) in walk and max(abs(fx - 8), abs(fy - 10)) <= 2


def test_every_door_tile_carries_a_trigger_and_the_gate_barrier_is_one_overlay(room):
    legend = room["tile_legend"]
    doors = {(x, y) for y, row in enumerate(room["tiles"]) for x, ch in enumerate(row) if legend[ch] == "door"}
    firing = {(t["x"], t["y"]) for t in room["triggers"]}
    assert doors <= firing, sorted(doors - firing)
    story = [(x, y) for y, row in enumerate(room["collision"]) for x, ch in enumerate(row) if ch == "2"]
    assert story == [(8, 8)] and room["story_flag"] == "gate_passed"


def test_the_osm_link_is_recorded_for_the_eight_named_places():
    prov = json.load(open(os.path.join(ROOT, "data", "maps", "LEVEL-PROVENANCE.json"), encoding="utf-8"))
    link = prov["v2"]["osm_link"]["landmarks"]
    assert len(link) == 8
    names = {item["name"] for item in link}
    assert {"Red Funnel Terminal 1", "Town Quay Offices", "Dancing Man (Wool House)"} <= names
    layout, d = mq.load_layout()
    for item in link:
        x, y = item["layout_door_tile"]
        assert layout[y][x] == "D", item
    assert "OpenStreetMap" in prov["source"] and "Google Maps" in prov["not_used"]

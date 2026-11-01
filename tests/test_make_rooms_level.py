"""make_rooms_level: the small room edits are idempotent and leave ship_small alone."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_rooms_level as mr  # noqa: E402


def test_setcell_sets_tile_and_collision():
    room = {"tiles": ["###"], "collision": ["111"]}
    mr.setcell(room, 1, 0, ".", 0)
    assert room["tiles"] == ["#.#"] and room["collision"] == ["101"]

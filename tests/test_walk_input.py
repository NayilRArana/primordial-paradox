"""The walk update's input routing: a held direction leaves a field box and then walks (card t_7baa8fb4).

Why this file exists. The judge panel read the 2026-10-26 nightly take and marked it down for "the log records 0
footstep cues with Right reaching dialogue not walk". The cause is in `pp_overworld_step`'s dialogue branch: it
returned unconditionally while a box was up, so every direction press went nowhere. A box left open on the field
(a talk entity, a `say` trigger) therefore froze the walker where he stood: no walk, no footstep, and a recording
that stalls on the field with the box on screen. The branch now closes a plain box on a held direction and falls
through to the walk, so the same press that leaves the box is the press that moves him.

Two rules that must not be lost, and both are pinned here:
  1. A box that OFFERS A CHOICE keeps the d-pad. Up and down are that page's cursor (`pp_dialogue_step`, D2.4), so
     leaving on a direction would eat the pick halfway through the gate's three replies.
  2. Leaving applies the entry's `sets` before it closes, because spec 05 says `sets` names flags applied when the
     box closes; leaving early must not drop a flag.

GameMaker cannot run in this suite, so the GML is read as text for the routing order, and the routing rule itself is
mirrored as a small decision table and measured there.

Sources this file measures, never restates: game/scripts/pp_overworld/pp_overworld.gml,
game/scripts/pp_dialogue/pp_dialogue.gml, game/scripts/pp_input/pp_input.gml.

Run: python -m pytest tests/test_walk_input.py -q
"""

from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERWORLD_GML = os.path.join(ROOT, "game", "scripts", "pp_overworld", "pp_overworld.gml")
DIALOGUE_GML = os.path.join(ROOT, "game", "scripts", "pp_dialogue", "pp_dialogue.gml")
INPUT_GML = os.path.join(ROOT, "game", "scripts", "pp_input", "pp_input.gml")


def read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def function_body(text, name):
    """The body of one GML function, from its `function <name>(` to the matching closing brace at column 0."""
    start = text.index("function %s(" % name)
    depth = 0
    index = text.index("{", start)
    for position in range(index, len(text)):
        if text[position] == "{":
            depth += 1
        elif text[position] == "}":
            depth -= 1
            if depth == 0:
                return text[start:position + 1]
    raise AssertionError("function %s has no closing brace" % name)


def dialogue_branch(step):
    """The `if (!pp_dialogue_closed(_world.dialogue))` block of pp_overworld_step, as text."""
    marker = "if (!pp_dialogue_closed(_world.dialogue)) {"
    start = step.index(marker)
    depth = 0
    for position in range(step.index("{", start), len(step)):
        if step[position] == "{":
            depth += 1
        elif step[position] == "}":
            depth -= 1
            if depth == 0:
                return step[start:position + 1]
    raise AssertionError("the dialogue branch has no closing brace")


# ---------------------------------------------------------------------------------------------------------------------
# 1. The GML: the leave is read before the box is stepped, and the branch only returns on the else side.


def test_a_held_direction_is_read_in_the_dialogue_branch_before_the_box_is_stepped():
    step = function_body(read(OVERWORLD_GML), "pp_overworld_step")
    branch = dialogue_branch(step)
    assert "pp_walk_x()" in branch and "pp_walk_y()" in branch, (
        "the dialogue branch reads no direction, so a box still eats every walk press: %s" % branch)
    assert "pp_dialogue_leave(_world.dialogue)" in branch, (
        "the dialogue branch never calls pp_dialogue_leave, so the box cannot be left: %s" % branch)
    leave = branch.index("pp_dialogue_leave(")
    assert leave < branch.index("pp_dialogue_step("), (
        "the box is stepped before the leave is read, so the press that leaves it is spent on the box")


def test_a_box_that_offers_a_choice_keeps_the_d_pad():
    step = function_body(read(OVERWORLD_GML), "pp_overworld_step")
    branch = dialogue_branch(step)
    assert "!pp_dialogue_on_choice_page(" in branch, (
        "the leave is not gated on the choice page, so a Down meant for the choice cursor would close the box: %s"
        % branch)
    gated = branch.index("!pp_dialogue_on_choice_page(")
    assert gated < branch.index("pp_dialogue_leave("), (
        "the choice page is asked after the leave, which is too late")


def test_leaving_the_walks_box_falls_through_to_the_walk_instead_of_returning():
    step = function_body(read(OVERWORLD_GML), "pp_overworld_step")
    branch = dialogue_branch(step)
    # The branch has exactly one `return`, and it sits on the else side: the leave side falls through to the
    # battle request and then to pp_world_free_step, which is what plays the footstep.
    assert branch.count("return;") == 1, "the dialogue branch returns on both sides, so leaving it cannot walk"
    return_at = branch.index("return;")
    leave_at = branch.index("pp_dialogue_leave(")
    else_at = branch.index("} else {")
    assert leave_at < else_at < return_at, (
        "the only return in the branch is not on the else (box-stepped) side, so a leaving step still returns")
    assert step.index(branch) < step.index("pp_world_free_step(_world)"), (
        "the walk runs before the dialogue branch, so the press that left the box would be spent for nothing")


def test_leaving_applies_the_entrys_sets_before_it_closes():
    body = function_body(read(DIALOGUE_GML), "pp_dialogue_leave")
    assert "pp_dialogue_apply_flags(_d.sets)" in body, (
        "leaving the box drops the entry's sets, which spec 05 applies when the box closes: %s" % body)
    assert body.index("pp_dialogue_apply_flags(_d.sets)") < body.index("_d.closed = true"), (
        "the box is closed before its flags are applied")
    assert "is_undefined(_d) || _d.closed" in body, "leaving a box that is already gone is not guarded"


def test_the_walk_vector_the_branch_reads_is_the_one_the_input_module_publishes():
    published = read(INPUT_GML)
    assert "_in.walk_x = _walk_x;" in published and "_in.walk_y = _walk_y;" in published, (
        "pp_input no longer publishes walk_x and walk_y, so the dialogue branch reads a field nobody writes")
    assert "if (pp_action(\"left\")) _walk_x -= 1;" in published, (
        "walk_x is no longer built from the dpad actions")


# ---------------------------------------------------------------------------------------------------------------------
# 2. The routing rule, as a decision table. This is the mirror of the branch above: it is the behaviour the branch
#    asserts, measured rather than read.


def leaves_box(walk_x, walk_y, on_choice_page, closed):
    """The branch's own decision, in one function: True when the press leaves the box and the step walks."""
    if closed:
        return False
    return (walk_x != 0 or walk_y != 0) and not on_choice_page


def test_right_held_on_a_plain_page_leaves_the_box_and_walks():
    assert leaves_box(1, 0, False, False) is True


def test_every_direction_leaves_a_plain_page():
    for walk_x, walk_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        assert leaves_box(walk_x, walk_y, False, False) is True, (walk_x, walk_y)


def test_the_choice_page_keeps_its_cursor_for_every_direction():
    for walk_x, walk_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        assert leaves_box(walk_x, walk_y, True, False) is False, (walk_x, walk_y)


def test_no_direction_leaves_the_box_and_a_closed_box_is_left_alone():
    assert leaves_box(0, 0, False, False) is False
    assert leaves_box(1, 0, False, True) is False

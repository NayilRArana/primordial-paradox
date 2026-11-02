/// pp_map_tile: the character to tile index tables for every environment sheet, and the plane each tile lives on
/// (spec 04, spec 15, card R28).
/// The map data names its tiles with one character per cell, so no sheet file name and no tile number ever appears in
/// data\maps\all.json. This module is the one place a character becomes an index, and it holds one table per set:
/// "ship" for the small warship (spec 15), "quay" for the Town Quay block and the dock office (card R46), with
/// "office" as the interior profile of the same sheet, because the office floor is its own tile, and "drive" for the
/// M3 corridor (card t_af836a62).
/// A table also says which of the three planes a tile is drawn on. The map carries one plane of text, the draw needs
/// three: ground and props go under the hero, above goes over him, so a lamp post or a sign can stand in front of the
/// walker without a second layer in the data.
/// A table also names the background palette group each tile spends, and the roles in it, because spec 13 caps a
/// screen at 16 colours and a tile may only spend a colour the map row's own room palette set declares.
/// Provenance: the exterior numbers and roles are read off game\sprites_src\env\quay\quay_tiles.json, which is card
/// R46's manifest and the authority on that sheet. The ship numbers are the ones the ship sheet's own tile names give
/// in game\sprites_src\env\ts_ship_tiled.json: bulkhead 8, deck_plain 2, hatch_open 13, crate 21, pipes 18,
/// deck_grate 3. Where this file and those two manifests disagree, the manifests win and this file is the bug.
/// The drive numbers are the index each tile carries in assets\tiles\drive\drive_tiles.json (index 0 road_surface to
/// index 23 barrier_end, character a to x), and its four groups print as palette.json roles in that same manifest.

#macro PP_TILE_PLANE_GROUND 0
#macro PP_TILE_PLANE_PROPS 1
#macro PP_TILE_PLANE_ABOVE 2

#macro PP_TILE_SET_SHIP "ship"
#macro PP_TILE_SET_QUAY "quay"
#macro PP_TILE_SET_OFFICE "office"
#macro PP_TILE_SET_DRIVE "drive"
/// Card WIRE-V2: the v2 Town Quay set. Its characters are NOT the v1 quay's (in v2 "W" is a wall, "w" a lit window, "~" mid
/// water), so it is a set of its own. A room picks it with its own `tileset` field (pp_map_tile_set in pp_map), never by its
/// room palette id. The rows below are generated from data\tile_classes_quay_v2.json and tests\test_quay_v2_wire.py pins them.
#macro PP_TILE_SET_QUAY_V2 "quay_v2"
/// The restyled ship interior (ship_small, ship_cabin; card SHIP-RESTYLE): picked by the room's own `tileset` field like the v2 quay.
#macro PP_TILE_SET_SHIP_INTERIOR "ship_interior"
#macro PP_TILE_SHEET_SHIP_INTERIOR "ship_interior_tiles"
#macro PP_TILE_COLUMNS_SHIP_INTERIOR 16

#macro PP_TILE_SHEET_SHIP "ts_ship"
#macro PP_TILE_SHEET_QUAY "quay_tiles"
#macro PP_TILE_SHEET_DRIVE "drive_tiles"
#macro PP_TILE_SHEET_QUAY_V2 "quay_v2_tiles"

/// The ship sheet is 16 cells across, the exterior sheet is 8 (quay_tiles.json names columns 8), and the drive sheet
/// is 8 too (assets\tiles\drive\drive_tiles.json names columns 8, 24 tiles, characters a to x).
#macro PP_TILE_COLUMNS_SHIP 16
#macro PP_TILE_COLUMNS_QUAY 8
#macro PP_TILE_COLUMNS_DRIVE 8
/// The v2 sheet is 16 cells across (256 x 64, 61 tiles, tile_classes_quay_v2.json names columns 16).
#macro PP_TILE_COLUMNS_QUAY_V2 16

/// Card R46 holds each water frame for 24 game frames: the slow swell the night quay wants, not a flicker.
#macro PP_TILE_WATER_HOLD 24

/// The four background palette groups of the exterior sheet, by role, in sheet order (quay_tiles.json palettes).
/// The drive sheet's four groups are answered here too, in palette.json names, because this is the one place a group
/// name becomes a role list and a second function would be a second answer to the same question.
function pp_map_tile_group_roles(_group) {
    switch (_group) {
        case "bg0_quay_stone":   return ["grey_4", "grey_5", "sea_1"];
        case "bg1_harbour_water": return ["sea_1", "sea_2", "sea_4"];
        case "bg2_brick_iron":   return ["blood_3", "stone_2", "blood_4"];
        case "bg3_lamp_glass":   return ["gold_4", "gold_5", "stone_2"];
        // drive_tiles.json palettes: asphalt (grey_1, grey_3, grey_5), verge (moss_1, moss_2, moss_5),
        // sign (moss_3, moss_2, grey_5), lamp (gold_5, stone_2, moss_2). All nine names are drive_night's own roles.
        case "bg0_asphalt":      return ["grey_1", "grey_3", "grey_5"];
        case "bg1_verge":        return ["moss_1", "moss_2", "moss_5"];
        case "bg2_sign":         return ["moss_3", "moss_2", "grey_5"];
        case "bg3_lamp":         return ["gold_5", "stone_2", "moss_2"];
    }
    return [];
}

/// The exterior rows, in sheet order, exactly as quay_tiles.json lists them. Plane is this module's decision: the
/// backdrops (paving, water, brick, window, office boards) are ground, the things that stand up out of the ground
/// (bollard, chain, barrier, both doors, the desk) are props under the hero, and the two things a walker passes
/// behind (the lamp post and the harbour sign) are above him.
function pp_map_tile_rows_quay() {
    return [
        { ch: ".", gid: 0,  plane: PP_TILE_PLANE_GROUND, group: "bg0_quay_stone" },
        { ch: ",", gid: 1,  plane: PP_TILE_PLANE_GROUND, group: "bg0_quay_stone" },
        { ch: "~", gid: 2,  plane: PP_TILE_PLANE_GROUND, group: "bg0_quay_stone" },
        { ch: "q", gid: 3,  plane: PP_TILE_PLANE_GROUND, group: "bg0_quay_stone" },
        { ch: "w", gid: 4,  plane: PP_TILE_PLANE_GROUND, group: "bg1_harbour_water" },
        { ch: "W", gid: 5,  plane: PP_TILE_PLANE_GROUND, group: "bg1_harbour_water" },
        { ch: "R", gid: 6,  plane: PP_TILE_PLANE_GROUND, group: "bg1_harbour_water" },
        { ch: "B", gid: 7,  plane: PP_TILE_PLANE_PROPS,  group: "bg0_quay_stone" },
        { ch: "c", gid: 8,  plane: PP_TILE_PLANE_PROPS,  group: "bg0_quay_stone" },
        { ch: "b", gid: 9,  plane: PP_TILE_PLANE_PROPS,  group: "bg0_quay_stone" },
        { ch: "#", gid: 10, plane: PP_TILE_PLANE_GROUND, group: "bg2_brick_iron" },
        { ch: "=", gid: 11, plane: PP_TILE_PLANE_GROUND, group: "bg2_brick_iron" },
        { ch: "D", gid: 12, plane: PP_TILE_PLANE_PROPS,  group: "bg2_brick_iron" },
        { ch: "d", gid: 13, plane: PP_TILE_PLANE_PROPS,  group: "bg2_brick_iron" },
        { ch: "o", gid: 14, plane: PP_TILE_PLANE_GROUND, group: "bg3_lamp_glass" },
        { ch: "O", gid: 15, plane: PP_TILE_PLANE_GROUND, group: "bg2_brick_iron" },
        { ch: "L", gid: 16, plane: PP_TILE_PLANE_ABOVE,  group: "bg3_lamp_glass" },
        { ch: "S", gid: 17, plane: PP_TILE_PLANE_ABOVE,  group: "bg3_lamp_glass" },
        { ch: "f", gid: 18, plane: PP_TILE_PLANE_GROUND, group: "bg2_brick_iron" },
        { ch: "k", gid: 19, plane: PP_TILE_PLANE_PROPS,  group: "bg2_brick_iron" }
    ];
}

/// The ship rows, from ts_ship_tiled.json's tile names. The ship has no props or above tiles yet: spec 15 draws every
/// fitting flat on the deck, so all six characters are ground.
function pp_map_tile_rows_ship() {
    return [
        { ch: "#", gid: 8,  plane: PP_TILE_PLANE_GROUND, group: "" },
        { ch: ".", gid: 2,  plane: PP_TILE_PLANE_GROUND, group: "" },
        { ch: "D", gid: 13, plane: PP_TILE_PLANE_GROUND, group: "" },
        { ch: "H", gid: 13, plane: PP_TILE_PLANE_GROUND, group: "" },
        { ch: "C", gid: 21, plane: PP_TILE_PLANE_GROUND, group: "" },
        { ch: "P", gid: 18, plane: PP_TILE_PLANE_GROUND, group: "" },
        { ch: "G", gid: 3,  plane: PP_TILE_PLANE_GROUND, group: "" }
    ];
}

/// The drive rows, in sheet order, exactly as assets\tiles\drive\drive_tiles.json lists them: index i is character
/// chr(97 + i), so "a" is road_surface at 0 and "x" is barrier_end at 23. Plane is this module's decision, and it is
/// the corridor's: everything the car or the camera travels on or over (road, lines, shoulder, verge, hedge, kerb) is
/// ground, everything that stands up out of the ground (posts, gantry, its sign, the barrier) is props, and nothing is
/// above, because no fitting on this corridor is drawn over a walker. The brief for the drive row is that the road is
/// two tiles wide with the shoulder outside it and the lane line between the lanes.
function pp_map_tile_rows_drive() {
    return [
        { ch: "a", gid: 0,  plane: PP_TILE_PLANE_GROUND, group: "bg0_asphalt" },
        { ch: "b", gid: 1,  plane: PP_TILE_PLANE_GROUND, group: "bg0_asphalt" },
        { ch: "c", gid: 2,  plane: PP_TILE_PLANE_GROUND, group: "bg0_asphalt" },
        { ch: "d", gid: 3,  plane: PP_TILE_PLANE_GROUND, group: "bg0_asphalt" },
        { ch: "e", gid: 4,  plane: PP_TILE_PLANE_GROUND, group: "bg0_asphalt" },
        { ch: "f", gid: 5,  plane: PP_TILE_PLANE_GROUND, group: "bg0_asphalt" },
        { ch: "g", gid: 6,  plane: PP_TILE_PLANE_GROUND, group: "bg0_asphalt" },
        { ch: "h", gid: 7,  plane: PP_TILE_PLANE_GROUND, group: "bg0_asphalt" },
        { ch: "i", gid: 8,  plane: PP_TILE_PLANE_GROUND, group: "bg1_verge" },
        { ch: "j", gid: 9,  plane: PP_TILE_PLANE_GROUND, group: "bg1_verge" },
        { ch: "k", gid: 10, plane: PP_TILE_PLANE_GROUND, group: "bg1_verge" },
        { ch: "l", gid: 11, plane: PP_TILE_PLANE_GROUND, group: "bg1_verge" },
        { ch: "m", gid: 12, plane: PP_TILE_PLANE_GROUND, group: "bg3_lamp" },
        { ch: "n", gid: 13, plane: PP_TILE_PLANE_PROPS,  group: "bg3_lamp" },
        { ch: "o", gid: 14, plane: PP_TILE_PLANE_PROPS,  group: "bg3_lamp" },
        { ch: "p", gid: 15, plane: PP_TILE_PLANE_PROPS,  group: "bg3_lamp" },
        { ch: "q", gid: 16, plane: PP_TILE_PLANE_PROPS,  group: "bg0_asphalt" },
        { ch: "r", gid: 17, plane: PP_TILE_PLANE_PROPS,  group: "bg0_asphalt" },
        { ch: "s", gid: 18, plane: PP_TILE_PLANE_PROPS,  group: "bg2_sign" },
        { ch: "t", gid: 19, plane: PP_TILE_PLANE_PROPS,  group: "bg2_sign" },
        { ch: "u", gid: 20, plane: PP_TILE_PLANE_PROPS,  group: "bg2_sign" },
        { ch: "v", gid: 21, plane: PP_TILE_PLANE_PROPS,  group: "bg0_asphalt" },
        { ch: "w", gid: 22, plane: PP_TILE_PLANE_PROPS,  group: "bg0_asphalt" },
        { ch: "x", gid: 23, plane: PP_TILE_PLANE_PROPS,  group: "bg0_asphalt" }
    ];
}

/// The v2 Town Quay rows, in sheet order, exactly as data\tile_classes_quay_v2.json lists them: gid is the class index, plane is
/// the class plane. `under` is the tile laid on the ground plane first when the art is not a full square of colour (a lamp
/// head, a tree crown, the crane jib, a sign): it is the paving, which is what the level renders put under every such tile,
/// and -1 means the tile is opaque and needs nothing under it. group is empty: the v2 palette audit is
/// tools\check_runtime_palette.py against the room's palette_indices, not the four v1 groups.
function pp_map_tile_rows_quay_v2() {
    return [
        { ch: "^", gid: 0, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // roof_ridge_a
        { ch: "r", gid: 1, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // roof_eave_a
        { ch: "Q", gid: 2, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // roof_ridge_b
        { ch: "q", gid: 3, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // roof_eave_b
        { ch: "C", gid: 4, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // chimney_a
        { ch: "E", gid: 5, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // chimney_b
        { ch: "W", gid: 6, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // wall
        { ch: "V", gid: 7, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // wall_boards
        { ch: "P", gid: 8, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // pilaster
        { ch: "w", gid: 9, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // window_lit
        { ch: "x", gid: 10, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // window_dark
        { ch: "D", gid: 11, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // door
        { ch: "S", gid: 12, plane: PP_TILE_PLANE_ABOVE, group: "", under: -1 },  // sign_board
        { ch: "A", gid: 13, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // awning
        { ch: "G", gid: 14, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // gable_clock
        { ch: "t", gid: 15, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // ticket_window
        { ch: "+", gid: 16, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // finial
        { ch: "k", gid: 17, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // band_stripe
        { ch: ".", gid: 18, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // open_ground
        { ch: ":", gid: 19, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // paving
        { ch: ",", gid: 20, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // paving_alt
        { ch: ";", gid: 21, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // paving_drain
        { ch: "T", gid: 22, plane: PP_TILE_PLANE_ABOVE, group: "", under: -1 },  // tree_canopy_a
        { ch: "Y", gid: 23, plane: PP_TILE_PLANE_ABOVE, group: "", under: -1 },  // tree_canopy_b
        { ch: "Z", gid: 24, plane: PP_TILE_PLANE_ABOVE, group: "", under: -1 },  // tree_canopy_c
        { ch: "f", gid: 25, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // fence_rail
        { ch: "F", gid: 26, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // fence_post
        { ch: "*", gid: 27, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // plaza_centrepiece
        { ch: "~", gid: 28, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // water_mid
        { ch: "_", gid: 29, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // water_deep
        { ch: "-", gid: 30, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // water_foam
        { ch: "=", gid: 31, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // coping
        { ch: "#", gid: 32, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // quay_wall_face
        { ch: "p", gid: 33, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // pier_plank_light
        { ch: "j", gid: 34, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // pier_plank_dark
        { ch: "b", gid: 35, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // bollard
        { ch: "s", gid: 36, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // step_light
        { ch: "e", gid: 37, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // step_mid
        { ch: "u", gid: 38, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // step_dark
        { ch: "|", gid: 39, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // pier_rail
        { ch: "L", gid: 40, plane: PP_TILE_PLANE_ABOVE, group: "", under: -1 },  // lamp_head
        { ch: "l", gid: 41, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // lamp_pole
        { ch: "h", gid: 42, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // bench
        { ch: "v", gid: 43, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // market_counter
        { ch: "o", gid: 44, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // crate
        { ch: "O", gid: 45, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // barrel
        { ch: "X", gid: 46, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // container_blue
        { ch: "I", gid: 47, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // container_green
        { ch: "n", gid: 48, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // tarp_pile
        { ch: "H", gid: 49, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // hull
        { ch: "d", gid: 50, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // deck_plank
        { ch: "c", gid: 51, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // cabin
        { ch: "m", gid: 52, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // mast
        { ch: "N", gid: 53, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // funnel
        { ch: ">", gid: 54, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bow
        { ch: "g", gid: 55, plane: PP_TILE_PLANE_PROPS, group: "", under: -1 },  // gangway
        { ch: "M", gid: 56, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // crane_mast
        { ch: "J", gid: 57, plane: PP_TILE_PLANE_ABOVE, group: "", under: 19 },  // crane_jib
        { ch: "U", gid: 58, plane: PP_TILE_PLANE_ABOVE, group: "", under: 19 },  // crane_hook
        { ch: "K", gid: 59, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // crane_base
        { ch: chr(923), gid: 60, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 }   // lighthouse_gallery
    ];
}

// SHIP-INTERIOR-ROWS BEGIN (generated by tools/make_ship_interior.py)
/// The ship interior rows (the restyled ship_small and ship_cabin, SHIP-RESTYLE): gid is the class index in
/// data\tile_classes_ship_interior.json and every tile is opaque ground, so none lays anything under itself.
/// tests\test_ship_interior.py pins these rows to the class file.
function pp_map_tile_rows_ship_interior() {
    return [
        { ch: ".", gid: 0, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // plank_a
        { ch: ",", gid: 1, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // plank_b
        { ch: ";", gid: 2, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // plank_knot
        { ch: ":", gid: 3, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // steel_plate
        { ch: "+", gid: 4, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // steel_tread
        { ch: "G", gid: 5, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // grating
        { ch: "H", gid: 6, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // deck_hatch
        { ch: "D", gid: 7, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // steel_door
        { ch: "#", gid: 8, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bulkhead_a
        { ch: "B", gid: 9, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bulkhead_panel
        { ch: "O", gid: 10, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bulkhead_porthole
        { ch: "L", gid: 11, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // lifebelt
        { ch: "E", gid: 12, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // white_ensign
        { ch: "Y", gid: 13, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // cage_lamp
        { ch: "C", gid: 14, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // crate
        { ch: "P", gid: 15, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // pipe_vertical
        { ch: "p", gid: 16, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // pipe_horizontal
        { ch: "w", gid: 17, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // wainscot
        { ch: "o", gid: 18, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // cabin_porthole
        { ch: "m", gid: 19, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // wall_chart
        { ch: "c", gid: 20, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // wall_clock
        { ch: "l", gid: 21, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // sconce
        { ch: "K", gid: 22, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bookcase
        { ch: "g", gid: 23, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // globe
        { ch: "f", gid: 24, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // floor_lamp
        { ch: "1", gid: 25, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // desk_left
        { ch: "2", gid: 26, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // desk_drawers
        { ch: "3", gid: 27, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // desk_papers
        { ch: "4", gid: 28, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // desk_right
        { ch: "5", gid: 29, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bunk_head
        { ch: "6", gid: 30, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bunk_blanket
        { ch: "7", gid: 31, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bunk_fold
        { ch: "8", gid: 32, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // bunk_foot
        { ch: "q", gid: 33, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // locker_steel
        { ch: "Q", gid: 34, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // wardrobe
        { ch: "d", gid: 35, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // oak_door
        { ch: "r", gid: 36, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // carpet
        { ch: "^", gid: 37, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // carpet_n
        { ch: "v", gid: 38, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // carpet_s
        { ch: "<", gid: 39, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // carpet_w
        { ch: ">", gid: 40, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // carpet_e
        { ch: "(", gid: 41, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // carpet_nw
        { ch: ")", gid: 42, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // carpet_ne
        { ch: "[", gid: 43, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 },  // carpet_sw
        { ch: "]", gid: 44, plane: PP_TILE_PLANE_GROUND, group: "", under: -1 }   // carpet_se
    ];
}
// SHIP-INTERIOR-ROWS END

/// Build one set's lookup: character to {gid, plane, group, roles}. The office profile is the quay sheet read as an
/// interior: the same bricks, the same door, and "." is the office's own boards rather than the quay's paving.
function pp_map_tile_build(_set) {
    var _rows = (_set == PP_TILE_SET_SHIP) ? pp_map_tile_rows_ship() : pp_map_tile_rows_quay();
    // Card t_af836a62: a fourth set answers with its own rows. Without this branch an unknown set still builds the
    // quay's table, which is how the drive room drew the ship's deck: wrong art AND the quay's planes and roles.
    if (_set == PP_TILE_SET_DRIVE) _rows = pp_map_tile_rows_drive();
    if (_set == PP_TILE_SET_QUAY_V2) _rows = pp_map_tile_rows_quay_v2();
    if (_set == PP_TILE_SET_SHIP_INTERIOR) _rows = pp_map_tile_rows_ship_interior();
    var _table = {};
    var _i = 0;
    while (_i < array_length(_rows)) {
        var _row = _rows[_i];
        _table[$ _row.ch] = {
            gid: _row.gid,
            plane: _row.plane,
            group: _row.group,
            roles: pp_map_tile_group_roles(_row.group),
            name: "",
            under: (variable_struct_exists(_row, "under") ? _row.under : -1)
        };
        _i += 1;
    }
    if (_set == PP_TILE_SET_OFFICE) {
        // Office floor: the interior's own boards, so the office does not draw as an outdoor quay.
        _table[$ "."] = { gid: 18, plane: PP_TILE_PLANE_GROUND, group: "bg2_brick_iron",
                          roles: pp_map_tile_group_roles("bg2_brick_iron"), name: "office_floor" };
        // The office set holds ten roles and is quay_night without the brightest teal, so the harbour's water tiles
        // cannot be coloured in it (quay_tiles.json, sets office_night). An office map that asks for water therefore
        // draws the office floor rather than a colour the room does not hold, and the checker counts that cell as a
        // character the set does not name.
        variable_struct_remove(_table, "w");
        variable_struct_remove(_table, "W");
        variable_struct_remove(_table, "R");
    }
    return _table;
}

/// The lookup for a set, built once and kept. A draw of a 16 by 15 tile window asks 240 times a frame, so a table
/// rebuilt per tile would be 240 struct builds a frame for no gain.
function pp_map_tile_table(_set) {
    if (!variable_global_exists("pp_map_tile_tables")) global.pp_map_tile_tables = {};
    var _name = string(_set);
    if (variable_struct_exists(global.pp_map_tile_tables, _name)) return global.pp_map_tile_tables[$ _name];
    var _table = pp_map_tile_build(_name);
    global.pp_map_tile_tables[$ _name] = _table;
    return _table;
}

/// One character's row in one set, or undefined when the set does not name that character.
function pp_map_tile_row(_set, _ch) {
    var _table = pp_map_tile_table(_set);
    if (variable_struct_exists(_table, _ch)) return _table[$ _ch];
    return undefined;
}

/// The ship set's index for a character, kept for the callers that predate the exterior sheet: pp_map_tile_gid() in
/// pp_map is the one name, and it asks this function.
function pp_map_tile_gid_in(_set, _ch) {
    var _row = pp_map_tile_row(_set, _ch);
    if (is_undefined(_row)) return pp_map_tile_default_gid(_set);
    return _row.gid;
}

/// The plane a character draws on. An unnamed character is ground, because that is where a hole would show.
function pp_map_tile_plane(_set, _ch) {
    var _row = pp_map_tile_row(_set, _ch);
    if (is_undefined(_row)) return PP_TILE_PLANE_GROUND;
    return _row.plane;
}

/// The palette roles a character spends in a set, for the 16 colour audit.
function pp_map_tile_roles(_set, _ch) {
    var _row = pp_map_tile_row(_set, _ch);
    if (is_undefined(_row)) return [];
    return _row.roles;
}

/// The index an unnamed character draws as: the plain floor of the set.
function pp_map_tile_default_gid(_set) {
    switch (_set) {
        case PP_TILE_SET_SHIP:   return 2;
        case PP_TILE_SET_OFFICE: return 18;
        case PP_TILE_SET_DRIVE: return 0;
        case PP_TILE_SET_QUAY_V2: return 19;
        case PP_TILE_SET_SHIP_INTERIOR: return 0;
    }
    return 0;
}

/// The sheet a set draws its art from. The build is asked first: a set whose sheet has not been mirrored draws flat,
/// which is the rule pp_map_draw already followed for the ship.
function pp_map_tile_sheet(_set) {
    switch (_set) {
        case PP_TILE_SET_SHIP:   return PP_TILE_SHEET_SHIP;
        case PP_TILE_SET_DRIVE:   return PP_TILE_SHEET_DRIVE;
        case PP_TILE_SET_QUAY_V2: return PP_TILE_SHEET_QUAY_V2;
        case PP_TILE_SET_SHIP_INTERIOR: return PP_TILE_SHEET_SHIP_INTERIOR;
    }
    return PP_TILE_SHEET_QUAY;
}

/// The cells across the sheet a set draws from.
function pp_map_tile_columns(_set) {
    if (_set == PP_TILE_SET_SHIP) return PP_TILE_COLUMNS_SHIP;
    if (_set == PP_TILE_SET_DRIVE) return PP_TILE_COLUMNS_DRIVE;
    if (_set == PP_TILE_SET_QUAY_V2) return PP_TILE_COLUMNS_QUAY_V2;
    if (_set == PP_TILE_SET_SHIP_INTERIOR) return PP_TILE_COLUMNS_SHIP_INTERIOR;
    return PP_TILE_COLUMNS_QUAY;
}

/// The set a room draws with, from the room palette id the map row names. The two exterior sets are quay_night and
/// office_night (quay_tiles.json declares both); every other room keeps the ship's set, which is the set that was
/// there before this card. Card ARRIVAL-MAP-2 appends the two sets to data\room_palettes.json; this function only
/// reads the id, so a room naming a set the data does not carry yet still resolves its tiles.
function pp_map_tile_set_for_room(_room_palette) {
    var _id = string(_room_palette);
    if (_id == "office_night") return PP_TILE_SET_OFFICE;
    if (_id == "quay_night") return PP_TILE_SET_QUAY;
    // The hurricane block draws the quay's own twenty tiles with the storm sheet (quay_storm_tiles), so it takes
    // the quay's table, planes and water animation: only the picture differs, and the map row names the sheet.
    if (_id == "quay_storm") return PP_TILE_SET_QUAY;
    if (_id == "drive_night") return PP_TILE_SET_DRIVE;
    return PP_TILE_SET_SHIP;
}

/// The water animation: the harbour is the only thing on the quay that moves, two frames held PP_TILE_WATER_HOLD each
/// (quay_tiles.json animation "water"). The branch names the quay set, not "everything but the ship": the drive sheet
/// spends "w" on barrier_post, so a set-agnostic branch would draw water in the middle of the barrier run (card
/// t_af836a62). Every other character, and every character of a set with no animation, draws the index its own row
/// names.
function pp_map_tile_gid_at(_set, _ch, _steps) {
    if (_set == PP_TILE_SET_QUAY && (_ch == "w" || _ch == "W")) {
        return (floor(_steps / PP_TILE_WATER_HOLD) mod 2 == 0) ? 4 : 5;
    }
    return pp_map_tile_gid_in(_set, _ch);
}

/// The tile gid a character lays on the ground plane before its own plane draws, or -1 for none (card WIRE-V2). Only the v2
/// rows carry one; every other set answers -1, so no other room draws a tile it did not draw before.
function pp_map_tile_under(_set, _ch) {
    var _row = pp_map_tile_row(_set, _ch);
    if (is_undefined(_row)) return -1;
    if (!variable_struct_exists(_row, "under")) return -1;
    return _row.under;
}

/// The roles one map's tiles spend that the room set it named does not declare. An empty list is the 16 colour rule
/// holding; a role here would draw as PP_COLOUR_MISSING in the flat fallback, so the caller logs it rather than
/// spending a colour the room does not hold.
function pp_map_tile_role_gaps(_map, _set) {
    var _gaps = [];
    var _seen = {};
    var _y = 0;
    while (_y < _map.h) {
        var _x = 0;
        while (_x < _map.w) {
            var _ch = pp_map_tile_char(_map, _x, _y);
            var _roles = pp_map_tile_roles(_set, _ch);
            var _i = 0;
            while (_i < array_length(_roles)) {
                var _role = _roles[_i];
                if (!variable_struct_exists(_seen, _role)) {
                    _seen[$ _role] = true;
                    if (pp_look_role_index(_role) < 0) array_push(_gaps, _role);
                }
                _i += 1;
            }
            _x += 1;
        }
        _y += 1;
    }
    return _gaps;
}

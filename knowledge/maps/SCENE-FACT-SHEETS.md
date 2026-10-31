# Scene fact sheets: the drive and the ship

Status: fact sheets, written 2026-10-22 by the assistant profile, card t_753fb388 (PINE-PLACES-DIGEST).
Owner of the decisions this file serves: the gamedev lane, with Nayil. This file decides nothing. Where it
disagrees with a spec, the shot list or the art, gamedev's call stands and the disagreement is written as a
`Q:` in section 6.

What it is for: the drive is twelve shots out of a real journey, and the ship is five places inside one small
warship. An artist or a coder can read one sheet, and know the real name of the place, where it sits in the
route order, what the real signage and livery look like, which of the film's 16 colours carry it, and three
small things a local would notice if they were drawn wrong.

## How to read this file

- `[S]` a sourced fact. The source is named in the line or in section 7.
- `[I]` an inference. I worked it out from sources with arithmetic or judgement; nobody states it directly.
- File paths are short names relative to `<repo>\`
  unless they start with `D:`.
- No source text is copied at length. Quoted strings are sign faces, proper names and tabulated values only.

Sources used, in one place:

- `<workspace>\Shared\projects\arananet\pine\data\results\place-westminster.json`,
  `place-m3.json`, `place-southampton-port.json` (file `place-soton-port.json`), `place-twyford.json`,
  `place-type23.json`, `place-rn-dress.json` [S, abbreviated below as `pine westminster`, `pine m3`,
  `pine soton`, `pine twyford`, `pine type23`, `pine rn`].
- `knowledge/maps/REAL-PLACES.md` and `data/maps/real_places.json` (OpenStreetMap geometry, ODbL 1.0) [S].
- `knowledge/DRIVE-SHOT-LIST.md` (the twelve shots, their bars, steps and asset names) [S].
- `specs/13-8bit-look.md`, `specs/15-env-tiles-ship.md`, `data/palette.json`, `data/nes_palette.json`,
  `data/room_palettes.json`, `data/maps/all.json`, `tools/art/make_title_world.py`, `data/title.json`,
  `data/title_timing.json` [S].
- `https://en.wikipedia.org/wiki/Road_signs_in_the_United_Kingdom` (the colour table quoted from the
  Traffic Signs Regulations and General Directions and the Guildford Rules) [S].
- `https://en.wikipedia.org/wiki/Westminster_Bridge`, `https://en.wikipedia.org/wiki/Big_Ben` [S].
- `https://moto-way.com/services/winchester-southbound` (Winchester services sit between M3 J8 and J9) [S].

---

## 1. What a 16 colour palette can show

The film is a night drive drawn to the 8 bit look, so the palette is a hardware budget, not taste.

The project rule [S `specs/13-8bit-look.md`]: one master palette of 54 colours in `data/palette.json`
(9 hues by 6 levels); at most 16 colours on screen at once, declared per room; at most 4 per sprite
including its outline; backgrounds may use 6; one shared transparent key; no gradients, dither only. The
test suite pins the same budget from the hardware side, "25 colours on screen at most, counted the way the
PPU counts them" [S `tests/test_scene_palettes.py` docstring], which is 12 background entries plus the
backdrop plus 12 sprite entries, less the shared black.

The hardware rule behind it [S spec 13, the colour rule in `specs/15-env-tiles-ship.md`, and the `rule`
line in every `data/palettes/scene_*.json`]: one backdrop shared by both layers, 4 background palettes of
3 entries on 16x16 areas, 4 sprite palettes of 3 entries plus transparency on 8x8 tiles. So "16 colours" is
usually 4 background groups plus a backdrop plus sprite groups; it is not 16 colours free to place anywhere,
and that is what every sheet below has to work inside.

Two systems are in use, and both are real, so a sheet can be read either way:

1. The artist's master roles. The drive art is drawn as indices into the 54 colour master palette, 14 of
   them [S `tools/art/make_title_world.py`, `SCENE_COLOURS`]: ink `#0b0b0f`, asphalt `#1c1c24`, dim
   `#4a4a58`, bright `#c8c8d4`, sky deep `#081420`, sky mid `#0d2b3a`, sky low `#11485c`, green deep
   `#232a12`, green mid `#3a4420`, green lit `#55632f`, green pale `#adbc74`, stone deep `#14110f`, stone
   mid `#3b3226`, gold `#e8c65a`; each layer's 16x16 areas get that layer's backdrop plus at most three of
   the rest [S same file, `LAYER_BACKDROP`].
2. The solved NES scene palettes. Every scene has a file in `data/palettes/` that maps the drawn art onto
   real 2C02 entry numbers [S `data/palettes/scene_title.json`, `scene_ship.json`, `scene_westminster.json`,
   `scene_winchester.json`, `scene_southampton.json`]. The drive is `scene_title.json`: backdrop entry 15
   (black); bg0 grey, blue and white (`#7c7c7c`, `#0078f8`, `#f8f8f8`); bg1 dark teal blue, blue and white
   (`#004058`, `#0058f8`, `#f8f8f8`); bg2 three greens (`#007800`, `#006800`, `#005800`); bg3 grey, deep
   blue and brown (`#7c7c7c`, `#0000bc`, `#503000`); sprite groups sp0 green and white, sp1 grey, black and
   gold, sp2 dark green, dark blue and light grey, sp3 blue, brown and orange.

The second system corrects an assumption that is easy to make from the first: the drive's palette is not
"14 colours with no blue". Its background groups already hold three blues and three whites [S
`scene_title.json`], and the exterior map scenes hold a stone group, a brick group, a green group and a
water blue group [S `scene_westminster.json`, `scene_winchester.json`, `scene_southampton.json`]. What is
tight is the sprite side: a sign is a sprite, and the solved sprite groups pair their blues with no white
(sp2 is dark blue with light grey; sp3 is blue with brown and orange; the current green face sits on sp0,
green with white) [S `scene_title.json`]. So a motorway plate in blue is drawable today as dark blue with
light grey, and a bright blue with true white would need a sprite group re-solved, not a new master colour.

What a screen like this can show, honestly: a night sky with a horizon band, a road that reads as road,
chalk that reads as chalk, a sign face that reads at a glance, a lit window, a headlight pool, a ship in
silhouette with warm lamps. What it cannot show: a gradient, translucency, wet asphalt reflections, milk
glass glowing, more than three colours of container in one 16x16 area, thin white details on a pale ground,
or any text smaller than the 8x8 font.

Consequence for this file: each sheet names the art role or the solved NES group, so a colour can move in
either system and the sheet can still be traced [S `data/room_palettes.json` notes and the scene files].

---

## 2. The route order, in one table

The film compresses 84.7 miles into 178 seconds with four plates at 55, 43, 30 and 20 miles remaining
[S `knowledge/DRIVE-SHOT-LIST.md` section 5]. The real distances in the fourth column are straight-line
miles from the Westminster Bridge anchor to each place anchor, computed here with the haversine formula on
the OpenStreetMap coordinates in `REAL-PLACES.md` [S geometry, I the calculation]; road miles are longer,
because the M3 does not run straight.

| Shot | Place in the film | Real place | Straight line miles from Westminster Bridge | Plate passed |
| --- | --- | --- | --- | --- |
| 1 | city, Big Ben | Westminster Bridge and the Elizabeth Tower corner | 0.0 | none |
| 2 | city, the street and the Thames | Bridge Street, Victoria Embankment, Westminster Bridge | 0.0 to 0.6 | none |
| 3 | gantry, sign 55 | the M3 north east end, between the M25 (J2) and Woking (J3) [I] | 24 to 30 [I] | SOUTHAMPTON 55, BASINGSTOKE 20 |
| 4 | open motorway, rain | the smart motorway stretch, J2 to J4A [I] | 30 to 34 [I] | none |
| 5 | open motorway, radio | the Fleet approach, J4A to J5 [I] | 34 | none |
| 6 | open motorway, sign 43 | Fleet services, J4A and J5 | 34.5 | SOUTHAMPTON 43, BASINGSTOKE 8 |
| interlude | the services, not a shot | Fleet services, Welcome Break west side and Shell both sides | 34.5 | services sign only |
| 7 | Twyford Down cutting | the M3 cutting through Twyford Down, J10 to J11 | 60.2 | none |
| 8 | cathedral silhouette | Winchester Cathedral, north west of the cutting | about 61 [I] | none |
| 9 | open motorway, sign 30 | the M3 south west of Winchester, J11 to J13 [I] | 62 to 66 [I] | SOUTHAMPTON 30, WINCHESTER 12 |
| 10 | downland and storm | the chalk down either side of the cutting | 60 to 66 [I] | none |
| 11 | slip road, sign 20 | the M3 terminus at J14 and the M27, then the A33 | 67 to 69 [I] | SOUTHAMPTON 20, WINCHESTER 2 |
| 12 | docks | Southampton Ocean Terminal, berths 44 to 47 | 69.4 | none |

Segment distances on the same calculation [S geometry, I calculation]: Westminster Bridge to Fleet 34.5
miles, Fleet to Twyford Down 26.4 miles, Twyford Down to Ocean Terminal 11.0 miles, Ocean Terminal to Dock
Gate 4 0.4 miles.

One thing the table already shows and section 6 asks about: on the film's own numbers, the 43 plate lands on
the Fleet approach, which agrees with the real place to within a mile [I], but the 30 and the 20 plates are
shown after the cutting, while 30 and 20 miles from Southampton belong north of it [I].

---

## 3. The drive sheets

Twelve sheets, one per shot, in shot order. Every shot in `knowledge/DRIVE-SHOT-LIST.md` has one, and the
services interlude follows as a thirteenth sheet because it owns a map of its own.

### Sheet 1. Big Ben, pan down to the street

- Film: shot 1, beat 7, 688 steps, 11.47 s, film bars 0 to 8, `music title_theme`, `fade in 12`, three
  `camera` moves of 24 steps, `title_BG_bigben` one 256x240 background, no scroll [S shot list].
- Real place: Westminster Bridge and the Big Ben corner, City of Westminster, London, anchor 51.500900,
  -0.124400, a 512 by 384 m frame at 8.0 m per tile [S `REAL-PLACES.md` place 1].
- Real names and offsets in the frame [S same, OpenStreetMap ways and nodes]: Elizabeth Tower, way 123557148,
  tile 30,26; the Big Ben clock node 1802652184, tile 30,26; Westminster Bridge, node 4084403503, tile 35,24;
  Westminster Pier, tile 34,14; Parliament Square, tile 13,34; Westminster Abbey, tile 6,41. Roads in frame:
  Bridge Street, Parliament Street, Victoria Embankment, Westminster Bridge, Great George Street.
- Order along the route: mile zero. The car leaves over Westminster Bridge on the A302 [S Westminster Bridge
  article: the bridge carries the A302], then west and south for the M3.
- Signage and colours: no road sign in this shot. The clock tower is the signage: four dials of about 7 m
  across (23 ft), milk glass lit from behind at night, and the Ayrton Light above them, lit when either House
  sits after dark [S pine westminster]. If a street sign appears, the real rule for a non primary road is
  black lettering on white [S sign colour table].
- Livery: sand coloured Anston limestone with later honey coloured Clipsham stone [S pine westminster]. The
  bridge behind it is painted predominantly green, a natural verdigris shade, to match the Commons benches;
  Lambeth Bridge upstream is red for the Lords [S Westminster Bridge article].
- NES 16 palette: the film's own 14 roles fit. Limestone reads on stone mid `#3b3226` with bright `#c8c8d4`
  for lit faces [I]; the dials are gold `#e8c65a` on bright [I]; the sky is sky deep and sky mid; the bridge
  green needs green deep or green mid, and the verdigris shade cannot be hit, so it will read as moss green
  [I]. Cannot show: the carved stone detail, the glass glow, the clock hands at 8 bit size.
- Three details only locals notice:
  1. Big Ben is the nickname of the Great Bell (13.5 long tons, cast at Whitechapel), and only by extension
     the tower; the tower has been the Elizabeth Tower since 2012 [S Big Ben article].
  2. The clock is regulated by adding or removing pre decimal pennies on the pendulum [S same].
  3. The bridge is green because the Commons is green; a local reads red paint as Lambeth Bridge, one bridge
     upstream [S Westminster Bridge article].
- Sources: `pine westminster`, `REAL-PLACES.md` place 1, Big Ben and Westminster Bridge articles.

### Sheet 2. The London street, the car pulls away, the Thames

- Film: shot 2, beat 8, 860 steps, 14.33 s, film bars 8 to 18, two `camera` moves, `sfx car_engine_loop`
  starts and runs to the end of the film [S shot list]. The shot's art does not exist yet (shot list `Q3`).
- Real place: the same frame as sheet 1, read as a street: Bridge Street and Parliament Street on the west
  bank, the Thames running north to south down the east side of the frame, Westminster Bridge crossing it
  [S `REAL-PLACES.md` place 1, water 988 tiles of 3,072, quay 38].
- Order along the route: mile 0 to about 0.6, the first minute of the drive [I from the frame geometry and
  the film's own opening].
- Signage and colours: none on the bridge itself. Non primary direction signs are black on white, primary
  route signs white on dark green, motorway signs white on blue [S sign colour table]. The gantry in sheet 3
  is the first of the film's four plates, so nothing here should read as a motorway sign [I].
- Livery: green bridge paint and stone balustrade [S as sheet 1]; the river surface, the embankment wall, the
  pier. The car is project art (`spr_title_car`) and has no real world livery to match [S shot list].
- NES 16 palette: water as sky low `#11485c` with a 50 percent checker of sky mid `#0d2b3a` [I, uses the two
  permitted dither patterns]; bridge as green mid with bright top rail; pier and embankment as stone mid and
  dim; lamps as gold. Two free slots are enough for one accent, a red bus or a yellow plate, not both.
- Three details only locals notice:
  1. The Thames is tidal and brown green here, not blue [I from the river's tidal character in `pine
     soton`]; a drawn blue river is the first thing a Londoner flags.
  2. Westminster Pier, tile 34,14, is a working river pier, so a boat should be moored, not a decorative
     one [S OpenStreetMap node 469762514].
  3. The bridge is 250 m long with 7 spans [S Westminster Bridge article], so at the film's scale it should
     read as three or four arches, not one.
- Sources: `REAL-PLACES.md` place 1, Westminster Bridge article, sign colour table.

### Sheet 3. The gantry: the first sign, SOUTHAMPTON 55

- Film: shot 3, beat 9, 602 steps, 10.03 s, film bars 18 to 25, `camera` 24 steps, `say drive_sign_55`,
  flag `sign_55_seen`, `spr_title_sign` frame 1 and `spr_title_cone` [S shot list sections 3 and 5].
- Real place: the north east end of the M3. The motorway runs about 59 miles from Sunbury-on-Thames to
  Chilworth on Southampton's edge, part of European route E05 [S pine m3]. On the film's 84.7 mile total, 55
  miles remaining is about 30 miles out, which is the M25 (J2) to Woking (J3) stretch [I].
- Order along the route: first plate of four, before the rain, before Fleet [S shot list order].
- Signage and colours, the important disagreement:
  - As drawn: the sign face is green, `GREEN_LIT` `#55632f`, lettering `BRIGHT` `#c8c8d4` [S
    `make_title_world.py`, `SIGN_TEXTS` and the palette constants]. The faces read BASINGSTOKE 20 on top and
    SOUTHAMPTON 55 below [S same].
  - As the real road does it: a motorway advance direction sign is white lettering on a blue background,
    with green panels reserved for destinations reached on a primary route and white panels for non primary
    ones, and route numbers in yellow on green; the green with white lettering combination is the primary
    route sign [S sign colour table, TSRGD and Guildford Rules].
  - So a real M3 gantry is blue, and the film's green face is the primary route sign colour [I]. This is `Q1`
    in section 6, not a correction: the art is gamedev's and it already ships green.
- Livery: the M3 route marker is a blue rectangle with white "M3" and a white motorway symbol [S pine m3];
  distances are in miles only, never metric [S sign colour table section on units]; the typeface is
  Transport Medium, mixed case, with the Motorway face for route numbers [S same, typefaces].
- NES 16 palette: a sign face needs three colours, the face, the lettering and an edge, and at 8x8 it must
  fit one sprite group. The current face is drawn on sp0, green `#007800` with white `#f8f8f8` [S
  `data/palettes/scene_title.json`]. A blue face is available from the same file as sp2, dark blue `#004058`
  with light grey `#bcbcbc`, or as sp3, blue `#0000bc` with brown and orange; a bright blue with true white
  would need a sprite group re-solved, which is gamedev's call, not a new master colour [S same].
- Three details only locals notice:
  1. The M3 does not start in London; it starts at Sunbury-on-Thames, so the first M3 plate is already 15
     miles or more from Westminster [S pine m3 + I the distance].
  2. A real southbound gantry near Basingstoke also carries "The South West" for the A303 at J8 [S junction
     list in pine m3, I the plate combination].
  3. Junction 2 to 4A is a smart motorway whose hard shoulder is a permanent fourth lane, with emergency
     refuge lay-bys instead of a hard shoulder [S pine m3]; a local notices a hard shoulder drawn on that
     stretch.
- Sources: `pine m3`, `make_title_world.py`, sign colour table, `data/palettes/scene_title.json`.

### Sheet 4. Open motorway, the rain starts, wipers

- Film: shot 4, beat 10, 774 steps, 12.90 s, film bars 25 to 34, one `camera` move, no rain cue exists yet
  (shot list `Q2`) and the rain and wiper art does not exist (shot list `Q3`) [S shot list].
- Real place: the smart motorway stretch of the M3, J2 to J4A [S pine m3 for the smart motorway extent, I
  for placing this shot there, since it is the rain and lane management stretch of the film].
- Order along the route: after the 55 plate, before Fleet services [S shot list order].
- Signage and colours: variable speed signs and lane closure signs on this stretch are motorway signs, white
  on blue [S sign colour table]; at night and in rain they read as pale rectangles, which is all an 8x8
  glyph can carry [I].
- Livery: dark asphalt, solid white edge lines and dashed lane lines [S pine m3, the Twyford Down photo
  description: divided dark asphalt, solid white lane and edge markings]; reflective white paint on a
  wet road goes grey, not white [I].
- NES 16 palette: rain is the 25 percent dither over the road band, allowed by spec 13 [S]; wipers are a two
  or three shape sprite at 3 colours [S detail budget in spec 13]; the wiper smear and the spray cannot be
  drawn, so the rain must be sold by sound and by the wiper rhythm [I]. No new colour is needed.
- Three details only locals notice:
  1. On J2 to J4A there is no hard shoulder to break down on, only refuge lay-bys, so a broken down car in
     the left lane is right and a car on a hard shoulder is wrong [S pine m3].
  2. The route crosses the South West Main Line near Fleet [S pine m3], so a rail bridge parapet belongs in
     this stretch.
  3. Between J8 and J9 the motorway drops to two lanes each way and returns to three at J9 [S pine m3]; the
     film does not show it, and a local would expect the lane drop before Winchester.
- Sources: `pine m3`, `specs/13-8bit-look.md`, shot list `Q2` and `Q3`.

### Sheet 5. Open motorway, radio pages 1 and 2, car in long shot

- Film: shot 5, beat 11 first half, 1,032 steps, 17.20 s, film bars 34 to 46, `say drive_radio_1`,
  `say drive_radio_2`, one `camera` move, L3 window 0 to 90 [S shot list].
- Real place: the Fleet approach on the M3, J4A to J5, where the services are signed [S pine m3 junction
  list and `REAL-PLACES.md` place 2, I the placement].
- Order along the route: after the rain, before the 43 plate [S shot list order].
- Signage and colours: services signs are motorway signs, white on blue, with the services symbol in white
  [S sign colour table + I the symbol rule]; the distance to the services is given in miles and yards [S
  sign colour table units section]. No sign is drawn in this shot [S shot list].
- Livery: the car in long shot, side on, at 1x with a 3 colour limit, so the body, the windows and the
  lights are the whole read [I from spec 13's sprite budget]; the road markings carry the speed.
- NES 16 palette: no new role. The car in long shot is the only moving object beyond the parallax, and it
  should stay on the film's dim and bright pair so it never competes with the sign [I].
- Three details only locals notice:
  1. Fleet services are a pair, one each side of the carriageway, joined by a footbridge [S
     `REAL-PLACES.md` place 2: the Former Scott Mills Bridge footway crosses both carriageways].
  2. The west side is a Welcome Break and the fuel is Shell on both sides [S same: way 32806558 and ways
     61478612 and 61478613].
  3. The M3 here runs through a cutting between Fleet and Hartley Wintney with no town street pattern, just
     hardstanding and two service blocks [S same].
- Sources: `REAL-PLACES.md` place 2, `pine m3`, sign colour table.

### Sheet 6. Open motorway, radio pages 3 and 4, the sign 43

- Film: shot 6, beat 11 second half, 1,118 steps, 18.63 s, film bars 46 to 59, `say drive_radio_3`,
  `say drive_radio_4`, `say drive_sign_43`, flag `sign_43_seen`, `spr_title_sign` frame 2, then `fade out 12`
  into the interlude [S shot list].
- Real place: Fleet services, Hampshire, between Fleet and Hartley Wintney, anchor 51.295800, -0.855200,
  768 by 576 m at 12.0 m per tile [S `REAL-PLACES.md` place 2].
- Order along the route: 34.5 straight line miles out [S geometry, I calculation]; on the film's numbers,
  43 miles remaining is about 42 miles out, which is the same place within a mile [I]. This is the one plate
  whose number and place agree.
- Signage and colours: as drawn, green face with BASINGSTOKE 8 and SOUTHAMPTON 43 [S `make_title_world.py`];
  the real plate would be white on blue with a green or white panel by destination class [S sign colour
  table]. Sign content, real: Fleet services and the A327 and A3013 at J4A, Hook at J5 [S pine m3].
- Livery: two service blocks, a lot of hardstanding, a wide road, no quay and no railway inside the frame
  [S `REAL-PLACES.md` place 2 tile counts: rail 0, quay 0, road 309, grass 807, building 664].
- NES 16 palette: at 12 m per tile the whole frame is 64 by 48 tiles, which is four NES screens [S
  `REAL-PLACES.md` method]; the film shows it as one scrolling background, so only the near verge and the
  sign get colour, and the services block should be a dark mass with gold lamps [I].
- Three details only locals notice:
  1. The footbridge that crosses both carriageways is mapped as the Former Scott Mills Bridge, a footway
     [S OpenStreetMap way 24428692]; a road bridge there is wrong.
  2. The frame has no working railway despite the South West Main Line running near Fleet [S place 2 zero
     counts, and pine m3 for the crossing], so a drawn rail line belongs outside this view.
  3. Fleet services is where the M3 leaves the Thames Valley heath for Hampshire chalk, so the grass in this
     frame is already downland turf, not the Surrey heath of sheet 3 [S pine m3 route order, I the read].
- Sources: `REAL-PLACES.md` place 2, `pine m3`, `make_title_world.py`.

### Sheet I. The interlude at the services (not one of the twelve shots)

- Film: 2,408 steps, 40.13 s, 28 bars of the same cue, one screen of walking, one sign, the first input in
  the game; it sits between shot 6 and shot 7 [S shot list section 6]. It is not in the 178 s and gets no
  sheet number.
- Real place: the candidate the map work has already surveyed is M3 Fleet services [S `REAL-PLACES.md` place
  2]. The other real pair on this stretch is Winchester services (Moto), on the M3 between J8 and J9 [S
  moto-way.com].
- Order along the route: Fleet fits the film. The stop comes straight after the 43 plate, and 43 miles from
  Southampton is the Fleet approach [I]; a Winchester stop would have to come after the 30 plate, between
  J8 and J9, which is after the film has already passed the cutting [I from the same sources].
- Signage and colours: the services sign at the entry is white on blue with the white services symbol [S
  sign colour table + I]; the site's own brand sign is Welcome Break on the west side [S `REAL-PLACES.md`
  place 2]. A brand sign is a trademark, so it should be drawn as a shape, not copied [S licence section of
  `REAL-PLACES.md`].
- Livery: hardstanding, a lit forecourt, canopy legs, a footbridge over both carriageways [S place 2].
- NES 16 palette: the same 14 roles. The canopy and the pumps in silhouette against the lit forecourt is the
  whole read, gold on dark, and it costs two roles [I].
- Three details only locals notice:
  1. The two sides are separate sites joined by a footbridge, so the player walks one side, not both [S
     place 2].
  2. There is no railway and no water in this frame [S place 2 zero counts], so a canal or a level crossing
     would be invented.
  3. The services sit between where traffic leaves for the A303 at J8 and where it joins from the A34 at J9
     only in the Winchester case [S motorwayservices.uk description of Winchester via the search result];
     Fleet sits between J4A, signed Farnborough and Fleet, and J5, signed Hook [S pine m3 junction list, I
     the between]. Do not mix the two sites.
- Sources: `REAL-PLACES.md` place 2, moto-way.com, `pine m3`, shot list section 6.

### Sheet 7. Twyford Down: the chalk cutting, the headlight pool

- Film: shot 7, beat 13, 860 steps, 14.33 s, film bars 69 to 79, first shot after the interlude, `fade in
  12`, one `camera` move, L3 offset 170 to 200 with the cutting at L3 x 232 to 300 [S shot list].
- Real place: the M3 cutting through Twyford Down, south east of Winchester, anchor 51.041500, -1.308500,
  1,152 by 864 m at 18.0 m per tile [S `REAL-PLACES.md` place 3].
- Real names and offsets [S same, OpenStreetMap]: Twyford Down Cutting, way 306310686, tagged cliff, tile
  31,19; Twyford Down locality, tile 29,29; Hockley Cross motorway junction, tile 15,35; Saint Catherine's
  Lock, tile 4,12; the Itchen Navigation (Disused), tile 0,24.
- Order along the route: 60.2 straight line miles from Westminster Bridge, 26.4 from Fleet [S geometry, I
  calculation]. This is 60 miles into a journey the film counts as 84.7, so the cutting is the last third.
- Signage and colours: no road sign is drawn. The one colour scheme sourced for this place is the protest:
  the Twyford Rising badge is bright green with black lettering and a black circular line emblem, and stencil
  versions appeared around Winchester in the early 1990s [S pine twyford]. A road side sign appears in the
  article photo as blue [S pine m3], which under the colour table is a motorway sign, white on blue [S sign
  colour table].
- Livery: pale chalk faces both sides, green and brown grassy banks, dark motorway lanes, solid white lane
  and edge markings [S pine m3 and pine twyford photo descriptions]. The film draws the chalk on bright
  `#c8c8d4` with dim `#4a4a58` and stone deep `#14110f` for the shadow [S `make_title_world.py`].
- NES 16 palette: chalk is the hard case. Bright is a cool grey white, which is right for chalk, and stone
  mid is too warm [I]; the two chalk faces and the road fit the 14 roles with nothing new. Cannot show: the
  texture of the chalk, the grass detail, the depth of the cutting; three shapes per 16x16 tile is the cap
  [S spec 13].
- Three details only locals notice:
  1. The cutting took 1.91 hectares, about 4.5 percent of the Site of Special Scientific Interest, which is
     why the name is loaded locally [S pine twyford].
  2. The 1930s A33 Winchester bypass ran immediately west of St Catherine's Hill with at grade crossings at
     Bar End and Hockley, and its Bar End to Compton section was closed and removed; 7.2 hectares of
     species rich grassland were planted on the old route [S same].
  3. The down's old animal herding trackways are called dongas, and Deacon Hill at 142 m is the highest point
     [S same].
- Sources: `REAL-PLACES.md` place 3, `pine twyford`, `pine m3`, `make_title_world.py`, spec 13.

### Sheet 8. The cathedral silhouette, one caption

- Film: shot 8, beat 14, 860 steps, 14.33 s, film bars 79 to 92, one `camera` move, `say drive_cathedral`,
  L3 offset 320 to 340, the nave at L3 x 400 to 452 [S shot list].
- Real place: Winchester Cathedral is the only cathedral on this route, in the city centre, which sits north
  west of the cutting [S `REAL-PLACES.md` place 3 places Winchester north west of the frame, I the
  identification and direction].
- Order along the route: immediately after the cutting, at about 61 straight line miles out [I].
- Signage and colours: no signage; the shot is one caption [S shot list]. If a road sign were included, a
  heritage or tourist direction sign is white on brown [S sign colour table].
- Livery: the silhouette is drawn in stone deep `#14110f` with gold `#e8c65a` windows [S
  `make_title_world.py` constants and the L3 layer]. The real stone is pale, so the night silhouette is the
  only honest way to draw it in this palette [I].
- NES 16 palette: one silhouette plus gold windows, on the sky band, no new role. The scale is the problem:
  the cathedral's tower is about 96 m at the real distance, so at 16 px tile scale it is a small shape, and
  the film's L3 x 400 to 452 window is 52 px wide, which reads correctly as a distant town [I].
- Three details only locals notice:
  1. Winchester is the county town and the M3 passes it to the south east, so a cathedral on the far side
     of the road from the city would be wrong [S `REAL-PLACES.md` place 3 region and pine m3 route order].
  2. St Catherine's Hill, with a 12th century Norman chapel on it, is beside the down, not part of the
     cathedral close [S pine twyford].
  3. A southbound driver has the cathedral behind them after the cutting, so the shot is a look back or a
     licence [I]; drawing it ahead is the single thing a Winchester local would question first.
- Sources: `REAL-PLACES.md` place 3, `pine twyford`, `pine m3`, shot list.

### Sheet 9. Open motorway, radio pages 5, 6 and 7, the sign 30

- Film: shot 9, beat 15, 1,118 steps, 18.63 s, film bars 92 to 105, `say drive_radio_5`, `say
  drive_radio_6`, `say drive_radio_7`, `say drive_sign_30`, flag `sign_30_seen`, `spr_title_sign` frame 3
  [S shot list].
- Real place: the M3 south west of Winchester, J11 (A3090) toward J12 and J13 (A335, Eastleigh and
  Chandler's Ford) [S pine m3 junction list, I the placement].
- Order along the route: after the cathedral, before the storm. As drawn the plate reads WINCHESTER 12 and
  SOUTHAMPTON 30 [S `make_title_world.py`]. On the real road, a "Winchester 12" plate belongs north of
  Winchester, about J7 to J8, which is before the cutting, not after it [I from the junction list and the
  geometry]; this is `Q2` in section 6.
- Signage and colours: green face as drawn, white lettering [S `make_title_world.py`]; the real motorway
  plate is white on blue [S sign colour table]. Junction numbers appear on the plate as "J11" style tags or
  on the slip road signs, in the Motorway typeface [S typeface section].
- Livery: here the route is still chalk downland, with Eastleigh's urban and suburban scenery coming in
  further south [S pine m3 urban and natural contrast]; so this shot should still be fields and verge, not
  town [I].
- NES 16 palette: same 14 roles; the verge green pale `#adbc74` is the closest to chalk turf in sunlight
  [I]. Nothing new needed.
- Three details only locals notice:
  1. Winchester services (Moto) sit on the M3 between J8 and J9, both sides, and are famously a long way
     from the city they are named for [S moto-way.com and motorwayservices.uk via the search result].
  2. At J9 the A34 joins from the Midlands and Newbury, so a real plate in this stretch carries "The
     Midlands" or "Newbury" as well as Southampton [S pine m3 junction list].
  3. The Spitfire Bridge carries the B3404 Alresford Road over the M3, and the parallel A272 spur from J9 to
     J10 is called the Spitfire Link [S pine m3]; a local knows that bridge by name.
- Sources: `pine m3`, `make_title_world.py`, sign colour table, moto-way.com.

### Sheet 10. Downland: the storm forms over the car, first lightning, moon

- Film: shot 10, beats 16 and 17, 1,118 steps, 18.63 s, film bars 105 to 120, one `camera` move, `sfx
  thunder_soft` on the lightning, `spr_title_cloud` then L3 offset 0 to 60, the chalk horse at L3 x 148, and
  the 2 frame palette flash is shot list `Q1` [S shot list].
- Real place: the open chalk down either side of Twyford Down, including St Catherine's Hill and the
  Hockley golf course [S `REAL-PLACES.md` place 3 and pine twyford].
- Order along the route: around the cutting, 60 to 66 straight line miles out [I].
- Signage and colours: none in frame. The only sourced colour scheme belonging to this downland is the
  Twyford Rising green and black badge [S pine twyford], which is a protest mark, not road signage.
- Livery: open chalk, grass, fence lines, a low horizon [S pine twyford visual cues]; the sky is the film's
  sky deep to sky low ramp with the two permitted dither patterns [S spec 13].
- NES 16 palette: the flash is a palette swap, not a new drawing, which is exactly what the 16 colour rule
  is worst at: the flash needs no extra colour, only two frames of the same 14 [S `data/title_flash.json`
  two frames, spec 13 palette swap rule]. The moon is bright `#c8c8d4`, one shape.
- Three details only locals notice:
  1. No chalk hill figure appears in the surveyed frame or in the sources read for Twyford Down [S
     `REAL-PLACES.md` place 3 feature classes and `pine twyford` feature list, I the negative], so the drawn
     horse is an invention and a Hampshire local would place a horse like that in Wiltshire, not here.
  2. Hockley Golf Club has been on the down since 1914 [S pine twyford], so a golf green or a flag pole is
     period correct.
  3. The Pilgrims' Trail crosses the down from Winchester toward Portsmouth [S pine twyford], so a footpath
     line on the chalk is right and a road is not.
- Sources: `REAL-PLACES.md` place 3, `pine twyford`, spec 13, shot list `Q1`.

### Sheet 11. Slip road: the Southampton sign 20, headlights

- Film: shot 11, beat 18, 688 steps, 11.47 s, film bars 120 to 133, one `camera` move, `say drive_sign_20`,
  flag `sign_20_seen`, `spr_title_sign` frame 4, cone up, the road narrowing to one lane [S shot list].
- Real place: the end of the M3 and the way into the docks. The M3 ends at J14 where it meets the M27 [S
  pine m3 junction list]; the A33 is the road into the Eastern Docks [S `REAL-PLACES.md` place 5 road
  relations].
- Order along the route: last road shot, 67 to 69 straight line miles out [I]. The plate as drawn reads
  WINCHESTER 2 and SOUTHAMPTON 20 [S `make_title_world.py`], which places it 20 miles short of
  Southampton, north of the cutting [I], while the film shows it at the slip road, about 11 miles out [S
  geometry, I calculation]; this is `Q2` in section 6.
- Signage and colours: green face, white lettering as drawn [S `make_title_world.py`]; the real sign at a
  motorway terminus is white on blue, and the destination reached on a primary route after leaving the
  motorway would sit on a green panel [S sign colour table]. Slip road signs use the Motorway typeface for
  route numbers [S typeface section].
- Livery: the road narrows to one lane with a headlight cone up [S shot list]; the real approach has
  roundabout and gyratory signs, which are white on blue for a roundabout symbol [I from the colour table's
  regulatory set].
- NES 16 palette: the headlight pool is the shot's whole lighting, which spec 13 permits as a hard edged
  shape, not a soft shadow [S]. Gold `#e8c65a` at 25 percent dither on asphalt reads as lamplight on wet
  tarmac [I].
- Three details only locals notice:
  1. The M3 becomes the M27 at J14, so the "M3" route marker should stop there and the M27 start [S pine
     m3 junction list].
  2. Dock Gate 4, the real gate into the Eastern Docks, is a wide dock road with port sheds and rail sidings
     [S `REAL-PLACES.md` place 5].
  3. The port's working railway in this frame is the Southampton Eastern Docks Branch [S place 5 working
     rail], so a level crossing near the gate is right and a closed line is not.
- Sources: `pine m3`, `REAL-PLACES.md` place 5, sign colour table, `make_title_world.py`.

### Sheet 12. Docks: cranes, containers, the ship lit at the quay

- Film: shot 12, beat 19, 962 steps, 16.03 s, film bars 133 to the fade, two `camera` moves, `wait 902`,
  `fade out 12`, `end`; the docks art does not exist yet (shot list `Q3`, whose nearest existing picture is
  the dusk `quay_dusk` battle background) [S shot list].
- Real place: Southampton Ocean Terminal and the Old Docks berths, Eastern Docks, anchor 50.893000,
  -1.399000, 768 by 576 m at 12.0 m per tile [S `REAL-PLACES.md` place 4].
- Real names and offsets [S same, OpenStreetMap]: Ocean Cruise Terminal, way 314606884, tile 24,24; Berth
  46, tile 29,21; Berth 45, tile 34,18; Berth 47, tile 26,35; Berth 44, tile 35,34; Eastern Docks quarter,
  tile 28,1. Roads: Atlantic Way, Ocean Way, Cunard Road, Maritime Walk, the A33.
- Order along the route: the end, 69.4 straight line miles out [S geometry, I calculation]; 0 miles
  remaining.
- Signage and colours: berth numbers are the port's own signage and the frame carries berths 44 to 47 [S
  OpenStreetMap nodes]; the sources read describe no universal port sign colour scheme, so any gate or
  berth sign is `[I]` and should be white on a dark board, the plainest choice [I]. The lit ship at night
  against dark cranes is sourced as a look: gantry cranes read as dark silhouettes with warm amber lights
  [S pine soton].
- Livery: container rows in dense red, blue and green; dark paved yards and vehicle lots [S pine soton];
  a Red Funnel car ferry is mostly white with a broad red lower hull band and red lettering [S same]. The
  ship itself is sheet SH1.
- NES 16 palette: the shot needs gold at two levels for the lamps, sea low for the water, and the three
  container colours of wine, sea and moss at one level each [I]. At three colours per 16x16 area, a
  container stack cannot be a rainbow; one hue per block, with the wine, sea and moss levels carrying the
  three colours [S hardware rule].
- Three details only locals notice:
  1. The tide range here is about 4 m, and the "double tides" give roughly 17 hours of rising water, which
     is why big ships can use the port about 80 percent of the time [S pine soton]; a drawn high water mark
     on the quay wall is the local tell.
  2. The quay handles 400 m ships and the dredged channel is 19 m deep [S pine soton], so a frigate of 133 m
     is a small ship for this berth, not a big one [I].
  3. The Marchwood incinerator is an aluminium dome about 110 m wide and 36 m high, a landmark on the Test
     side [S pine soton]; and Redbridge is named for reeds, never for a red bridge [S same].
- Sources: `REAL-PLACES.md` place 4, `pine soton`, shot list `Q3`.

---

## 4. The ship sheets

Five sheets. The ship in the game is two built maps and one spec sample [S `data/maps/all.json`,
`specs/15-env-tiles-ship.md`]: the weather deck `ship_small`, 20 by 15, room palette `deck_day`; the cabin
`ship_cabin`, 16 by 15, room palette `ship_cabin`, which holds Percy's wardroom fight; and the spec 15
sample map with an officer cabin, a wardroom, an engine space, a corridor and a hold, using the
`lower_deck` palette for the hold. The two sheets for the quay and the berth cover the ship as it is seen
from land, which is shot 12.

The class is the Type 23 frigate, the Duke class, about 133.0 m long, 16.1 m beam, 7.3 m draught, about
4,900 t [S pine type23]. That is what the ship on screen should look like from outside.

The ship's solved palette is `data/palettes/scene_ship.json` [S]: backdrop entry 15 black for the hull
shadow and the hatch void; bg0 greys (`#7c7c7c`, `#bcbcbc`, `#fcfcfc`); bg1 blue, gold and white
(`#0058f8`, `#f8b800`, `#fcfcfc`); bg2 deep blue, brown and orange (`#0000bc`, `#881400`, `#e45c10`); bg3
grey, deep blue and light blue (`#7c7c7c`, `#0000bc`, `#3cbcfc`). The sprite groups carry the cast: sp0
grey, black and light grey; sp1 blue and white; sp2 brown, orange and skin `#f0d0b0`; sp3 brown, peach and
gold. That is what makes a sailor's face and a navy collar possible at 8x8, and it is why the sheets below
say the crew read is a sprite problem, not a background one [I from same].

### Sheet SH1. The berth: Ocean Terminal, berth 46, night

- Where it is: Southampton Ocean Terminal, berths 44 to 47, Eastern Docks; the anchor and tile offsets are in
  sheet 12 [S `REAL-PLACES.md` place 4].
- Order: last place of the film, the ship lit at the quay, shot 12 [S shot list].
- Signage and colours: berth number 46 is the real designation of the Ocean Cruise Terminal berth [S
  OpenStreetMap node 729188561 and the terminal way], so any painted number on the quay should read 46, not
  a number the game invents [I].
- Livery: hull and superstructure a uniform medium naval grey, decks darker grey, pale or white flight deck
  markings [S pine type23]. The quay behind is quay cap, quay stone and dark quay tiles [S spec 15 row 3].
- NES 16 palette: `deck_day` names 14 roles and the map declares 10 colours [S `data/room_palettes.json`
  and `data/maps/all.json` `palette_indices`]. At night the same roles read as a silhouette plus amber
  lamps, which is the sourced look [S pine soton].
- Three details only locals notice:
  1. A cruise berth is numbered, and Ocean is berth 46, next to 45 and 47 [S OpenStreetMap].
  2. Ships use the port about 80 percent of the time because of the double tide [S pine soton], so a
     half loaded ship sitting on the bottom at the quay is wrong here.
  3. The lit ship against dark cranes is what the port looks like after dark, not a ship under floodlights
     [S pine soton photo description].
- Sources: `REAL-PLACES.md` place 4, `pine type23`, `pine soton`, spec 15, `room_palettes.json`.

### Sheet SH2. The quay and the walk to the ship

- Where it is: Dock Gate 4 and the Eastern Docks road, the real gate into the port, a wide dock road with
  port sheds and rail sidings and the River Itchen cutting the east edge [S `REAL-PLACES.md` place 5].
- Order: the step between the docks shot and the deck, not a shot of its own [S spec 15, the player walks in
  from the harbour].
- Real names and offsets [S place 5]: Dock Gate 4, way 1043468564, tile 7,29; The Dock House, tile 35,27;
  River Itchen, tile 56,24; Ocean Village Marina; Itchen Bridge; Southampton Eastern Docks Branch railway.
- Signage and colours: the gate is a structure, not a sign; any gate board is `[I]`, and the plain choice is
  white on dark [I]. Port road markings are white [I].
- Livery: the spec's own quay tiles are quay stone two variants, dark quay, quay cap, bollard, rail post and
  rail bar, with water frames and foam [S spec 15 row 3].
- NES 16 palette: `deck_day` carries it: bronze for the quay stone and bollards, sea for the water, gold for
  a lamp, grey for the gate [I on the mapping, the roles are from `data/room_palettes.json`].
- Three details only locals notice:
  1. The railway in this frame is working, the Southampton Eastern Docks Branch [S place 5], so a train or a
     wagon is correct here and a disused line is not.
  2. Ocean Village Marina sits south of the Itchen Bridge, and Itchen Marine is north of it [S pine soton],
     so the marina is the far side of the bridge from the docks.
  3. The Itchen Bridge has an 800 m span with 29 m of shipping clearance above chart datum [S pine soton],
     which is why the bridge is high in any view up river.
- Sources: `REAL-PLACES.md` place 5, `pine soton`, `pine type23`, spec 15, `room_palettes.json`.

### Sheet SH3. The weather deck: map `ship_small`

- Where it is: `ship_small`, 20 by 15 tiles, room palette `deck_day`, music PP-05 [S `data/maps/all.json`].
  Spawns: start 2,7; after_percy 17,7; from_cabin 17,7. Door `D` at 18,7 opens into `ship_cabin` when
  `ship_door_open` is set; triggers: save `deck_save` at 2,5, battle `tutorial_sailors` at 4,7, flag
  `ship_deck_seen` at 14,8, say `ship_rail_note` at 2,2, scene `ship_boarding` at 10,13 [S same].
- Order in the ship: first place the player walks after boarding, since `start` is 2,7 and the boarding
  scene plays on this map at 10,13; the cabin door is at the far end of the same screen, x 18 of 20 [S
  `data/maps/all.json`, I the reading of the spawn order].
- Real counterpart: a Type 23 weather deck. From stern to bow: the flight deck with a circular landing
  marking, the enclosed hangar, the central superstructure with the tall mast and the Artisan radar, then
  the forward deck and the bow gun [S pine type23].
- Signage and colours: "painted lines" on the steel deck are part of the spec's tile set [S spec 15], and
  the real deck markings are pale or white on darker grey [S pine type23]. Rank and name boards are `[I]`.
- Livery: medium naval grey hull, darker grey decks, red, white and blue in the stern flag [S pine type23].
- NES 16 palette: `deck_day` 14 roles, map declares 10 colours [S]. The deck reads on grey levels plus
  bronze hull; sea needs two levels for the animated water frames [S spec 15 animations].
- Three details only locals notice:
  1. The class is the Duke class, named for dukes, and HMS Westminster, HMS Northumberland, HMS Richmond,
     HMS Sutherland and HMS Iron Duke are all real Type 23 names [S pine type23]; a made up ship name is
     the first thing a Navy reader catches.
  2. The flight deck marking is circular, not rectangular [S pine type23 overhead photo description].
  3. The ship carries two Pacific 24 rigid inflatable boats, and her complement is 185 with accommodation
     for up to 205 [S pine type23], so the deck is busy with people in the real thing.
- Sources: `data/maps/all.json`, spec 15, `pine type23`, `room_palettes.json`.

### Sheet SH4. The cabin and Percy's wardroom: map `ship_cabin`

- Where it is: `ship_cabin`, 16 by 15 tiles, room palette `ship_cabin`; spawn from_deck 2,7; the door at
  1,7 returns to `ship_small`; scene `percy_lore_stop` at 7,3 conditioned on `ship_deck_seen`; the Percy
  battle at 7,2 conditioned on `percy_standing` [S `data/maps/all.json`]. The character is Percy Skye, 23, a
  Royal Navy lieutenant, and the boss fight happens inside the ship, in grey steel corridors, bulkheads and
  a wardroom [S spec 15 opening and `knowledge/CHARACTER-BIBLE.md` as cited there].
- Order in the ship: second place in the sequence, entered through the deck door when `ship_door_open` is
  set; the lore stop is at 7,3 and the Percy fight at 7,2, so this is the last room of the ship run [S
  `data/maps/all.json`, I the sequence from the spawns and conditions].
- Real counterpart: an officer's cabin and the wardroom. The spec 15 sample adds a separate officer cabin
  and wardroom with wood deck, table, bunk, locker, crate, barrel and lifebuoy [S spec 15 rows 2 to 7].
- Signage and colours: a wardroom sign tile exists in the spec's set [S spec 15 row 3], which is the one
  sign that should be legible, and it is a 16x16 tile, so the 8x8 font in caps is the limit [S spec 13].
- Livery: the wardroom wood floor in two variants, warmer than the steel, with wine trim and gold fittings
  [S spec 15 and the `ship_cabin` palette note].
- NES 16 palette: `ship_cabin` 13 roles, map declares 7 colours [S `data/room_palettes.json` and
  `data/maps/all.json`]. Seven is the tightest room in the game and it is deliberate: wood, lamp, hull, one
  red accent.
- Three details only locals notice:
  1. Officers' evening dress is No. 2A, a navy mess jacket with a white waistcoat and miniature medals, and
     the informal onboard rig is "red sea rig", a white short sleeved shirt with shoulder boards and a black
     cummerbund [S pine rn]. A lieutenant in a wardroom at night is in one of those, not in a suit.
  2. Junior ratings wear square rig: white undershirt, navy jumper and bell bottoms, a square blue collar
     with white stripes, a black silk scarf, a white lanyard, and a peakless cap with the ship's name on the
     tally [S pine rn], which is how the ship's name becomes visible at 8 px.
  3. A wardroom is the officers' dining and social room, junior officers included [I]; it is not the
     captain's cabin, and a local reader of naval fiction will notice the difference.
- Sources: `data/maps/all.json`, spec 15, `pine rn`, `room_palettes.json`.

### Sheet SH5. The corridor and the hold: spec 15 sample map

- Where it is: the spec 15 sample map, 20 by 15, rows 8 and 9 the corridor, row 10 the bulkhead to the hold,
  rows 11 to 13 the hold with stairs up at the starboard end and a ladder down beside them; exits
  `ladder_down` to `ship_lower_deck`, `stairs_up` to `ship_weather_deck`, and `hatch_percy` to
  `percy_wardroom` gated by `ship_hatch_open` [S spec 15 sample map section]. This map is a sample, not in
  `data/maps/all.json`, so it is a place the game may use rather than one it ships today [S].
- Order in the ship: the lowest place in the sample, reached from the corridor through the bulkhead at row
  10 and its two tile sill, with the ladder down to `ship_lower_deck` at 17,12 and the stairs up to
  `ship_weather_deck` at 17,11 [S spec 15 sample map, I the vertical order from the exits].
- Real counterpart: the Type 23's internal layout is not in the sources read beyond corridors, bulkheads and
  a wardroom, so anything below the weather deck is `[I]` at the level of which room is where; the fittings
  are sourced by the spec's tile list [S spec 15].
- Signage and colours: the spec's sign tiles are the wardroom sign, the machinery sign and the bridge sign
  [S spec 15 row 3]; painted lines run horizontally, vertically and around corners as separate tiles, and
  hazard stripes are a tile [S same row 1 and 2].
- Livery: steel deck plates, rivet plate, grating, plain plate, rivet bulkheads, painted lines, hazard
  stripes, pipes and cable runs; the hold is darker bronze with sea light through the hatch and wine trim
  [S spec 15 and the `lower_deck` palette note].
- NES 16 palette: `lower_deck` 13 roles [S `data/room_palettes.json`]; spec 15's own rule is 10 colours for
  the whole sheet, all exact Ricoh 2C02 outputs, and at most 3 non backdrop colours per 16x16 tile [S spec
  15 colour rule]. The pattern is: one grey per zone, one accent for hazard paint, one for the sea light.
- Three details only locals notice:
  1. The current working rig is RIG22, navy blue and fire retardant, with a Velcro name tape, rank on the
     shoulder, a navy beret, a stable belt and black "steaming" boots; it went Navy wide in 2022 and the
     rollout was not complete everywhere until early 2026, and RIG24 adds a Velcro White Ensign sleeve patch
     [S pine rn]. Crew in the corridor should be in that, not in square rig.
  2. Petty officers wear their rate insignia on the left sleeve, and ratings in No. 1A add a white web belt
     and gaiters when carrying rifles [S pine rn], which is two pixels of white in the right place.
  3. Every hatch is either open or closed, and the spec makes the closed hatch solid and the open hatch
     walkable [S spec 15 tiles and collision], so a closed hatch that the player can walk through is the one
     error a Navy reader would spot at once [I].
- Sources: spec 15, `room_palettes.json`, `pine rn`.

---

## 5. Signage and livery, the master table

The one rule that fixes every sign colour on the drive [S sign colour table, quoting the Traffic Signs
Regulations and General Directions and the Guildford Rules]:

| Sign background | Border | Lettering | Used for |
| --- | --- | --- | --- |
| Blue | White | White | motorways, the M3 |
| Green | White | White, route numbers yellow | primary routes, the A roads |
| White | Black | Black | non primary routes and local destinations |
| Brown | White | White | tourist attractions |
| Yellow | Black | Black | temporary and diversion signs |

Route status on a single sign is carried by panels: blue for a motorway, green for a primary route, brown for
a tourist attraction, white with a red border for a Ministry of Defence site; a patch may only be blue or
green [S same, panel table]. Distances are in miles and yards only [S same, units section]. Typefaces are
Transport Medium (light on dark) and Transport Heavy (dark on light), with the Motorway face for route
numbers [S same, typefaces]. The M3 route marker itself is a blue rectangle with a white "M3" and a white
motorway symbol [S pine m3].

So, for the film as drawn: sheets 3, 6, 9 and 11 all draw the plate green with white lettering, which is the
primary route sign [S `make_title_world.py`]. The film's own shot list calls it "a green sign over the road"
[S shot list section 4], so the art and the shot list agree with each other and disagree with the real
motorway rule [S sign colour table]. `Q1`.

The palette does not force the green. The drive's background groups hold three blues and three whites, and
the sprite group sp2 holds dark blue `#004058` with light grey `#bcbcbc`, so a dark blue plate with pale
lettering is drawable in the solved scene today [S `data/palettes/scene_title.json`]. The exterior map
scenes hold a stone group, a brick group, a green group, and for Southampton a water blue group [S
`data/palettes/scene_westminster.json`, `scene_winchester.json`, `scene_southampton.json`].

---

## 6. Q: for gamedev

These are disagreements between this file's sources, the shot list and the art as it stands. I am not
deciding any of them. None of them changes a shot's steps or bars.

- `Q1` Sign face colour. The shot list and `make_title_world.py` draw the four plates green with white
  lettering; the real rule for a motorway advance direction sign is white lettering on blue, with green
  reserved for primary route panels and destinations reached off the motorway. Gamedev to decide: keep the
  green face as an art decision, or move to blue. If blue, the drive's solved background groups already hold
  blue and white, and the sprite group sp2 (dark blue with light grey) could carry a motorway plate today; a
  brighter blue with true white means re-solving a sprite group [S `data/palettes/scene_title.json`].
- `Q2` Plate text and plate position. On the film's numbers, 43 miles remaining falls on the Fleet
  approach, so sheet 6 agrees with the real place. The 30 and 20 plates, however, are shown after the
  cutting, while 30 and 20 miles from Southampton lie north of it, and the "WINCHESTER 12" and "WINCHESTER
  2" lines belong respectively north of Winchester and just before it, not south of it. Gamedev to decide:
  keep the film's compression and the plates where the beats put them, or re-read the last two plates to
  places that are real at that point (for example "SOUTHAMPTON 12" and "SOUTHAMPTON 8", or dropping
  Winchester once it is behind the car).
- `Q3` The cathedral's direction. A southbound driver has Winchester Cathedral behind them after the
  cutting. This is not a conflict with any spec, only a fact the shot list cannot know; if gamedev wants a
  cathedral ahead at that point, the nearest real cathedral ahead is not on this route at all. Recorded, not
  raised as a conflict.
- `Q4` The services identity. The interlude is at "the services" and the surveyed map is Fleet, which fits
  the film's position after the 43 plate. Winchester services sit between J8 and J9, after the 30 plate in
  real order. If gamedev intends Winchester, the interlude sheet's place changes and the map work needs that
  frame instead of Fleet's. Gamedev to confirm which site.
- `Q5` Art gaps already in the shot list. Shot 2 (the London street and the Thames), shot 4 (rain and
  wipers) and shot 12 (the night docks) have no picture in the title layer set; that is the shot list's own
  `Q3`, repeated here only so the art owner sees it next to the fact sheets. The docks sheet adds one
  constraint: the nearest existing picture, `quay_dusk`, is dusk, and the sourced port look at night is dark
  cranes with warm amber lamps and a lit ship, which is a different picture.
- `Q6` The chalk horse. The drawn horse at L3 x 148 has no counterpart in the surveyed frame or in the
  sources read; chalk figures of that kind belong to Wiltshire and Oxfordshire, not to this down [I].
  Gamedev to decide whether to keep an invented figure or drop it. Recorded, not raised as a conflict.

---

## 7. Check, with the numbers printed

- Sheets for drive shots: 12 shots in `knowledge/DRIVE-SHOT-LIST.md` section 2, and 12 sheets in section 3.
  Checked shot by shot: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12. Every one is present, and each names its own
  commands, bars and asset names from the shot list.
- Extra sheets: 1 for the services interlude (marked as not one of the twelve, so the count of 12 is not
  inflated) and 5 for the ship, so 18 sheets in all.
- Ship locations covered: the berth (Ocean Terminal, berth 46), the quay and gate (Dock Gate 4), the
  weather deck (`ship_small`), the cabin and wardroom (`ship_cabin`), the corridor and hold (spec 15
  sample). The two built maps are both covered, and the three sample rooms are covered in sheet SH5.
- Grades in the file: a scan of the 18 sheets after writing split each sheet into bullet blocks and
  reported every block holding neither an `[S]` nor an `[I]` tag. It reports 18, one per sheet, and all 18
  are the per sheet `Sources:` list, which is the source list itself. Every other fact block carries a tag.
- Palette numbers: 54 master colours; spec 13 caps a room at 16 and the test pins 25 entries by PPU
  counting; the drive art uses 14 master roles and resolves to backdrop 15 plus 4 background groups of 3 and
  4 sprite groups of 3 in `data/palettes/scene_title.json`; `deck_day` 14 roles, `ship_cabin` 13,
  `lower_deck` 13, with map declarations of 10 and 7; the ship scene resolves to backdrop 15 plus 4 groups
  of 3 each way in `scene_ship.json`; spec 15's own sheet uses 10 colours. All read from the named files,
  none counted by eye.
- Distances: 4 figures computed here by haversine on OpenStreetMap anchors (34.5, 60.2, 69.4 and 0.4
  miles), marked `[I]` in the sheets because a straight line is not a road.
- Copyright: no source text is copied. Sign strings (`SOUTHAMPTON`, `BASINGSTOKE`, `WINCHESTER` and the
  numbers), proper names, and tabulated colour and dimension values are the only verbatim material. Every
  other line is a paraphrase with its source named. The OpenStreetMap geometry is ODbL 1.0 and the derived
  measurements are attributed in the sheets; Wikipedia text is CC BY SA 4.0 and was read, not copied.
- Dashes: this file contains no em dash and no en dash. Checked with a character search over the file after
  writing.

## 8. What this file does not do

It does not choose a palette for a new room, add a colour, change a sign frame, move a shot, or touch
`data/scenes/all.json`, `data/maps/*`, `data/palette.json` or any art script. It does not place NPCs or
triggers. Those are gamedev's. It also does not fill the art gaps in `Q5`; it names them so the art owner
can see them against the facts.

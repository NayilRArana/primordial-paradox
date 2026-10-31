# Real places: five tile map specs built from OpenStreetMap

Status: draft specs for the gamedev lane, generated from live map data on 2026-10-22T19:42:36+00:00.
This file is the written spec. The machine copy with the same numbers is
`data/maps/real_places.json`; if the two ever disagree, the JSON is the one that was
measured and this file is stale.

## Why this exists

Nayil's rule for this project: maps must be real places, not invented layouts. Every
coordinate, road line, water edge and building block below comes from OpenStreetMap
geometry, rasterised at a stated scale. Nothing here is drawn by eye, and no map or
satellite image was traced or downloaded.

## Method

1. Pick an anchor coordinate and a metres per tile so the frame is exactly 64 by 48
   tiles, which at 16 px tiles is 1024 by 768 px, four NES screens of 256 by 192.
2. Read the area from the OpenStreetMap map API (`api.openstreetmap.org/api/0.6/map`)
   for a box 1.5 times the frame, so river and dock polygons have room to close.
3. Where a water area is a relation whose ring still cannot close, read that relation
   with `/full` so its complete outline arrives, then fill it.
4. Rasterise with the project's existing rasteriser, `tools/osm_to_map.py`
   (`build_map`), which classifies ways and areas and paints them in a fixed layer order
   with water and quay edges cleaned of one tile islands.
5. Print one character per tile.

Polite use: one request per place, a User-Agent naming the project, a few seconds
between requests, and every response cached on disk so a rerun reads the cache. Overpass
was the first choice and it was answering 502 at capacity during this run, so the map API
is the live source. Nominatim answered 403 to this client, so it is not used.

## Legend

| glyph | class | meaning |
| --- | --- | --- |
| `R` | road | major road: motorway, trunk, primary, secondary, and their links |
| `-` | road | minor road: tertiary, residential, service, unclassified |
| `~` | water | river, dock, sea |
| `B` | building | any building footprint (doors folded into the footprint) |
| `,` | grass | park, downland, verge, golf course, playing field |
| `#` | rail | railway, siding, platform |
| `p` | path | footway, path, cycleway |
| `=` | quay | quay, pier, dock apron |
| `.` | ground | hardstanding, bare ground, anything not classified |

The card asks for five classes: road, water, building, grass, rail. All five are
present. Path and quay are added because a footway is not a road and a dock apron is not
ground, and folding either into a neighbour would misreport the place. Ground is the
fallback for everything the source does not classify.

## The five places at a glance

| # | place | anchor (lat, lon) | frame | metres per tile | size |
| --- | --- | --- | --- | --- | --- |
| 1 | Westminster Bridge and the Big Ben corner | 51.500900, -0.124400 | 64x48 | 8.0 | 512 by 384 m |
| 2 | M3 Fleet services, both carriageways | 51.295800, -0.855200 | 64x48 | 12.0 | 768 by 576 m |
| 3 | Winchester, the M3 cutting through Twyford Down | 51.041500, -1.308500 | 64x48 | 18.0 | 1152 by 864 m |
| 4 | Southampton Ocean Terminal and the Old Docks berths | 50.893000, -1.399000 | 64x48 | 12.0 | 768 by 576 m |
| 5 | Southampton Dock Gate 4 and the Eastern Docks road | 50.897000, -1.392900 | 64x48 | 16.0 | 1024 by 768 m |

## 1. Westminster Bridge and the Big Ben corner

Region: London, City of Westminster.

The river is the spine of this box: the Thames runs north to south down the east side, Westminster Bridge crosses it, and the Palace of Westminster with the Elizabeth Tower (Big Ben) fills the west bank. Traffic runs on the Embankment and Bridge Street; Parliament Square sits behind the palace.

Frame: 64 by 48 tiles, 512 by 384 m, 8.0 m per tile, north up, origin top left.

Bounding box: south 51.499175, west -0.128094, north 51.502625, east -0.120706. Anchor 51.500900, -0.124400.

### Landmarks, with real offsets from the frame centre

| landmark | OSM | kind | lat, lon | east m | north m | tile x, y |
| --- | --- | --- | --- | --- | --- | --- |
| Elizabeth Tower | way 123557148 | yes | 51.500712, -0.124552 | -10.5 | -20.9 | 30, 26 |
| Big Ben | node 1802652184 | clock | 51.500704, -0.124572 | -11.9 | -21.8 | 30, 26 |
| Westminster Bridge | node 4084403503 | feature | 51.500856, -0.123964 | +30.2 | -4.9 | 35, 24 |
| Westminster Abbey | node 6188865202 | feature | 51.499662, -0.127313 | -201.9 | -137.8 | 6, 41 |
| Westminster Pier | node 469762514 | feature | 51.501595, -0.124062 | +23.4 | +77.4 | 34, 14 |
| Parliament Square | node 11939799210 | feature | 51.500156, -0.126525 | -147.3 | -82.8 | 13, 34 |

### Road layout

Named major roads in frame: Bridge Street, Broad Sanctuary, Great George Street, Old Palace Yard, Parliament Square, Parliament Street, Saint Margaret Street, St. Margaret Street, Victoria Embankment, Westminster Bridge.
Named minor roads in frame: Canon Row, Commissioner's Yard, Derby Gate, Great George Street, King Charles Street, Laundry Road, Little George Street, New Palace Yard, Old Palace Yard, Parliament Square.

Water named in frame: Jubilee Fountain.
Working rail named in frame: Jubilee Line.

### Grid

```
   0000000000111111111122222222223333333333444444444455555555556666
   0123456789012345678901234567890123456789012345678901234567890123
00 BBBBBBBBBBBBBBBpRRRR.BBBBBBBB-BBBBBBRRRpp~==~~~~~~~~~~~~~~~~~~~~
01 BBBBBBBBBBBBBBBpRRRBBBBBBBB------B--RRppp~==~~~~~~~~~~~~~~~~~~~~
02 BBBBBBBBBBBBBBBpRRRBBBBBBBBBBBBBBBBBRRppp~==~~~~~~~~~~~~~~~~~~~~
03 BBBBBBBBBBBBBBBpRRRBBBBBBB-BBBBBBBBBRRpp~~==~~~~~~~~~~~~~~~~~~~~
04 BBBBBBBBBBBBBBBBRRRBBBBBBBBBBBBBBBBpRRpp~~==~~~~~~~~~~~~~~~~~~~~
05 ------ppBBBBBBBBRRRBBBBBBB-BBBBBBBBpRRpp~===~~~~~~~~~~~~~~~~~~~~
06 pp--pp------BB-pRRRBBBBBB.BBBBBBBBBRRRpp~===~~~~~~~~~~~~~~~~~~~~
07 BBBBBBBBBBBpBBp-RRRBBBBBB-BBBBBBBBBRRRpp~===~~~~~~~~~~~~~~~~~~~~
08 BBBBBBBBBBBBBBBpRRRBBBB---BBBBBBBBpRRppp~===~~~~~~~~~~~~~~~~~~~~
09 BBBBBBBBBBBBBBBpRRRBBBBBBBBBB------RRppp~===~~~~~~~~~~~~~~~~~~~~
10 BBBBBBBBBBBBBBppRRRBBBBBBBBBBBBBBBpRRppp~==~~~~~~~~~~~~~~~~~~~~~
11 BBBBBBBBBBBBBBppRRRBBBBBBBBBBBBBBBpRRpp~~p=~~~~~~~~~~~~~~~~~~~~~
12 BBBBBBBBBBBBBBpRRRRBBBBBBBBBBBBBBBpRRpp~ppp~~~~~~~~~~~~~~~~~~~~~
13 BBBBBBBBBBBBBBBRRRRBBBBBBBBBBBBBBBRRRpppppp~~~~~~~~~~~~~~~~~~~~~
14 BBBBBBBBBBBBBBpRRRRBBBBBBBBBBBBBBpRRpBppp==~~~~~~~~~~~~~~~~~~###
15 BBBBBBBBBBBBBBpRRRRBBBBBBBBBBBBBBpRRRBppp==~~~~~~~~~~~~~~#######
16 BBBBBBBBBBBBBBpRRRRBBBBBBBBBBBBBBpRRRBpp~==~~~~~~~~~~~##########
17 BBBBBBBBBBBBBBpRRRRBBBBBBBBBBBBBBBRRRpp~~==~~~~~~~~#############
18 BBBBBBBBBBBBBBpRRRBBBBBBBBBBBBBBBBRRRpp~~==~~~~~#############~~~
19 p--pBBBBBBBBBBpRRRBBBBBBBBBBBBBBBpRRRpp~~~~~##############~~~~~~
20 ------ppppppBBpRRRBBBBBBBBBBBBBBBRRRRpp##############~~~~~~~~~~~
21 BBpp---RRRRRRRRRRRRBBBBBBBBBBBBBBRRRRpp########~~~~~~~~~~~~~~~~~
22 BB##-.RRRRRRRRRRRRRRRRRRRRRRRRRppRRRRpppppppp~~~~~~~~~~~~~~~~~~~
23 BB##-RRRRpRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRppppppppppppppppppppp
24 BB#ppRR#ppppp#RRRRpBpppppppppRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRpp
25 BB,p#RR#p###ppppRRpBB#,,,pppBBBBpppppppppRRRRRRRRRRRRRRRRRRRRRRR
26 BB,p.RR.p,,,,,#pRRpBBB------BBBB,,,,,,p~~~~~~~~~~~~~~pppppppRRRR
27 BB,pRRR.p,,,,##pRRp-B-------BBBB,,,,,~p~~~~~~~~~~~~~~~~~~~~~~~~~
28 BB,pRRppp,,####pRR---,,,~~,-BBBBBBBB,~~~~~~~~~~~~~~~~~~~~~~~~~~~
29 BBppRRpp,,#####pRR---,,,~~,-BBBBBBBBBBB~~~~~~~~~~~~~~~~~~~~~~~~~
30 BBppRRpp######,pRRp,--,,,,,-BBBBBBBBBBB~~~~~~~~~~~~~~~~~~~~~~~~~
31 BBppRRRpppp#,,,pRRpp-----.--BBBBBBBBBBB~~~~~~~~~~~~~~~~~~~~~~~~~
32 BBppRRRRpppppppRRRBBBpBB----BBBBBBBBBBB~~~~~~~~~~~~~~~~~~~~~~~~~
33 BBpRRRRRRRRRRRRRRRBBBBBBBBBBBBBBBBBBBBB~~~~~~~~~~~~~~~~~~~~~~~~~
34 RRRRRRRRRRRRRRRRRRBBBBBBBBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~
35 RRRRRRRRRBB,,,pRRRR,,BBBBBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~
36 RRRR,,,p,BBBBBBRRRR,,BBBBBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~
37 RR,,,,,pBBBBBBBpRRR,BBBBBBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~
38 ,,,,,,,pBBBBBBBpRRRBBBBBBBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~
39 pppppp,p,BBBBBBpRRRBBBBBBBBBBBBBBBBB.p~~~~~~~~~~~~~~~~~~~~~~~~~~
40 .BBBBBBBBppppBBpRRR,BBBBBBBBBBBBBBBB.p~~~~~~~~~~~~~~~~~~~~~~~~~~
41 .BBBBBBBBB,,,,,pRRp,BBBBBBBBBBBBBBBBpp~~~~~~~~~~~~~~~~~~~~~~~~~~
42 BBBBBBBBBBB,,,,pRRppBBBBBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~~
43 BBBBBBBBBBBBBB--RRp.BBBBBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~~
44 BBBBBBBBBBBBBBBBRRR.BBBBBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~~
45 BBBBBBBBBBBBBBBBBRR....BBBBBBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~~
46 BBBBBBBBBBBBBBBBBRR.....BB.BBBBBBBBBp~~~~~~~~~~~~~~~~~~~~~~~~~~~
47 BBBBBBBBBBBB-BB--RRp...BBBBBBBBBBBB.p~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

Tile counts (frame holds 3072 tiles): R road 391; - road 91; ~ water 988; B building 1065; , grass 87; # rail 114; p path 271; = quay 38; . ground 27.

### Sources

Geometry: OpenStreetMap, read through the map API on 2026-10-22, ODbL 1.0.
Text consulted: https://en.wikipedia.org/wiki/Westminster_Bridge (CC BY-SA 4.0, no images downloaded).
Text consulted: https://en.wikipedia.org/wiki/Big_Ben (CC BY-SA 4.0, no images downloaded).
Text consulted: https://en.wikipedia.org/wiki/Palace_of_Westminster (CC BY-SA 4.0, no images downloaded).

## 2. M3 Fleet services, both carriageways

Region: Hampshire, between Fleet and Hartley Wintney.

A motorway services pair: the M3 runs southwest to northeast through the middle, a service area sits on each side, and a footbridge crosses the carriageways. The card's real geometry is two blocks of buildings, a lot of hardstanding, and a wide road; there is no town street pattern here.

Frame: 64 by 48 tiles, 768 by 576 m, 12.0 m per tile, north up, origin top left.

Bounding box: south 51.293213, west -0.860717, north 51.298387, east -0.849683. Anchor 51.295800, -0.855200.

### Landmarks, with real offsets from the frame centre

| landmark | OSM | kind | lat, lon | east m | north m | tile x, y |
| --- | --- | --- | --- | --- | --- | --- |
| Welcome Break Fleet Services | way 32806558 | services | 51.294530, -0.860547 | -372.2 | -141.4 | 0, 35 |
| Fleet Services | node 503401213 | bus_stop | 51.297292, -0.853549 | +114.9 | +166.1 | 41, 10 |
| Shell Fleet Services (West) | way 61478612 | fuel | 51.294682, -0.859727 | -315.1 | -124.5 | 5, 34 |
| Shell Fleet Services (East) | way 61478613 | service | 51.297190, -0.852574 | +182.8 | +154.7 | 47, 11 |
| Former Scott Mills Bridge | way 24428692 | footway | 51.296026, -0.855598 | -27.7 | +25.2 | 29, 21 |

### Road layout

Road route relations in frame: M3 J4a, M3 motorway, Strategic Road Network.
Named minor roads in frame: Ramsdell Road, Rotten Green, Shell Fleet Services (East), Stockbridge Road, Tadley Close, Tunworth Close, Turgis Road, Turners Avenue, Twyford Close, Upper Wield Drive.


### Grid

```
   0000000000111111111122222222223333333333444444444455555555556666
   0123456789012345678901234567890123456789012345678901234567890123
00 .........................,,,,,,,,,,,--,,,,,,,,,--.............BB
01 ........................,,,,,,,,,,,--,,,,,,,,,,,,--............-
02 ......................,,,,,,,,,,,,--,,,,,,,,,,,,,,--.......---BB
03 ......................,,,,,,,,,,,--.,,,,,,,,,,,,,,,,--.-----..BB
04 .......,.............,,,,,,,,,,--,----,,,,,,,,,,,,,,,--........-
05 .....,,,.........,,,.,,,,,,,,,-----...---,,,,,,,,,,,,,,........-
06 ....,,,,........,,,,,,,,,,,,--,-------..---,,,,,,,,,,,,,,......-
07 ...,,,,,,.......,,,,,,,,,,,--,--,.--.--....-,,,,,,,,,,,,,,.....-
08 ..,,,,,,,,,..........,,,,,----,,,..-..--...--BB---,,,,,,,,,,,,,,
09 ,,,,,,,,,,,,......BBB,,,--,---,,,..-...-...-.BBBBB------,,,,,,,,
10 ,,,,,,,,,,,,,,,,,,BB--,----.--,,,,.-.----..-.BBBBB.BBB-RRRRRR,,,
11 ,,,,,,,,,,,,,,,,,,,-------..--,,,,.---..--.-.BBBBB----,RRRRRRRRR
12 ,,,,,,,,,,,,,,,,,-----,--.----,,,,.-.....---.BB----,,,,,,,,,RRRR
13 ,,,,,,,,,,,,,,-------,--------,,,,--,,,,,,,-----,,,,,,,,,.RRRRRR
14 ,,,,,,,,,,,----,,,-,--..------,BB,-,,,,,,,,-,,,,,,,,,.RRRRRRRRRR
15 ,,,,,,,,,,-,,,,,--,,-.----.BBBBBB,-,,,,,,,,,,,,,.RRRRRRRRRRRRRRR
16 ,,,,,,,,,-,,,,,--,,--------BBBBBBBB,,,,,,,,,.RRRRRRRRRRRRRRRRRRR
17 ,BB,,,,--,,,,--,,,----.----BBBBB..B,,,,..RRRRRRRRRRRRRRRRRRR.--B
18 .BB.,,--,,,,--,,,,-----.---BBBBB....RRRRRRRRRRRRRRRRRRRRRBB--BBB
19 .....--,,,--,,,,,--------...pB..RRRRRRRRRRRRRRRRRRRRRBBBBBBBBBB.
20 ....-,,,,--,,,,,------......RRRRRRRRRRRRRRRRRRRRRR-..BBBB---BBBB
21 ...--,,--.,,,,,,-.......RRRRRRRRRRRRRRRRR--RRRRRB-B-B-BBBB-BBBBB
22 ..---,--,,,,,.RRR...RRRRRRRRRRRRRRRR..-----RRR,,BBBBBBBBBB-BBBB,
23 ..-,---,,,.RRRRRRRRRRRRRRRRRRRRR....---..-,,,,,,,BB-BBBBBB-BBB-p
24 .----,,..RRRRRRRRRRRRRRRRRRR.BpB.-----..-,,,,,,ppppp-BBBBBBB.BBp
25 --,,.RRRRRRRRRRRRRRRRRRR..BBBBBBB.-------,,pppp,,,,,ppp---BBBB,p
26 ,,RRRRRRRRRRRRRRRRRR..---BBBBBBBB--.----.BBBB,pppppppBBBp--BBBpp
27 RRRRRRRRRRRRRRR..-----....BBBBBBB---.---.B-BB~~~~,,pp.BBBBBp-Bp,
28 RRRRRRRRRRR...----.......BBBBBBBB------.BBBBBB~~~~~~pBB--B.BBBpp
29 RRRRRRR.....--....-----...BBBBBBB-.----..BBBBBB~~~~pBB.-BBBBBBp,
30 RRR.........-.-----...-.ppBBpp---------BBBBBBBBB~BppBBpBBBBBBp,,
31 ..-------B-----..--...-..pp.....-------.BB-BBBB-BBp-BB-BB-BBBp,,
32 ---.--BB-BB-,,,-.-...-....pBB.B.------.BB-BBBBB-BB..BBBBBBBB,p,,
33 --....BBBBB-,,,--....-...pBBBBB.--BB--BBBBB-.BBB-BBBBBB.BBB-,,,,
34 ..---BBBBBB-,,,,,-..-....pBBBBB.--BB-.BBBBB-B.BBB-BBBBB.BB-,,,,,
35 B....--BBB--,,,,,--.-...pp.--BB-...-.BB.BB-BBBBpBB-BBBBBBB,,,,,,
36 BB......-B--,,,,,,--..p----.-.--.--..BBBB.BBBBBB.BB-BB.BB-,,,,,,
37 .--.......---,,,,,,--.p-.---------BBBBBB-BBB--BB.BB-BBBBB,,,,,,,
38 -..--...---..--,,,,,-.p--.----..BBBBBBB..BB-B-BB.BBBBBBBB,,,,,,,
39 B-..----......---,,,,-----.,,,BBBBBBBB-BBB--BBBBB.BBB-BBB,,,,,,,
40 B-..............------.,,,,,,,,BB---BB.BB--BB.B-BB.BBBBBB,,,,,,,
41 BBBBB...............-,,,,,,,,,,BBBBB-.BB--BB-.BB-BBBBBB-,,,,,,,,
42 ,BBBB...........-.B.BB,,,,,,,,,BBBBB.BB--BB.--.BBBBBBBB-,,,,,,,p
43 pBBB.-B.....BBBBBBBBBB,,,,,,,,,,BB--BB--BB-BBB-.B-BBB--,,,,,,,,p
44 ppBB--BBBBBBBBBBBBB-BB,,,,,,,,,,B..BB.-BBB.BBBBBBBBB-,,,,,,,,,p,
45 ppBBBB-BBBBBB-BBBBBBBB,,,,,,,,,,,-BBB-BBB.BBBBBBBBBB,,,,,,,,,p,,
46 ,BBBB-BB-BBBB-BBBBB---,,,,,,,..BBB---BBB.BBBBBBBBBBB,,,,,,,,pp,,
47 BBBBB-BB.BBBB-BBB----.B,,,.....BBBB-BBB-.BBBB-BBBBB,,,,,,,,pp,,,
```

Tile counts (frame holds 3072 tiles): R road 309; - road 593; ~ water 15; B building 664; , grass 807; p path 71; . ground 613.
Glyphs with zero tiles in this frame: # (rail): no working railway inside this frame; = (quay): no mapped quay or apron inside this frame. That is a fact about the place, not a gap in the data: the frame was chosen for its landmark, not to force every class into shot.

### Sources

Geometry: OpenStreetMap, read through the map API on 2026-10-22, ODbL 1.0.
Text consulted: https://en.wikipedia.org/wiki/Fleet_Services (CC BY-SA 4.0, no images downloaded).
Text consulted: https://en.wikipedia.org/wiki/M3_motorway_(Great_Britain) (CC BY-SA 4.0, no images downloaded).

## 3. Winchester, the M3 cutting through Twyford Down

Region: Hampshire, southeast of Winchester.

Chalk downland with a motorway cut through it. The M3 sweeps in a wide curve through a chalk cutting, the Itchen Navigation and the River Itchen run in the valley to the west, and the ground either side is open down and golf course. This is the emptiest of the five boxes and the best one for a long visible road line.

Frame: 64 by 48 tiles, 1152 by 864 m, 18.0 m per tile, north up, origin top left.

Bounding box: south 51.037619, west -1.316729, north 51.045381, east -1.300271. Anchor 51.041500, -1.308500.

### Landmarks, with real offsets from the frame centre

| landmark | OSM | kind | lat, lon | east m | north m | tile x, y |
| --- | --- | --- | --- | --- | --- | --- |
| Twyford Down Cutting | way 306310686 | cliff | 51.042283, -1.308587 | -6.1 | +87.2 | 31, 19 |
| Twyford Down | node 3111838899 | locality | 51.040627, -1.309250 | -52.5 | -97.2 | 29, 29 |
| Hockley Cross | node 1596591884 | motorway_junction | 51.039716, -1.312775 | -299.2 | -198.6 | 15, 35 |
| Saint Catherine's Lock | node 611718036 | weir | 51.043411, -1.315638 | -499.6 | +212.7 | 4, 12 |
| Itchen Navigation (Disused) | way 44911141 | stream | 51.041412, -1.316511 | -560.7 | -9.8 | 0, 24 |

### Road layout

Road route relations in frame: European route E05, M3 J10, M3 J11, M3 motorway, Strategic Road Network.

Water named in frame: Itchen Navigation (Disused), Saint Catherine's Lock.
Disused rail named in frame, not drawn: Newbury and Winchester Line.

### Grid

```
   0000000000111111111122222222223333333333444444444455555555556666
   0123456789012345678901234567890123456789012345678901234567890123
00 ,,,,,~pp,,,,pp,,,pp,,p,,,pp,ppp,,,.......,pp,,p,pRRRRp,,pppp,,,,
01 ,,,,~~pp,,,,pp,,,ppppp,,,pp,ppp,........,,p,,,pp.RRRRp,,,p,,,,..
02 ,,,,~~pp,,,,pp,,,p,p,,,,,ppppppp.......,,ppppppp.RRRR,,,,,p,,...
03 ,,,,~ppp,,,,pp,,,p,p,,,,,,pppp,pp.....,,ppp,,,ppRRRRp,,,pppp....
04 ,,,,~p,p,,,,ppp,,pp,,,,,,pppp,,,pp...,,,p,,,,,p.RRRRp,pp,,,p,...
05 ,,,,~ppp,,,,,ppp,p,,,,,,ppp,ppp,ppp..,,p,,,,,ppRRRRR,p,,,..pp,..
06 ,,,,~pp,,,,,,,ppppp,pppppppp,ppppppp,,pp,,,,,ppRRRRpp,,,....p,..
07 ,,,,~pp,,,,,pppppppppppppppppppppppppp,,,,,,ppRRRRRp,,......,p,.
08 ,,,,~pp,,,,p,,,,,,,,p,,,,,,,,,,,p,,,pp,,,,,pp.RRRRp,,........pp.
09 ,,,,~pp,,,p,,,,,,,,,p,,,,,,,,,,,pp,pp,,,,,,ppRRRRR,...........pp
10 ,,,,~pp,pp,,,,,,,,,,p,,,,,,,,,,,pppp,,,,,,pp.RRRRp............,p
11 ,,,,~ppppp,,,,,,,,,p,,,,,,,,,,,ppp,,,,,,,pp.RRRRp..............,
12 ,,,~~p,,ppppp,,,,,,pp,,,,,,pppppp,,,,,,,pp.RRRRRp...............
13 ~~~~p,,,pp,,ppppp,,pp,ppppp,,,pp,,,,,,,pppRRRRR.p...............
14 ~~~~p,,,pp,,,,,,ppppppp,,,,,,pp,,,,,,,pppRRRRR..p...............
15 ~~,~p,,,pp,,,,,,,,,pp,,,,,,,,,pp,,,,,pppRRRRR...p...............
16 ,,,~p,,,ppp,,,,,,,,p,,,,,,,,,,,ppp,,pp.RRRRR....p...............
17 ,,,~p,,,p,p,,,,,,,,p,,,,,,,,,,,,,pppp.RRRRRR....p...............
18 ,,~p,,,,p,p,,,,,,,,pp,,,,,,,,,,,,ppp.RRRRRR.....p...............
19 ,,~p,,,,p,,p,,,,,,,,p,,,,,,,,,,pppp.RRRRR.......p...............
20 ,,~p,,,,pp,p,,,,,,,,p,,,,,,,,pppp.RRRRRR.........p..............
21 ,~~p,,,,ppppp,,,,,,,p,,,,,,ppppp.RRRRRR..........p..............
22 ,~pp,,,ppp,pp,,,,,,,p,,,ppp,pp..RRRRRR...........p..............
23 ,~p,,,,pppppp,,,,ppppppp,,,pp..RRRRRR............p..............
24 ~~p,,,,p,ppppppppp,,,,,,,ppp.RRRRRR...............p.............
25 ~pp,,,ppp,,,,,,,,,,,,,,,pp.RRRRRR.................p.............
26 ~p,,,,pp,,,,,,,,,,,,,,pp..RRRRRR...................p............
27 ~p,,,,p,,,,,,,,,,,,,,pp.RRRRRRR....................p............
28 pp,,,pp,,,,,,,,,,,,pp..RRRRRR......................p............
29 p.,,,p,,,,,,,,,,,pp..RRRRRR........................p............
30 p,,,,p,,,,,,,,,,pp..RRRRRR........................pp............
31 p,,,,p,,,,,,,,pp..RRRRRR.........................pp.............
32 p,,,pp,,,,,,,pp.RRRRRRR..........................p..............
33 p,,,p,,,,,,pp..RRRRRR...........................pp..............
34 ,,,pp,,,,,pp.RRRRRRR...........................pp...............
35 ,,,p,,,,pp..RRRRRRp............................p................
36 ,,pp,,,pp..RRRRRR.............................pp................
37 ,pp,,,ppRRRRRRRR..............................p.................
38 ,p,,ppRRRRRRRRR...............................p.................
39 p,,pRRRRRRRRR.................................p.................
40 p,pRRRRRRRRR.................................p..................
41 ,RRRRRRRRRR..................................p..................
42 RRRRRRRRRR..................................pp..................
43 RRRRRRRR....................................p...................
44 RRRRRRR....................................p....................
45 RRRRRR....................................pp....................
46 RRRR......................................p.....................
47 RRR......................................p......................
```

Tile counts (frame holds 3072 tiles): R road 281; ~ water 41; , grass 794; p path 503; . ground 1453.
Glyphs with zero tiles in this frame: - (road): no tertiary, residential or service road inside this frame; B (building): no building footprint inside this frame; # (rail): no working railway inside this frame; = (quay): no mapped quay or apron inside this frame. That is a fact about the place, not a gap in the data: the frame was chosen for its landmark, not to force every class into shot.

### Sources

Geometry: OpenStreetMap, read through the map API on 2026-10-22, ODbL 1.0.
Text consulted: https://en.wikipedia.org/wiki/Twyford_Down (CC BY-SA 4.0, no images downloaded).
Text consulted: https://en.wikipedia.org/wiki/St_Catherine%27s_Hill (CC BY-SA 4.0, no images downloaded).

## 4. Southampton Ocean Terminal and the Old Docks berths

Region: Southampton, Eastern Docks.

A cruise quay: deep water on the west side, a straight quay line, a terminal shed and berth heads along it. Almost everything else in the box is hardstanding, which makes the water and quay edge the whole read of the map.

Frame: 64 by 48 tiles, 768 by 576 m, 12.0 m per tile, north up, origin top left.

Bounding box: south 50.890413, west -1.404469, north 50.895587, east -1.393531. Anchor 50.893000, -1.399000.

### Landmarks, with real offsets from the frame centre

| landmark | OSM | kind | lat, lon | east m | north m | tile x, y |
| --- | --- | --- | --- | --- | --- | --- |
| Ocean Cruise Terminal | way 314606884 | commercial | 50.892923, -1.400214 | -85.2 | -8.6 | 24, 24 |
| Berth 46 | node 729188561 | locality | 50.893320, -1.399398 | -27.9 | +35.6 | 29, 21 |
| Berth 45 | node 729188724 | locality | 50.893614, -1.398533 | +32.8 | +68.4 | 34, 18 |
| Berth 47 | node 729188786 | locality | 50.891713, -1.399996 | -69.9 | -143.3 | 26, 35 |
| Berth 44 | node 729188488 | locality | 50.891916, -1.398454 | +38.3 | -120.7 | 35, 34 |
| Eastern Docks | node 13332325982 | quarter | 50.895417, -1.399533 | -37.4 | +269.1 | 28, 1 |

### Road layout

Road route relations in frame: A33.
Named minor roads in frame: Atlantic Way, Central Road, Cunard Road, European Way, Lane 1, Lane 2, Lane 3, Maritime Walk, Ocean Road, Ocean Way.

Water named in frame: Berth 49.

### Grid

```
   0000000000111111111122222222223333333333444444444455555555556666
   0123456789012345678901234567890123456789012345678901234567890123
00 ~~~---.--------------.-........----.---BBBBBBB....BBBB-BB-.-.BBB
01 ==~~~~~-..------------.--....---..-.---BBBBBBB....BBB.-BB-.-....
02 ~===~~~---------------..------.----.--BBBBBBBB....BBBB-BB---....
03 ~~~==~~-------.-----.---....-.------.BBBBBBBBB....BBB.-BBBB-....
04 ==~~~.~----.-----------.-...---BB---.-BB#.........BBBB-BBBB-----
05 ~==~~~~--------------..--.B---BBBB-----##.........BBBB-......BBB
06 ~~~==~~-------------.----.B-.-BBBB-----##.........BBB.-BBBB-.BBB
07 ~~~~===~---------------------..BB---B---#.........BBBB-BBBB-.--B
08 ==~~~~=~------.---------..-------BBBBB--#.........BBBB------.--.
09 .===~=~~---------------..----.~~~BBBBB--##........BBBB---------.
10 ========~-----------.--..----.~~~BBBBB--##..........B.----...---
11 ========~-------.--.--------..~~~~BB...--#............---------B
12 ~~===~==~---------------.-BB..~~~~.BBB.-##..............------BB
13 ~~~~=~~~~~--.----------.--BBB.~~~~.BBB.-###...............-BBBB,
14 ~~==~~===~----------.--.--BBB~~~~~~BBBB-------............-BBBB,
15 ~~~======~~~-----------.--BBB~~~~~~BB...-##.---...........-BBBB,
16 ~~~~~===~~~~--.--------.-BBBB~~~~~~~....-##-BB-------......BBBBB
17 ~~~~~~~===~~~---------.--BBB.~~~~~~~....-#-BBB-----.-------.---B
18 ~~~~~~~===~~~-------.-.--BBB~~~~~~~~~...---#B-..-BB---.BB..-----
19 ~~~~~~~~~~~~~~...-~.----BBBB~~~~~~~~~....--#-..-.BBB---BB-------
20 ~~~~~~~~~=~~BB.BB-~~~-.-BBBB~~~~~~~~~....-#-.---.BBBB--p-pBB-..-
21 ~~~~~~~~~==~BB.BB~~~--.BBBB.~~~~~~~~~~...-#-..-.BBBBBB---BBB-.--
22 ~~~~~~~~~~~~~BBBB~~~-..BBBB.~~~~~~~~~~...#---.B.BBBBBBB--BBB--BB
23 ~~~~~~~~~~~=~BB-B~~~-..BBBB~~~~~~~~~~~~..#-B.BBBBB.BBBBBBBBBBBBB
24 ~~~~~~~~~===~~~--~~~-..BBBB~~~~~~~~~~~~..#-BB-BBB.--BBBBBBBBBBBB
25 ~~~~~~~~~~=~~~~~BBBB---BBBB~~~~~~~~~~~...#------.-.--.B.BBBBBBBB
26 ~~~~~~~~~~~~~~~~~BBBBBBBBB.~~~~~~~~~~~...-#BB--.--...--BBBBBBBBB
27 ~~~~~~~~~~===~~~~~BBBBBBBB.~~~~~~~~~~~...--BB.----....-BBBBBBBBB
28 ~~~~~~~~~~~=~~~~~~~~~BBBBB~~~~~~~~~~~~..#--...-~~--..-BBBBBBBBBB
29 ~~~~~~~~~~~~~~~~~~==~-BBBB~~~~~~~~~~~...#--...-~~~~---BBBBBBBBBB
30 ~~~~~~~~~~~~~~~~~~===-BBB.~~~~~~~~~~~...#--...-~~~~~.-BBBBBBBBBB
31 ~~~~~~~~~~~~~~~~~~~==BBBB.~~~~~~~~~~~...#--...-~~~~~~.-BBBBBBBBB
32 ~~~~~~~~~~~~~~~~~~~~~BBBB~~~~~~~~~~~~...#--...-~~~~~~~~--BBBBB-B
33 ~~~~~~~~~~~~~~~~~~~~.BBBB~~~~~~~~~~~~...---...-~~~~~~~~~--BBBBBB
34 ~~~~~~~~~~~~~~~~~~~~-..BB~~~~~~~~~~~...#-#-...-~~~~~~~~~~~-BBBB.
35 ~~~~~~~~~~~~~~~~~~~~-BBB.~~~~~~~~~~~...#-#-...-~~~~~~~~~~~~--BBB
36 ~~~~~~~~~~~~~~~~~~~~-BBB~~~~~~~~~~~~...#-#-..-.~~~~~~~~~~~~~.-BB
37 ~~~~~~~~~~~~~~~~~~~~.-BB~~~~~~~~~~~~...#-.-....~~~~~~~~~~~~~~.BB
38 ~~~~~~~~~~~~~~~~~~~...-B~~~~~~~~~~~....-#.-...~~~~~~~~~~~~~~~~pB
39 ~~~~~~~~~~~~~~~~~~~...-.~~~~~~~~~~~...#-#-....~~~~~~~~~~~~~~~pp=
40 ~~~~~~~~~~~~~~~~~~~...-.~~~~~~~~~~~...#-#-....~~~~~~~~~~~~~~pp==
41 ~~~~~~~~~~~~~~~~~~~..--~~~~~~~~~~~~...#-#-....~~~~~~~~~~~~~~~==-
42 ~~~~~~~~~~~~~~~~~~~..-.~~~~~~~~~~~~...--.-....~~~~~~~~~~~~~~~~~-
43 ~~~~~~~~~~~~~~~~~~~~.-.~~~~~~~~~~~...#-#.-...~~~~~~~~~~~~~~~~~~-
44 ~~~~~~~~~~~~~~~~~~~~...~~~~~~~~~~~...#-#.-...~~~~~~~~~~~~~~~~~~-
45 ~~~~~~~~~~~~~~~~~~~~~.~~~~~~~~~~~~...#-#.-...~~~~~~~~~~~~~~~~~~~
46 ~~~~~~~~~~~~~~~~~~~~~.~~~~~~~~~~~~...#-..-...~~==~~~~~~~~~~~~~~~
47 ~~~~~~~~~~~~~~~~~~~~~.~~~~~~~~~~~....-----...~~=~~~~~~~~~~~~~~~~
```

Tile counts (frame holds 3072 tiles): - road 660; ~ water 1257; B building 461; , grass 3; # rail 57; p path 7; = quay 92; . ground 535.
Glyphs with zero tiles in this frame: R (road): no motorway, trunk, primary or secondary road inside this frame. That is a fact about the place, not a gap in the data: the frame was chosen for its landmark, not to force every class into shot.

### Sources

Geometry: OpenStreetMap, read through the map API on 2026-10-22, ODbL 1.0.
Text consulted: https://en.wikipedia.org/wiki/Port_of_Southampton (CC BY-SA 4.0, no images downloaded).
Text consulted: https://en.wikipedia.org/wiki/Southampton (CC BY-SA 4.0, no images downloaded).

## 5. Southampton Dock Gate 4 and the Eastern Docks road

Region: Southampton, Dock Gate 4.

The gate itself is the landmark: a wide dock road, a gate structure, port sheds and rail sidings, with the River Itchen cutting the east edge of the box. This is the only one of the five with working railway in frame.

Frame: 64 by 48 tiles, 1024 by 768 m, 16.0 m per tile, north up, origin top left.

Bounding box: south 50.893550, west -1.400192, north 50.900450, east -1.385608. Anchor 50.897000, -1.392900.

### Landmarks, with real offsets from the frame centre

| landmark | OSM | kind | lat, lon | east m | north m | tile x, y |
| --- | --- | --- | --- | --- | --- | --- |
| Dock Gate 4 | way 1043468564 | yes | 50.896259, -1.398554 | -397.0 | -82.5 | 7, 29 |
| European Vehicle Terminal | node 1418768385 | locality | 50.895749, -1.397101 | -295.0 | -139.3 | 13, 32 |
| Eastern Docks | node 13332325982 | quarter | 50.895417, -1.399533 | -465.7 | -176.2 | 2, 35 |
| River Itchen | way 310937889 | river | 50.896876, -1.387335 | +390.7 | -13.8 | 56, 24 |
| Old Docks PSS | way 1465356953 | feature | 50.896108, -1.395530 | -184.7 | -99.3 | 20, 30 |
| The Dock House | node 11455376818 | restaurant | 50.896458, -1.392056 | +59.3 | -60.3 | 35, 27 |

### Road layout

Named major roads in frame: Albert Road North, Bernard Street, Canute Road, Central Bridge, Itchen Bridge, Platform Road, Royal Crescent Road, Saltmarsh Road, Terminus Terrace, Threefield Lane.
Road route relations in frame: A33, B3038 Road (Great Britain), B3039 Road (Great Britain).
Named minor roads in frame: Albert Road South, Alcantara Crescent, Anderson's Road, Andes Close, Asturias Way, Atlantic Close, Atlantic Way, Bernard Street, Canute Road, Captains Place.

Water named in frame: Ocean Village Marina, River Itchen.
Working rail named in frame: Southampton Eastern Docks Branch.

### Grid

```
   0000000000111111111122222222223333333333444444444455555555556666
   0123456789012345678901234567890123456789012345678901234567890123
00 -BBBBBBB-BBBB-BBBBBRRRB-.BBB-p-BBBB--BBBBB.-BBBBB--...BB-~~~~~~~
01 BBBBBB-B-BRBBBB.-BBBRBBB-.BB-p-BBBB-BBBRRBBBBB.B.--...BB.~~~~~~~
02 B-----BB-BRR-BBB-BBBRBBBBB--#--BBBBBBBBRBBBBB---.--...--.~~~~~~~
03 -BB,ppBBBBBBBBBBBBB-RBBBBBBBpp-B,B-B-BBRBBBBB-.B......--~~~~~~~~
04 BBB,,,BBBpBBBBBBBBBRRBB-BBBBBBBBBB-B-BBRBBBBBBBB-....---pp~~~~~~
05 BBB,,ppBBpBBBB.BBBBRBBBBB-BBBB-BBBBB-BBRBBBBBBBB-BBBBBB-,p~~~~~~
06 .BBBBpBBBBRBBBBBBB-RRBBBBBBBBBB---BB-BBRBBBBBB-BBBBB-----p~~~~~~
07 -BBBBBBBBBRR---BBBRRRBRRBBB#BBBBB-BBBBBR..-BBBBBBBB-BBBp~~~~~~~~
08 B-BB--BBBBR-------RBBBBBRRBR-BBBB-BBBRRR..-BBBB..---BBB~~~~~~~~~
09 B-BBBBBBBBRRRR----RBBBBBBBRRRBRBBBBBpRRRpp----------BBB.~~~~~~~~
10 BBBB.-BBBBBBBBRRRRRBBBBBBBBBBBRBBBBpRRRpp.pp..-.----BB..~~~~~~~~
11 BBBBB--.BBBBBBBBRRR--BBBBBBBBBRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
12 BBBBBB-BBBBBBBBBRBBBBBBBB#BBBBBBBRRRRRRRRRRRRRBBBBRBBRBRRRRRRRRR
13 BBBBBBBBBBBBBBBBBBBBBBBBB-BBBBBBBBRRR-BBBBBp-BBBBB-B--B--~~~~~~~
14 BB.BBBBBBBBBBBBBBBBBBBBBB-BBB-BBBRRRp-BBBBB--BB-BB-BBBBBB~~~~~~~
15 B..BBB-BBBBBBBBBBBBBBBBB#BBBB-RRBBBB-BBBBB--BBBBBB-BBBBBBp===~~~
16 BB.BBBBBBBBBBBBBBBBBBBBB-BBBBRBBBBB-BBBBB--BBBBBBBBBBBBBBB===~~~
17 BBBBBBBBBBBBBBRBBBBBBBBBBBBBRBBBBBBBBBBB.--BpppppBBBBBBBBp~~~~~~
18 --BBBBBBBBBBBBRBBB--.-BBBBBBRBBB-BBBBB-BBB-BBBBppBBppppBBp~~~~~~
19 pppp---BBBBBBBBBBB---#BBBBBBRRBBBBBBB-BBBB-BBBBBBBBBBBBBBp~~~~~~
20 pp,pp,p,--BBBBBBBBB--BBBBB-BBBBBBBBBBBBBBBB-----BBBBBBBBB~~~~~~~
21 pppppppp,,,pRBBBBBB-BBBBBB-BBBBBBBBBBBBBBBB---------.--BB~~~~~~~
22 pp,pp,ppppppRBBBBB-#BBBBBBBBBBBBBBBB--BBBBBBBBBB-------BB~~~~~~~
23 pppppppRRRRRRBBBBBRRBBBBBBBBBBBB-BBBBBBBBBBBBBBB----BBBBB~~~~~~~
24 RRRRRRRRRRRBBBBBBBBBBBBBBBBBBRBB--BBBBBBBBBBB-BB-----BBBp~~~~~~~
25 RRRRRRRBBBBBBBBB#BBBBBBBBBBBBBBBB-BBBBBBBBpBB---BB----BB~~~~~~~~
26 RRRBBBBBBBBBBB--#--BBBBB---BBB-BB-BBBBBp====ppppBBp-BBBB~~~~~~~~
27 ,,,BBBB---...#--.--BB-BBBBB-----B-BBBBp~========BBBBBBBp~~~~~~~~
28 ......-B-----#BB.--BB-BBBBB-----BBBBpp~~~=========pBBBB~~~~~~~~~
29 ......-B.--.#-BB...BB.BBBBBBB---BBBp==============-BBBB~~~~~~~~~
30 .......-----#--....BB.BBBBBBBB.-BBp===============BBBBp~~~~~~~~~
31 .......--.-----.......----BBBB-BBB===============BBBBB~~~~~~~~~~
32 .......-------.....BBB-BBB----BBBB===============BBBBB~~~~~~~~~~
33 ......--------....BBBBBBBB.BBBBBBB===============BBBB~~~~~~~~~~~
34 ....---.---BBBBB..BBBBBB--.BBBBBBB======~~=======BBBBp~~~~~~~~~~
35 ----.-----BBBBBB..BBBBBB--...BBBBp=======~========pppp~~~~~~~~~~
36 ..-------BBBBBBB..BBB.BBBB...BBBBBBBBBB==~==~~~~==~~~~~~~~~~~~~~
37 .B--BB--.BB##.....BBBBBBBB-BBBBBBBBBBBB==~~~~~~~===~~~~~~~~~~~~~
38 BB--BBB----##.....BBBBBBBB.BBBBBB========~~========~~~~~~~~~~~~~
39 ---.BB--B--##.....BBBBBBBB-BBBBBp===================~~~~~~~~~~~~
40 ------BBBB-##.....BBBB-------BBBp===================~~~~~~~~~~~~
41 ---.~~BBBB--#......BBB-------BBB-=============BBBBB~~~~~~~~~~~~~
42 ---.~~BBB.--#.........------BBBBppppppBBBB====BBBBBp~~~~~~~~~~~~
43 -BB~~~~BBB--##..........--BBBBBBpBBpBBBBBB===pB-BB-p~~~~~~~~~~~~
44 -BB~~~~.BB.----..........BBB,,BB-BBpBBB-BBBBBBBBBB-~~~~~~~~~~~~~
45 BBB~~~~~BB.-#-----.......BBBBBBB-BBBBBBBBBBBB--BBBp~~~~~~~~~~~~~
46 BBB~~~~~...-#-BB-------..--BBBBB-BBBB.BBBB-BBBBBB-~~~~~~~~~~~~~~
47 BBB~~~~~~..-#BB-.-B--.-B------------BBBBBBBB-BBBB-~~~~~~~~~~~~~~
```

Tile counts (frame holds 3072 tiles): R road 168; - road 444; ~ water 459; B building 1395; , grass 21; # rail 27; p path 113; = quay 214; . ground 231.

### Sources

Geometry: OpenStreetMap, read through the map API on 2026-10-22, ODbL 1.0.
Text consulted: https://en.wikipedia.org/wiki/Port_of_Southampton (CC BY-SA 4.0, no images downloaded).
Text consulted: https://en.wikipedia.org/wiki/River_Itchen (CC BY-SA 4.0, no images downloaded).

## What this does not do

- It does not place NPCs, triggers or spawns. Those belong to the gamedev lane and to the
  map files, not to a spec of the ground.
- It does not choose a palette. The five classes are named so a palette pass can bind
  them; the NES limits (four background palettes, three colours each) apply at that
  point.
- It does not simplify to NES tile budgets. A 64 by 48 frame of 16 px tiles is 1024 by
  768 px, so the gamedev lane decides whether these become four screens, a scrolling
  strip, or a scaled single screen.
- The rasteriser rounds to whole tiles: a 6 m wide street and a 30 m wide quay both land
  on the same grid, so widths read as one or two tiles, not as surveyed widths.

## Licence and attribution

(c) OpenStreetMap contributors, Open Database Licence (ODbL) 1.0, https://www.openstreetmap.org/copyright

Wikipedia text is CC BY-SA 4.0 and was read, not copied at length. No images from
Wikipedia or Wikimedia Commons were downloaded; only the URLs are cited so a later pass
can check a licence before using a photograph.

Regenerate with `gen_real_places.py` then `md_from_json.py` (this run kept both in the
card workspace, not in the repo, because the card scoped the two deliverables only).

# PP-SCENES-1: S1 to S3 review sheet and screenplay

Card: t_31079972. Authoring draft for Nayil, 2026-10-26. Not wired into the route.

## Nayil's one page review sheet

### Ten best lines

1. KONRAD: "Six rooms on your floor. Beat five."
2. KONRAD: "Average is a hobby. Choose a better one."
3. KONRAD: "I could eat you up. You were always filling."
4. KONRAD: "Before is needy. After is data."
5. NARRATOR: Laundry card: DECLINED.
6. ZANDER: "A worthy opponent."
7. URIEN: "I used to own it. Terrible overheads."
8. SAILOR: "Page twelve says consult page twelve."
9. PERCY: "Can a hurricane validate parking?"
10. ZANDER: "Approved."

### Three knife names, pick one

1. Dad's Good Knife (the working name used below).
2. The Sandwich Sickle.
3. Old Family Recipe.

### Kronos's treatment of Zeus, every line for veto

K1: "Montefiore. Good."
K2: "Your room has a desk."
K3: "Use both."
K4: "Aim for a first, Zander."
K5: "Six rooms on your floor."
K6: "Beat five."
K7: Konrad eats your snacks.
K8: "Research," he says.
K9: "One last improvement."
K10: "Be exceptional."
K11: ZANDER REPLY OPTION: Thanks, Dad.
K12: ZANDER REPLY OPTION: Average.
K13: ZANDER REPLY OPTION: My snacks.
K14: "You are welcome."
K15: "Make it count."
K16: "Average is a hobby."
K17: "Choose a better one."
K18: "I could eat you up."
K19: "You were always filling."
K20: Konrad packs a knife.
K21: Dad's Good Knife.
K22: "For sandwiches."
K23: "Difficult packaging."
K24: "Ring after your lecture."
K25: "Before is needy."
K26: "After is data."
K27: You swallow your anger.
K28: Your cloud darkens.
K29: He takes the last snack.
K30: "Thanks for driving, Dad."
K31: "Any time, Zander."
K32: He holds the door open.
K33: You let him.
K34: BOX: One book, twelve cables, and a jumper your father calls optimistic.
K35: BED: So tightly tucked it has already disappointed your father.
K36: SNACK BAG: Empty except for the academic concept of crisps.
K37: KNIFE CASE: Dad's Good Knife, professionally sandwich adjacent.

## Data and wiring contract

The drafts live under authoring/, outside data/, the live registries and the runtime mirror. They need no mirror helper change, are not loaded by pp_data and are not in the demo route. PP-SCENES-WIRE owns the merge, the three maps, real start tiles, object positions and captures.

The placeholder map ids are wessex_lane_montefiore, southampton_high_street and the existing southampton_town_quay. PP-SCENES-WIRE supplies the hurricane variant and real start tiles; zero is an authoring placeholder, not playable geometry. Merge authoring/flags_s1_s3.json into data/flags.json, merge each dialogue list into data/dialogue/all.json, and merge each scene row into data/scenes/all.json. No battle, item, music, art or route file is changed here.

Name plates use the adopted names Konrad and Zander. Urien is the old man's only spoken name. The replay line is "So was mine.": a sandwich on first reading, a blade on replay. Nothing calls him a villain.

The running gag is "One last improvement": Konrad sets it up, Urien repeats it, and the wind twists it. Object flavour and S3's post-handoff wonder checks are excluded from dialogue budgets and capped at 15 words each.

## S1 MOVE-IN: Wessex Lane Halls, Montefiore

LOCATION: wessex_lane_montefiore (placeholder map id; PP-SCENES-WIRE supplies the room).
CAST: Zander (Zeus) and Konrad (Kronos).
WANT: Zander wants his room unloaded and his father gone.
STOPS: Konrad turns independence into another assessed result.
CHANGE: Zander keeps the room, swallows his anger, and his cloud darkens.
BUTTON: The laundry card declines him.

### Beats and every line

After the drive. Boxes come in. Konrad comes in after them. Zander's little cloud waits outside.

Dialogue id: s1_arrival
  KONRAD (Kronos) (page 1):
    * "Montefiore. Good."
    * "Your room has a desk."
    * "Use both."

  KONRAD (Kronos) (page 2):
    * "Aim for a first, Zander."
    * "Six rooms on your floor."
    * "Beat five."

  NARRATOR (page 3):
    * Konrad eats your snacks.
    * "Research," he says.

Dialogue id: s1_improvement
  KONRAD (Kronos) (page 1):
    * "One last improvement."
    * "Be exceptional."

  CHOICE: Thanks, Dad. -> s1_reply_thanks
  CHOICE: Average. -> s1_reply_average
  CHOICE: My snacks. -> s1_reply_snacks

Dialogue id: s1_reply_thanks
  KONRAD (Kronos) (page 1):
    * "You are welcome."
    * "Make it count."

Dialogue id: s1_reply_average
  KONRAD (Kronos) (page 1):
    * "Average is a hobby."
    * "Choose a better one."

Dialogue id: s1_reply_snacks
  KONRAD (Kronos) (page 1):
    * "I could eat you up."
    * "You were always filling."

Dialogue id: s1_knife
  NARRATOR (page 1):
    * Konrad packs a knife.
    * Dad's Good Knife.

  KONRAD (Kronos) (page 2):
    * "For sandwiches."
    * "Difficult packaging."

Dialogue id: s1_departure
  KONRAD (Kronos) (page 1):
    * "Ring after your lecture."
    * "Before is needy."
    * "After is data."

  NARRATOR (page 2):
    * You swallow your anger.
    * Your cloud darkens.

  NARRATOR (page 3):
    * He takes the last snack.

Dialogue id: s1_laundry_button
  NARRATOR (page 1):
    * Laundry card: DECLINED.

  ZANDER (Zeus) (page 2):
    * "A worthy opponent."

Dialogue id: s1_goodbye
  ZANDER (Zeus) (page 1):
    * "Thanks for driving, Dad."

  KONRAD (Kronos) (page 2):
    * "Any time, Zander."

  NARRATOR (page 3):
    * He holds the door open.
    * You let him.

### Optional object checks, available before the closing beat

moving_box (s1_check_moving_box):
    * BOX: One book, twelve cables, and a jumper your father calls optimistic.

bed (s1_check_bed):
    * BED: So tightly tucked it has already disappointed your father.

kettle (s1_check_kettle):
    * KETTLE: Two cups, or one mug with postgraduate ambitions.

poster (s1_check_poster):
    * POSTER: The beach looks warm. The small print says STUDIO.

laundry_card (s1_check_laundry_card):
    * LAUNDRY SIGN: Card only. Exact change has lost its tenure.

bin (s1_check_bin):
    * BIN: Six welcome leaflets and one brave fork.

room_key (s1_check_room_key):
    * ROOM KEY: Opens your room. Adulthood remains locked.

snack_bag (s1_check_snack_bag):
    * SNACK BAG: Empty except for the academic concept of crisps.

knife_case (s1_check_knife_case):
    * KNIFE CASE: Dad's Good Knife, professionally sandwich adjacent.

SINCERE BEAT: Konrad holds the door open, and Zander lets him.
CUT AWAY: no explanation follows.

## S2 HIGH STREET: Southampton, rain getting serious

LOCATION: southampton_high_street (placeholder map id; PP-SCENES-WIRE supplies the room).
CAST: Zander and Urien, a jovial, unassuming old man (Ouranos).
WANT: Zander wants to explore and replace his snacks without commentary.
STOPS: Urien reacts to the knife, and thunder turns toward Town Quay.
CHANGE: Zander walks toward the thunder, suspecting nothing.
BUTTON: Zander calls the darkening sky proper rain.

### Beats and every line

Zander explores. At a bus shelter, Urien smiles at the rain. The sky is already darker than it was at Wessex Lane.

Dialogue id: s2_meet_old_man
  URIEN (old man) (page 1):
    * "Urien. Lovely rain."
    * "I used to own it."
    * "Terrible overheads."

  URIEN (old man) (page 2):
    * "One last improvement."

Dialogue id: s2_knife
  NARRATOR (page 1):
    * You open your bag.
    * Dad's Good Knife.
    * Urien flinches.

  URIEN (old man) (page 2):
    * "Put it away, lad."
    * "Bad memories."

Dialogue id: s2_sandwich_choice
  ZANDER (Zeus) (page 1):
    * "Only for sandwiches."

  CHOICE: Offer one. -> s2_reply_offer
  CHOICE: Keep snacks. -> s2_reply_keep

Dialogue id: s2_reply_offer
  URIEN (old man) (page 1):
    * "So was mine."
    * "Take two."

Dialogue id: s2_reply_keep
  URIEN (old man) (page 1):
    * "So was mine."
    * "Fair enough."

Dialogue id: s2_sky_darkens
  NARRATOR (page 1):
    * The sky darkens.
    * Thunder at Town Quay.

Dialogue id: s2_rain_button
  ZANDER (Zeus) (page 1):
    * "Finally, proper rain."

Dialogue id: s2_sincere
  NARRATOR (page 1):
    * He folds your bag shut.

### Optional object checks, available before the closing beat

bus_timetable (s2_check_bus_timetable):
    * BUS TIMETABLE: Portswood buses are due, which is different from coming.

ferry_leaflet (s2_check_ferry_leaflet):
    * RED FUNNEL LEAFLET: Island ferries, tide times and absolutely no laundry refuge.

shop_window (s2_check_shop_window):
    * SHOP WINDOW: Student meal deal. Choose a main, a snack and a personality.

street_bin (s2_check_street_bin):
    * BIN: Accepts rubbish, wet leaflets and most undergraduate forecasts.

street_sign (s2_check_street_sign):
    * SIGN: Above Bar, High Street, Town Quay. Choose your own weather.

pastry_bag (s2_check_pastry_bag):
    * PASTRY BAG: Rainproof until held by a student.

SINCERE BEAT: Urien folds Zander's bag shut against the rain.
CUT AWAY: no explanation follows.

## S3 HURRICANE: Town Quay, gameplay handoff

LOCATION: southampton_town_quay (placeholder map id; PP-SCENES-WIRE supplies the room).
CAST: Zander, Lt. Percy and three sailors.
WANT: Zander wants a closer look at the storm.
STOPS: Percy and his men are crashing out around him.
CHANGE: Control returns; the player may suspect Zander, but he does not.
BUTTON: The wind takes Percy's cap, and Zander approves.

### Beats and every line

The hurricane breaks toward Town Quay. Zander stays calm and curious. Percy and his men lose their grip on the quay and themselves.

Dialogue id: s3_arrival
  NARRATOR (page 1):
    * Rain crosses Town Quay.
    * The Itchen is sideways.

  LT. PERCY (page 2):
    * "Why are you smiling?"

  ZANDER (Zeus) (page 3):
    * "Home, possibly."

  CHOICE: Like home. -> s3_reply_home
  CHOICE: Just rain. -> s3_reply_rain

Dialogue id: s3_reply_home
  LT. PERCY (page 1):
    * "Move home, then."

Dialogue id: s3_reply_rain
  LT. PERCY (page 1):
    * "This is not rain."

Dialogue id: s3_denial
  ZANDER (Zeus) (page 1):
    * "I did not do that."

  LT. PERCY (page 2):
    * "Nobody asked."

Dialogue id: s3_storm_manual
  NARRATOR (page 1):
    * A soaked manual.

  SAILOR (soaked manual) (page 2):
    * "Page twelve says"
    * "consult page twelve."

Dialogue id: s3_wind_arrest
  NARRATOR (page 1):
    * Wind arrest.

  SAILOR (arresting wind) (page 2):
    * "Wind! You are under"
    * "arrest!"

Dialogue id: s3_filming
  NARRATOR (page 1):
    * Vertical video.

  SAILOR (filming) (page 2):
    * "Sir, sound calm."

Dialogue id: s3_percy_parking
  LT. PERCY (page 1):
    * "My car: double yellows."
    * "Can a hurricane validate
    * parking?"

Dialogue id: s3_improvement
  LT. PERCY (page 1):
    * "One last improvement."
    * "Men."

  NARRATOR (page 2):
    * The wind takes his cap.

  ZANDER (Zeus) (page 3):
    * "Approved."

Dialogue id: s3_sincere
  NARRATOR (page 1):
    * Percy gives a sailor
    * his dry gloves.

  NARRATOR (page 2):
    * Zeus walks into the rain.

### Gameplay wonder checks, after control returns

cloud (s3_check_cloud):
    * "My cloud is enjoying this."

wind (s3_check_wind):
    * "That wind has excellent timing."

bollard (s3_check_bollard):
    * "The bollard is winning."

SINCERE BEAT: Percy gives a sailor his dry gloves.
CUT AWAY: no explanation follows.

## Read-aloud edit

Lines break at breaths. Repeated explanations were cut. The small wants stay audible: snacks, marks, packaging, parking, gloves and laundry. The sincere actions get no explanation. The storm never gets a speech.

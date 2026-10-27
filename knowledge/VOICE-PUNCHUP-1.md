# PP-VOICE-1 punch-up and veto record

Card t_df00acbe. Every prose change from the pre-pass live baseline is listed below for veto by file and key. The first ten are the strongest changes.

JSON keys use the record id, field, and zero-based list index. GML keys use the owning function. Other cards' structural additions, S1 to S3 authoring, generated answers, and live-talk prompts are excluded.

Save errors and control hints stay plain. No ids, flags, numeric values, branches, live-talk prompts, or mechanics were edited.

| # | Old line | New line | File | Key |
| ---: | --- | --- | --- | --- |
| 1 | * He will not move. | * He checks his parking ticket. | `data/dialogue/all.json` | `ship_rail_note.lines[2]` |
| 2 |  | * The poster looks relieved. | `data/dialogue/all.json` | `say_door_playhouse.pages[0].lines[1]` |
| 3 | * Rain all night, no cargo. | * One pen. Also chained. | `data/dialogue/all.json` | `ship_log_open.pages[0].lines[2]` |
| 4 | * "Everything at once, then." | * "FULL FLOOD. AUTHORISED." | `data/dialogue/all.json` | `percy_phase3_line.lines[1]` |
| 5 | The watch is long. That is all. | The watch is long. The break is not. | `data/talk_cards.json` | `navy_sailor.pools.neutral[1]` |
| 6 |  | Salt in a jar. Restores 6 HP. Not a beverage. | `data/items.json` | `salve.description` |
| 7 | * He does not look down. | * The page says TEA. | `data/dialogue/all.json` | `quay_gate_bluff.pages[1].lines[0]` |
| 8 | * Nobody gives a cause. | * The fridge goes on strike. | `data/dialogue/all.json` | `drive_radio_4.lines[2]` |
| 9 | "NOTHING HERE YET" | "SETTINGS ARE ON SHORE LEAVE" | `game/scripts/pp_title/pp_title.gml` | `pp_title_draw_settings` |
| 10 |  | THEY WERE PUT IN STORAGE. | `data/intro_text.json` | `beats[0][1]` |
| 11 | THEY WERE FORGOTTEN, | WE FORGOT THEM. THE VEIL | `data/intro_text.json` | `beats[1][0]` |
| 12 | AND THE VEIL BETWEEN | BETWEEN THEIR WORLD AND OURS | `data/intro_text.json` | `beats[1][1]` |
| 13 | THEIR WORLD AND OURS | IS COMING APART AT THE SEAMS. | `data/intro_text.json` | `beats[1][2]` |
| 14 | WEARS THIN. |  | `data/intro_text.json` | `beats[1][3]` |
| 15 | TODAY A SCIENTIST, A STUDENT, | TODAY, A SCIENTIST, A STUDENT, | `data/intro_text.json` | `beats[2][0]` |
| 16 | A SAILOR AND A CEO | A SAILOR AND A CEO FORGET | `data/intro_text.json` | `beats[2][1]` |
| 17 | DO NOT KNOW WHO | WHO THEY WERE. WELCOME BACK. | `data/intro_text.json` | `beats[2][2]` |
| 18 | THEY WERE. |  | `data/intro_text.json` | `beats[2][3]` |
| 19 | HIS SON SOUTH, TO THE SEA. | HIS SON SOUTH TO THE SEA. | `data/intro_text.json` | `beats[3][1]` |
| 20 |  | THE SNACKS ARE NOT FOR YOU. | `data/intro_text.json` | `beats[3][2]` |
| 21 |  | THE QUEUE IS NOT. | `data/intro_text.json` | `beats[4][1]` |
| 22 |  | RAIN, OBVIOUSLY. | `data/intro_text.json` | `beats[5][2]` |
| 23 | * The deck tilts. | * The deck tilts. The mop does not. | `data/dialogue/all.json` | `ship_rail_note.lines[0]` |
| 24 | * "The sea hears you." | * "NAME. BUSINESS. VEIL." | `data/dialogue/all.json` | `percy_lore_stop.lines[1]` |
| 25 | * "Show me the veil." | * "IN THAT ORDER." | `data/dialogue/all.json` | `percy_lore_stop.lines[2]` |
| 26 | * "The sea does not care." | * "STATE YOUR BUSINESS." | `data/dialogue/all.json` | `percy_entry.lines[1]` |
| 27 | * "You still talk. How dull." | * "STILL TALKING. NOTED." | `data/dialogue/all.json` | `talk_percy.lines[0]` |
| 28 | * "Ask what the veil is." | * "THE VEIL. YOUR QUESTION." | `data/dialogue/all.json` | `talk_percy.lines[1]` |
| 29 | * "Ask it plainly." | * "PLAINLY." | `data/dialogue/all.json` | `talk_percy.lines[2]` |
| 30 | * "The tide turns anyway." | * "THE TIDE TURNS. LOG IT." | `data/dialogue/all.json` | `talk_percy_phase2.lines[0]` |
| 31 | * "You asked about the veil." | * "THE VEIL. AGAIN." | `data/dialogue/all.json` | `talk_percy_phase2.lines[1]` |
| 32 | * "That is the veil." | * "THAT IS THE VEIL." | `data/dialogue/all.json` | `talk_percy_phase2.lines[2]` |
| 33 | * "So. You have hurt me." | * "INJURY. NOT SURRENDER." | `data/dialogue/all.json` | `percy_phase2_line.lines[1]` |
| 34 | * "Rain. Wall. Now the fan." | * "RAIN. WALL. FAN." | `data/dialogue/all.json` | `talk_percy_phase3.lines[0]` |
| 35 | * "Last of the three." | * "FINAL DRILL." | `data/dialogue/all.json` | `talk_percy_phase3.lines[1]` |
| 36 | * "Name me, or drown." | * "NAME ME, OR DROWN." | `data/dialogue/all.json` | `talk_percy_phase3.lines[2]` |
| 37 | * A wardroom hatch, shut. | * The mop has seen worse. | `data/dialogue/all.json` | `ship_gangway.pages[0].lines[2]` |
| 38 | * A hound on the deck. It is thin. | * A thin hound guards one knot. | `data/dialogue/all.json` | `battle_intro_hound.lines[1]` |
| 39 | * It waits for you to move first. | * It waits. You have the knife. | `data/dialogue/all.json` | `talk_deck_hound.lines[2]` |
| 40 | * Its eyes follow the water. | * It keeps the knot. | `data/dialogue/all.json` | `hound_win_spare.lines[2]` |
| 41 | * The man inside stands up. | * The guard hides a form. | `data/dialogue/all.json` | `quay_gate_checkpoint.pages[0].lines[2]` |
| 42 | * He holds a clipboard. | * He caps his pen twice. | `data/dialogue/all.json` | `quay_gate_checkpoint.pages[1].lines[2]` |
| 43 | * One lamp on the water. | * The Itchen takes the rain. | `data/dialogue/all.json` | `quay_gate_checkpoint.pages[2].lines[2]` |
| 44 | * The last hand is tight. | * The last entry: no cargo. | `data/dialogue/all.json` | `ship_log_open.pages[0].lines[1]` |
| 45 | * You add a line and a date. | * You sign below that. | `data/dialogue/all.json` | `ship_log_open.pages[1].lines[0]` |
| 46 | * The page takes the ink. | * The pen works. Suspicious. | `data/dialogue/all.json` | `ship_log_open.pages[1].lines[1]` |
| 47 | Ask him. | Officer. | `data/dialogue/all.json` | `quay_gate_choice.choices[2].label` |
| 48 | * He waits, pen ready. | * The pen waits. It is dry. | `data/dialogue/all.json` | `quay_gate_choice.pages[0].lines[2]` |
| 49 | * He does not believe it. | * The kettle snores too. | `data/dialogue/all.json` | `quay_gate_authority.pages[1].lines[0]` |
| 50 | * The other is not. | * The other owns the kettle. | `data/dialogue/all.json` | `quay_dock_office.pages[0].lines[2]` |
| 51 | * Not the clerk's hand. | * Beside it: a tea ring. | `data/dialogue/all.json` | `quay_dock_office.pages[2].lines[2]` |
| 52 | * He does not look up. | * "It is holding my tea." | `data/dialogue/all.json` | `quay_dock_office_pass.pages[1].lines[2]` |
| 53 | * Behind them the gate shut. | * The gate shuts behind you. | `data/dialogue/all.json` | `quay_dock_office_pass.pages[2].lines[2]` |
| 54 | * Registry office. Shut. | * Registry shut. No queue. | `data/dialogue/all.json` | `say_door_register.pages[0].lines[0]` |
| 55 |  | * Your number is up. Later. | `data/dialogue/all.json` | `say_door_register.pages[0].lines[1]` |
| 56 | * A pub. Warm and loud. | * A pub. Warm. Loud. Dry. | `data/dialogue/all.json` | `say_door_dancing_man.pages[0].lines[0]` |
| 57 |  | * Rain files a complaint. | `data/dialogue/all.json` | `say_door_dancing_man.pages[0].lines[1]` |
| 58 | * Flats. Every bell dead. | * Flats. The bells quit. | `data/dialogue/all.json` | `say_door_oceana.pages[0].lines[0]` |
| 59 |  | * Everyone waits for a text. | `data/dialogue/all.json` | `say_door_oceana.pages[0].lines[1]` |
| 60 |  | * The receiver is off duty. | `data/dialogue/all.json` | `say_door_telephone.pages[0].lines[1]` |
| 61 | * Nobody asks your name. | * Your welcome: a wet sock. | `data/dialogue/all.json` | `ship_aboard.pages[0].lines[2]` |
| 62 |  | * Vinegar. Hot oil. Salt. | `data/dialogue/all.json` | `say_door_kuti.pages[0].lines[1]` |
| 63 |  | * Yours has worse snacks. | `data/dialogue/all.json` | `say_door_red_funnel.pages[0].lines[1]` |
| 64 | * A door with no light. | * Dark door. Tonight: SHUT. | `data/dialogue/all.json` | `say_door_playhouse.pages[0].lines[0]` |
| 65 | * Twelve miles gone. | * Twelve miles gone. No crisps. | `data/dialogue/all.json` | `drive_sign_43.lines[2]` |
| 66 | * One lane now. | * One lane now. Snack wrapper. | `data/dialogue/all.json` | `drive_sign_20.lines[2]` |
| 67 | * A weather bulletin. | * Rain from the west. | `data/dialogue/all.json` | `drive_radio_1.lines[1]` |
| 68 | * Rain from the west. | * It sends its regards. | `data/dialogue/all.json` | `drive_radio_1.lines[2]` |
| 69 | * A traffic report. | * Winchester loses a lane. | `data/dialogue/all.json` | `drive_radio_2.lines[0]` |
| 70 | * A lane shut at Winchester. | * The car does not slow. | `data/dialogue/all.json` | `drive_radio_2.lines[1]` |
| 71 | * The car does not slow. | * Dad calls it momentum. | `data/dialogue/all.json` | `drive_radio_2.lines[2]` |
| 72 | * The signal drifts. | * His bins are still outside. | `data/dialogue/all.json` | `drive_radio_3.lines[2]` |
| 73 | * TALK can calm this. | * His mop is regulation. | `data/dialogue/all.json` | `battle_intro_sailors.lines[1]` |
| 74 | * FIGHT can end it faster. | * TALK or FIGHT. Choose. | `data/dialogue/all.json` | `battle_intro_sailors.lines[2]` |
| 75 | * The shipping forecast. | * Wight. Portland. Force 8. | `data/dialogue/all.json` | `drive_radio_5.lines[0]` |
| 76 | * Wight. Portland. Force 8. | * The reader says it twice. | `data/dialogue/all.json` | `drive_radio_5.lines[1]` |
| 77 | * The reader says it twice. | * The sea was not listening. | `data/dialogue/all.json` | `drive_radio_5.lines[2]` |
| 78 | * The wipers keep time. | * The car is not a boat. | `data/dialogue/all.json` | `drive_radio_6.lines[2]` |
| 79 | * "Go on. I hate the watch." | * "Go on. My break is late." | `data/dialogue/all.json` | `talk_navy_sailor.lines[2]` |
| 80 | * "Bridge is that way." | * "Bridge is that way. Move." | `data/dialogue/all.json` | `navy_win_spare.lines[2]` |
| 81 | * The sailor does not. | * The sailor keeps his mop up. | `data/dialogue/all.json` | `navy_spare_refused.lines[1]` |
| 82 | * "Not this time. Not for you." | * "Not before my relief." | `data/dialogue/all.json` | `navy_spare_refused.lines[2]` |
| 83 | * Nobody counts the spared. | * He writes one name in the book. | `data/dialogue/all.json` | `navy_epilogue_spare.lines[2]` |
| 84 | Words like that do not open hatches. | Words do not open hatches. | `data/talk_cards.json` | `navy_sailor.pools.cheat[0]` |
| 85 | Say what you came to say. | Say it. The form is listening. | `data/talk_cards.json` | `navy_sailor.pools.neutral[2]` |
| 86 | Keep it civil or keep it quiet. | Keep it civil. Mop hears. | `data/talk_cards.json` | `navy_sailor.pools.rude[2]` |
| 87 | The bridge sees all. | The bridge sees all. Sadly. | `data/talk_cards.json` | `navy_sailor.pools.strong.low[0]` |
| 88 | Say that again and this gets loud. | Say that again. Louder, perhaps. | `data/talk_cards.json` | `navy_sailor.pools.strong.mid[0]` |
| 89 | You are on the list now. | You are on the list now. Bad news. | `data/talk_cards.json` | `navy_sailor.pools.strong.mid[1]` |
| 90 | A smoke? After this, maybe. | A smoke? After this watch. | `data/talk_cards.json` | `navy_sailor.pools.weak.mid[0]` |
| 91 | Do not say that too loud. | Quiet. The bridge sleeps. | `data/talk_cards.json` | `navy_sailor.pools.weak.mid[1]` |
| 92 | Words like orders. Try again. | WORDS LIKE ORDERS. AGAIN. | `data/talk_cards.json` | `percy.pools.cheat[0]` |
| 93 | You talk like a clerk with a script. | A CLERK WITH A SCRIPT. | `data/talk_cards.json` | `percy.pools.cheat[1]` |
| 94 | A script will not save you. | THAT SCRIPT IS NOT A PASS. | `data/talk_cards.json` | `percy.pools.cheat[2]` |
| 95 | Show me the veil. | STATE YOUR QUESTION. | `data/talk_cards.json` | `percy.pools.neutral[0]` |
| 96 | Words. The sea has heard worse. | WORDS. THE SEA HEARS WORSE. | `data/talk_cards.json` | `percy.pools.neutral[1]` |
| 97 | You are wasting water. | MAKE YOUR POINT. BRIEFLY. | `data/talk_cards.json` | `percy.pools.neutral[2]` |
| 98 | A stowaway with a mouth. | A STOWAWAY WITH A MOUTH. | `data/talk_cards.json` | `percy.pools.rude[0]` |
| 99 | Mind your tone in my ship. | MIND YOUR TONE. MY SHIP. | `data/talk_cards.json` | `percy.pools.rude[1]` |
| 100 | Rudeness. How very mortal. | RUDENESS. NOTED. | `data/talk_cards.json` | `percy.pools.rude[2]` |
| 101 | Say my father's name again. | FATHER'S NAME. SAY IT AGAIN. | `data/talk_cards.json` | `percy.pools.strong.high[0]` |
| 102 | The tide turns anyway. | THE TIDE TURNS. LOG IT. | `data/talk_cards.json` | `percy.pools.strong.high[1]` |
| 103 | You still talk. How dull. | YOU STILL TALK. HOW DULL. | `data/talk_cards.json` | `percy.pools.strong.low[0]` |
| 104 | The sea does not care. | THE SEA DOES NOT CARE. | `data/talk_cards.json` | `percy.pools.strong.low[1]` |
| 105 | Do not dress me in titles. | DO NOT DRESS ME IN TITLES. | `data/talk_cards.json` | `percy.pools.strong.mid[0]` |
| 106 | That is the wrong question. | THAT IS THE WRONG QUESTION. | `data/talk_cards.json` | `percy.pools.strong.mid[1]` |
| 107 | Ask it plainly, then. I am listening. | ASK PLAINLY. I AM LISTENING. | `data/talk_cards.json` | `percy.pools.weak.high[0]` |
| 108 | You have earned one honest answer. | ONE HONEST ANSWER. EARNED. | `data/talk_cards.json` | `percy.pools.weak.high[1]` |
| 109 | Plain. Good. Keep it that way. | PLAIN. GOOD. KEEP IT SHORT. | `data/talk_cards.json` | `percy.pools.weak.low[0]` |
| 110 | You ask like a sailor, not a clerk. | YOU ASK LIKE A SAILOR. | `data/talk_cards.json` | `percy.pools.weak.low[1]` |
| 111 | The sea hears you. So do I. | THE SEA HEARS YOU. SO DO I. | `data/talk_cards.json` | `percy.pools.weak.mid[0]` |
| 112 | That is closer to the truth. | THAT IS CLOSER TO THE TRUTH. | `data/talk_cards.json` | `percy.pools.weak.mid[1]` |
| 113 | Words like orders. Try again. | WORDS LIKE ORDERS. AGAIN. | `data/talk_cards.json` | `percy_phase2.pools.cheat[0]` |
| 114 | You talk like a clerk with a script. | A CLERK WITH A SCRIPT. | `data/talk_cards.json` | `percy_phase2.pools.cheat[1]` |
| 115 | A script will not save you. | THAT SCRIPT IS NOT A PASS. | `data/talk_cards.json` | `percy_phase2.pools.cheat[2]` |
| 116 | Show me the veil. | STATE YOUR QUESTION. | `data/talk_cards.json` | `percy_phase2.pools.neutral[0]` |
| 117 | Words. The sea has heard worse. | WORDS. THE SEA HEARS WORSE. | `data/talk_cards.json` | `percy_phase2.pools.neutral[1]` |
| 118 | You are wasting water. | MAKE YOUR POINT. BRIEFLY. | `data/talk_cards.json` | `percy_phase2.pools.neutral[2]` |
| 119 | A stowaway with a mouth. | A STOWAWAY WITH A MOUTH. | `data/talk_cards.json` | `percy_phase2.pools.rude[0]` |
| 120 | Mind your tone in my ship. | MIND YOUR TONE. MY SHIP. | `data/talk_cards.json` | `percy_phase2.pools.rude[1]` |
| 121 | Rudeness. How very mortal. | RUDENESS. NOTED. | `data/talk_cards.json` | `percy_phase2.pools.rude[2]` |
| 122 | Blood on the deck. Say it again. | Father's name. Say it again. | `data/talk_cards.json` | `percy_phase2.pools.strong.high[0]` |
| 123 | Plain. Good. Keep it that way. | PLAIN. GOOD. KEEP IT SHORT. | `data/talk_cards.json` | `percy_phase2.pools.weak.low[0]` |
| 124 | You ask like a sailor, not a clerk. | YOU ASK LIKE A SAILOR. | `data/talk_cards.json` | `percy_phase2.pools.weak.low[1]` |
| 125 | Winded. Do not mistake it for soft. | Winded. Do not call it soft. | `data/talk_cards.json` | `percy_phase2.pools.weak.mid[0]` |
| 126 | It waits for you to move first. | It waits. You have the knife. | `data/talk_cards.json` | `deck_hound.pools.neutral[2]` |
| 127 | The tail moves once. | The tail moves once. Overtime. | `data/talk_cards.json` | `deck_hound.pools.weak[1]` |
| 128 | The ledger is in order. Good. | The ledger balances. Small miracle. | `data/talk_cards.json` | `petty_officer.pools.weak[1]` |
| 129 | You smell like nothing. | You smell like no lunch. | `data/talk_cards.json` | `deck_rat.pools.neutral[2]` |
| 130 | Good wind. Good wind. | Good wind. Good chips. | `data/talk_cards.json` | `gull.pools.weak[1]` |
| 131 | You stand on wood. I am below it. | You stand on wood. I am below. | `data/talk_cards.json` | `rogue_wave.pools.neutral[0]` |
| 132 | Two years of night watches and a mop he treats like a rifle: tired, decent, and not paid enough to care who you are. | Two years of night watches and a mop he treats like a rifle: tired, decent, and worried about a parking ticket. | `data/enemies/roster.json` | `navy_sailor.personality` |
| 133 | Has eaten better than the crew for three years and knows exactly which stores hatch is loose. | Has eaten better than the crew for three years; the loose stores hatch is his dining room. | `data/enemies/roster.json` | `deck_rat.personality` |
| 134 | Screaming, thieving, entirely convinced the ship was built as a restaurant for one. | Screaming, thieving, entirely convinced the ship is a restaurant with very slow service. | `data/enemies/roster.json` | `gull.personality` |
| 135 | The sea got tired of being told what to do and grew eyes about it. | The sea got tired of being told what to do and grew eyes to file a complaint. | `data/enemies/roster.json` | `rogue_wave.personality` |
| 136 | Nobody tied it and nobody can untie it, and it has opinions about both facts. | Nobody tied it and nobody can untie it. It has applied for permanence. | `data/enemies/roster.json` | `rope_knot.personality` |
| 137 | The bottom of the ship learned to want things: warmth, a biscuit, and the sound of someone saying its name. | The bottom of the ship learned to want things: warmth, a biscuit, and someone to hold the ladder. | `data/enemies/roster.json` | `bilge_slime.personality` |
| 138 | A thin rope yard dog on the foredeck: it holds the line nobody else was given, and it has decided you are the thing to watch. | A thin rope yard dog on the foredeck: it guards the line nobody else wanted, and it takes the job personally. | `data/enemies/roster.json` | `deck_hound.personality` |
| 139 | Say what you came to say. | Say it. The form is listening. | `data/encounters/all.json` | `tutorial_sailors.talk.fallback_line` |
| 140 | The watch is long. That is all. | The watch is long. The break is not. | `data/encounters/all.json` | `tutorial_sailors.talk.fallback_pool[1]` |
| 141 | Say what you came to say. | Say it. The form is listening. | `data/encounters/all.json` | `tutorial_sailors.talk.fallback_pool[2]` |
| 142 | It waits for you to move first. | * It waits. You have the knife. | `data/encounters/all.json` | `deck_hound.talk.fallback_line` |
| 143 | * It waits for you to move first. | * It waits. You have the knife. | `data/encounters/all.json` | `deck_hound.talk.fallback_pool[2]` |
| 144 | * It lands for {damage}. Nobody says anything. | * It lands for {damage}. Nobody mentions the sandwiches. | `data/items.json` | `dads_good_knife.damage_line` |
| 145 | "no power taken yet" | "no power. none taken" | `game/scripts/pp_battle_commands/pp_battle_commands.gml` | `pp_command_state` |
| 146 | "no will" | "no will left" | `game/scripts/pp_battle_commands/pp_battle_commands.gml` | `pp_command_state` |
| 147 | "nothing to say to this one" | "it is not listening" | `game/scripts/pp_battle_commands/pp_battle_commands.gml` | `pp_command_state` |
| 148 | "no item" | "pockets empty" | `game/scripts/pp_battle_commands/pp_battle_commands.gml` | `pp_command_state` |
| 149 | "* You strike for " + string(_damage) + "." | "* You swing for " + string(_damage) + ". No comment." | `game/scripts/pp_battle_director/pp_battle_director.gml` | `pp_battle_fight_lines` |
| 150 | " lands for " + string(_power.power) + "." | " hits for " + string(_power.power) + ". The sea sighs." | `game/scripts/pp_battle_director/pp_battle_director.gml` | `pp_battle_step_resolve` |
| 151 | "* The fight ends." | "* Nobody applauds." | `game/scripts/pp_battle_director/pp_battle_director.gml` | `pp_battle_enter_result` |
| 152 | "here it comes" | "brace yourself" | `game/scripts/pp_battle_director/pp_battle_director.gml` | `pp_battle_draw` |
| 153 | " stands over you." | " wins. awkward." | `game/scripts/pp_battle_director/pp_battle_director.gml` | `pp_battle_draw_gameover` |
| 154 | "TWO MEN WHO DO NOT KNOW EACH OTHER." | "TWO STRANGERS IN ONE CAR." | `game/scripts/pp_title/pp_title.gml` | `pp_title_defaults` |
| 155 | "ONE OF THEM IS WAITING FOR THE OTHER." | "ONE OF THEM KNOWS THE WAY." | `game/scripts/pp_title/pp_title.gml` | `pp_title_defaults` |
| 156 | "THEY WERE FORGOTTEN." | "THEY GOT PART-TIME JOBS." | `game/scripts/pp_title/pp_title.gml` | `pp_title_intro_beats` |

## Counts

| File | Prose rows |
| --- | ---: |
| data/intro_text.json | 13 |
| data/dialogue/all.json | 67 |
| data/talk_cards.json | 49 |
| data/items.json | 2 |
| data/enemies/roster.json | 7 |
| data/encounters/all.json | 5 |
| game/scripts/pp_battle_commands/pp_battle_commands.gml | 4 |
| game/scripts/pp_battle_director/pp_battle_director.gml | 5 |
| game/scripts/pp_title/pp_title.gml | 4 |

Total: 156 review rows.

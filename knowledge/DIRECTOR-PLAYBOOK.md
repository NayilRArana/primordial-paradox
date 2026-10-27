# DIRECTOR-PLAYBOOK: the design half

Card GD-1a (t_1034799a), sections 1 to 3 of GD-1, the game director's research card. Rules extracted from primary sources, not admiration. Every checklist line carries a source tag; tags resolve with link and date in SOURCES.md. Lines marked "our decision" are this project's own call, not a source.

Frame: Primordial Paradox is a NES-styled JRPG, art direction style B (late NES polish: the Kirby's Adventure and Little Samson tier, bold 1 px outlines, three-tone shading, detailed tiles). Everything below is written against that frame.

## 1. JRPG design that holds up today

### 1.1 Overworld movement and feel
- [ ] No random encounters. Enemies are visible on the field and battle opens in the same map with no transition screen. Sea of Stars ships "no random encounters, no transitions to separate battlefields" [S9]; Chained Echoes copied Chrono Trigger's visible enemies because it is "a lot smoother this way" [S11].
- [ ] Traversal is the reward. Sea of Stars "Unshackled traversal" (swim, climb, vault, jump, hoist ledges) deliberately "breaks free from the classic bound-to-the-grid tileset movement" [S9]. Our 16x16 overworld sprite stays, but a ledge or a vault moment beats a straight walk.
- [ ] The player should feel where they are, not watch a claustrophobic first person box. Itoi chose Mother 2's overhead view to "better capture that feeling of being in a location, rather than the limited first-person perspective of Wizardry" [S1].
- [ ] Towns get moving NPCs, not statues. Itoi: "that's why I made the other characters move around a lot more this time for Mother 2" [S1]. It is the cheapest signal that a town is alive and it reads in a 3 minute video.

### 1.2 Encounter and battle design
- [ ] Stage set-piece battles. Chrono Trigger's Active Time Event logic system treats a fight as a scene, not a menu pop: Sakaguchi's framing was "Imagine a play on stage" [S2].
- [ ] Give the player a lever to pull mid-fight so a turn is a decision, not a wait. Sea of Stars' "locks" system and timed hits [S9]; Chained Echoes' Overdrive gauge, which Linda adapted from Final Fantasy X's timed cursor but "without the QTE thing" [S11]. One such lever is enough; two is a game.
- [ ] Battle must be readable at a glance: party where you expect it, enemies where you expect them, and one clear cost per action. Final Fantasy VI and its generation fixed the side view, party stacked down one edge, enemies opposite [S3].
- [ ] Cut systems that add weight without fun. Linda dropped a third (airship) battle system: "it was too much for the game... The game would be worse with the airship battles than without" [S11].
- [ ] Battle as character. Undertale's mercy route came first, then everything else: "The battle system arose first. Where not killing everything is actually a viable option" [S4]. The fight IS the statement about who the player is.

### 1.3 Difficulty curve and demo pacing
- [ ] No grinding in the demo path. Sea of Stars removes grinding entirely [S9]; the 3 minute demo must not ask the judge to level.
- [ ] Front-load one system at a time. Sabotage "always start from nothing and every single system is added," discovering each system's reason before adding it, and shipping "the leanest version that's the most in tune with the rest" [S10].
- [ ] Pacing a short demo: one location, one fight, one choice, one hook. Toby Fox keeps Deltarune's optional gags and RPG encounters even inside a platforming stretch because "this kept the mood from drifting too far from the main game" [S5]. The mood never drifts; the player always knows what game they are in.

### 1.4 Comedic writing technique
- [ ] Write dialogue the way a JRPG reads in translation, not the way a wiki reads. Toby Fox wrote Undertale's lines "as if it's a Japanese JRPG being translated to English" (reported by players; the DEV 2 DEV interview is the primary source for his design intent) [S4].
- [ ] Humour is cumulative and call-back heavy, not one liners. Deltarune leans on "lots of stupid optional dialogue for doing different things" as a core technique [S5].
- [ ] Trust the player. Itoi refused to stamp speaker names over dialogue because it broke immersion: "I kept my promise not to put names at the start of dialogue to show who's speaking" [S1].
- [ ] A word earns its weight by what the player did to reach it. Itoi: worn words "start to feel vivid and alive" in a game "because of all the time you've put in leading up to it" [S1].

### 1.5 Music and sound as feedback
- [ ] Spend the budget on music and let it direct the scene. Earthbound reserved 8 megabits for music, and Itoi argued the cost openly rather than cutting it [S1].
- [ ] Sound answers the player, always. Damage and confirmation need a sound on the same frame as the visual, per the juice and game-feel rules in section 2 [S12] [S13].

## 2. Game feel and polish for a 2D pixel game

Measured numbers where the source gives one, so a director can turn a taste call into a budget.

- [ ] Input responsiveness first: reaction on the next frame, not after a 250 ms wind-up animation. If a wind-up is needed, "start moving during the animation, not after it" [S12].
- [ ] Coyote time: allow a jump about 0.1 s after leaving a ledge [S12].
- [ ] Input buffering: remember a jump pressed about 0.12 s before landing and fire it on touchdown [S12].
- [ ] Variable jump height: tap is a short hop, hold is a full jump (a jump cut on release) [S12].
- [ ] Separate acceleration and deceleration; snappy stop reads as tight control [S12].
- [ ] Hit stop: freeze 3 to 6 frames at the moment of impact, then knockback [S12].
- [ ] Camera shake: short, and it "fades out quickly"; a long shake becomes noise [S12]. Use a trauma model (shake grows with trauma squared, trauma decays) per Squirrel Eiserloh's camera talk [S12].
- [ ] Juice is surface polish, not content. Jonasson and Purho's "Juice it or lose it" (GDC 2012) showed the same game feel dramatically better by adding feedback only [S13].
- [ ] What a judge notices in 3 minutes: particles on hit, a score or damage number, a shake, a flash, a sound. None of these change the rules; all of them change the read [S13].
- [ ] Our decision: apply hit stop, shake and buffer to the tutorial fight and the Percy fight first, because those are the two fights the demo shows.

## 3. Pixel art direction for a professional NES-styled game (style B)

### 3.1 Palette discipline
- [ ] One locked master palette, every asset drawn inside it, never converted in afterward. This is our RULE 0 and it matches Saint11's "fire and forget" colour limit: one palette loaded every time you draw [S15].
- [ ] Fewer, well-chosen colours beat more colours. "Fewer, well-chosen colors produce stronger cohesion than large palettes" [S18].
- [ ] Separate the hero's palette from the enemies' and from the ground behind it. Castlevania gives Simon a palette with no black while enemies hold black, which is why he reads clearly [S14]. Our RULE 0 point 2 is the same rule made measurable (row gap or 3:1 contrast).
- [ ] Match colour count to the hardware ceiling (25 on screen), and keep the scene palette written in a data file a checker reads. Our decision, consistent with [S15].

### 3.2 Readability
- [ ] One outline weight, one light direction, one proportion set across every asset. "One off-model sprite breaks a game's visual identity" [S18].
- [ ] A figure reads first by silhouette, second by colour, third by detail. At 40 px tall (style B), the silhouette must carry the character before the three tones do [S14] [S15].
- [ ] Avoid "sticky pixels": clusters that never change across animation frames read as frozen noise [S14].
- [ ] Decide a base resolution and scale the whole canvas by an integer with nearest-neighbour; never smooth-scale pixel art [S15].

### 3.3 Animation frame budgets
- [ ] A walk is 2 drawn frames plus reuse, ping-ponged, with the idle as the extra frame: the NES budget (Super Mario Bros. 3, Castlevania III, Mega Man) [S14].
- [ ] Reuse before redraw: split torso and legs so an attack does not need new leg frames, and flip or recolour before drawing a new pose [S14]. Our RULE 0 point 3 and the Castlevania findings agree.
- [ ] Cut frames down to the style. Dadako tried an 8 frame walk on an NES-plus look and cut it back because it "seemed out of place with the overall NES+ feel" [S14]. More frames is not automatically more polished.
- [ ] With few frames, put motion everywhere: "If one thing is moving left, make another thing move up" [S14].

### 3.4 How one small team keeps a single style
- [ ] Write an art bible: proportions, colour logic, outline weight, materials, named per asset. [S15] and our ART-BIBLE.md.
- [ ] Quarantine styles into worlds. Saint11 kept Celeste's Game, UI and Map in three distinct styles and the rule was "styles never leak from one world to another" [S15]. We already do this (NES playfield, one palette set, no HD leaks).
- [ ] Six programmers shipped Octopath: the cost is in the asset volume, not the headcount. Acquire "only had six programmers" at peak and leaned on the engine to iterate [S8].
- [ ] Keep the team small on purpose. Sabotage stopped growing at 25 and operates "100% on trust" [S10].

### 3.5 How studios clean up AI-generated art
- [ ] Treat AI output as concept art and direction, not production assets. "AI pixel art generators are strongest at concept art, art direction, and style exploration," while sprite editors "are still required for production-ready sprites at exact resolutions" [S18].
- [ ] The failure mode is "pixel-style" blur, not pixels: "most image models produce pixel-style images, not true pixel-grid assets" [S18]. Cleanup means snapping to the grid and re-drawing, not just recolouring.
- [ ] Judge AI art on grid fidelity, palette lock, cross-asset consistency and honest scope, and know "when output needs manual cleanup before it goes into a game engine" [S18].
- [ ] Our decision: concept art from Gemini or Kaggle is accepted only after quantization to the scene palette and a pass by tools\palette_synergy.py (already RULE 0 point 5). AI never draws the shipped sprite; a tool draws the shipped sprite and a checker proves it.
- [ ] Watch the licence and clone risk, not just the pixels: in 2025 a studio delayed a public playtest "over concerns of AI cloning" [S17]. Keep generated art out of anything we publish until the rights are settled.

Word target: this half is under 2,000 words. The production and directing half (GD-1 sections 4 to 6) is the other card.

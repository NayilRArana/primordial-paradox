# Winners study: five rules from demos that won, each with its example

Card t_29274e89 (WINNERS-STUDY), research-assistant, written 2026-10-23 for Primordial Paradox and the Meta/Cerebral Valley
hackathon. Scope: this file only. It changes no spec, no data file and no shot.

Why it exists: PLAN-WIN section 1 says the judging is creativity, technical ambition and whether it works. This card buys the
third one, by studying events where a demo was the unit of judgement, and what that demo had on screen in its first 30 seconds.

What it is not: a list of games to copy. No asset, name or text from any entry below is reused. Each example carries at most
one short quoted line, for study only.

## 0. The five entries, and how each was read

| # | Event (named) | Entry (named) | Its result | Page read |
| --- | --- | --- | --- | --- |
| 1 | GMTK Game Jam 2024, "Built to Scale", 7,511 entries, Aug 2024 | That Time I Got Reincarnated as a Panda and had to Collect Coins by Rolling Away on Built-to-Scale Platforms, by Colisan | 1st overall, 4.689, Style 2nd | https://colisan.itch.io/that-time-i-got-reincarnated-as-a-panda-a-h-t-c-c-b-r-a-o-b-t-s-p and its postmortem devlog |
| 2 | GMTK Game Jam 2024, same event | Pizzascaper, by Yoyoyollie, Arcy, Jett Mance | 2nd overall, 4.583, Top Marks 1st | https://yoyoyollie.itch.io/pizzascaper |
| 3 | js13kGames 2024, theme Triskaidekaphobia, 13 KB size limit, Sept 2024 | 13th Floor, by Rob Louie | Listed first on the 2024 winners page, 57 stars | https://js13kgames.com/2024/games/13th-floor |
| 4 | Ludum Dare 55, theme Summoning, April 2024, 2,194 Jam entries | Would you still love me if I was a worm, by Guy, Lucy, Joao, Sam, Martin, Joe | Jam 1st | https://ldjam.com/events/ludum-dare/55/would-you-still-love-me-if-i-was-a-worm and https://guyunger.itch.io/would-you-still-love-me-if-i-was-a-worm |
| 5 | Meta Llama 3 Hackathon, San Francisco, May 2024, Meta plus Cerebral Valley, 24 hours, live demos, 51 projects | OpenGlass | 1st | https://ai.meta.com/blog/llama-3-hackathon-recap-cerebral-valley/ (read 2026-10-22 for `..\arananet\meta-hackathon\WIN-LESSONS.md`) |

Two jam-results pages were read at the event level as well, so the placings above are not second hand:
https://itch.io/jam/gmtk-2024/results and https://js13kgames.com/2024/ .

Evidence limits, stated up front so no reader over-reads this file: no entry was played on screen for this card, and no
recording was reviewed. Every first-30-seconds claim below rests on something written and quotable: the entry's own page, the
winner's own postmortem, one player's written feedback, or the hackathon host's own recap. Where a claim is my inference from
those documents, the rule says so and the inference is marked.

---

## Rule 1: the first ten seconds must be safe to be bad at

The rule: the opening is a teaching window, not a test. Nothing in the first ten seconds may kill, fail or time out the
player, and nothing may ask the player for anything (a name, a difficulty, a control it has not taught) before the game has
shown what it is. If the first mistake is unavoidable, the player blames the game, and the grade follows.

The example: GMTK Game Jam 2024, 1st overall of 7,511 entries, the panda roller by Colisan
(https://colisan.itch.io/that-time-i-got-reincarnated-as-a-panda-a-h-t-c-c-b-r-a-o-b-t-s-p). The post-jam fix list on the entry
page adds "a mandatory drop after the spawn, to encourage building in the gap", which is a designer forcing the first action
to be the taught action. In the postmortem (devlog 789531) the author names the rule himself, quotes it as
`FTUE should be flawless`, then admits he broke it: he asked for the player name before the two-second in-run death, and says
the bottom 60 per cent of his own leaderboard filled with keyboard mash. He also reports the pacing target behind it: each run
starts slow and picks up fast, aimed at about two minutes for a low to mid level player.

What we would have to change on Monday if this is true: our demo has no safe window at all, it has a wall. From
`knowledge/DEMO-SCRIPT.md`: S1 runs 0:00.00 to 0:16.00 with no input at all until 0:11.80, S2 runs 0:16.00 to 0:29.00 as
text, S3 runs 0:29.00 to 0:39.03 as an unskippable cutscene whose only input closes a caption, and the first input that
changes anything the player owns is S4's Down press at 0:54.23, which moves a choice cursor. That is 54.23 seconds, 30 per cent
of the demo, before the judge has done one thing. The fix is not a redesign; it is accepting a key at 0:02.00 in S1 that
lifts the logo and starts the menu early, and letting S2's held confirm start at 0:17.00 instead of 0:22.00.

## Rule 2: put the verb the theme asked for on a default input, not in a menu

The rule: whatever the entry is about, the player must be able to do it with the first controls they are given. If the
distinctive verb lives behind a menu, an upgrade or a second level, the judge meets a generic game first and the distinctive
one, if ever, late.

The example: GMTK Game Jam 2024, Pizzascaper by Yoyoyollie, Arcy and Jett Mance
(https://yoyoyollie.itch.io/pizzascaper), 2nd overall and 1st in Mark Brown's Top
Marks. The jam theme was scale. On the entry page, the four line control list puts it in the second line: `Right Mouse - Scale
Projectile`. Not a key, not a shop, not a late unlock: the right hand, from the first shot, on the thing the game is named for.

What we would have to change on Monday if this is true: our distinctive verb is the talk-fight, and it arrives at 1:53.03,
two thirds of the way in. The judge's first 113 seconds are a menu, a crawl, a drive, a checkpoint and a clerk; the thing we
would want quoted back to us happens after they have already formed a view. Either one TALK box moves into S4's gate
checkpoint (Morgan already asks a three option question there, so the licence to talk exists), or S1's caption stops
describing the engine and says what the game does.

## Rule 3: the first room must carry a threat, or a promise, before any input

The rule: a demo that is quiet for its first half minute reads as empty, not as restrained. Sound and one visible thing that
can hurt or reward the player should be running at t equals zero, before the player is asked to move.

The example: js13kGames 2024, 13th Floor by Rob Louie (https://js13kgames.com/2024/games/13th-floor), listed first on that
year's winners page and playable in one click at
play.js13kgames.com/13th-floor with no install, inside a 13 KB budget. The strongest evidence on the page is not the author's:
a player writes, `It took me a couple of minutes to get the courage to even leave the first room after I picked the key up.`
and credits the design in the same breath, the first footsteps you slowly start to hear. The threat was audible before it was
visible, and it was audible in the first room.

What we would have to change on Monday if this is true: nothing structural. `knowledge/DEMO-SCRIPT.md` already satisfies this
one, which is worth saying plainly because it is the counterexample to rules 1 and 2: `title_theme` starts on step 0 of S1, the
road dashes land one per beat, the car bobs, the lightning swaps the palette for two frames, `car_engine_loop` runs under the
whole drive, and no shot in the file is silent. The gap is not atmosphere, it is agency, which is rules 1 and 2.

## Rule 4: one sentence of premise, absurd and specific, is the whole sales pitch

The rule: a judge who has 40 tabs open will not read a paragraph. The premise has to fit in one line, name what you do and
what you want, and be strange enough to be repeatable. Do not explain the joke; state it and start.

The example: Ludum Dare 55 (theme Summoning, April 2024), Jam 1st place, Would you still love me if I was a worm by Guy and
five others (https://ldjam.com/events/ludum-dare/55/would-you-still-love-me-if-i-was-a-worm). The entry page opens on one sentence about revenge on an ex-girlfriend and all the birds on earth, the controls
are `Click on stuff`, and the rest of the page is four animated gifs of the verb doing itself. Six people, 72 hours, and the
page never asks the reader to understand a system before it promises a feeling.

What we would have to change on Monday if this is true: our one line is not written yet as one line. The write-up and the
demo captions say "AI that obeys hardware limits" and "Kronos and Zeus reincarnated on the M3", which are two different
sentences for two different judges. Pick one and let the other be the second sentence.

## Rule 5: the first 30 seconds must contain the one thing a judge will repeat to somebody else

The rule: in a demo-judged event the unit of memory is one sentence someone says to a colleague afterwards. If that sentence
is about the plan, the roadmap or the architecture, the entry loses to the one whose sentence is about a thing it visibly did.

The example: Meta Llama 3 Hackathon, San Francisco, May 2024, Meta with Cerebral Valley, 24 hours and 51 projects, judged on
live demos (https://ai.meta.com/blog/llama-3-hackathon-recap-cerebral-valley/). 1st place went to OpenGlass: glasses built for about 20 USD that describe what the wearer is looking at, down to
reading fruit and returning calorie counts. The sentence is "twenty dollar glasses that tell you what you are looking at", and
it survives being repeated badly. Source: the Meta recap page above, as recorded in `WIN-LESSONS.md` section 1.1 (page read
2026-10-22; this card re-cited the finding, it did not re-fetch the page).

What we would have to change on Monday if this is true: our repeatable sentence is "a Meta model answering inside an NES text
box", and per `knowledge/DEMO-SCRIPT.md` the first bake row appears at 1:19.03, in S5. For the first 79 seconds the judge sees
a competent NES game and no Meta. Either a three second bake row is drawn over S1's caption, or a single line of the crawl
says who is answering, in the crawl's own voice, not in caption voice.

---

## 6. The Monday list, if all five hold

| # | Change | Where it bites | Cost |
| --- | --- | --- | --- |
| M1 | S1 accepts a key at 0:02.00; menu reachable by 0:04.00 | DEMO-SCRIPT S1 table, steps 0 to 240 | one row in the script, one check in the recorder |
| M2 | S2's held confirm starts at 0:17.00, 5 s earlier, so the reveal can clear by about 0:24.00 and S3 starts on a bar | DEMO-SCRIPT S2, step 1,320 becomes 1,020 | no new art, one timing constant |
| M3 | One Meta bake row drawn over S1, or named in the crawl | DEMO-SCRIPT S1, VIDEO-PLAN overlay list | one overlay, already a data field |
| M4 | One TALK exchange reachable in S4's gate checkpoint | needs gamedev's ruling, it touches spec 19 and the S4 beat budget | not a research call |

Only M1 to M3 are inside this card's competence. M4 belongs to gamedev and is written as a question below, not as a decision.

Card checks, met: five rules, each with a named event and a named entry and a URL; rule 1 and rule 5 both carry a Monday
change with a step number in it. No em dash or en dash in this file (checked with grep on 2026-10-23).

## 7. What this study cannot tell you

1. It cannot tell you what the winning frames looked like. No entry was played for this card, so nothing here is a claim about
   art, colour or motion at a specific second. The claims are about what the entry pages, postmortems and one player's feedback
   say, which is weaker evidence than watching the recording.
2. Three of the five events are ranked by peer jam voters, not by a panel with a budget. Rule 5 is the only one drawn from a
   judged hackathon, and it is the one that maps most directly onto our event; the other four are analogies, useful ones.
3. One counter-signal is recorded rather than smoothed over: in GMTK 2024 the entry that took 1st in Top Marks, Picture
   Perfect, placed 20th overall (4.432) with 202 ratings. A curator's favourite and a crowd's favourite are different games,
   so rule 2 is evidence about one voter, Mark Brown, not about the field.

## 8. Q: for gamedev

1. M4, does one TALK exchange fit inside S4's 2,400 steps without moving the gate's three option choice? If no, rule 2 stays
   a miss and I would rather you rule on it than have the script silently drift.
2. Is S1's 16.00 s fixed by `data/title_timing.json` as a contract, or is it a value the script chose? M1 assumes the second;
   if it is the first, M1 becomes a change to the contract and not to the demo.
3. Rule 4 needs one sentence chosen between "AI that obeys hardware limits" and "Kronos and Zeus reincarnated on the M3".
   PLAN-WIN uses the first as the story and the second as the creativity; the demo caption can only carry one, and I would put
   the first on S1 and the second on S2.

## 9. Applied to our demo

Checked against `knowledge/DEMO-SCRIPT.md` as it stands on 2026-10-23, shot by shot. This is the last section on purpose: it is
the part gamedev should read first.

| Rule | Satisfied today? | The evidence in the script, or the miss |
| --- | --- | --- |
| 1: safe first ten seconds | No | S1 takes no input until 0:11.80 (step 708); first player-owned input is S4's Down at 0:54.23. There is no fail state in the window, so the safe half is met, the teaching half is not. |
| 2: theme verb on a default input | No | The talk-fight first appears in S6, 1:53.03, which is 63 per cent of the way through the demo. |
| 3: threat or promise before input | Yes | S1: `title_theme` from step 0, road dashes one per beat, car bob, the 2 frame lightning at 0:11.60; S3 carries `car_engine_loop`. No silent shot in the file. |
| 4: premise in one sentence | Partly | Two one-liners exist and compete: "AI that obeys hardware limits" and "Kronos and Zeus reincarnated on the M3". One has to win. |
| 5: the repeatable thing inside 30 s | No | The first bake row is at 1:19.03. S1's caption talks about boot time and the palette, which is the how, not the what. |

Score today: one clean pass (rule 3), one partial (rule 4), three misses (rules 1, 2, 5). Two of the three misses are overlay
or timing edits, which is the reason this study was worth 35 minutes and not a redesign.

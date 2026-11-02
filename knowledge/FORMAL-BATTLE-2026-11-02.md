# Formal proof of the battle phase machine (2026-11-02, card t_1b355b57)

Nayil's order for this card: every battle must complete from start to finish, by spare or by hp 0.
The real game proof is `knowledge/battle-proof-2026-11-02/REPORT.md` (six runs of the GML build,
spare and kill for morgan_gate, tutorial_sailors and percy, all reaching the ending frame and
back in the world). This document adds the formal proof of the state machine underneath it.

Nothing in `game/scripts/` was edited. `pp_battle_director.gml` was read only.

## Files

| path | what it is |
|---|---|
| `projects/arananet/manager/formal/BattlePhases.tla` | the model: 8 phases, 5 commands, trust, both health pools, the turn counter |
| `projects/arananet/manager/formal/BattlePhasesBroken.tla` | the deliberately broken variant: the transition out of the result phase is removed |
| `projects/arananet/manager/formal/BattlePhasesUnguardedSpare.tla` | a second broken variant: the spare gate is removed from the press |
| `projects/arananet/manager/formal/battle/*.cfg` | one TLC configuration per instance (four encounters, four reachability witnesses, two broken variants) |
| `projects/arananet/manager/formal/battle/logs/*.log` | the raw TLC output of every run |
| `projects/arananet/manager/formal/battle/run_tlc.py` | runs all fourteen checks |
| `projects/arananet/manager/formal/Pfair.tla` | the three line probe of the fairness assumption the spec uses |
| `projects/arananet/manager/formal/battle/write_cfgs.py` | writes the .cfg files from one table of values |
| `projects/arananet/manager/formal/battle/make_variants.py` | writes the two variant modules from the faithful one |
| `tests/test_formal_battle_constants.py` | fails when a .cfg constant stops matching the data, and when a variant drifts from the faithful module |

Tool: TLC 2.19 (tla2tools.jar at `D:\Tools\tla2tools.jar`), Java 17.0.20.1 Temurin, node CitadelArana.

## The machine, and the code it comes from

| phase or step | the GML it mirrors |
|---|---|
| intro | `pp_battle_step_intro`, including the `forced_defeat` branch on the intro's first step |
| menu | `pp_battle_step_menu` and `pp_battle_begin_action`: FIGHT, POWER, TALK, SPARE, ITEM |
| resolve | `pp_battle_step_resolve`, then `pp_battle_hurt_enemy` |
| message | `pp_battle_step_message` and `pp_battle_after_message`, in the code's own order |
| telegraph | `pp_battle_step_telegraph` |
| dodge | `pp_battle_step_dodge` (a hit of the enemy's band, or a miss, then the menu) |
| result | `pp_battle_step_result` and `pp_battle_enter_result`, closing board first |
| ended | `PPBattlePhase.ended` (win, spare, interrupt) |
| gameover | `pp_battle_step_gameover`: a defeat is held in the result phase with the game over card, whose two rows are CONTINUE and RETURN TO TITLE |

The spare gate is `pp_battle_spare_allowed` word for word: health above 0 and
(`trust >= trust_to_spare` or `hp * 100 <= max_hp * spare_hp_percent`). The interrupt gate is
`pp_battle_interrupt_ready` word for word. The kill is `pp_battle_hurt_enemy`'s
"bar reaches 0 and the result is still none". The defeat is `pp_battle_step_dodge`'s hp 0.

## Constants, and where each one comes from

Every value below is a field of the game's data, not a choice of the model. The four model-only
bounds are named as such.

| constant | morgan_gate | tutorial_sailors | percy | source |
|---|---|---|---|---|
| EnemyMaxHP | 28 | 24 | 40 | `data/enemies/all.json` max_hp |
| EnemyAtkMin / EnemyAtkMax | 2 / 3 | 2 / 2 | 3 / 6 | the row's attack band, widened by every phase row's attack (percy's phase rows raise the top to 6) |
| TrustToSpare | 3 | 3 | 3 | trust_to_spare |
| SpareHPPercent | 25 | 25 | 25 | spare_hp_percent |
| InterruptHPPercent | 0 | 0 | 40 | interrupt.hp_at_or_below, 0 when the row has no block |
| FlagMetPrometheus | FALSE | FALSE | FALSE | the block's unless_flag, unset for these runs |
| TrustPerTalk | 1 | 1 | 1 | `data/encounters/all.json` trust_per_talk |
| HasTalk | TRUE | TRUE | TRUE | the enemy row's talk_dialogue |
| ForcedDefeat | FALSE | FALSE | FALSE | the encounter row's forced_defeat (TRUE for deck_collapse) |
| PartyMaxHP | 20 | 20 | 20 | `data/characters/party.json` hero max_hp |
| ItemCount / ItemHeal | 2 / 6 | 2 / 6 | 2 / 6 | starting_items salve x2, `data/items.json` heal 6 |
| PowerCost / PowerDamage | 1 / 6 | 1 / 6 | 1 / 6 | `data/powers.json` tide_step cost 1, power 6 |
| WillMax | 3 | 3 | 3 | hero will_max |
| FightMaxHit | 12 | 12 | 12 | `PP_FIGHT_DAMAGE_MAX` 12 at power_multiplier 1.0 |
| MaxTurn | 6 | 6 | 6 | model only: turn saturates, and nothing reads turn as a gate |
| IntroSteps / MessageReads / BarReads | 2 / 2 / 3 | same | same | model only: countdowns with no effect on a meter |

`tests/test_formal_battle_constants.py` reads these .cfg files back and compares every one of them
with the JSON and with `pp_config.gml`, so a rebalance that misses the spec fails the suite.
`pp_battle_director.gml` reads `_battle.turn` only in three debug lines, the ledger's exit row and
the art frame (grep, 2026-11-02), which is why the turn may saturate at MaxTurn without changing a
transition.

## Properties

Run over the instances with `DecisivePlayer = FALSE` (every press the menu offers) unless the row
says otherwise.

| property | kind | what it says | result |
|---|---|---|---|
| TypeOK | invariant | every variable stays in its own set; the talk panel is only open in the menu phase | holds |
| NoDeadlock | invariant | every reachable state is an ending (`ended`, `gameover`) or has an enabled step | holds |
| SpareOnlyWhenConditionsMet | invariant | a spare that ended a fight was taken when `pp_battle_spare_allowed` held (the latch records which clause let it through: trust or health) | holds |
| EndedReason | invariant | the ended phase always carries a result and is not a defeat | holds |
| GameOverIsDefeat | invariant | the game over state is a defeat and nothing else | holds |
| ZeroBarAfterSpareOrKill | invariant | a spare or a kill leaves the enemy's bar at 0 and nothing raises it | holds |
| Termination | liveness, `DecisivePlayer = TRUE` | every behaviour reaches `ended` or `gameover` | holds |
| WitnessSpare | reachability | a behaviour ends by spare | witness found (trust 3, gate "trust": the three talk spare) |
| WitnessKill | reachability | a behaviour ends by kill | witness found (bar 0, result kill) |
| WitnessDefeat | reachability | a behaviour ends in the game over state | witness found (party hp 0, defeated) |
| WitnessInterrupt | reachability | a refused spare inside percy's band ends the fight | witness found (16 hp of 40, result interrupt) |

The four witnesses are checked in the standard TLC way: the invariant is the *negation* of the
claim, so the violation TLC reports is the trace that proves the claim. Their last states are in
`battle/logs/witness_*.log`.

## TLC output

The real spec, morgan_gate, safety (all six invariants):

    Model checking completed. No error has been found.
    1487750 states generated, 288150 distinct states found, 0 states left on queue.
    Finished in 03s

The real spec, morgan_gate, termination (`DecisivePlayer = TRUE`, invariants and Termination):

    Checking temporal properties for the complete state space with 12319 total distinct states
    Model checking completed. No error has been found.
    67528 states generated, 12319 distinct states found, 0 states left on queue.
    Finished in 02s

The broken variant (result phase exit removed), invariants:

    Error: Invariant NoDeadlock is violated.
    6612 states generated, 1883 distinct states found, 531 states left on queue.

The broken variant, Termination alone:

    Error: Temporal properties were violated.
    136647 states generated, 24680 distinct states found, 0 states left on queue.

The second broken variant (spare gate removed):

    Error: Invariant SpareOnlyWhenConditionsMet is violated.
    69 states generated, 45 distinct states found, 15 states left on queue.

So the checks are not vacuous: removing one transition and removing one guard are both caught, and
the two variants differ from the faithful module in exactly that block and nothing else (asserted by
the test).

## State counts

| run | generated | distinct |
|---|---|---|
| morgan_gate, safety | 1,487,750 | 288,150 |
| morgan_gate, termination | 67,528 | 12,319 |
| tutorial_sailors, safety | 552,873 | 110,744 |
| tutorial_sailors, termination | 27,039 | 5,081 |
| percy, safety | 2,696,730 | 519,361 |
| percy, termination | 137,082 | 25,115 |
| deck_collapse, safety (the forced defeat) | 6 | 6 |
| witness spare / kill / defeat / interrupt | 73,969 / 81,676 / 213,945 / 25,199 | 25,076 / 25,723 / 57,504 / 9,218 |
| broken, invariants / termination | 6,612 / 136,647 | 1,883 / 24,680 |
| unguarded spare | 69 | 45 |

## The one behaviour that does not end, and why it is not a softlock

The game cannot promise that every player ends a fight. TALK is always offered, the arena's hit is
optional, and the TLC counterexample this model found for the unrestricted player is exactly that
loop: menu, TALK, message, telegraph, dodge (missed), menu, with the bar untouched at 1 hp and the
party at 2. It is a legal, infinite behaviour of the shipped code.

It is not a softlock, and this is the distinction the card's question turns on:

- the menu is live at every step, so the player can always leave the loop;
- SPARE is enabled the moment trust reaches the row's threshold (after three talks) or the bar
  falls to 25 percent, and it is checked here as a property of the state, not of the trace;
- no meter is corrupted by the loop: hp, trust, items and the turn counter are all in TypeOK.

Termination is therefore stated for the player who presses the two decisive commands, and the model
carries that as a mode (`DecisivePlayer = TRUE`) rather than as a fairness assumption. Under that
mode the state graph has no cycle at all: a SPARE press ends the fight, and a FIGHT press takes at
least one from the enemy's bar, floor 1 in the code (`max(1, round(...))` in
`pp_battle_fight_damage`), and nothing puts a point back. The only fairness used is
`WF_vars(Next)`, which says the machine takes a step when it has one; a three line probe of that
form, `manager/formal/Pfair.tla`, is kept beside the spec because it is what showed, on this PC,
that this TLC honours `WF_vars` of the whole next-state relation (it does not exclude a cycle that
is unfair to one disjunct of `Next`, which is why the player's habit is a mode here and not a
`WF_vars(MenuFight)` conjunct).

## What is not modelled, and why it cannot hide a softlock

- The timing bar's 0..100 float position: what it decides is one number, the damage of a press,
  and the model takes the damage from 1..FightMaxHit, which covers every value the bar can produce.
- The arena's hazards: their effect on the machine is that the party loses 0..EnemyAtkMax hp and
  the dodge ends. The pattern's own shape cannot change a phase transition.
- The telegraph's 12 steps: a countdown with no state carrying effect, taken as one step.
- The live talk box (`pp_talk_live_*`) and the model backed persona: they move `talk_mercy`, which
  no phase transition reads. The trust meter the spare gate reads is the encounter row's
  trust_per_talk, which the TALK command adds.
- Frame by frame animation values (popup, flash, shake, cursor note): none of them gates a phase.

## How to re-run

    cd "<workspace>/Shared/projects/arananet/manager/formal"
    set TEMP=D:\Temp\hermes-tmp
    set TMP=D:\Temp\hermes-tmp
    python battle/write_cfgs.py
    python battle/make_variants.py
    python battle/run_tlc.py

    cd "<repo>"
    python -m pytest tests/test_formal_battle_constants.py -q

`run_tlc.py` runs TLC with `-deadlock`, because the ending phases are states with nothing left to
do and TLC's own deadlock detector would call those stuck. The machine's own NoDeadlock invariant is
the check that replaces it, and it covers every other phase.

## Verdict

For the three encounters that were proved in the real build (morgan_gate, tutorial_sailors, percy)
and for the forced defeat row (deck_collapse), the phase machine has no deadlock, no state where a
spare is granted off gate, and no behaviour of a decisive player that fails to reach `ended` or the
game over state. All four endings are reachable. The two deliberately broken variants are rejected.

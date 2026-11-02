"""Headless mirror of the battle director for the three demo fights (card THREE-BATTLES, 2026-11-01).

No GML runs on this host, so this mirrors the menu gate (pp_command_state), the spare gate, the interrupt gate, the damage
formula, the ACT effects, the phase crossings and the TALK hint as the GML reads them from data, plus the scene runner's
branch and battle commands. tests/test_three_battles.py pins the GML text so the mirror cannot drift silently.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as handle:
        return json.load(handle)


def macro(name):
    with open(os.path.join(ROOT, "game", "scripts", "pp_config", "pp_config.gml"), encoding="utf-8") as handle:
        return int(re.search(r"#macro %s (\d+)" % name, handle.read()).group(1))


DMG_MIN = macro("PP_FIGHT_DAMAGE_MIN")
DMG_MAX = macro("PP_FIGHT_DAMAGE_MAX")
ENEMIES = {e["id"]: e for e in load("data/enemies/all.json")["enemies"]}
ENCOUNTERS = {e["id"]: e for e in load("data/encounters/all.json")["encounters"]}
DIALOGUE = {d["id"]: d for d in load("data/dialogue/all.json")["dialogue"]}
SCENES = {s["id"]: s for s in load("data/scenes/all.json")["scenes"]}
MAPS = {m["id"]: m for m in load("data/maps/all.json")["maps"]}
PARTY = load("data/characters/party.json")["characters"][0]
POWERS = {p["id"]: p for p in load("data/powers.json")["powers"]}


def damage(bar_power, multiplier=1.0):
    p = max(0, min(100, bar_power))
    return max(1, round((DMG_MIN + (DMG_MAX - DMG_MIN) * (p / 100.0)) * multiplier))


def pacing_seconds(turns):
    """The project's own pacing numbers (data/encounters tutorial_sailors.pacing): 27 s fixed, 21 s a turn."""
    return 27 + 21 * turns


class Battle:
    def __init__(self, enc_id, flags=(), route="pacifist"):
        self.enc = ENCOUNTERS[enc_id]
        self.enemy = ENEMIES[self.enc["enemies"][0]]
        self.flags, self.route = set(flags), route
        self.hp, self.max_hp, self.will = PARTY["max_hp"], PARTY["max_hp"], PARTY["will_max"]
        self.powers = [POWERS[i] for i in PARTY.get("starting_powers", []) if i in POWERS]
        self.enemy_hp, self.trust, self.turn = self.enemy["max_hp"], 0, 0
        self.pool, self.attack, self.phase = list(self.enemy["patterns"]), dict(self.enemy["attack"]), 0
        self.skip, self.result, self.defeated, self.hint = False, "none", False, ""
        self.refusals, self.crossed = [], []

    # pp_battle_spare_allowed, pp_battle_spare_route_refused, pp_battle_interrupt_ready
    def spare_allowed(self):
        if self.enemy_hp <= 0:
            return False
        if self.trust >= self.enemy["trust_to_spare"]:
            return True
        return self.enemy_hp <= self.enemy["max_hp"] * self.enemy["spare_hp_percent"] / 100.0

    def route_refused(self):
        r = self.enc.get("spare_refuses_on_route", "")
        return bool(r) and self.route == r

    def interrupt_ready(self):
        blk = self.enemy.get("interrupt")
        if self.enemy_hp <= 0 or self.spare_allowed() or not blk or blk.get("on") != "spare_refused":
            return False
        if blk.get("unless_flag") and blk["unless_flag"] in self.flags:
            return False
        return self.enemy_hp * 100 <= blk["hp_at_or_below"] * self.enemy["max_hp"]

    def command_state(self, cmd):
        if cmd == "power":
            if not self.powers:
                return False, "no power. none taken"
            return (False, "no will left") if self.will <= 0 else (True, "")
        if cmd == "spare":
            if self.interrupt_ready():
                return True, ""
            if self.route_refused():
                return False, "mercy is off duty"
            if not self.spare_allowed():
                return False, self.enemy.get("spare_refusal", "it is not ready")
        return True, ""

    def spare_hint(self):
        need = max(0, self.enemy["trust_to_spare"] - self.trust)
        key = "spare_hint" if need > 0 else "spare_ready_hint"
        return self.enemy.get(key, "").replace("{n}", str(need), 1)

    def hurt(self, dmg):
        self.enemy_hp = max(0, self.enemy_hp - dmg)
        if self.enemy_hp <= 0 and self.result == "none":
            self.result = "kill"
        rows = self.enemy.get("phases", [])
        while self.enemy_hp > 0 and self.phase < len(rows):
            row = rows[self.phase]
            if not self.enemy_hp * 100 <= row["hp_at_or_below"] * self.enemy["max_hp"]:
                break
            self.phase += 1
            self.pool.append(row["pattern_id"])
            self.crossed.append(row["pattern_id"])
            if "attack" in row:
                self.attack = dict(row["attack"])

    def act(self, option):
        for r in self.enemy.get("act_responses", []):
            if r["option"] != option:
                continue
            if "pattern_pool" in r:
                self.pool = list(r["pattern_pool"])
            if "attack_delta" in r:
                self.attack = {"min": max(1, self.attack["min"] + r["attack_delta"]), "max": max(1, self.attack["max"] + r["attack_delta"])}
            if r.get("skip_turn"):
                self.skip = True

    def ended(self):
        return self.result in ("kill", "spare", "interrupt") or self.defeated

    def outcome(self):
        if self.defeated:
            return "defeat"
        return {"interrupt": "interrupted", "spare": "spare", "kill": "kill"}.get(self.result, "unresolved")

    def do(self, cmd, arg=None, dodge="clean"):
        ok, why = self.command_state(cmd)
        if not ok:
            self.refusals.append((cmd, why))
            return "refused"
        self.turn += 1
        if cmd == "fight":
            self.hurt(damage(60 if arg is None else arg))
        elif cmd == "power":
            self.will = max(0, self.will - self.powers[0]["cost"])
            self.hurt(self.powers[0]["power"])
        elif cmd == "talk":
            self.trust += self.enc["trust_per_talk"]
            self.act(arg or 0)
            self.hint = self.spare_hint()
        elif cmd == "spare":
            if self.spare_allowed() and not self.route_refused():
                self.result, self.enemy_hp = "spare", 0
            elif self.interrupt_ready():
                self.result = "interrupt"
        if self.ended():
            return self.outcome()
        if self.skip:
            self.skip = False
        elif dodge == "stand":
            self.hp = max(0, self.hp - self.attack["max"])
            self.defeated = self.hp <= 0
        return self.outcome() if self.ended() else "continue"


def start_points(enc_id):
    """Every door that starts the encounter: (room, how, tile). A scene battle command or a map battle or marker trigger."""
    out = []
    for s in SCENES.values():
        if any(c.get("cmd") == "battle" and c.get("id") == enc_id for c in s["commands"]):
            out.append((s["map"], "scene:" + s["id"], (s["start"]["x"], s["start"]["y"])))
    for m in MAPS.values():
        for t in m.get("triggers", []):
            if t["kind"] in ("battle", "marker") and t["id"] == enc_id:
                out.append((m["id"], "trigger:%d,%d" % (t["x"], t["y"]), (t["x"], t["y"])))
    return out


def run_scene(scene_id, flags, outcomes, choice=0):
    """Walk a scene as pp_scene does: branch re-enters the target in place, battle waits for an outcome, an interrupted
    fight replaces the runner with the scene the enemy row names (remaining commands never play)."""
    flags, started, seen, said = set(flags), [], [scene_id], []
    cur, i = SCENES[scene_id], 0
    for _ in range(1000):
        cmd = cur["commands"][i]
        k = cmd["cmd"]
        if k == "say":
            d = DIALOGUE[cmd["id"]]
            said.append(cmd["id"])
            flags.update(d.get("sets", []))
            if "choices" in d:
                ch = d["choices"][choice]
                flags.update(ch.get("sets", []))
                said.append(ch["goto"])
                flags.update(DIALOGUE[ch["goto"]].get("sets", []))
        elif k == "setflag":
            (flags.add if cmd.get("value", True) else flags.discard)(cmd["name"])
        elif k == "battle":
            enc = ENCOUNTERS[cmd["id"]]
            started.append(cmd["id"])
            out = outcomes[cmd["id"]]
            if out == "kill":
                flags.update(enc.get("flags_on_kill", []))
            if out == "spare":
                flags.update(enc.get("flags_on_spare", []))
            if out == "interrupted":
                cur, i = SCENES[ENEMIES[enc["enemies"][0]]["interrupt"]["scene"]], 0
                seen.append(cur["id"])
                continue
        elif k == "branch":
            if cmd["flag"] in flags:
                cur, i = SCENES[cmd["scene"]], 0
                seen.append(cur["id"])
                continue
        elif k == "end":
            break
        i += 1
    return {"flags": flags, "started": started, "seen": seen, "said": said, "last": cur["id"], "map": cur.get("map")}

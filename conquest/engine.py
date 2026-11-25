# The rukes of conquest
#
# Everything the UI, the server and the tests need to know about game state
# lives in `Game`. The UI only ever reads from it to draw and calls its
# methods to act. Illegal actions raise `IllegalAction` and don't change
# state, so a server can feed untrusted client messages straight to
# `Game.apply_action`.
#
# Rule assumptions:
#   * movement is 4-directional (no diagonals) and cannot pass through units or obstacles
#   * range is Manhattan distance
#   * a defender retaliates only if the attacker is inside the defender's range
#   * a buff's extra health is clamped away when it expires (health = min(health, max))
#   * Bombard is not "damage", so Shield Wall does not reduce it
#   * commands are free to pick in the loadout (only troops cost gold)
import random
from collections import deque
from dataclasses import dataclass, field

import data

BOARD_SIZE = 20
MAX_TROOPS = 10
MAX_COMMANDS = 4
STARTING_GOLD = 1000
COMMANDS_COST_GOLD = False          # the wiki is ambiguous; the original code only charged for troops
COMMAND_POINTS_PER_TURN = 25
STARTING_COMMAND_POINTS = 0
OBSTACLE_ROWS = (5, 14)             # inclusive; leaves rows 0-4 and 15-19 clear for the armies
START_ROWS = {0: (17, 18, 19), 1: (0, 1, 2)}   # player 0 starts at the bottom of the board

SELECTION, MOVEMENT, COMBAT, RALLY = "SELECTION", "MOVEMENT", "COMBAT", "RALLY"
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class IllegalAction(Exception):
    """Raised when a player tries something the rules do not allow."""


def _int(value):
    """Untrusted input from the network: accept real ints only."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise IllegalAction("expected a whole number, got %r" % (value,))
    return value


def _str(value):
    if not isinstance(value, str):
        raise IllegalAction("expected text, got %r" % (value,))
    return value


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ---------------------------------------------------------------- loadouts --

@dataclass
class Loadout:
    """A player's squad before the game: which troops and commands they bought."""
    troops: list = field(default_factory=list)      # list of keys from data.TROOPS
    commands: list = field(default_factory=list)    # list of keys from data.COMMANDS

    @property
    def gold_spent(self):
        spent = sum(data.TROOPS[t]["cost"] for t in self.troops)
        if COMMANDS_COST_GOLD:
            spent += sum(data.COMMANDS[c]["cost"] for c in self.commands)
        return spent

    @property
    def gold_left(self):
        return STARTING_GOLD - self.gold_spent

    def can_add_troop(self, kind):
        return (kind in data.TROOPS and len(self.troops) < MAX_TROOPS
                and data.TROOPS[kind]["cost"] <= self.gold_left)

    def add_troop(self, kind):
        if not self.can_add_troop(kind):
            raise IllegalAction("cannot add troop %r" % (kind,))
        self.troops.append(kind)

    def remove_troop(self, index):
        if not 0 <= index < len(self.troops):
            raise IllegalAction("no troop at index %r" % (index,))
        self.troops.pop(index)

    def can_add_command(self, key):
        if key not in data.COMMANDS or key in self.commands or len(self.commands) >= MAX_COMMANDS:
            return False
        if COMMANDS_COST_GOLD and data.COMMANDS[key]["cost"] > self.gold_left:
            return False
        return True

    def add_command(self, key):
        if not self.can_add_command(key):
            raise IllegalAction("cannot add command %r" % (key,))
        self.commands.append(key)

    def remove_command(self, index):
        if not 0 <= index < len(self.commands):
            raise IllegalAction("no command at index %r" % (index,))
        self.commands.pop(index)

    def validate(self):
        """Raise IllegalAction unless this is a legal squad (what the server checks)."""
        if not 1 <= len(self.troops) <= MAX_TROOPS:
            raise IllegalAction("a squad needs between 1 and %d troops" % MAX_TROOPS)
        if any(t not in data.TROOPS for t in self.troops):
            raise IllegalAction("unknown troop")
        if len(self.commands) > MAX_COMMANDS or len(set(self.commands)) != len(self.commands):
            raise IllegalAction("at most %d different commands" % MAX_COMMANDS)
        if any(c not in data.COMMANDS for c in self.commands):
            raise IllegalAction("unknown command")
        if self.gold_left < 0:
            raise IllegalAction("squad costs more than %d gold" % STARTING_GOLD)

    @property
    def is_ready(self):
        try:
            self.validate()
        except IllegalAction:
            return False
        return True

    def to_dict(self):
        return {"troops": list(self.troops), "commands": list(self.commands)}

    @classmethod
    def from_dict(cls, d):
        return cls(troops=list(d.get("troops", [])), commands=list(d.get("commands", [])))


# --------------------------------------------------- board generation ------

# (height, width): 1x1 and 2x2 squares, plus lines of length 2, 3 and 4 in both orientations
OBSTACLE_SHAPES = [(1, 1), (2, 2), (1, 2), (2, 1), (1, 3), (3, 1), (1, 4), (4, 1)]


def generate_obstacles(rng=None):
    """Return a set of (row, col) blocked tiles: 1-3 non-overlapping obstacles in the middle rows."""
    rng = rng or random.Random()
    wanted = rng.randint(1, 3)
    cells, placed, attempts = set(), 0, 0
    while placed < wanted and attempts < 200:
        attempts += 1
        h, w = rng.choice(OBSTACLE_SHAPES)
        row = rng.randint(OBSTACLE_ROWS[0], OBSTACLE_ROWS[1] - h + 1)
        col = rng.randint(0, BOARD_SIZE - w)
        shape = {(row + i, col + j) for i in range(h) for j in range(w)}
        if shape & cells:
            continue
        cells |= shape
        placed += 1
    return cells


def auto_formation(troops, player):
    """Spread troops over the player's three start rows, centred. Returns [(row, col)] in troop order."""
    rows = START_ROWS[player]
    slots = {r: [] for r in rows}
    for i in range(len(troops)):
        slots[rows[i % 3]].append(i)
    positions = [None] * len(troops)
    for r, indices in slots.items():
        n = len(indices)
        start = (BOARD_SIZE - (2 * n - 1)) // 2 if n else 0
        for j, idx in enumerate(indices):
            positions[idx] = (r, start + 2 * j)
    return positions


# ---------------------------------------------------------------- units -----

@dataclass
class Unit:
    uid: int
    owner: int
    kind: str
    row: int
    col: int
    health: int
    effects: dict = field(default_factory=dict)     # active command key -> player who cast it

    @property
    def pos(self):
        return (self.row, self.col)

    @property
    def stats(self):
        return data.TROOPS[self.kind]

    @property
    def name(self):
        return self.stats["name"]

    @property
    def cost(self):
        return self.stats["cost"]

    @property
    def speed(self):
        return self.stats["speed"]

    @property
    def range(self):
        return self.stats["range"]

    @property
    def max_health(self):
        return self.stats["health"]

    @property
    def damage(self):
        return self.stats["damage"] + sum(data.COMMANDS[e].get("damage_bonus", 0) for e in self.effects)

    @property
    def effective_max_health(self):
        return self.max_health + sum(data.COMMANDS[e].get("health_bonus", 0) for e in self.effects)

    @property
    def damage_cap(self):
        caps = [data.COMMANDS[e]["damage_cap"] for e in self.effects if "damage_cap" in data.COMMANDS[e]]
        return min(caps) if caps else None

    @property
    def first_strike(self):
        return "vigilance" in self.effects

    @property
    def chastised(self):
        return "chastise" in self.effects

    def to_dict(self):
        return {"uid": self.uid, "owner": self.owner, "kind": self.kind, "row": self.row, "col": self.col,
                "health": self.health, "effects": dict(self.effects)}

    @classmethod
    def from_dict(cls, d):
        return cls(d["uid"], d["owner"], d["kind"], d["row"], d["col"], d["health"], dict(d.get("effects", {})))


# ----------------------------------------------------------------- game -----

class Game:
    def __init__(self):
        self.units = {}                 # uid -> Unit
        self.obstacles = set()
        self.commands = [[], []]        # command keys each player brought
        self.cooldowns = [{}, {}]       # per player: command key -> turns remaining
        self.command_points = [STARTING_COMMAND_POINTS, STARTING_COMMAND_POINTS]
        self.current = 0
        self.turn_number = 0            # counts each player's turn, so it is 1 on the very first turn
        self.phase = SELECTION
        self.selected = None            # uid of the unit acting this turn
        self.moves_left = 0
        self.has_attacked = False
        self.winner = None
        self.next_uid = 1
        self.log = []                   # human readable event history, newest last

    # ---- construction

    @classmethod
    def new(cls, loadouts, formations=None, obstacles=None, rng=None):
        """Start a game. `loadouts` is [Loadout, Loadout]; `formations` is an optional
        [[(row, col)...], [(row, col)...]] aligned with each loadout's troop order."""
        rng = rng or random.Random()
        game = cls()
        game.obstacles = set(obstacles) if obstacles is not None else generate_obstacles(rng)
        for player in (0, 1):
            loadout = loadouts[player]
            loadout.validate()
            game.commands[player] = list(loadout.commands)
            game.cooldowns[player] = {c: 0 for c in loadout.commands}
            spots = formations[player] if formations else auto_formation(loadout.troops, player)
            if len(spots) != len(loadout.troops):
                raise IllegalAction("formation does not match troops")
            for kind, (row, col) in zip(loadout.troops, spots):
                if row not in START_ROWS[player] or not 0 <= col < BOARD_SIZE:
                    raise IllegalAction("troops must start inside your first three rows")
                if game.is_blocked(row, col):
                    raise IllegalAction("two troops cannot share a tile")
                game._spawn(player, kind, row, col)
        game._start_turn(0)
        return game

    def _spawn(self, owner, kind, row, col):
        unit = Unit(self.next_uid, owner, kind, row, col, data.TROOPS[kind]["health"])
        self.units[unit.uid] = unit
        self.next_uid += 1
        return unit

    # ---- queries

    @staticmethod
    def in_bounds(row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def unit_at(self, row, col):
        for unit in self.units.values():
            if unit.row == row and unit.col == col:
                return unit
        return None

    def units_of(self, player):
        return [u for u in self.units.values() if u.owner == player]

    def is_blocked(self, row, col):
        return (row, col) in self.obstacles or self.unit_at(row, col) is not None

    @property
    def selected_unit(self):
        return self.units.get(self.selected) if self.selected is not None else None

    def movement_allowance(self, unit):
        """Tiles this unit may still walk: what is left if it is acting now, else its full allowance."""
        if self.selected == unit.uid:
            return self.moves_left
        return unit.speed * (2 if "charge" in unit.effects else 1)

    def reachable_tiles(self, unit, budget=None):
        """{(row, col): steps} of every tile the unit could walk to (breadth first, 4-directional)."""
        if unit.chastised:
            return {}
        if budget is None:
            budget = self.movement_allowance(unit)
        start = unit.pos
        dist = {start: 0}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            if dist[cur] == budget:
                continue
            for dr, dc in DIRECTIONS:
                nxt = (cur[0] + dr, cur[1] + dc)
                if nxt in dist or not self.in_bounds(*nxt) or self.is_blocked(*nxt):
                    continue
                dist[nxt] = dist[cur] + 1
                queue.append(nxt)
        del dist[start]
        return dist

    def attack_targets(self, unit):
        """Enemy units inside the unit's range right now."""
        if unit.chastised:
            return []
        return [u for u in self.units.values()
                if u.owner != unit.owner and manhattan(unit.pos, u.pos) <= unit.range]

    def command_status(self, player, key):
        """None if `player` could use the command right now, otherwise the reason they cannot."""
        if self.winner is not None:
            return "the game is over"
        if player != self.current:
            return "not your turn"
        if key not in self.commands[player]:
            return "command not in your squad"
        if self.cooldowns[player][key] > 0:
            return "on cooldown for %d more turns" % self.cooldowns[player][key]
        if self.command_points[player] < data.COMMANDS[key]["cost"]:
            return "not enough command points"
        if key == "charge" and self.phase not in (SELECTION, MOVEMENT):
            return "Charge must be used before or during movement"
        if key == "winds_of_fate" and not any(
                k != key and turns > 0 for k, turns in self.cooldowns[player].items()):
            return "no other command is on cooldown"
        return None

    # ---- turn flow

    def _start_turn(self, player):
        self.current = player
        self.turn_number += 1
        self.phase = SELECTION
        self.selected = None
        self.moves_left = 0
        self.has_attacked = False
        # Everything this player cast on their previous turn wears off now.
        for unit in self.units.values():
            for effect in [e for e, caster in unit.effects.items() if caster == player]:
                del unit.effects[effect]
            unit.health = min(unit.health, unit.effective_max_health)
        self.command_points[player] += COMMAND_POINTS_PER_TURN
        for key in self.cooldowns[player]:
            if self.cooldowns[player][key] > 0:
                self.cooldowns[player][key] -= 1
        self._log("Turn %d: player %d" % (self.turn_number, player + 1))

    def end_turn(self):
        self._require_live()
        for unit in self.units.values():
            unit.effects.pop("charge", None)        # Charge only lasts for the turn it is cast
        self._start_turn(1 - self.current)

    def end_phase(self):
        self._require_live()
        if self.phase == SELECTION:
            self.phase = RALLY                      # nothing selected: skip straight to commands
        elif self.phase == MOVEMENT:
            self.phase = COMBAT
        elif self.phase == COMBAT:
            self.phase = RALLY
        else:
            self.end_turn()

    def resign(self, player):
        if self.winner is None:
            self.winner = 1 - player
            self._log("Player %d resigned" % (player + 1))

    # ---- actions

    def select_unit(self, uid):
        self._require_live()
        if self.phase != SELECTION:
            raise IllegalAction("you can only pick a unit in the selection phase")
        unit = self.units.get(uid)
        if unit is None or unit.owner != self.current:
            raise IllegalAction("pick one of your own troops")
        if unit.chastised:
            raise IllegalAction("that troop has been chastised")
        self.selected = uid
        self.moves_left = unit.speed * (2 if "charge" in unit.effects else 1)
        self.phase = MOVEMENT

    def move_unit(self, row, col):
        self._require_live()
        if self.phase != MOVEMENT or self.selected_unit is None:
            raise IllegalAction("you can only move during the movement phase")
        unit = self.selected_unit
        cost = self.reachable_tiles(unit).get((row, col))
        if cost is None:
            raise IllegalAction("that tile is out of reach")
        unit.row, unit.col = row, col
        self.moves_left -= cost

    def attack(self, target_uid):
        self._require_live()
        if self.phase not in (MOVEMENT, COMBAT) or self.selected_unit is None:
            raise IllegalAction("select a troop before attacking")
        if self.has_attacked:
            raise IllegalAction("already attacked this turn")
        attacker = self.selected_unit
        defender = self.units.get(target_uid)
        if defender is None or defender.owner == attacker.owner:
            raise IllegalAction("pick an enemy troop")
        if defender not in self.attack_targets(attacker):
            raise IllegalAction("target is out of range")
        self.phase = COMBAT
        self.has_attacked = True
        in_reach = manhattan(attacker.pos, defender.pos) <= defender.range
        if defender.first_strike and in_reach:
            self._strike(defender, attacker)
            if attacker.uid in self.units:
                self._strike(attacker, defender)
        else:
            self._strike(attacker, defender)
            if defender.uid in self.units and in_reach:
                self._strike(defender, attacker)
        if self.selected not in self.units:
            self.selected = None
        if self.winner is None:
            self.phase = RALLY

    def use_command(self, key, target_uid=None):
        self._require_live()
        player = self.current
        reason = self.command_status(player, key)
        if reason:
            raise IllegalAction(reason)
        spec = data.COMMANDS[key]
        target = self.units.get(target_uid) if target_uid is not None else None
        if spec["target"] == "ally" and (target is None or target.owner != player):
            raise IllegalAction("%s needs one of your troops as its target" % spec["name"])
        if spec["target"] == "enemy" and (target is None or target.owner == player):
            raise IllegalAction("%s needs an enemy troop as its target" % spec["name"])

        if key in ("battle_cry", "stoicism", "shield_wall", "vigilance"):
            if key in target.effects:
                raise IllegalAction("%s is already active on that troop" % spec["name"])
            target.effects[key] = player
            target.health += spec.get("health_bonus", 0)
        elif key == "regenerate":
            target.health = target.effective_max_health
        elif key == "bombard":
            target.health -= 100
            if target.health <= 0:
                self._remove(target, credit=None)      # no command points for a Bombard kill
        elif key == "chastise":
            if len(self.units_of(target.owner)) <= 1:
                raise IllegalAction("cannot chastise a last remaining troop")
            target.effects["chastise"] = player
        elif key == "charge":
            if "charge" in target.effects:
                raise IllegalAction("Charge is already active on that troop")
            target.effects["charge"] = player
            if self.selected == target.uid:             # already walking: add the second helping now
                self.moves_left += target.speed
        elif key == "winds_of_fate":
            choices = sorted(k for k, t in self.cooldowns[player].items() if k != key and t > 0)
            self.cooldowns[player][random.choice(choices)] = 0

        self.command_points[player] -= spec["cost"]
        self.cooldowns[player][key] = spec["cooldown"]
        self._log("Player %d used %s" % (player + 1, spec["name"]))

    # ---- combat internals

    def _strike(self, striker, victim):
        dmg = striker.damage
        cap = victim.damage_cap
        if cap is not None:
            dmg = min(dmg, cap)
        victim.health -= dmg
        self._log("%s hits %s for %d" % (striker.name, victim.name, dmg))
        if victim.health <= 0:
            self._remove(victim, credit=striker.owner)

    def _remove(self, unit, credit):
        del self.units[unit.uid]
        self._log("%s is defeated" % unit.name)
        if credit is not None:
            self.command_points[credit] += unit.cost
        if not self.units_of(unit.owner):
            self.winner = 1 - unit.owner
            self._log("Player %d wins" % (self.winner + 1))

    def _require_live(self):
        if self.winner is not None:
            raise IllegalAction("the game is over")

    def _log(self, text):
        self.log.append(text)
        del self.log[:-200]

    # ---- serialisation (for the network and for tests)

    def to_dict(self):
        return {
            "units": [u.to_dict() for u in sorted(self.units.values(), key=lambda u: u.uid)],
            "obstacles": sorted(self.obstacles),
            "commands": [list(c) for c in self.commands],
            "cooldowns": [dict(c) for c in self.cooldowns],
            "command_points": list(self.command_points),
            "current": self.current, "turn_number": self.turn_number, "phase": self.phase,
            "selected": self.selected, "moves_left": self.moves_left, "has_attacked": self.has_attacked,
            "winner": self.winner, "next_uid": self.next_uid, "log": list(self.log),
        }

    @classmethod
    def from_dict(cls, d):
        game = cls()
        game.units = {u["uid"]: Unit.from_dict(u) for u in d["units"]}
        game.obstacles = {tuple(c) for c in d["obstacles"]}
        game.commands = [list(c) for c in d["commands"]]
        game.cooldowns = [dict(c) for c in d["cooldowns"]]
        game.command_points = list(d["command_points"])
        game.current, game.turn_number, game.phase = d["current"], d["turn_number"], d["phase"]
        game.selected, game.moves_left, game.has_attacked = d["selected"], d["moves_left"], d["has_attacked"]
        game.winner, game.next_uid, game.log = d["winner"], d["next_uid"], list(d["log"])
        return game

    def apply_action(self, player, action):
        """Run one JSON-style action dict for `player`. This is the only entry point a server needs.
        Examples: {"type": "select", "unit": 3}, {"type": "move", "row": 10, "col": 4},
        {"type": "attack", "target": 12}, {"type": "command", "command": "charge", "target": 3},
        {"type": "end_phase"}, {"type": "end_turn"}, {"type": "resign"}."""
        kind = action.get("type") if isinstance(action, dict) else None
        if kind == "resign":
            self.resign(player)
            return
        self._require_live()
        if player != self.current:
            raise IllegalAction("not your turn")
        if kind == "select":
            self.select_unit(_int(action.get("unit")))
        elif kind == "move":
            self.move_unit(_int(action.get("row")), _int(action.get("col")))
        elif kind == "attack":
            self.attack(_int(action.get("target")))
        elif kind == "command":
            target = action.get("target")
            self.use_command(_str(action.get("command")), None if target is None else _int(target))
        elif kind == "end_phase":
            self.end_phase()
        elif kind == "end_turn":
            self.end_turn()
        else:
            raise IllegalAction("unknown action %r" % (kind,))

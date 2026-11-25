# Pure data: troop and command definitions. No pygame in here, so the rules
# engine, the server and the tests can all import it.
#
# Troop stats come from game.txt / the RuneScape wiki.
# Command effects are data driven: the engine reads "damage_bonus",
# "health_bonus" (temporary hit points) and "damage_cap" off any command that is currently
# active on a unit, so adding a buff command is just a new entry here.

TROOPS = {
    "scout":       dict(name="Scout",        cost=25,  damage=100, health=100, range=1, speed=6, icon="letter_s.png"),
    "foot_soldier": dict(name="Foot Soldier", cost=50,  damage=100, health=300, range=1, speed=4, icon="letter_f.png"),
    "halberdier":  dict(name="Halberdier",   cost=75,  damage=200, health=200, range=2, speed=4, icon="letter_h.png"),
    "archer":      dict(name="Archer",       cost=100, damage=100, health=100, range=6, speed=3, icon="letter_a.png"),
    "mage":        dict(name="Mage",         cost=100, damage=200, health=100, range=4, speed=4, icon="letter_m.png"),
    "knight":      dict(name="Knight",       cost=100, damage=300, health=300, range=1, speed=4, icon="letter_k.png"),
    "champion":    dict(name="Champion",     cost=200, damage=400, health=500, range=1, speed=4, icon="letter_c.png"),
}

# target: "ally" = a troop you control, "enemy" = an opposing troop, "none" = no target
COMMANDS = {
    "battle_cry": dict(
        name="Battle Cry", cost=75, cooldown=5, target="ally", icon="letter_c.png",
        damage_bonus=200, health_bonus=200,
        text="A target troop you control gains +200 damage and 200 temporary health until the start of your next turn."),
    "bombard": dict(
        name="Bombard", cost=200, cooldown=2, target="enemy", icon="letter_c.png",
        text="A target enemy troop's health is reduced by 100. Troops defeated do not grant Command points."),
    "charge": dict(
        name="Charge", cost=75, cooldown=5, target="ally", icon="letter_c.png",
        text="A target troop you control has its movement attribute doubled for this turn."),
    "chastise": dict(
        name="Chastise", cost=50, cooldown=3, target="enemy", icon="letter_c.png",
        text="A target enemy troop cannot move or attack during your opponent's next turn. Cannot be used on an"
             " opponent's last remaining troop. Chastise does not prevent units from auto-retaliating if attacked"
             " during your own turn."),
    "regenerate": dict(
        name="Regenerate", cost=150, cooldown=4, target="ally", icon="letter_c.png",
        text="A target troop you control has its health completely restored."),
    "shield_wall": dict(
        name="Shield Wall", cost=50, cooldown=5, target="ally", icon="letter_c.png",
        damage_cap=100,
        text="All damage dealt to target troop you control is reduced to 100 until the start of your next turn."),
    "stoicism": dict(
        name="Stoicism", cost=75, cooldown=5, target="ally", icon="letter_c.png",
        health_bonus=400,
        text="A target troop you control gains 400 temporary health until the start of your next turn."),
    "vigilance": dict(
        name="Vigilance", cost=50, cooldown=3, target="ally", icon="letter_c.png",
        text="A target troop you control strikes first when defending until the start of your next turn."),
    "winds_of_fate": dict(
        name="Winds of Fate", cost=150, cooldown=2, target="none", icon="letter_c.png",
        text="A command, at random, reaches the end of its cool-down period and is ready to use."),
}

# Temporary health is a separate pool: damage drains it before real health, and whatever is left
# is stripped away at the start of the caster's next turn (see engine.Game._start_turn).

TROOP_ORDER = list(TROOPS)
COMMAND_ORDER = list(COMMANDS)

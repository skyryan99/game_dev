# Defines all entities in the game
import os
import pygame


class Scout:
    kind = "troop"

    def __init__(self):
        self.name = "Scout"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_s.png")
        self.cost = 25
        self.damage = 100
        self.max_health = 100
        self.health = self.max_health
        self.range = 1
        self.speed = 6
        self.effects = []
        self.row = 0
        self.col = 0


class FootSoldier:
    kind = "troop"

    def __init__(self):
        self.name = "Foot Soldier"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_f.png")
        self.cost = 50
        self.damage = 100
        self.max_health = 300
        self.health = self.max_health
        self.range = 1
        self.speed = 4
        self.effects = []
        self.row = 0
        self.col = 0


class Halberdier:
    kind = "troop"

    def __init__(self):
        self.name = "Halberdier"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_h.png")
        self.cost = 75
        self.damage = 200
        self.max_health = 200
        self.health = self.max_health
        self.range = 2
        self.speed = 4
        self.effects = []
        self.row = 0
        self.col = 0


class Archer:
    kind = "troop"

    def __init__(self):
        self.name = "Archer"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_a.png")
        self.cost = 100
        self.damage = 100
        self.max_health = 100
        self.health = self.max_health
        self.range = 6
        self.speed = 3
        self.effects = []
        self.row = 0
        self.col = 0


class Mage:
    kind = "troop"

    def __init__(self):
        self.name = "Mage"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_m.png")
        self.cost = 100
        self.damage = 200
        self.max_health = 100
        self.health = self.max_health
        self.range = 4
        self.speed = 4
        self.effects = []
        self.row = 0
        self.col = 0


class Knight:
    kind = "troop"

    def __init__(self):
        self.name = "Knight"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_k.png")
        self.cost = 100
        self.damage = 300
        self.max_health = 300
        self.health = self.max_health
        self.range = 1
        self.speed = 4
        self.effects = []
        self.row = 0
        self.col = 0


class Champion:
    kind = "troop"

    def __init__(self):
        self.name = "Champion"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.cost = 200
        self.damage = 400
        self.max_health = 500
        self.health = self.max_health
        self.range = 1
        self.speed = 4
        self.effects = []
        self.row = 0
        self.col = 0


class BattleCry:
    kind = "command"

    def __init__(self):
        self.name = "Battle Cry"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Self"
        self.cost = 75
        self. cooldown = 5
        self.effects = {"dmg_buf":      200,
                        "hp_buf":       200,
                        "move_buf":     1,
                        "armor":        0,
                        "first_strike": False
                        }
        self.text = "A target troop you control gains +200 damage and +200 health until the start of your next turn."


class Bombard:
    kind = "command"

    def __init__(self):
        self.name = "Bombard"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Opponent"
        self.cost = 200
        self.cooldown = 2
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       -100,           # DOES NOT GRANT COMMAND POINTS IN RETURN
                        "move_buf":     1,
                        "armor":        0,
                        "first_strike": False
                        }
        self.text = "A target enemy troop's health is reduced by 100. Troops defeated do not grant Command points."


class Charge:
    kind = "command"

    def __init__(self):
        self.name = "Charge"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Self"
        self.cost = 75
        self.cooldown = 5
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     2,
                        "armor":        0,
                        "first_strike": False
                        }
        self.text = "A target troop you control has its movement attribute doubled for this turn."


class Chastise:
    kind = "command"

    def __init__(self):
        self.name = "Chastise"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Opponent"
        self.cost = 50
        self.cooldown = 3
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     0,              # CANNOT USE ON LAST TROOP
                        "armor":        0,
                        "first_strike": False
                        }
        self.text = "A target enemy troop cannot move or attack during your opponent's next turn. Cannot be used on an"\
                " opponent's last remaining troop. Chastise does not prevent units from auto-retaliating if attacked"\
                " during your own turn."


class Regenerate:                                       # DOES NOT HAVE EFFECTS, LOGIC IMPLEMENTED MANUALLY
    kind = "command"                                    # FULL HEALS A UNIT

    def __init__(self):
        self.name = "Regenerate"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Self"
        self.cost = 150
        self.cooldown = 4
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     1,
                        "armor":        0,
                        "first_strike": False
                        }
        self.text = "A target troop you control has its health completely restored."


class ShieldWall:
    kind = "command"

    def __init__(self):
        self.name = "Shield Wall"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Self"
        self.cost = 50
        self.cooldown = 5
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     1,
                        "armor":        100,
                        "first_strike": False
                        }
        self.text = "All damage dealt to target troop you control is reduced to 100 until the start of your next turn."


class Stoicism:
    kind = "command"

    def __init__(self):
        self.name = "Stoicism"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Self"
        self.cost = 75
        self.cooldown = 5
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       400,
                        "move_mul":     1,
                        "armor":        0,
                        "first_strike": False
                        }
        self.text = "A target troop you control gains +400 health until the start of your next turn."

class Vigilance:
    kind = "command"

    def __init__(self):
        self.name = "Vigilance"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Self"
        self.cost = 50
        self.cooldown = 3
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     1,
                        "armor":        0,
                        "first_strike": True                # ONLY TRIGGERS ON DEFENCE
                        }
        self.text = "A target troop you control strikes first when defending until the start of your next turn."


class WindsOfFate:                                          # DOES NOT HAVE EFFECTS, LOGIC IMPLEMENTED MANUALLY
    kind = "command"                                        # RESET COOLDOWN OF ANOTHER COMMAND

    def __init__(self):
        self.name = "Winds of Fate"
        self.image = pygame.image.load(os.getcwd() + "/images/letter_c.png")
        self.target = "Self"
        self.cost = 150
        self.cooldown = 2
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     1,
                        "armor":        0,
                        "first_strike": False
                        }
        self.text = "A command, at random, reaches the end of its cool-down period and is ready to use."

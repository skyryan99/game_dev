# Defines all entities in the game

class Scout:
    kind = "troop"

    def __init__(self):
        self.name = "Scout"
        self.cost = 25
        self.damage = 100
        self.max_health = 100
        self.health = self.max_health
        self.range = 1
        self.speed = 6
        self.effects = []


class FootSoldier:
    kind = "troop"

    def __init__(self):
        self.name = "Foot Soldier"
        self.cost = 50
        self.damage = 100
        self.max_health = 300
        self.health = self.max_health
        self.range = 1
        self.speed = 4
        self.effects = []


class Halberdier:
    kind = "troop"

    def __init__(self):
        self.name = "Halberdier"
        self.cost = 75
        self.damage = 200
        self.max_health = 200
        self.health = self.max_health
        self.range = 2
        self.speed = 4
        self.effects = []


class Archer:
    kind = "troop"

    def __init__(self):
        self.name = "Archer"
        self.cost = 100
        self.damage = 100
        self.max_health = 100
        self.health = self.max_health
        self.range = 6
        self.speed = 3
        self.effects = []


class Mage:
    kind = "troop"

    def __init__(self):
        self.name = "Mage"
        self.cost = 100
        self.damage = 200
        self.max_health = 100
        self.health = self.max_health
        self.range = 4
        self.speed = 4
        self.effects = []


class Knight:
    kind = "troop"

    def __init__(self):
        self.name = "Knight"
        self.cost = 100
        self.damage = 300
        self.max_health = 300
        self.health = self.max_health
        self.range = 1
        self.speed = 4
        self.effects = []


class Champion:
    kind = "troop"

    def __init__(self):
        self.name = "Champion"
        self.cost = 200
        self.damage = 400
        self.max_health = 500
        self.health = self.max_health
        self.range = 1
        self.speed = 4
        self.effects = []


class BattleCry:
    kind = "command"

    def __init__(self):
        self.name = "Battle Cry"
        self.target = "Self"
        self.cost = 75
        self. cooldown = 5
        self.effects = {"dmg_buf":      200,
                        "hp_buf":       200,
                        "move_buf":     1,
                        "armor":        0,
                        "first_strike": False
                        }


class Bombard:
    kind = "command"

    def __init__(self):
        self.name = "Bombard"
        self.target = "Opponent"
        self.cost = 200
        self.cooldown = 2
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       -100,           # DOES NOT GRANT COMMAND POINTS IN RETURN
                        "move_buf":     1,
                        "armor":        0,
                        "first_strike": False
                        }


class Charge:
    kind = "command"

    def __init__(self):
        self.name = "Charge"
        self.target = "Self"
        self.cost = 75
        self.cooldown = 5
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     2,
                        "armor":        0,
                        "first_strike": False
                        }


class Chastise:
    kind = "command"

    def __init__(self):
        self.name = "Chastise"
        self.target = "Opponent"
        self.cost = 50
        self.cooldown = 3
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     0,              # CANNOT USE ON LAST TROOP
                        "armor":        0,
                        "first_strike": False
                        }


class Regenerate:                                       # DOES NOT HAVE EFFECTS, LOGIC IMPLEMENTED MANUALLY
    kind = "command"                                    # FULL HEALS A UNIT

    def __init__(self):
        self.name = "Regenerate"
        self.target = "Self"
        self.cost = 150
        self.cooldown = 4
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     1,
                        "armor":        0,
                        "first_strike": False
                        }


class ShieldWall:
    kind = "command"

    def __init__(self):
        self.name = "Shield Wall"
        self.target = "Self"
        self.cost = 50
        self.cooldown = 5
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     1,
                        "armor":        100,
                        "first_strike": False
                        }


class Stoicism:
    kind = "command"

    def __init__(self):
        self.name = "Stoicism"
        self.target = "Self"
        self.cost = 75
        self.cooldown = 5
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       400,
                        "move_mul":     1,
                        "armor":        0,
                        "first_strike": False
                        }


class Vigilance:
    kind = "command"

    def __init__(self):
        self.name = "Vigilance"
        self.target = "Self"
        self.cost = 50
        self.cooldown = 3
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     1,
                        "armor":        0,
                        "first_strike": True                # ONLY TRIGGERS ON DEFENCE
                        }


class WindsOfFate:                                          # DOES NOT HAVE EFFECTS, LOGIC IMPLEMENTED MANUALLY
    kind = "command"                                        # RESET COOLDOWN OF ANOTHER COMMAND

    def __init__(self):
        self.name = "Winds of Fate"
        self.target = "Self"
        self.cost = 150
        self.cooldown = 2
        self.effects = {"dmg_buf":      0,
                        "hp_buf":       0,
                        "move_mul":     1,
                        "armor":        0,
                        "first_strike": False
                        }

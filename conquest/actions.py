# Turns mouse clicks into game actions. Every change to the game goes through
# Controller.perform(), which hands an action dict to Game.apply_action -- the exact same
# entry point the server uses, so wiring up online play later means swapping that one line
# for "send the action over the network".
import data
import engine
from engine import IllegalAction


class Controller:
    def __init__(self, game):
        self.game = game
        self.armed = None           # command key waiting for the player to click a target
        self.message = ""           # last problem to show the player

    def perform(self, action):
        try:
            self.game.apply_action(self.game.current, action)
            self.message = ""
            return True
        except IllegalAction as exc:
            self.message = str(exc)
            return False

    # ---- board clicks

    def click_tile(self, tile):
        game = self.game
        if game.winner is not None or tile is None:
            return
        unit = game.unit_at(*tile)
        if self.armed:
            key, self.armed = self.armed, None
            if unit is None:
                self.message = "That tile has no troop on it"
            else:
                self.perform({"type": "command", "command": key, "target": unit.uid})
            return
        if game.phase == engine.SELECTION:
            if unit is not None:
                self.perform({"type": "select", "unit": unit.uid})
        elif game.phase in (engine.MOVEMENT, engine.COMBAT):
            if unit is not None and unit.owner != game.current:
                self.perform({"type": "attack", "target": unit.uid})
            elif unit is None and game.phase == engine.MOVEMENT:
                self.perform({"type": "move", "row": tile[0], "col": tile[1]})

    def cancel(self):
        self.armed = None
        self.message = ""

    # ---- side panel clicks

    def click_button(self, button):
        if button is None:
            return
        if button.kind == "command":
            key = button.key
            reason = self.game.command_status(self.game.current, key)
            if reason:
                self.message = reason
            elif data.COMMANDS[key]["target"] == "none":
                self.armed = None
                self.perform({"type": "command", "command": key})
            else:
                self.armed = None if self.armed == key else key
                self.message = ""
            return
        if not button.enabled:                       # a phase button for a phase that is not the current one
            return
        self.armed = None
        self.perform({"type": {"phase": "end_phase", "end_turn": "end_turn", "resign": "resign"}[button.kind]})

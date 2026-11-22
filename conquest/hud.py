# The two panels on the right of the game screen: turn controls and unit details.
import pygame

import data
import engine

PANEL_BG = (3, 13, 46)
DETAILS_BG = (108, 79, 35)          # average of the two board colours
WHITE = (255, 255, 255)
HIGHLIGHT = (156, 118, 58)
DISABLED = (110, 110, 110)
ERROR = (255, 120, 120)


class HudButton:
    def __init__(self, rect, kind, key, label, enabled):
        self.rect, self.kind, self.key, self.label, self.enabled = rect, kind, key, label, enabled


def panel_x(screen):
    return int(screen.get_width() * 0.8)


def build_buttons(screen, game):
    """Every clickable thing in the top-right panel, for the player whose turn it is."""
    x0 = panel_x(screen)
    left, width, height, gap = x0 + 20, screen.get_width() - x0 - 40, 40, 8
    y = 165
    buttons = []
    live = game.winner is None
    for kind, label in (("end_phase", "End Phase"), ("end_turn", "End Turn"), ("resign", "Resign")):
        buttons.append(HudButton(pygame.Rect(left, y, width, height), kind, None, label, live))
        y += height + gap
    y += 10
    for key in game.commands[game.current]:
        spec = data.COMMANDS[key]
        reason = game.command_status(game.current, key)
        label = "%s  (%d)" % (spec["name"], spec["cost"])
        if game.cooldowns[game.current][key] > 0:
            label = "%s  CD %d" % (spec["name"], game.cooldowns[game.current][key])
        buttons.append(HudButton(pygame.Rect(left, y, width, height), "command", key, label, reason is None))
        y += height + gap
    return buttons


def button_at(screen, game, pos):
    for button in build_buttons(screen, game):
        if button.rect.collidepoint(pos):
            return button
    return None


def draw(screen, fonts, game, mouse_pos, hover_unit, armed, message):
    x0 = panel_x(screen)
    width, height = screen.get_width() - x0, screen.get_height()
    half = height // 2
    pygame.draw.rect(screen, PANEL_BG, (x0, 0, width, half))
    pygame.draw.rect(screen, DETAILS_BG, (x0, half, width, height - half))
    pygame.draw.line(screen, WHITE, (x0 - 2, 0), (x0 - 2, height), width=2)

    # ---- turn info
    cur = game.current
    lines = [("Player %d's turn" % (cur + 1), fonts[2]),
             ("Phase: %s" % game.phase.capitalize(), fonts[1]),
             ("Command points: %d" % game.command_points[cur], fonts[1])]
    if game.phase == engine.MOVEMENT:
        lines.append(("Moves left: %d" % game.moves_left, fonts[1]))
    y = 12
    for text, font in lines:
        screen.blit(font.render(text, True, WHITE), (x0 + 20, y))
        y += font.get_height() + 2

    # ---- buttons
    for button in build_buttons(screen, game):
        hovered = button.rect.collidepoint(mouse_pos)
        color = DISABLED if not button.enabled else (HIGHLIGHT if hovered or armed == button.key else WHITE)
        pygame.draw.rect(screen, color, button.rect, width=2)
        label = fonts[1].render(button.label, True, color)
        screen.blit(label, (button.rect.x + 12, button.rect.y + (button.rect.height - label.get_height()) // 2))
    # one status line between the turn info and the buttons (an error beats the targeting hint)
    if message:
        screen.blit(fonts[0].render(message, True, ERROR), (x0 + 20, 143))
    elif armed:
        msg = "Pick a target for %s (right-click cancels)" % data.COMMANDS[armed]["name"]
        screen.blit(fonts[0].render(msg, True, HIGHLIGHT), (x0 + 20, 143))

    # ---- details: hovered command, else hovered troop, else the acting troop
    hover_button = next((b for b in build_buttons(screen, game) if b.rect.collidepoint(mouse_pos)
                         and b.kind == "command"), None)
    draw_details(screen, fonts, game, x0, half, height, hover_button, hover_unit)


def wrap_text(font, text, max_width):
    """Split text into lines no wider than max_width pixels."""
    lines, line = [], []
    for word in text.split():
        if line and font.size(" ".join(line + [word]))[0] > max_width:
            lines.append(" ".join(line))
            line = []
        line.append(word)
    if line:
        lines.append(" ".join(line))
    return lines


TARGET_TEXT = {"ally": "one of your troops", "enemy": "an enemy troop", "none": "no target needed"}


def draw_details(screen, fonts, game, x0, top, bottom, hover_button, hover_unit):
    text_w = screen.get_width() - x0 - 40
    left = x0 + 20
    y = top + 12

    def put(text, font, color=WHITE):
        nonlocal y
        screen.blit(font.render(text, True, color), (left, y))
        y += font.get_height() + 2

    def put_wrapped(text, font, color=WHITE):
        for line in wrap_text(font, text, text_w):
            put(line, font, color)

    if hover_button is not None:                       # a command in the side panel
        spec = data.COMMANDS[hover_button.key]
        put(spec["name"], fonts[2])
        put("Cost: %d command points" % spec["cost"], fonts[1])
        put("Cooldown: %d turns" % spec["cooldown"], fonts[1])
        put("Target: %s" % TARGET_TEXT[spec["target"]], fonts[1])
        reason = game.command_status(game.current, hover_button.key)
        put("Ready to use" if reason is None else "Unavailable: %s" % reason, fonts[1],
            HIGHLIGHT if reason is None else ERROR)
        y += 6
        put_wrapped(spec["text"], fonts[1])
    else:
        unit = hover_unit or game.selected_unit
        if unit is not None:                           # a troop on the board
            put(unit.name, fonts[2])
            put("Player %d    Cost: %d" % (unit.owner + 1, unit.cost), fonts[1])
            hp_bonus = unit.effective_max_health - unit.max_health
            put("Health: %d / %d%s" % (unit.health, unit.effective_max_health,
                                       "  (+%d)" % hp_bonus if hp_bonus else ""), fonts[1])
            dmg_bonus = unit.damage - unit.stats["damage"]
            put("Damage: %d%s" % (unit.damage, "  (+%d)" % dmg_bonus if dmg_bonus else ""), fonts[1])
            put("Range: %d    Movement: %d" % (unit.range, unit.speed), fonts[1])
            if unit.damage_cap is not None:
                put("Takes at most %d damage per hit" % unit.damage_cap, fonts[1])
            if unit.first_strike:
                put("Strikes first when defending", fonts[1])
            if unit.chastised:
                put("Cannot move or attack", fonts[1], ERROR)
            for effect in unit.effects:
                y += 4
                put("Active: %s" % data.COMMANDS[effect]["name"], fonts[1], HIGHLIGHT)
                put_wrapped(data.COMMANDS[effect]["text"], fonts[0])
        y += 10
    # recent events fill whatever room is left at the bottom
    line_h = fonts[0].get_height() + 3
    room = (bottom - 8 - y) // line_h
    if room > 0:
        for line in game.log[-room:]:
            screen.blit(fonts[0].render(line, True, WHITE), (left, y))
            y += line_h

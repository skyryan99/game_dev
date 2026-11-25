# The two panels on the right of the game screen: turn controls and unit details.
import math

import pygame

import data
import engine

PANEL_BG = (3, 13, 46)
HOVER_FILL = (14, 30, 72)            # button background while the mouse is over it
DETAILS_BG = (108, 79, 35)           # average of the two board colours
WHITE = (255, 255, 255)
HOVER = (190, 146, 72)               # border + text colour on hover (the troop menu's brown, brightened for navy)
HIGHLIGHT = HOVER                    # (used by the details panel)
DISABLED = (110, 110, 110)
ERROR = (255, 120, 120)
TEMP_HEALTH = (90, 190, 255)
GOLD = (255, 200, 60)

TOP_H = 560                          # height of the turn-controls panel; the details panel fills the rest
BUTTON_H = 38
GAP = 6
SPIN_SECONDS = 1.6                   # one lap of the glow around the active phase button
TAIL = 0.38                          # how much of the lap the glow's tail covers

PHASE_BUTTONS = [(engine.SELECTION, "End Selection"), (engine.MOVEMENT, "End Movement"),
                 (engine.COMBAT, "End Combat"), (engine.RALLY, "End Rally")]


class HudButton:
    def __init__(self, rect, kind, key, label, enabled, glowing=False):
        self.rect, self.kind, self.key, self.label = rect, kind, key, label
        self.enabled, self.glowing = enabled, glowing


def panel_x(screen):
    return int(screen.get_width() * 0.8)


def build_buttons(screen, game):
    """Every clickable thing in the top-right panel, for the player whose turn it is.
    One button per phase (only the current phase's is live and glowing), then the squad's
    commands, then End Turn and Resign side by side."""
    x0 = panel_x(screen)
    left, width = x0 + 20, screen.get_width() - x0 - 40
    live = game.winner is None
    y = 138
    buttons = []
    for phase, label in PHASE_BUTTONS:
        current = live and game.phase == phase
        buttons.append(HudButton(pygame.Rect(left, y, width, BUTTON_H), "phase", phase, label, current, current))
        y += BUTTON_H + GAP
    y += 8
    for key in game.commands[game.current]:
        spec = data.COMMANDS[key]
        reason = game.command_status(game.current, key)
        label = "%s  (%d)" % (spec["name"], spec["cost"])
        if game.cooldowns[game.current][key] > 0:
            label = "%s  CD %d" % (spec["name"], game.cooldowns[game.current][key])
        buttons.append(HudButton(pygame.Rect(left, y, width, BUTTON_H), "command", key, label, reason is None))
        y += BUTTON_H + GAP
    y += 8
    half = (width - GAP) // 2
    buttons.append(HudButton(pygame.Rect(left, y, half, BUTTON_H), "end_turn", None, "End Turn", live))
    buttons.append(HudButton(pygame.Rect(left + half + GAP, y, half, BUTTON_H), "resign", None, "Resign", live))
    return buttons


def button_at(screen, game, pos):
    for button in build_buttons(screen, game):
        if button.rect.collidepoint(pos):
            return button
    return None


# ------------------------------------------------------------ glow ring -----

def perimeter_segments(rect, step=6):
    """Walk once clockwise around the rectangle's border. Returns [(start, end, t)] where t in [0, 1)
    is how far round the lap the segment's midpoint is."""
    x0, y0, x1, y1 = rect.left, rect.top, rect.right - 1, rect.bottom - 1
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    total = 2 * ((x1 - x0) + (y1 - y0))
    segments, travelled = [], 0.0
    for (ax, ay), (bx, by) in zip(corners, corners[1:]):
        length = math.hypot(bx - ax, by - ay)
        count = max(1, int(length // step))
        for k in range(count):
            f0, f1 = k / count, (k + 1) / count
            start = (ax + (bx - ax) * f0, ay + (by - ay) * f0)
            end = (ax + (bx - ax) * f1, ay + (by - ay) * f1)
            mid = travelled + length * (f0 + f1) / 2
            segments.append((start, end, mid / total))
        travelled += length
    return segments


def draw_glow(screen, rect, now):
    """A golden border with a bright comet that circles the button like a loading wheel."""
    head = (now / SPIN_SECONDS) % 1.0
    for start, end, t in perimeter_segments(rect):
        behind = (head - t) % 1.0                           # 0 at the comet's head, growing along its tail
        level = max(0.0, 1.0 - behind / TAIL)
        strength = 0.3 + 0.7 * level                        # a faint gold border even where the tail has faded
        pygame.draw.line(screen, tuple(int(c * strength * 0.35) for c in GOLD), start, end, 7)   # soft halo
        pygame.draw.line(screen, tuple(int(c * strength) for c in GOLD), start, end, 3)


# ------------------------------------------------------------- drawing ------

def draw_button(screen, fonts, button, hovered, armed, now):
    """Hover: border and text warm up and the button fills in slightly, like the troop menu cards.
    The glowing phase button keeps its gold ring exactly as is; only its text and fill respond."""
    hot = button.enabled and (hovered or armed)
    text_color = DISABLED if not button.enabled else (HOVER if hot else WHITE)
    if hot:
        pygame.draw.rect(screen, HOVER_FILL, button.rect)
    if button.glowing:
        draw_glow(screen, button.rect, now)
    else:
        pygame.draw.rect(screen, text_color, button.rect, width=2)
    label = fonts[1].render(button.label, True, text_color)
    screen.blit(label, (button.rect.x + 12, button.rect.y + (button.rect.height - label.get_height()) // 2))


def draw(screen, fonts, game, mouse_pos, hover_unit, armed, message, now=0.0):
    x0 = panel_x(screen)
    width, height = screen.get_width() - x0, screen.get_height()
    pygame.draw.rect(screen, PANEL_BG, (x0, 0, width, TOP_H))
    pygame.draw.rect(screen, DETAILS_BG, (x0, TOP_H, width, height - TOP_H))
    pygame.draw.line(screen, WHITE, (x0 - 2, 0), (x0 - 2, height), width=2)

    # ---- turn info (the phase itself is shown by which button is glowing)
    cur = game.current
    lines = [("Player %d's turn" % (cur + 1), fonts[2]),
             ("Command points: %d" % game.command_points[cur], fonts[1])]
    if game.phase == engine.MOVEMENT:
        lines.append(("Moves left: %d" % game.moves_left, fonts[1]))
    y = 12
    for text, font in lines:
        screen.blit(font.render(text, True, WHITE), (x0 + 20, y))
        y += font.get_height() + 2

    # one status line above the buttons (an error beats the targeting hint)
    if message:
        screen.blit(fonts[0].render(message, True, ERROR), (x0 + 20, 117))
    elif armed:
        msg = "Pick a target for %s (right-click cancels)" % data.COMMANDS[armed]["name"]
        screen.blit(fonts[0].render(msg, True, HOVER), (x0 + 20, 117))

    buttons = build_buttons(screen, game)
    for button in buttons:
        draw_button(screen, fonts, button, button.rect.collidepoint(mouse_pos),
                    armed is not None and button.kind == "command" and button.key == armed, now)

    # ---- details: hovered command, else hovered troop, else the acting troop
    hover_button = next((b for b in buttons if b.kind == "command" and b.rect.collidepoint(mouse_pos)), None)
    draw_details(screen, fonts, game, x0, TOP_H, height, hover_button, hover_unit)


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
            put("Health: %d / %d" % (unit.health, unit.max_health), fonts[1])
            if unit.temp_health:
                put("Temporary health: +%d" % unit.temp_health, fonts[1], TEMP_HEALTH)
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

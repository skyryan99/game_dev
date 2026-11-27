# The two panels on the right of the game screen: turn controls (phases, commands) and the details + log.
import math

import pygame

import data
import engine
from menus import COMMAND_POINTS, GOLD

PANEL_BG = (3, 13, 46)
HOVER_FILL = (14, 30, 72)            # button background while the mouse is over it
DETAILS_BG = (108, 79, 35)           # average of the two board colours
LOG_BG = (86, 62, 26)
WHITE = (255, 255, 255)
HOVER = (190, 146, 72)               # border + text colour on hover (the troop menu's brown, brightened for navy)
HIGHLIGHT = HOVER                    # (used by the details panel)
LABEL = (150, 135, 105)              # the "Phases" / "Commands" captions
LOG_TITLE = (215, 195, 150)
LOG_TURN = (235, 190, 90)            # the "Turn N: player P" lines in the log
DISABLED = (110, 110, 110)
ERROR = (255, 120, 120)
TEMP_HEALTH = (90, 190, 255)
GLOW = (255, 200, 60)                # the rotating border on the live phase button

TOP_H = 556                          # height of the turn-controls panel; the details panel fills the rest
BUTTON_H = 34
GAP = 4
LOG_H = 200                          # the turn log is a fixed-size box at the bottom of the details panel
LOG_MARGIN = 12
DETAILS_GAP = 26                     # breathing room between the details slab and the log box
LOG_LINE = 16
SPIN_SECONDS = 3.2                   # one lap of the glow around the active phase button
TAIL = 0.38                          # how much of the lap the glow's tail covers

PHASE_BUTTONS = [(engine.SELECTION, "End Selection"), (engine.MOVEMENT, "End Movement"),
                 (engine.COMBAT, "End Combat"), (engine.RALLY, "End Rally")]


class HudButton:
    def __init__(self, rect, kind, key, label, enabled, glowing=False):
        self.rect, self.kind, self.key, self.label = rect, kind, key, label
        self.enabled, self.glowing = enabled, glowing


def panel_x(screen):
    return int(screen.get_width() * 0.8)


def log_top(screen):
    return screen.get_height() - LOG_MARGIN - LOG_H


def layout(screen):
    """Vertical positions of the two captions and the button rows, shared by build_buttons and draw."""
    return {"phases_label": 132, "phases": 162, "turn_row": 162 + 4 * (BUTTON_H + GAP),
            "commands_label": 162 + 4 * (BUTTON_H + GAP) + BUTTON_H + GAP + 10,
            "commands": 162 + 4 * (BUTTON_H + GAP) + BUTTON_H + GAP + 10 + 30}


def build_buttons(screen, game):
    """Every clickable thing in the top-right panel, for the player whose turn it is.
    Phases section: one button per phase (only the current phase's is live and glowing) with End Turn and
    Resign under them. Commands section: the squad's commands."""
    x0 = panel_x(screen)
    left, width = x0 + 20, screen.get_width() - x0 - 40
    live = game.winner is None
    rows = layout(screen)
    buttons = []
    y = rows["phases"]
    for phase, label in PHASE_BUTTONS:
        current = live and game.phase == phase
        buttons.append(HudButton(pygame.Rect(left, y, width, BUTTON_H), "phase", phase, label, current, current))
        y += BUTTON_H + GAP
    half = (width - GAP) // 2
    buttons.append(HudButton(pygame.Rect(left, y, half, BUTTON_H), "end_turn", None, "End Turn", live))
    buttons.append(HudButton(pygame.Rect(left + half + GAP, y, half, BUTTON_H), "resign", None, "Resign", live))
    y = rows["commands"]
    for key in game.commands[game.current]:
        spec = data.COMMANDS[key]
        reason = game.command_status(game.current, key)
        label = "%s  (%d)" % (spec["name"], spec["cost"])
        if game.cooldowns[game.current][key] > 0:
            label = "%s  CD %d" % (spec["name"], game.cooldowns[game.current][key])
        buttons.append(HudButton(pygame.Rect(left, y, width, BUTTON_H), "command", key, label, reason is None))
        y += BUTTON_H + GAP
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
        pygame.draw.line(screen, tuple(int(c * strength * 0.35) for c in GLOW), start, end, 7)   # soft halo
        pygame.draw.line(screen, tuple(int(c * strength) for c in GLOW), start, end, 3)


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


def draw_caption(screen, fonts, text, x, y, width):
    """A section caption with a thin rule running to the right edge."""
    label = fonts[1].render(text, True, LABEL)
    screen.blit(label, (x, y))
    mid = y + label.get_height() // 2
    pygame.draw.line(screen, LABEL, (x + label.get_width() + 10, mid), (x + width, mid), 1)


def format_time(seconds):
    """0:45 style countdown (rounded up, so it reads 0:01 until the very last moment)."""
    whole = int(math.ceil(seconds))
    return "%d:%02d" % (whole // 60, whole % 60)


def draw(screen, fonts, game, mouse_pos, hover_unit, armed, message, now=0.0, log_view=None):
    x0 = panel_x(screen)
    left, width = x0 + 20, screen.get_width() - x0 - 40
    height = screen.get_height()
    pygame.draw.rect(screen, PANEL_BG, (x0, 0, screen.get_width() - x0, TOP_H))
    pygame.draw.rect(screen, DETAILS_BG, (x0, TOP_H, screen.get_width() - x0, height - TOP_H))
    pygame.draw.line(screen, WHITE, (x0 + 1, 0), (x0 + 1, height), width=2)       # inside the sidebar, so it travels with it

    # ---- turn info; the phase itself is shown by which button is glowing
    cur = game.current
    title = fonts[2].render("Player %d's turn" % (cur + 1), True, WHITE)
    screen.blit(title, (left, 12))
    remaining = game.time_left()
    if remaining is not None:                                  # unlimited turns show no clock at all
        clock = fonts[2].render(format_time(remaining), True, ERROR if remaining <= 10 else WHITE)
        screen.blit(clock, (left + width - clock.get_width(), 12))
    screen.blit(fonts[1].render("Command points: %d" % game.command_points[cur], True, COMMAND_POINTS), (left, 55))
    turn = fonts[1].render("Turn %d" % game.turn_number, True, LABEL)
    screen.blit(turn, (left + width - turn.get_width(), 55))
    if game.phase == engine.MOVEMENT:
        screen.blit(fonts[1].render("Moves left: %d" % game.moves_left, True, WHITE), (left, 83))

    # one status line above the buttons (an error beats the targeting hint)
    if message:
        screen.blit(fonts[0].render(message, True, ERROR), (left, 111))
    elif armed:
        msg = "Pick a target for %s (right-click cancels)" % data.COMMANDS[armed]["name"]
        screen.blit(fonts[0].render(msg, True, HOVER), (left, 111))

    rows = layout(screen)
    draw_caption(screen, fonts, "Phases", left, rows["phases_label"], width)
    draw_caption(screen, fonts, "Commands", left, rows["commands_label"], width)
    buttons = build_buttons(screen, game)
    for button in buttons:
        draw_button(screen, fonts, button, button.rect.collidepoint(mouse_pos),
                    armed is not None and button.kind == "command" and button.key == armed, now)
    if not game.commands[cur]:
        screen.blit(fonts[0].render("No commands in this squad", True, DISABLED), (left, rows["commands"] + 4))

    # ---- details slab (hovered command, else hovered troop, else the acting troop), then the fixed turn log
    hover_button = next((b for b in buttons if b.kind == "command" and b.rect.collidepoint(mouse_pos)), None)
    top_of_log = log_top(screen)
    draw_details(screen, fonts, game, x0, TOP_H, top_of_log - DETAILS_GAP, hover_button, hover_unit)
    draw_log(screen, fonts, game, x0, top_of_log, screen.get_width() - x0, log_view)


def fit_text(font, text, max_width):
    """Shorten text with "..." so it never runs past max_width."""
    if font.size(text)[0] <= max_width:
        return text
    while text and font.size(text + "...")[0] > max_width:
        text = text[:-1]
    return text + "..."


LOG_CAPACITY = (LOG_H - 36) // LOG_LINE          # lines visible at once
BAR_W = 8


def log_box(screen):
    x0 = panel_x(screen)
    return pygame.Rect(x0 + 12, log_top(screen), screen.get_width() - x0 - 24, LOG_H)


class LogView:
    """Scroll state of the turn log. `offset` is how many lines up from the newest the view is; 0 follows the
    newest lines. While scrolled up, new lines arriving do not push what you are reading out of view."""

    def __init__(self):
        self.offset = 0
        self.last_total = 0
        self.dragging = False
        self._grab = 0

    def max_offset(self, total):
        return max(0, total - LOG_CAPACITY)

    def sync(self, total):
        if self.offset > 0 and total > self.last_total:
            self.offset += total - self.last_total
        self.last_total = total
        self.offset = max(0, min(self.offset, self.max_offset(total)))

    def scroll(self, lines, total):
        """Positive scrolls toward older lines."""
        self.offset = max(0, min(self.offset + lines, self.max_offset(total)))

    # the scroll bar: a thin track along the right inside edge of the box, with a draggable thumb
    def track(self, box):
        return pygame.Rect(box.right - BAR_W - 6, box.y + 32, BAR_W, LOG_H - 40)

    def thumb(self, box, total):
        track = self.track(box)
        if total <= LOG_CAPACITY:
            return None
        height = max(18, int(track.height * LOG_CAPACITY / total))
        travel = track.height - height
        top = track.y + int(travel * (1 - self.offset / self.max_offset(total)))
        return pygame.Rect(track.x, top, track.width, height)

    def press(self, pos, box, total):
        """Handle a left click. Returns True if it landed on the scroll bar."""
        thumb = self.thumb(box, total)
        if thumb is None:
            return False
        track = self.track(box)
        if thumb.inflate(8, 0).collidepoint(pos):
            self.dragging, self._grab = True, pos[1] - thumb.y
            return True
        if track.inflate(8, 0).collidepoint(pos):                     # click the track: jump a page that way
            self.scroll(LOG_CAPACITY if pos[1] < thumb.y else -LOG_CAPACITY, total)
            return True
        return False

    def drag(self, pos, box, total):
        thumb = self.thumb(box, total)
        if not self.dragging or thumb is None:
            return
        track = self.track(box)
        travel = track.height - thumb.height
        top = max(0, min(travel, pos[1] - self._grab - track.y))
        self.offset = round((1 - top / travel) * self.max_offset(total)) if travel else 0

    def release(self):
        self.dragging = False


def draw_log(screen, fonts, game, x0, top, panel_width, view=None):
    """A fixed-size box of the whole history; the scroll bar appears once it no longer fits."""
    box = pygame.Rect(x0 + 12, top, panel_width - 24, LOG_H)
    view = view or LogView()
    total = len(game.log)
    view.sync(total)
    pygame.draw.rect(screen, LOG_BG, box)
    pygame.draw.rect(screen, HOVER, box, width=1)
    screen.blit(fonts[1].render("Turn log", True, LOG_TITLE), (box.x + 10, box.y + 4))
    last = total - view.offset
    first = max(0, last - LOG_CAPACITY)
    y = box.y + 32
    text_w = box.width - 20 - (BAR_W + 8 if total > LOG_CAPACITY else 0)
    for line in game.log[first:last]:
        color = LOG_TURN if line.startswith("Turn ") else WHITE
        screen.blit(fonts[0].render(fit_text(fonts[0], line, text_w), True, color), (box.x + 10, y))
        y += LOG_LINE
    thumb = view.thumb(box, total)
    if thumb is not None:
        pygame.draw.rect(screen, (60, 44, 18), view.track(box))
        pygame.draw.rect(screen, WHITE if view.dragging else HOVER, thumb)
        if view.offset:                                               # a hint that newer lines are below
            screen.blit(fonts[0].render("scrolled up", True, LOG_TITLE), (box.right - 90 - BAR_W - 14, box.y + 8))


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
    """The info slab. `bottom` is the lowest y it may use; anything that would run past it is left out."""
    text_w = screen.get_width() - x0 - 40
    left = x0 + 20
    y = top + 14

    def put(text, font, color=WHITE):
        nonlocal y
        if y + font.get_height() <= bottom:
            screen.blit(font.render(text, True, color), (left, y))
        y += font.get_height() + 2

    def put_wrapped(text, font, color=WHITE):
        for line in wrap_text(font, text, text_w):
            put(line, font, color)

    if hover_button is not None:                       # a command in the side panel
        spec = data.COMMANDS[hover_button.key]
        put(spec["name"], fonts[2])
        put("Command point cost: %d" % spec["cost"], fonts[1], COMMAND_POINTS)
        put("Cooldown: %d turns" % spec["cooldown"], fonts[1])
        put("Target: %s" % TARGET_TEXT[spec["target"]], fonts[1])
        reason = game.command_status(game.current, hover_button.key)
        put_wrapped("Ready to use" if reason is None else "Unavailable: %s" % reason, fonts[1],
                    HIGHLIGHT if reason is None else ERROR)
        y += 6
        put_wrapped(spec["text"], fonts[1])
        return
    unit = hover_unit or game.selected_unit
    if unit is None:
        return
    put(unit.name, fonts[2])
    put("Player %d    Gold cost: %d" % (unit.owner + 1, unit.cost), fonts[1], GOLD)
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

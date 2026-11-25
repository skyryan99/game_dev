# Start screen and the pre-game troop / command pickers.
#
# Nothing in here blocks. main.py passes each left-click to `handle_click`, and `draw` is called
# once per frame. What the player has bought lives in an engine.Loadout, so the budget and the
# "max 10 troops / 4 commands" rules are enforced (and tested) in one place.
import pygame

import assets
import data
import engine

LIGHT_BROWN = (156, 118, 58)
DARK_BROWN = (59, 40, 12)
BACK_COLOR = (89, 60, 20)
MAIN_TAB = (48, 32, 10)
SEC_TAB = (31, 21, 7)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (230, 190, 60)            # squad gold (spent in the loadout)
COMMAND_POINTS = (110, 170, 255)  # command points (spent in the game)
GREY = (110, 110, 110)

BORDER = 20
PADDING = 10
BETWEEN = 50
BORDER_WIDTH = 2


class Dropdown:
    """A small drop-down list. `options` is [(label, value)]. Any click while it is open picks the option
    under the mouse (if any) and closes it, and is swallowed so it does not also hit what is underneath."""

    def __init__(self, rect, options, index):
        self.rect, self.options, self.index, self.open = rect, options, index, False

    @property
    def value(self):
        return self.options[self.index][1]

    def option_rect(self, i):
        return pygame.Rect(self.rect.x, self.rect.bottom + 2 + i * self.rect.height, self.rect.width, self.rect.height)

    def handle_click(self, pos):
        """Returns True when the click belonged to the dropdown."""
        if self.open:
            for i in range(len(self.options)):
                if self.option_rect(i).collidepoint(pos):
                    self.index = i
            self.open = False
            return True
        if self.rect.collidepoint(pos):
            self.open = True
            return True
        return False

    def draw(self, screen, fonts, mouse_pos):
        hot = self.rect.collidepoint(mouse_pos) or self.open
        color = LIGHT_BROWN if hot else WHITE
        pygame.draw.rect(screen, BLACK, self.rect)
        pygame.draw.rect(screen, color, self.rect, width=2)
        label = fonts[2].render(self.options[self.index][0], True, color)
        screen.blit(label, (self.rect.x + 14, self.rect.centery - label.get_height() // 2))
        cx, cy = self.rect.right - 22, self.rect.centery            # a little down-pointing triangle
        pygame.draw.polygon(screen, color, [(cx - 8, cy - 4), (cx + 8, cy - 4), (cx, cy + 6)])
        if self.open:
            for i, (text, _) in enumerate(self.options):
                row = self.option_rect(i)
                over = row.collidepoint(mouse_pos)
                pygame.draw.rect(screen, MAIN_TAB if over else BLACK, row)
                pygame.draw.rect(screen, LIGHT_BROWN if over else WHITE, row, width=2)
                screen.blit(fonts[2].render(text, True, LIGHT_BROWN if over else WHITE),
                            (row.x + 14, row.centery - fonts[2].get_height() // 2))


def turn_limit_label(limit):
    return "\u221e" if limit is None else "%ds" % limit


class Card:
    """One big clickable rectangle (a troop or a command) plus the spots things are drawn at."""

    def __init__(self, row, col, width, height, spacing, key):
        x = (width + spacing) * col + spacing
        y = (height + spacing) * row + spacing + 85
        self.key = key
        self.outer = pygame.Rect(x, y, width, height)
        self.inner = pygame.Rect(x + BORDER_WIDTH, y + BORDER_WIDTH, width - 2 * BORDER_WIDTH, height - 2 * BORDER_WIDTH)
        self.img_pos = (x + 3 * BORDER_WIDTH, y + 3 * BORDER_WIDTH)
        self.name_pos = (x + 3 * BORDER_WIDTH + 32 * 5, y + 3 * BORDER_WIDTH)
        self.cost_pos = (x + 3 * BORDER_WIDTH, y + 32 * 3 + 20)
        self.cooldown_pos = (x + 3 * BORDER_WIDTH, y + 32 * 4)
        self.stats_pos = (x + 3 * BORDER_WIDTH + 32 * 5, y + 4 * BORDER_WIDTH + 32 * 2)


def _wrap(font, text, max_width):
    words, lines, line = text.split(), [], []
    for word in words:
        if line and font.size(" ".join(line + [word]))[0] > max_width:
            lines.append(" ".join(line))
            line = []
        line.append(word)
    if line:
        lines.append(" ".join(line))
    return lines


# --------------------------------------------------------------- start ------

def start_button_rect(fonts, screen_width):
    label_w, label_h = fonts[2].size(START_LABEL)
    return pygame.Rect(screen_width // 2 - label_w // 2 - 30, 520, label_w + 60, label_h + 30)


START_LABEL = "Play  (two players, one screen)"


def draw_start(screen, fonts, mouse_pos):
    """Title screen. Returns the Play button rect so the caller can hit-test clicks."""
    screen.fill(BACK_COLOR)
    title = fonts[4].render("CONQUEST", True, LIGHT_BROWN)
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 260))
    rect = start_button_rect(fonts, screen.get_width())
    hovered = rect.collidepoint(mouse_pos)
    color = LIGHT_BROWN if hovered else WHITE
    pygame.draw.rect(screen, MAIN_TAB, rect)
    pygame.draw.rect(screen, color, rect, width=2)
    screen.blit(fonts[2].render(START_LABEL, True, color), (rect.x + 30, rect.y + 15))
    return rect


# ------------------------------------------------------------- loadout ------

class LoadoutMenu:
    def __init__(self, fonts, screen_size, loadout=None):
        self.fonts = fonts
        self.loadout = loadout or engine.Loadout()
        self.tab = "troops"                         # or "commands"
        sw, sh = screen_size

        troops_size = fonts[3].size("Select Troops")
        commands_size = fonts[3].size("Select Commands")
        troops_rect = pygame.Rect(BORDER, BORDER, *troops_size)
        commands_rect = pygame.Rect(troops_size[0] + BETWEEN, BORDER, *commands_size)
        self.troops_rect, self.commands_rect = troops_rect, commands_rect
        self.resource_pos = (commands_rect.x + commands_size[0] + BETWEEN, int(1.5 * BORDER))
        self.troops_tab = troops_rect.inflate(2 * PADDING, 2 * PADDING)
        self.commands_tab = commands_rect.inflate(2 * PADDING, 2 * PADDING)
        self.selection_rect = pygame.Rect(self.troops_tab.x, self.troops_tab.bottom, sw - BORDER,
                                          sh - BORDER - self.troops_tab.bottom + PADDING)
        self.troop_count_pos = (self.resource_pos[0] - 240, sh - 200)
        # The empty 10th command slot (bottom right of the grid) holds the counter and a note about points.
        self.command_count_pos = (troops_size[0] + commands_size[0] + BETWEEN,
                                  sh - fonts[4].get_height() - 30)
        self.command_note_pos = (self.command_count_pos[0], (170 + 20) * 4 + 20 + 85 + 4)
        self.ready_rect = pygame.Rect(1500, 25, fonts[2].size("READY UP!")[0], 40)
        # turn timer setting: a label and a drop-down in the header, between "Squad Gold" and READY UP
        self.timer_label_pos = (1235, 38)
        self.turn_dropdown = Dropdown(
            pygame.Rect(1355, 27, 120, 44),
            [(turn_limit_label(limit), limit) for limit in engine.TURN_LIMITS],
            engine.TURN_LIMITS.index(engine.DEFAULT_TURN_LIMIT))

        # troop cards: 2 columns x 4 rows (the last slot is empty)
        self.troop_cards = [Card(row, col, 550, 200, 40, data.TROOP_ORDER[col * 4 + row])
                            for row in range(4) for col in range(2) if col * 4 + row < len(data.TROOP_ORDER)]
        self.troop_bar = pygame.Rect(1330, 125, 550, (200 + 40) * 4 - 40)
        self.troop_bar_inner = self.troop_bar.inflate(-10, -10)
        # command cards: 2 columns x 5 rows
        self.command_cards = [Card(row, col, 800, 170, 20, data.COMMAND_ORDER[col + 2 * row])
                              for row in range(5) for col in range(2) if col + 2 * row < len(data.COMMAND_ORDER)]
        self.command_bar = pygame.Rect(1665, 105, 220, 935)
        self.command_bar_inner = self.command_bar.inflate(-10, -10)

    # ---- geometry of the "what I've picked so far" side bars

    def _troop_row(self, i):
        inner = self.troop_bar_inner
        return pygame.Rect(inner.x, inner.y + 90 * i, inner.width, 90)

    def _command_row(self, i):
        inner = self.command_bar_inner
        return pygame.Rect(inner.x, inner.y + 230 * i + 15, inner.width, 215)

    @property
    def turn_limit(self):
        """Seconds each turn may last, or None for no limit."""
        return self.turn_dropdown.value

    # ---- input

    def handle_click(self, pos):
        """React to one left click. Returns "GAME" when the player readies up, else None."""
        lo = self.loadout
        if self.turn_dropdown.handle_click(pos):
            return None
        if self.troops_tab.collidepoint(pos):
            self.tab = "troops"
        elif self.commands_tab.collidepoint(pos):
            self.tab = "commands"
        elif lo.is_ready and self.ready_rect.collidepoint(pos):
            return "GAME"
        elif self.tab == "troops":
            for card in self.troop_cards:
                if card.outer.collidepoint(pos) and lo.can_add_troop(card.key):
                    lo.add_troop(card.key)
                    return None
            for i in range(len(lo.troops)):
                if self._troop_row(i).collidepoint(pos):
                    lo.remove_troop(i)
                    break
        else:
            for card in self.command_cards:
                if card.outer.collidepoint(pos) and lo.can_add_command(card.key):
                    lo.add_command(card.key)
                    return None
            for i in range(len(lo.commands)):
                if self._command_row(i).collidepoint(pos):
                    lo.remove_command(i)
                    break
        return None

    # ---- drawing

    def draw(self, screen, mouse_pos):
        fonts, lo = self.fonts, self.loadout
        on_troops = self.tab == "troops"
        screen.fill(BACK_COLOR)
        screen.fill(MAIN_TAB if on_troops else SEC_TAB, self.troops_tab)
        screen.fill(SEC_TAB if on_troops else MAIN_TAB, self.commands_tab)
        screen.fill(MAIN_TAB, self.selection_rect)

        def tab_color(active, tab_rect):
            if active:
                return LIGHT_BROWN
            return LIGHT_BROWN if tab_rect.collidepoint(mouse_pos) else DARK_BROWN

        screen.blit(fonts[3].render("Select Troops", True, tab_color(on_troops, self.troops_tab)),
                    self.troops_rect.topleft)
        screen.blit(fonts[3].render("Select Commands", True, tab_color(not on_troops, self.commands_tab)),
                    self.commands_rect.topleft)
        screen.blit(fonts[2].render("Squad Gold: %d" % lo.gold_left, True, LIGHT_BROWN), self.resource_pos)

        if on_troops:
            self._draw_troop_cards(screen, mouse_pos)
            self._draw_troop_bar(screen, mouse_pos)
            screen.blit(fonts[4].render("Troops: %d/%d" % (len(lo.troops), engine.MAX_TROOPS), True, WHITE),
                        self.troop_count_pos)
        else:
            self._draw_command_cards(screen, mouse_pos)
            self._draw_command_bar(screen, mouse_pos)
            screen.blit(fonts[4].render("Commands: %d/%d" % (len(lo.commands), engine.MAX_COMMANDS), True, WHITE),
                        self.command_count_pos)
            note = ("Commands cost no squad gold. In the game they spend command points: you gain %d at the "
                    "start of every turn, plus the gold cost of each troop you defeat."
                    % engine.COMMAND_POINTS_PER_TURN)
            y = self.command_note_pos[1]
            for line in _wrap(fonts[1], note, 760):
                screen.blit(fonts[1].render(line, True, COMMAND_POINTS), (self.command_note_pos[0], y))
                y += fonts[1].get_height()

        if lo.is_ready:
            hovered = self.ready_rect.collidepoint(mouse_pos)
            screen.fill(SEC_TAB, self.ready_rect)
            screen.blit(fonts[2].render("READY UP!", True, LIGHT_BROWN if hovered else WHITE), self.ready_rect.topleft)
        screen.blit(fonts[1].render("Turn timer", True, LIGHT_BROWN), self.timer_label_pos)
        self.turn_dropdown.draw(screen, fonts, mouse_pos)          # last, so its list opens over the cards

    def _card_frame(self, screen, card, mouse_pos, enabled):
        hovered = card.outer.collidepoint(mouse_pos)
        color = LIGHT_BROWN if hovered and enabled else WHITE
        if not enabled:
            color = (110, 110, 110)
        pygame.draw.rect(screen, color, card.outer)
        pygame.draw.rect(screen, BLACK, card.inner)
        pygame.draw.line(screen, color, (card.name_pos[0], card.name_pos[1] + 50),
                         (card.name_pos[0] + 300, card.name_pos[1] + 50))
        return color

    def _draw_cost(self, screen, card, text, color):
        """The price, right-aligned in the card's header row and labelled with its currency."""
        label = self.fonts[1].render(text, True, color, BLACK)
        screen.blit(label, (card.outer.right - 16 - label.get_width(), card.outer.y + 16))

    def _draw_troop_cards(self, screen, mouse_pos):
        fonts = self.fonts
        for card in self.troop_cards:
            spec = data.TROOPS[card.key]
            color = self._card_frame(screen, card, mouse_pos, self.loadout.can_add_troop(card.key))
            screen.blit(fonts[2].render(spec["name"], True, color, BLACK), card.name_pos)
            self._draw_cost(screen, card, "Gold cost: %d" % spec["cost"],
                            GOLD if self.loadout.can_add_troop(card.key) else GREY)
            stats = ["Movement: %d" % spec["speed"], "Damage: %d" % spec["damage"],
                     "Health: %d" % spec["health"], "Range: %d" % spec["range"]]
            line_h = fonts[1].size("STAT HEIGHT")[1]
            for j, stat in enumerate(stats):
                screen.blit(fonts[1].render(stat, True, color, BLACK), (card.stats_pos[0], card.stats_pos[1] + j * line_h))
            screen.blit(assets.scaled(spec["icon"], 32 * 4), card.img_pos)

    def _draw_troop_bar(self, screen, mouse_pos):
        fonts = self.fonts
        pygame.draw.rect(screen, WHITE, self.troop_bar)
        pygame.draw.rect(screen, BLACK, self.troop_bar_inner)
        inner = self.troop_bar_inner
        for i, key in enumerate(self.loadout.troops):
            spec = data.TROOPS[key]
            row = self._troop_row(i)
            color = LIGHT_BROWN if row.collidepoint(mouse_pos) else WHITE
            base = row.y
            screen.blit(assets.scaled(spec["icon"], 32 * 2), (inner.x + 25, base + 15))
            screen.blit(fonts[1].render(spec["name"], True, color, BLACK), (inner.x + 32 * 4, base + 10))
            screen.blit(fonts[1].render("Gold cost: %d" % spec["cost"], True, GOLD, BLACK), (inner.x + 32 * 9 + 10, base + 10))
            stats = ["Movement: %d" % spec["speed"], "Damage: %d" % spec["damage"],
                     "Health: %d" % spec["health"], "Range: %d" % spec["range"]]
            for j, stat in enumerate(stats):
                screen.blit(fonts[0].render(stat, True, color, BLACK), (inner.x + 32 * 4 + j * 100, base + 50))

    def _draw_command_cards(self, screen, mouse_pos):
        fonts = self.fonts
        for card in self.command_cards:
            spec = data.COMMANDS[card.key]
            color = self._card_frame(screen, card, mouse_pos, self.loadout.can_add_command(card.key))
            screen.blit(fonts[2].render(spec["name"], True, color, BLACK), card.name_pos)
            self._draw_cost(screen, card, "Command point cost: %d" % spec["cost"],
                            COMMAND_POINTS if self.loadout.can_add_command(card.key) else GREY)
            screen.blit(fonts[2].render("CD: %d" % spec["cooldown"], True, color, BLACK), card.cooldown_pos)
            screen.blit(assets.scaled(spec["icon"], 90), card.img_pos)
            y = card.stats_pos[1] - 12
            for line in _wrap(fonts[1], spec["text"], 620):
                screen.blit(fonts[1].render(line, True, color, BLACK), (card.stats_pos[0], y))
                y += fonts[1].size(line)[1]

    def _draw_command_bar(self, screen, mouse_pos):
        fonts = self.fonts
        pygame.draw.rect(screen, WHITE, self.command_bar)
        pygame.draw.rect(screen, BLACK, self.command_bar_inner)
        inner = self.command_bar_inner
        for i, key in enumerate(self.loadout.commands):
            spec = data.COMMANDS[key]
            row = self._command_row(i)
            color = LIGHT_BROWN if row.collidepoint(mouse_pos) else WHITE
            screen.blit(assets.scaled(spec["icon"], 160), (inner.x + 25, row.y))
            name = fonts[1].render(spec["name"], True, color, BLACK)
            screen.blit(name, (inner.x + (inner.width - name.get_width()) // 2, row.y + 165))

# Draws the game world from engine state. Nothing in here changes the game.
import pygame

import assets
import engine
import screenconfig

BACKGROUND = (3, 13, 46)            # navy blue
PLAYER_COLORS = [(70, 130, 255), (230, 70, 70)]
EFFECT_COLORS = {
    "battle_cry": (255, 150, 30), "stoicism": (60, 200, 90), "shield_wall": (150, 170, 200),
    "vigilance": (240, 220, 60), "chastise": (170, 80, 220), "charge": (255, 255, 255),
}
HOVER_TILE = (255, 238, 180, 62)   # translucent warm wash over a hovered troop's square
_overlays = {}


def draw_background(screen, color=BACKGROUND):
    screen.fill(color)


def draw_board(screen, board, anchor):
    screen.blit(board, (int(anchor[0]), int(anchor[1])))


def _overlay(size, color):
    key = (size, color)
    if key not in _overlays:
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        surface.fill(color)
        _overlays[key] = surface
    return _overlays[key]


def _tile_xy(tile, cell, anchor, scale):
    size = cell * scale
    return int(anchor[0] + tile[1] * size), int(anchor[1] + tile[0] * size), size


def draw_highlights(screen, game, hover_unit, cell, anchor, scale):
    """Show where the selected (or hovered) troop can walk and whom it can hit."""
    unit = game.selected_unit or hover_unit
    if unit is None:
        return
    if hover_unit is not None:                           # the square under the mouse warms up a little
        x, y, size = _tile_xy(hover_unit.pos, cell, anchor, scale)
        screen.blit(_overlay(size, HOVER_TILE), (x, y))
    if game.selected_unit is None or game.phase == engine.MOVEMENT:
        for tile in game.reachable_tiles(unit):
            x, y, size = _tile_xy(tile, cell, anchor, scale)
            screen.blit(_overlay(size, (60, 120, 255, 90)), (x, y))
    if game.selected_unit is None or not game.has_attacked:
        for target in game.attack_targets(unit):             # an outline, not a fill: troops' squares keep their colour
            x, y, size = _tile_xy(target.pos, cell, anchor, scale)
            pygame.draw.rect(screen, (255, 70, 70), (x, y, size, size), width=max(3, size // 12))
    if game.selected_unit is not None:
        x, y, size = _tile_xy(unit.pos, cell, anchor, scale)
        pygame.draw.rect(screen, (255, 235, 90), (x, y, size, size), width=max(2, size // 12))


def draw_units(screen, game, cell, anchor, scale):
    for unit in game.units.values():
        x, y, size = _tile_xy(unit.pos, cell, anchor, scale)
        pygame.draw.rect(screen, PLAYER_COLORS[unit.owner], (x + 2, y + 2, size - 4, size - 4),
                         width=max(2, size // 16))
        icon = assets.scaled(unit.stats["icon"], int(size * 0.6))
        screen.blit(icon, (x + (size - icon.get_width()) // 2, y + (size - icon.get_height()) // 2))
        # health bar along the bottom of the tile
        bar_w, bar_h = size - 8, max(3, size // 12)
        pygame.draw.rect(screen, (90, 20, 20), (x + 4, y + size - bar_h - 4, bar_w, bar_h))
        frac = max(0.0, min(1.0, unit.health / unit.max_health))
        pygame.draw.rect(screen, (60, 200, 80), (x + 4, y + size - bar_h - 4, int(bar_w * frac), bar_h))
        # temporary health: a thin blue bar stacked above the real one (full when the buff was cast)
        if unit.temp_capacity:
            tfrac = max(0.0, min(1.0, unit.temp_health / unit.temp_capacity))
            top = y + size - 2 * bar_h - 6
            pygame.draw.rect(screen, (30, 50, 80), (x + 4, top, bar_w, bar_h))
            pygame.draw.rect(screen, (90, 190, 255), (x + 4, top, int(bar_w * tfrac), bar_h))
        # one coloured pip per active effect, top left
        pip = max(4, size // 8)
        for i, effect in enumerate(unit.effects):
            pygame.draw.rect(screen, EFFECT_COLORS.get(effect, (255, 255, 255)), (x + 5 + i * (pip + 2), y + 5, pip, pip))


def draw_winner(screen, fonts, winner):
    shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 150))
    screen.blit(shade, (0, 0))
    text = fonts[4].render("Player %d wins!" % (winner + 1), True, (255, 255, 255))
    sub = fonts[2].render("Click or press Enter to play again", True, (200, 200, 200))
    cx, cy = screen.get_width() // 2, screen.get_height() // 2
    screen.blit(text, (cx - text.get_width() // 2, cy - text.get_height()))
    screen.blit(sub, (cx - sub.get_width() // 2, cy + 20))


FLASH_SECONDS = 0.75
_flash_cache = {}


def _cached(key, make):
    if key not in _flash_cache:
        _flash_cache[key] = make()
    return _flash_cache[key]


def draw_turn_flash(screen, fonts, player, turn_number, progress):
    """A quick flash across the screen when a new player's turn begins. `progress` runs 0 -> 1 over
    FLASH_SECONDS: a colour wash that fades, a bright band that sweeps left to right, and a banner."""
    color = PLAYER_COLORS[player]
    w, h = screen.get_size()

    wash = _cached(("wash", color, w, h), lambda: _filled(w, h, color))       # fading tint over everything
    wash.set_alpha(int(75 * (1 - progress) ** 2))
    screen.blit(wash, (0, 0))

    sweep = min(1.0, progress / 0.65)                                         # the band crosses the screen first
    strips, strip_w = 28, 22
    centre = -strips * strip_w / 2 + (w + strips * strip_w) * sweep
    for i in range(strips):
        x = int(centre + (i - strips / 2) * strip_w)
        if x + strip_w < 0 or x > w:
            continue
        falloff = 1.0 - abs(i + 0.5 - strips / 2) / (strips / 2)
        strip = _cached(("strip", color, h, i), lambda f=falloff: _strip(strip_w, h, color, int(190 * f)))
        screen.blit(strip, (x, 0))

    fade = max(0.0, min(1.0, (1 - progress) / 0.6))                           # banner stays, then fades out
    banner = _cached(("banner", player), lambda: fonts[4].render("Player %d's turn" % (player + 1), True,
                                                                   tuple(min(255, c + 90) for c in color)))
    sub = _cached(("sub", turn_number), lambda: fonts[2].render("Turn %d" % turn_number, True, (255, 255, 255)))
    cx, cy = w // 2, h // 2
    for surf, y in ((banner, cy - banner.get_height()), (sub, cy + 8)):
        surf.set_alpha(int(255 * fade))
        screen.blit(surf, (cx - surf.get_width() // 2, y))


def _filled(w, h, color):
    surface = pygame.Surface((w, h))
    surface.fill(color)
    return surface


def _strip(w, h, color, alpha):
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    surface.fill(tuple(min(255, c + 60) for c in color) + (alpha,))
    return surface


def present(fake_screen, screen, bar_color=(0, 0, 0), split_x=None):
    """Scale the fixed-size drawing surface to fit the real window, keeping its shape; any leftover
    window space is filled with `bar_color`.

    split_x=None: the canvas is centred (menus).
    split_x=<canvas x>: in-game layout. The sidebar (everything right of split_x) is pinned to the right
    edge of the window and the board area is centred in the space that is left of it."""
    fw, fh = fake_screen.get_size()
    screen.fill(bar_color)
    if split_x is None:
        scale, ox, oy = screenconfig.fit(screen.get_size(), (fw, fh))
        size = (max(1, int(fw * scale)), max(1, int(fh * scale)))
        screen.blit(pygame.transform.scale(fake_screen, size), (int(ox), int(oy)))
    else:
        scale, board_ox, _, oy = screenconfig.fit_split(screen.get_size(), (fw, fh), split_x)
        size = (max(1, int(fw * scale)), max(1, int(fh * scale)))
        scaled = pygame.transform.scale(fake_screen, size)
        split_px = int(split_x * scale)
        side_w = size[0] - split_px
        screen.blit(scaled, (int(board_ox), int(oy)), pygame.Rect(0, 0, split_px, size[1]))
        screen.blit(scaled, (screen.get_width() - side_w, int(oy)), pygame.Rect(split_px, 0, side_w, size[1]))
    pygame.display.update()

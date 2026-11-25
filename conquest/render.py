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
    if game.selected_unit is None or game.phase == engine.MOVEMENT:
        for tile in game.reachable_tiles(unit):
            x, y, size = _tile_xy(tile, cell, anchor, scale)
            screen.blit(_overlay(size, (60, 120, 255, 90)), (x, y))
    if game.selected_unit is None or not game.has_attacked:
        for target in game.attack_targets(unit):
            x, y, size = _tile_xy(target.pos, cell, anchor, scale)
            screen.blit(_overlay(size, (255, 60, 60, 120)), (x, y))
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
        frac = max(0.0, min(1.0, unit.health / unit.effective_max_health))
        pygame.draw.rect(screen, (60, 200, 80), (x + 4, y + size - bar_h - 4, int(bar_w * frac), bar_h))
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


def present(fake_screen, screen):
    """Scale the fixed-size drawing surface to fit the real window, centred, keeping its shape.
    Windows that are not 16:9 get black bars rather than a stretched board."""
    scale, ox, oy = screenconfig.fit(screen.get_size(), fake_screen.get_size())
    size = (max(1, int(fake_screen.get_width() * scale)), max(1, int(fake_screen.get_height() * scale)))
    screen.fill((0, 0, 0))
    screen.blit(pygame.transform.scale(fake_screen, size), (int(ox), int(oy)))
    pygame.display.update()

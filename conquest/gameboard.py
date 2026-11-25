# Board geometry and drawing. Which tiles are blocked is decided by engine.generate_obstacles;
# this file only turns that data into pixels (and pixels back into tiles).
import pygame

import engine
import textures

VARIANTS = 8                        # distinct wood tiles per colour; each square picks one
SHADOW = (0, 0, 0, 80)


def board_cell_size(screen):
    """Cell size in pixels at 1x zoom: leaves at least 20% on the right for the menus."""
    return int(min(screen.get_width() / 25, screen.get_height() / 20))


def _variant(row, col):
    """Which wood variant a square uses. Fixed per square, so zooming never reshuffles the board."""
    return (row * 31 + col * 17 + row * col * 7) % VARIANTS


def create_board(cell, obstacles):
    """Draw the textured board at `cell` pixels per tile. Called once per zoom level, so grain and
    rocks are redrawn crisply at each size instead of being blown up."""
    n = engine.BOARD_SIZE
    board = pygame.Surface((cell * n, cell * n))
    light = [textures.wood_tile(cell, True, seed) for seed in range(VARIANTS)]
    dark = [textures.wood_tile(cell, False, 1000 + seed) for seed in range(VARIANTS)]
    for row in range(n):
        for col in range(n):
            tiles = light if (row + col) % 2 == 0 else dark
            board.blit(tiles[_variant(row, col)], (col * cell, row * cell))

    # a soft shadow on the floor just below and to the right of every rock
    band = max(3, cell // 7)
    shade_h = pygame.Surface((cell, band), pygame.SRCALPHA)
    shade_h.fill(SHADOW)
    shade_v = pygame.Surface((band, cell), pygame.SRCALPHA)
    shade_v.fill(SHADOW)
    for row, col in obstacles:
        if row + 1 < n and (row + 1, col) not in obstacles:
            board.blit(shade_h, (col * cell, (row + 1) * cell))
        if col + 1 < n and (row, col + 1) not in obstacles:
            board.blit(shade_v, ((col + 1) * cell, row * cell))

    for row, col in obstacles:
        exposed = set()
        if (row - 1, col) not in obstacles:
            exposed.add("n")
        if (row + 1, col) not in obstacles:
            exposed.add("s")
        if (row, col - 1) not in obstacles:
            exposed.add("w")
        if (row, col + 1) not in obstacles:
            exposed.add("e")
        neighbours = {(dr, dc): (row + dr) * n + (col + dc)
                      for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                      if (dr or dc) and (row + dr, col + dc) in obstacles}
        board.blit(textures.rock_tile(cell, row * n + col, exposed, neighbours), (col * cell, row * cell))

    pygame.draw.rect(board, (255, 255, 255), (0, 0, cell * n, cell * n), width=2)
    return board


def tile_at(pos, anchor, cell, scale):
    """(row, col) under a screen position, or None if it is outside the board."""
    size = cell * scale
    col = int((pos[0] - anchor[0]) // size)
    row = int((pos[1] - anchor[1]) // size)
    if 0 <= row < engine.BOARD_SIZE and 0 <= col < engine.BOARD_SIZE:
        return (row, col)
    return None


def saturate_anchor(anchor, screen, scale_idx, scales):
    """Keep the zoomed board from being dragged too far off screen."""
    buffer = 100 * scales[scale_idx]
    if scale_idx == 0:
        return 0, 0
    if anchor[0] > buffer:
        anchor = (buffer, anchor[1])
    if anchor[1] > buffer:
        anchor = (anchor[0], buffer)
    if anchor[0] < -screen.get_height() * scales[scale_idx] + screen.get_width() * 0.8 - buffer:
        anchor = (-screen.get_height() * scales[scale_idx] + screen.get_width() * 0.8 - buffer, anchor[1])
    if anchor[1] < -screen.get_height() * scales[scale_idx] + screen.get_height() - buffer:
        anchor = (anchor[0], -screen.get_height() * scales[scale_idx] + screen.get_height() - buffer)
    return anchor

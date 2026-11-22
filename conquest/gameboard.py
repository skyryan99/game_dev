# Board geometry and drawing. Which tiles are blocked is decided by engine.generate_obstacles;
# this file only turns that data into pixels (and pixels back into tiles).
import pygame

import engine

LIGHT = (156, 118, 58)
DARK = (59, 40, 12)
OBSTACLE = (176, 176, 176)
OBSTACLE_EDGE = (110, 110, 110)


def board_cell_size(screen):
    """Cell size in pixels at 1x zoom: leaves at least 20% on the right for the menus."""
    return int(min(screen.get_width() / 25, screen.get_height() / 20))


def create_board(cell, obstacles):
    """Draw the board at `cell` pixels per tile. Called once per zoom level, so lines stay crisp."""
    n = engine.BOARD_SIZE
    board = pygame.Surface((cell * n, cell * n))
    board.fill(DARK)
    for row in range(n):
        for col in range(n):
            if (row + col) % 2 == 0:
                pygame.draw.rect(board, LIGHT, (col * cell, row * cell, cell, cell))
    for row, col in obstacles:
        rect = (col * cell, row * cell, cell, cell)
        pygame.draw.rect(board, OBSTACLE, rect)
        pygame.draw.rect(board, OBSTACLE_EDGE, rect, width=max(1, cell // 18))
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

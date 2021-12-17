# Create the game board at the start of a game
import pygame
import random


def add_border(board, size):
    line_width = 2
    color = (255, 255, 255)
    pygame.draw.line(board, color, (0, 0), (20*size, 0), width=line_width)
    pygame.draw.line(board, color, (0, 0), (0, 20*size), width=line_width)
    pygame.draw.line(board, color, (20*size-line_width, 20*size), (20*size-line_width, 0), width=line_width)
    pygame.draw.line(board, color, (20*size, 20*size-line_width), (0, 20*size-line_width), width=line_width)


def add_obstacles(board, size):
    color = (176, 176, 176)
    singles = random.randint(2, 3)
    triples = random.randint(0, 2)
    quads = random.randint(0, 1)
    # Draw the single tiles
    for i in range(singles):
        # Span the entire width except borders
        x = random.randint(1, 18)
        # Between rows 6 and 14 (2 rows of space between troop placement zone and closest spawns)
        y = random.randint(6, 13)
        pygame.draw.rect(board, color, (x * size, y * size, size, size))
    # Draw the triples
    for i in range(triples):
        # Horizontals
        if i%2 == 0:
            x = random.randint(0, 17)
            y = random.randint(6, 13)
            pygame.draw.rect(board, color, (x * size, y * size, size, size))
            pygame.draw.rect(board, color, ((x + 1) * size, y * size, size, size))
            pygame.draw.rect(board, color, ((x + 2) * size, y * size, size, size))
        # Verticals
        else:
            x = random.randint(1, 18)
            y = random.randint(6, 11)
            pygame.draw.rect(board, color, (x * size, y * size, size, size))
            pygame.draw.rect(board, color, (x * size, (y + 1) * size, size, size))
            pygame.draw.rect(board, color, (x * size, (y + 2) * size, size, size))
    # Draw the quads
    for i in range(quads):
        # Horizontals
        if i%2 == 0:
            x = random.randint(0, 16)
            y = random.randint(6, 13)
            pygame.draw.rect(board, color, (x * size, y * size, size, size))
            pygame.draw.rect(board, color, ((x + 1) * size, y * size, size, size))
            pygame.draw.rect(board, color, ((x + 2) * size, y * size, size, size))
            pygame.draw.rect(board, color, ((x + 3) * size, y * size, size, size))
        # Verticals
        else:
            x = random.randint(1, 18)
            y = random.randint(6, 10)
            pygame.draw.rect(board, color, (x * size, y * size, size, size))
            pygame.draw.rect(board, color, (x * size, (y + 1) * size, size, size))
            pygame.draw.rect(board, color, (x * size, (y + 2) * size, size, size))
            pygame.draw.rect(board, color, (x * size, (y + 3) * size, size, size))
    return board


def create_board(screen):
    cell_size = min(screen.get_width()/25, screen.get_height()/20)  # Leaves min 20% left side, stays above bottom
    board = pygame.Surface((cell_size*20, cell_size*20))
    board.fill((59, 40, 12))  # Dark squares
    for i in range(0, 20, 2):
        for j in range(0, 20, 2):  # Light Squares
            pygame.draw.rect(board, (156, 118, 58), (i*cell_size, j*cell_size, cell_size, cell_size))
    for i in range(1, 20, 2):
        for j in range(1, 20, 2):  # Light Squares
            pygame.draw.rect(board, (156, 118, 58), (i*cell_size, j*cell_size, cell_size, cell_size))
    board = add_obstacles(board, cell_size)
    add_border(board, cell_size)
    return board


def saturate_anchor(anchor, screen, scale_idx, scales):
    buffer = 50*scales[scale_idx]
    if scale_idx == 0:
        return 0, 0
    if anchor[0] > buffer:
        anchor = (buffer, anchor[1])
    if anchor[1] > buffer:
        anchor = (anchor[0], buffer)
    if anchor[0] < -screen.get_height()*scales[scale_idx] + screen.get_width()*0.8 - buffer:
        anchor = (-screen.get_height()*scales[scale_idx] + screen.get_width()*0.8 - buffer, anchor[1])
    if anchor[1] < -screen.get_height()*scales[scale_idx] + screen.get_height() - buffer:
        anchor = (anchor[0], -screen.get_height()*scales[scale_idx] + screen.get_height() - buffer)
    return anchor

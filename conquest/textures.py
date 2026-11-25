# Procedurally drawn tile textures, so the board needs no image files.
#
# Everything is described in fractions of the tile size and seeded, so a tile looks the same at
# every zoom level (only sharper when zoomed in) and the same seed always gives the same tile.
#
#   wood_tile(size, light, seed)    a parquet tile: 2-3 planks with grain, end joints and the odd knot
#   rock_tile(size, seed, exposed)  a rough boulder tile, bevelled on the sides that face open floor
import math
import random

import pygame

# Palette sampled from the reference screenshot (a dim tan and a dark olive-brown), lifted a little
# so the white unit icons stay readable on top.
LIGHT_WOOD = (122, 112, 84)
DARK_WOOD = (56, 50, 37)
ROCK = (116, 112, 104)


def shade(color, factor):
    """Multiply a colour's brightness (factor > 1 lightens, < 1 darkens)."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)


# ------------------------------------------------------------------ wood ----

def wood_tile(size, light, seed):
    """One square of parquet. Light tiles have planks running up-down, dark tiles left-right,
    which gives the checkerboard its woven look (as in the reference picture)."""
    rng = random.Random(seed)
    base = LIGHT_WOOD if light else DARK_WOOD
    tile = pygame.Surface((size, size))
    tile.fill(base)
    vertical = light

    def pt(u, v):                       # u runs along the plank, v across it
        return (v, u) if vertical else (u, v)

    thin = max(1, size // 64)
    seam = max(1, size // 40)
    planks = rng.choice((2, 3, 3))
    cuts = [0] + [int(size * (i + rng.uniform(-0.12, 0.12)) / planks) for i in range(1, planks)] + [size]
    step = max(2, size // 6)

    for i in range(planks):
        v0, v1 = cuts[i], cuts[i + 1]
        plank = shade(base, rng.uniform(0.88, 1.12))
        rect = (v0, 0, v1 - v0, size) if vertical else (0, v0, size, v1 - v0)
        pygame.draw.rect(tile, plank, rect)

        # grain: long, slightly wavy streaks, some lighter and some darker than the plank
        for _ in range(max(3, (v1 - v0) // max(2, size // 14))):
            v = rng.uniform(v0 + 1, v1 - 1)
            wobble = size * 0.012
            points = [pt(u, v + rng.uniform(-wobble, wobble)) for u in range(0, size + 1, step)]
            pygame.draw.lines(tile, shade(plank, rng.choice((0.78, 0.86, 1.14, 1.22))), False, points, thin)

        # end joint: where one board stops and the next begins
        if rng.random() < 0.7:
            u = int(rng.uniform(0.25, 0.8) * size)
            pygame.draw.line(tile, shade(plank, 0.5), pt(u, v0), pt(u, v1), seam)
            pygame.draw.line(tile, shade(plank, 1.18), pt(u + seam, v0), pt(u + seam, v1), 1)

        # occasional knot
        if rng.random() < 0.22:
            centre = pt(rng.uniform(0.2, 0.8) * size, (v0 + v1) / 2)
            radius = max(2, (v1 - v0) // 5)
            pygame.draw.circle(tile, shade(plank, 0.68), centre, radius, thin)
            pygame.draw.circle(tile, shade(plank, 0.8), centre, max(1, radius // 2))

        # seam between this plank and the previous one
        if i > 0:
            pygame.draw.line(tile, shade(base, 0.45), pt(0, v0), pt(size, v0), seam)
            pygame.draw.line(tile, shade(base, 1.2), pt(0, v0 + seam), pt(size, v0 + seam), 1)

    pygame.draw.rect(tile, shade(base, 0.72), (0, 0, size, size), max(1, size // 70))
    return tile


# ------------------------------------------------------------------ rock ----

def _rock_facets(seed, size):
    """The stones belonging to one rock cell: (polygon, colour) pairs. They may spill over the cell's
    border; neighbouring rock cells draw each other's stones so the join is seamless."""
    rng = random.Random(seed)
    facets = []
    for _ in range(5):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        radius = size * rng.uniform(0.3, 0.55)
        sides = rng.randint(5, 7)
        offset = rng.uniform(0, math.tau)
        points = []
        for k in range(sides):                  # increasing angle = clockwise on screen (y points down)
            angle = offset + math.tau * k / sides + rng.uniform(-0.25, 0.25)
            r = radius * rng.uniform(0.65, 1.0)
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        facets.append((points, shade(ROCK, rng.uniform(0.82, 1.14))))
    return facets


def _draw_facet(tile, points, color, dx, dy, edge):
    """One lit stone: fill, then each edge lighter or darker depending on whether it faces the light
    (which comes from the top-left)."""
    pts = [(x + dx, y + dy) for x, y in points]
    pygame.draw.polygon(tile, color, pts)
    for k in range(len(pts)):
        (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % len(pts)]
        length = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = (y1 - y0) / length, -(x1 - x0) / length          # outward normal for a clockwise polygon
        lit = -(nx + ny) / math.sqrt(2)                              # +1 facing the light, -1 facing away
        pygame.draw.line(tile, shade(color, 1 + 0.3 * lit), (x0, y0), (x1, y1), edge)


def rock_tile(size, seed, exposed, neighbours=None):
    """A boulder tile.

    exposed     sides ("n", "s", "e", "w") facing open floor; they get a rounded, shaded edge
                (bright on the top/left, dark on the bottom/right) so a group looks like one lump of stone.
    neighbours  {(row_offset, col_offset): seed} of the adjacent rock cells (8 directions). Their stones
                are drawn here too, in a fixed global order, so stones carry across tile borders.
    """
    rng = random.Random(seed)
    tile = pygame.Surface((size, size))
    tile.fill(shade(ROCK, 0.95))
    edge = max(1, size // 45)

    cells = dict(neighbours or {})
    cells[(0, 0)] = seed
    for (dr, dc) in sorted(cells):              # row-major, the same order every overlapping tile uses
        for points, color in _rock_facets(cells[(dr, dc)], size):
            _draw_facet(tile, points, color, dc * size, dr * size, edge)

    # fine speckle and a crack or two, kept inside this tile
    for _ in range(max(5, size // 8)):
        pygame.draw.circle(tile, shade(ROCK, rng.choice((0.62, 0.75, 1.25, 1.38))),
                           (rng.randint(0, size), rng.randint(0, size)), max(1, size // 100))
    for _ in range(rng.randint(0, 2)):
        x, y = rng.uniform(0.15, 0.85) * size, rng.uniform(0.15, 0.85) * size
        points = [(x, y)]
        for _ in range(3):
            x = min(size, max(0, x + rng.uniform(-0.16, 0.16) * size))
            y = min(size, max(0, y + rng.uniform(-0.16, 0.16) * size))
            points.append((x, y))
        pygame.draw.lines(tile, shade(ROCK, 0.42), False, points, max(1, size // 70))

    # rounded, shaded edges where the rock meets the floor: darkest/brightest at the very edge, fading inward
    depth = max(3, size // 6)
    for k in range(depth):
        fade = 1.0 - k / depth
        bright, dark = shade(ROCK, 1.0 + 0.38 * fade), shade(ROCK, 1.0 - 0.55 * fade)
        if "n" in exposed:
            pygame.draw.line(tile, bright, (0, k), (size, k))
        if "w" in exposed:
            pygame.draw.line(tile, bright, (k, 0), (k, size))
        if "s" in exposed:
            pygame.draw.line(tile, dark, (0, size - 1 - k), (size, size - 1 - k))
        if "e" in exposed:
            pygame.draw.line(tile, dark, (size - 1 - k, 0), (size - 1 - k, size))
    return tile

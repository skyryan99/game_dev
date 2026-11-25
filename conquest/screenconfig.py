# Window / display settings and the maths that maps the fixed 1920x1080 game canvas onto
# whatever the real window is. No pygame in here, so it is unit tested.
#
# The whole game (board, menus, HUD) is drawn at BASE_SIZE and then scaled to the window, so
# changing the resolution or going fullscreen never needs any layout code to change. If the
# window is not 16:9 the canvas is letterboxed (black bars) instead of stretched.
import json
import os
from dataclasses import dataclass

BASE_SIZE = (1920, 1080)
MIN_SIZE = (640, 360)
PRESETS = [(1280, 720), (1366, 768), (1600, 900), (1920, 1080), (2560, 1440), (3840, 2160)]


@dataclass
class Settings:
    fullscreen: bool = False
    width: int = 1920            # windowed size; kept while fullscreen so we can come back to it
    height: int = 1080

    @property
    def size(self):
        return (self.width, self.height)


def available_resolutions(desktop):
    """Presets that fit on the desktop, smallest first (never empty)."""
    options = [p for p in PRESETS if p[0] <= desktop[0] and p[1] <= desktop[1]]
    return options or [MIN_SIZE]


def fit_to_desktop(size, desktop, options):
    """Keep `size` if it fits the desktop, otherwise fall back to the largest preset that does."""
    if size[0] <= desktop[0] and size[1] <= desktop[1]:
        return size
    return options[-1]


def step_resolution(current, direction, options):
    """The next (+1) or previous (-1) preset by width. Works from a custom, dragged-out size too.
    Returns `current` unchanged when there is nothing further in that direction."""
    if direction > 0:
        bigger = [o for o in options if o[0] > current[0]]
        return bigger[0] if bigger else current
    smaller = [o for o in options if o[0] < current[0]]
    return smaller[-1] if smaller else current


def fit(window, base=BASE_SIZE):
    """(scale, offset_x, offset_y) that centres the base canvas inside the window, keeping its shape."""
    scale = min(window[0] / base[0], window[1] / base[1])
    scale = max(scale, 1e-6)
    return scale, (window[0] - base[0] * scale) / 2, (window[1] - base[1] * scale) / 2


def window_to_base(pos, window, base=BASE_SIZE):
    """Convert a mouse position in the window to canvas (1920x1080) coordinates."""
    scale, ox, oy = fit(window, base)
    return (pos[0] - ox) / scale, (pos[1] - oy) / scale


def load(path):
    """Read settings from JSON; any missing or corrupt file just gives the defaults."""
    settings = Settings()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        settings.fullscreen = bool(raw.get("fullscreen", settings.fullscreen))
        width, height = int(raw.get("width", settings.width)), int(raw.get("height", settings.height))
        if width >= MIN_SIZE[0] and height >= MIN_SIZE[1]:
            settings.width, settings.height = width, height
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return settings


def save(settings, path):
    """Write settings to JSON. Returns False (and carries on) if the disk says no."""
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"fullscreen": settings.fullscreen, "width": settings.width, "height": settings.height},
                      handle, indent=2)
        return True
    except OSError:
        return False

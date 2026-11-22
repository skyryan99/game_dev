# Loads images and fonts exactly once. Paths are relative to this file, so the game runs no
# matter which directory you launch it from (the old code used os.getcwd()).
import os

import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_images = {}
_scaled = {}


def path(*parts):
    return os.path.join(BASE_DIR, *parts)


def font_path(name="Montserrat-Regular.ttf"):
    return path("fonts", name)


def image(name):
    """The image from images/<name>, loaded on first use and cached."""
    if name not in _images:
        surface = pygame.image.load(path("images", name))
        if pygame.display.get_surface() is not None:
            surface = surface.convert_alpha()
        _images[name] = surface
    return _images[name]


def scaled(name, size):
    """The image at size x size pixels, cached (scaling every frame was wasteful)."""
    key = (name, size)
    if key not in _scaled:
        _scaled[key] = pygame.transform.smoothscale(image(name), (size, size))
    return _scaled[key]

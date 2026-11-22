# Runs the game window.
#
#   python main.py
#
# States:  START -> LOADOUT -> GAME -> (winner overlay) -> START
#
# Everything is drawn onto a fixed 1920x1080 surface ("fake screen") which is then stretched to the
# real, resizable window, so every coordinate below is in 1920x1080 space. Mouse positions are
# converted with App.to_fake().
import ctypes
import random
import sys

import pygame

import actions
import assets
import engine
import gameboard
import hud
import menus
import render

DEFAULT_SIZE = (1920, 1080)
SCALES = [1, 2, 4]                  # zoom levels
FPS = 60


class App:
    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("Conquest")
        # Windows only: gives the app its own taskbar icon instead of python's. Must precede set_mode.
        if sys.platform == "win32":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("skyryan99.conquest")
        self.screen = pygame.display.set_mode(DEFAULT_SIZE, pygame.RESIZABLE)
        pygame.display.set_icon(assets.image("conquest_icon.png"))
        self.fake = pygame.Surface(DEFAULT_SIZE)
        self.clock = pygame.time.Clock()
        font = assets.font_path("Montserrat-Regular.ttf")
        # small, medium, large, extra large and huge
        self.fonts = [pygame.font.Font(font, size) for size in (12, 20, 32, 52, 72)]

        self.state = "START"
        self.mouse = (0, 0)                 # always in fake-screen coordinates
        self.start_rect = menus.start_button_rect(self.fonts, DEFAULT_SIZE[0])
        self.menu = None
        self.game = None
        self.controller = None
        self.cell = gameboard.board_cell_size(self.fake)
        self.boards = []                    # the board pre-drawn at each zoom level
        self.scale_idx = 0
        self.anchor = (0, 0)
        self.dragging = False
        self.drag_origin = ((0, 0), (0, 0))

    # ---- helpers

    def to_fake(self, pos):
        w, h = self.screen.get_size()
        return pos[0] * DEFAULT_SIZE[0] / w, pos[1] * DEFAULT_SIZE[1] / h

    def hover_unit(self):
        if self.state != "GAME" or self.mouse[0] >= hud.panel_x(self.fake):
            return None
        tile = gameboard.tile_at(self.mouse, self.anchor, self.cell, SCALES[self.scale_idx])
        return self.game.unit_at(*tile) if tile else None

    def new_menu(self):
        self.menu = menus.LoadoutMenu(self.fonts, DEFAULT_SIZE)

    def start_game(self):
        # Hot-seat for now: player 2 gets a copy of player 1's squad until online play is hooked up.
        loadouts = [self.menu.loadout, engine.Loadout.from_dict(self.menu.loadout.to_dict())]
        self.game = engine.Game.new(loadouts, rng=random.Random())
        self.controller = actions.Controller(self.game)
        self.boards = [gameboard.create_board(self.cell * s, self.game.obstacles) for s in SCALES]
        self.scale_idx = 0
        self.anchor = (0, 0)
        self.state = "GAME"

    # ---- events

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        elif event.type == pygame.VIDEORESIZE:
            width = max(640, event.size[0])
            self.screen = pygame.display.set_mode((width, int(width * DEFAULT_SIZE[1] / DEFAULT_SIZE[0])),
                                                  pygame.RESIZABLE)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse = self.to_fake(event.pos)
            if self.dragging:
                (mx0, my0), (ax0, ay0) = self.drag_origin
                self.anchor = (ax0 + self.mouse[0] - mx0, ay0 + self.mouse[1] - my0)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse = self.to_fake(event.pos)
            self.on_mouse_down(event.button)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self.dragging = False
        elif event.type == pygame.MOUSEWHEEL:
            if self.state == "GAME":
                self.zoom(event.y)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.state == "GAME":
                self.controller.cancel()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.state == "GAME" and self.game.winner is not None:
                self.state = "START"

    def on_mouse_down(self, button):
        if self.state == "START":
            if button == 1 and self.start_rect.collidepoint(self.mouse):
                self.new_menu()
                self.state = "LOADOUT"
        elif self.state == "LOADOUT":
            if button == 1 and self.menu.handle_click(self.mouse) == "GAME":
                self.start_game()
        elif self.state == "GAME":
            if self.game.winner is not None:
                if button == 1:
                    self.state = "START"
            elif button == 2:
                if self.scale_idx > 0:
                    self.dragging = True
                    self.drag_origin = (self.mouse, self.anchor)
            elif button == 3:
                self.controller.cancel()
            elif button == 1:
                if self.mouse[0] >= hud.panel_x(self.fake):
                    self.controller.click_button(hud.button_at(self.fake, self.game, self.mouse))
                else:
                    tile = gameboard.tile_at(self.mouse, self.anchor, self.cell, SCALES[self.scale_idx])
                    self.controller.click_tile(tile)

    def zoom(self, direction):
        """Zoom one level in (direction > 0) or out, keeping the tile under the mouse in place."""
        mx, my = self.mouse
        ax, ay = self.anchor
        if direction > 0 and self.scale_idx < len(SCALES) - 1:
            self.anchor = (ax * 2 - mx, ay * 2 - my)
            self.scale_idx += 1
        elif direction < 0 and self.scale_idx > 0:
            self.anchor = (ax * 0.5 + mx * 0.5, ay * 0.5 + my * 0.5)
            self.scale_idx -= 1

    # ---- drawing

    def draw(self):
        if self.state == "START":
            self.start_rect = menus.draw_start(self.fake, self.fonts, self.mouse)
        elif self.state == "LOADOUT":
            self.menu.draw(self.fake, self.mouse)
        elif self.state == "GAME":
            self.anchor = gameboard.saturate_anchor(self.anchor, self.fake, self.scale_idx, SCALES)
            scale = SCALES[self.scale_idx]
            # self.boards[i] is pre-drawn at cell * SCALES[i] pixels, so the board stays crisp at every zoom
            render.draw_background(self.fake)
            render.draw_board(self.fake, self.boards[self.scale_idx], self.anchor)
            hover = self.hover_unit()
            render.draw_highlights(self.fake, self.game, hover, self.cell, self.anchor, scale)
            render.draw_units(self.fake, self.game, self.cell, self.anchor, scale)
            hud.draw(self.fake, self.fonts, self.game, self.mouse, hover, self.controller.armed,
                     self.controller.message)
            if self.game.winner is not None:
                render.draw_winner(self.fake, self.fonts, self.game.winner)
        render.present(self.fake, self.screen)

    def run(self):
        while True:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    pygame.init()
    App().run()

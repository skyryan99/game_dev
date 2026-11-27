# Runs the game window.
#
#   python main.py
#
# States:  START -> LOADOUT -> GAME -> (winner overlay) -> START      (Esc opens the menu in any state)
#
# Everything is drawn onto a fixed 1920x1080 surface ("fake screen") which is then scaled to fit the
# real window (letterboxed if it is not 16:9), so every coordinate below is in 1920x1080 space.
# Mouse positions are converted with App.set_mouse(). Window size and fullscreen live in
# screenconfig.Settings and are applied in App.apply_display().
import ctypes
import random
import sys

import pygame

import actions
import assets
import engine
import gameboard
import gamemenu
import hud
import menus
import render
import screenconfig

DEFAULT_SIZE = screenconfig.BASE_SIZE
SETTINGS_PATH = assets.path("settings.json")
SCALES = [1, 2, 4]                  # zoom levels
FPS = 60
STALL_SECONDS = 0.5                # a frame longer than this was a stall (window drag, mode switch, ...)
LOG_WHEEL_LINES = 3                 # lines per mouse-wheel notch over the turn log


def desktop_size():
    """Size of the monitor in pixels (falls back to 1920x1080 if pygame cannot tell us)."""
    try:
        return tuple(pygame.display.get_desktop_sizes()[0])
    except (AttributeError, IndexError, pygame.error):
        return DEFAULT_SIZE


class App:
    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("Conquest")
        if sys.platform == "win32":
            # Without this, Windows display scaling (125%, 150%...) makes pygame's window bigger than the
            # resolution you asked for and fullscreen blurry. Must come before the window exists.
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass
            # Gives the app its own taskbar icon instead of python's.
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("skyryan99.conquest")
        self.settings = screenconfig.load(SETTINGS_PATH)
        self.desktop = desktop_size()
        self.resolutions = screenconfig.available_resolutions(self.desktop)
        self.settings.width, self.settings.height = screenconfig.fit_to_desktop(
            self.settings.size, self.desktop, self.resolutions)
        self.screen = None
        self.apply_display()
        pygame.display.set_icon(assets.image("conquest_icon.png"))
        self.fake = pygame.Surface(DEFAULT_SIZE)
        self.clock = pygame.time.Clock()
        font = assets.font_path("Montserrat-Regular.ttf")
        # small, medium, large, extra large and huge
        self.fonts = [pygame.font.Font(font, size) for size in (12, 20, 32, 52, 72)]
        self.game_menu = gamemenu.GameMenu(self.fonts)
        self.menu_open = False

        self.state = "START"
        self.mouse = (0, 0)                 # always in fake-screen coordinates
        self.region = "main"                # where the mouse is in game: "main" (board), "side" (sidebar) or "bar"
        self.log_view = hud.LogView()
        self.turn_key = None                # (turn, player) last seen, to notice a new turn and flash
        self.flash_started = None
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

    def set_mouse(self, pos):
        """Convert a window position to canvas coordinates (and note which part of the screen it is over)."""
        if self.state == "GAME":
            x, y, self.region = screenconfig.window_to_base_split(
                pos, self.screen.get_size(), DEFAULT_SIZE, hud.panel_x(self.fake))
        else:
            x, y = screenconfig.window_to_base(pos, self.screen.get_size(), DEFAULT_SIZE)
            self.region = "main"
        self.mouse = (x, y)

    def bar_color(self):
        """What fills the window around the canvas: the game's blue in game, the menus' brown elsewhere."""
        return render.BACKGROUND if self.state == "GAME" else menus.BACK_COLOR

    def apply_display(self):
        """(Re)create the window from self.settings. Fullscreen always uses the desktop resolution."""
        if self.settings.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.settings.size, pygame.RESIZABLE)

    def menu_state(self):
        """What the ESC menu needs to know: can the resolution arrows still go anywhere?"""
        windowed = not self.settings.fullscreen
        cur = self.settings.size
        can_prev = windowed and screenconfig.step_resolution(cur, -1, self.resolutions) != cur
        can_next = windowed and screenconfig.step_resolution(cur, 1, self.resolutions) != cur
        return can_prev, can_next

    def apply_menu_action(self, action):
        if action == "resume":
            self.menu_open = False
        elif action == "fullscreen":
            self.settings.fullscreen = not self.settings.fullscreen
            self.apply_display()
        elif action in ("prev", "next"):
            new = screenconfig.step_resolution(self.settings.size, -1 if action == "prev" else 1, self.resolutions)
            self.settings.width, self.settings.height = new
            self.apply_display()
        screenconfig.save(self.settings, SETTINGS_PATH)

    def on_escape(self):
        """In a game, Esc first backs out of a half-finished action (a command waiting for its target).
        With nothing to cancel, or anywhere else, it opens or closes the menu."""
        if self.state == "GAME" and not self.menu_open and self.controller.armed:
            self.controller.cancel()
        else:
            self.toggle_menu()

    def toggle_menu(self):
        self.menu_open = not self.menu_open
        if self.menu_open:
            self.dragging = False
            if self.state == "GAME":
                self.controller.cancel()

    def hover_unit(self):
        if self.state != "GAME" or self.menu_open or self.region != "main":
            return None
        tile = gameboard.tile_at(self.mouse, self.anchor, self.cell, SCALES[self.scale_idx])
        return self.game.unit_at(*tile) if tile else None

    def new_menu(self):
        self.menu = menus.LoadoutMenu(self.fonts, DEFAULT_SIZE)

    def start_game(self):
        # Hot-seat for now: player 2 gets a copy of player 1's squad until online play is hooked up.
        loadouts = [self.menu.loadout, engine.Loadout.from_dict(self.menu.loadout.to_dict())]
        rng = random.Random()
        obstacles = engine.generate_obstacles(rng)
        # Draw the (slow-ish) textured boards *before* the game exists, so nobody's first turn clock is running
        # while we are busy.
        self.boards = [gameboard.create_board(self.cell * s, obstacles) for s in SCALES]
        self.game = engine.Game.new(loadouts, obstacles=obstacles, rng=rng, turn_limit=self.menu.turn_limit)
        self.controller = actions.Controller(self.game)
        self.log_view = hud.LogView()
        self.turn_key = None
        self.flash_started = None
        self.scale_idx = 0
        self.anchor = (0, 0)
        self.state = "GAME"

    # ---- events

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            screenconfig.save(self.settings, SETTINGS_PATH)
            pygame.quit()
            sys.exit(0)
        elif event.type == pygame.VIDEORESIZE:
            # The player dragged the window edge. The canvas just rescales (letterboxed), so all we do is
            # remember the new size for next launch.
            self.screen = pygame.display.get_surface()
            if not self.settings.fullscreen:
                self.settings.width, self.settings.height = self.screen.get_size()
        elif event.type == pygame.MOUSEMOTION:
            self.set_mouse(event.pos)
            if self.log_view.dragging:
                self.log_view.drag(self.mouse, hud.log_box(self.fake), len(self.game.log))
            if self.dragging:
                (mx0, my0), (ax0, ay0) = self.drag_origin
                self.anchor = (ax0 + self.mouse[0] - mx0, ay0 + self.mouse[1] - my0)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.set_mouse(event.pos)
            self.on_mouse_down(event.button)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self.dragging = False
            elif event.button == 1:
                self.log_view.release()
        elif event.type == pygame.MOUSEWHEEL:
            if self.state == "GAME" and not self.menu_open:
                if self.region == "main":
                    self.zoom(event.y)
                elif self.region == "side" and hud.log_box(self.fake).collidepoint(self.mouse):
                    self.log_view.scroll(event.y * LOG_WHEEL_LINES, len(self.game.log))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.on_escape()
            elif self.menu_open:
                pass
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.state == "GAME" and self.game.winner is not None:
                self.state = "START"

    def on_mouse_down(self, button):
        if self.menu_open:                      # the menu swallows every click while it is up
            if button == 1:
                can_prev, can_next = self.menu_state()
                self.apply_menu_action(self.game_menu.handle_click(self.mouse, can_prev, can_next))
            return
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
            elif self.region == "bar":
                return                                      # the empty bars around the game do nothing
            elif button == 2:
                if self.scale_idx > 0 and self.region == "main":
                    self.dragging = True
                    self.drag_origin = (self.mouse, self.anchor)
            elif button == 3:
                self.controller.cancel()
            elif button == 1:
                if self.region == "side":
                    if not self.log_view.press(self.mouse, hud.log_box(self.fake), len(self.game.log)):
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
                     self.controller.message, pygame.time.get_ticks() / 1000.0, self.log_view)
            if self.game.winner is not None:
                render.draw_winner(self.fake, self.fonts, self.game.winner)
            elif self.flash_started is not None:
                progress = (pygame.time.get_ticks() / 1000.0 - self.flash_started) / render.FLASH_SECONDS
                if progress < 1.0:
                    render.draw_turn_flash(self.fake, self.fonts, self.game.current, self.game.turn_number, progress)
                else:
                    self.flash_started = None
        if self.menu_open:
            can_prev, can_next = self.menu_state()
            self.game_menu.draw(self.fake, self.mouse, self.settings, can_prev, can_next)
        render.present(self.fake, self.screen, self.bar_color(),
                       hud.panel_x(self.fake) if self.state == "GAME" else None)

    def update(self, dt):
        """Advance the turn clock by one frame. It stands still while the menu is open."""
        if self.state != "GAME" or self.game.winner is not None:
            return
        key = (self.game.turn_number, self.game.current)
        if key != self.turn_key:                    # a new player's turn: flash across the screen
            self.turn_key = key
            self.flash_started = pygame.time.get_ticks() / 1000.0
        if self.menu_open or dt > STALL_SECONDS:   # a menu, or a stalled frame (dragging the window...): not the player's fault
            self.game.pause_for(dt)
        elif self.game.tick():                  # time ran out: the turn changed hands underneath the player
            self.controller.cancel()

    def run(self):
        dt = 0.0
        while True:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            dt = self.clock.tick(FPS) / 1000.0


if __name__ == "__main__":
    pygame.init()
    App().run()

# The ESC menu: a fullscreen checkbox and a resolution picker. It is drawn on the fixed 1920x1080
# canvas like everything else, so it scales with the window automatically.
#
# handle_click() only reports *what* was clicked ("fullscreen", "prev", "next", "resume");
# main.App decides what that means for the real window.
import pygame

import screenconfig
from menus import BACK_COLOR, LIGHT_BROWN, MAIN_TAB, WHITE

DISABLED = (110, 110, 110)


class GameMenu:
    def __init__(self, fonts, base_size=screenconfig.BASE_SIZE):
        self.fonts = fonts
        w, h = base_size
        self.panel = pygame.Rect(w // 2 - 360, h // 2 - 250, 720, 500)
        left, top = self.panel.x + 50, self.panel.y
        self.title_pos = (self.panel.x + 50, top + 30)
        self.check_rect = pygame.Rect(left, top + 140, 44, 44)
        self.check_label_pos = (left + 64, top + 140 + (44 - fonts[2].get_height()) // 2)
        label_w = fonts[2].size("Fullscreen")[0]
        self.fullscreen_hit = pygame.Rect(left, top + 130, 64 + label_w, 64)
        self.res_label_pos = (left, top + 230)
        self.prev_rect = pygame.Rect(left, top + 285, 60, 56)
        self.value_rect = pygame.Rect(left + 80, top + 285, 360, 56)
        self.next_rect = pygame.Rect(left + 460, top + 285, 60, 56)
        self.resume_rect = pygame.Rect(self.panel.centerx - 150, self.panel.bottom - 100, 300, 64)

    def handle_click(self, pos, can_prev, can_next):
        """Returns "fullscreen", "prev", "next", "resume" or None."""
        if self.fullscreen_hit.collidepoint(pos):
            return "fullscreen"
        if can_prev and self.prev_rect.collidepoint(pos):
            return "prev"
        if can_next and self.next_rect.collidepoint(pos):
            return "next"
        if self.resume_rect.collidepoint(pos):
            return "resume"
        return None

    def draw(self, screen, mouse_pos, settings, can_prev, can_next):
        fonts = self.fonts
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 150))
        screen.blit(shade, (0, 0))
        pygame.draw.rect(screen, MAIN_TAB, self.panel)
        pygame.draw.rect(screen, WHITE, self.panel, width=2)
        screen.blit(fonts[3].render("Menu", True, LIGHT_BROWN), self.title_pos)

        # fullscreen checkbox
        hot = self.fullscreen_hit.collidepoint(mouse_pos)
        color = LIGHT_BROWN if hot else WHITE
        pygame.draw.rect(screen, color, self.check_rect, width=3)
        if settings.fullscreen:
            r = self.check_rect
            pygame.draw.line(screen, color, (r.x + 9, r.y + 23), (r.x + 18, r.y + 33), width=5)
            pygame.draw.line(screen, color, (r.x + 18, r.y + 33), (r.x + 36, r.y + 10), width=5)
        screen.blit(fonts[2].render("Fullscreen", True, color), self.check_label_pos)

        # resolution picker (greyed out while fullscreen: fullscreen always uses the desktop resolution)
        windowed = not settings.fullscreen
        screen.blit(fonts[2].render("Window resolution", True, WHITE if windowed else DISABLED), self.res_label_pos)
        for rect, text, enabled in ((self.prev_rect, "<", can_prev), (self.next_rect, ">", can_next)):
            color = DISABLED if not enabled else (LIGHT_BROWN if rect.collidepoint(mouse_pos) else WHITE)
            pygame.draw.rect(screen, color, rect, width=2)
            glyph = fonts[2].render(text, True, color)
            screen.blit(glyph, (rect.centerx - glyph.get_width() // 2, rect.centery - glyph.get_height() // 2))
        value = "%d x %d" % settings.size if windowed else "Desktop resolution"
        pygame.draw.rect(screen, WHITE if windowed else DISABLED, self.value_rect, width=2)
        text = fonts[2].render(value, True, WHITE if windowed else DISABLED)
        screen.blit(text, (self.value_rect.centerx - text.get_width() // 2,
                           self.value_rect.centery - text.get_height() // 2))

        # resume
        color = LIGHT_BROWN if self.resume_rect.collidepoint(mouse_pos) else WHITE
        pygame.draw.rect(screen, color, self.resume_rect, width=2)
        text = fonts[2].render("Resume  (Esc)", True, color)
        screen.blit(text, (self.resume_rect.centerx - text.get_width() // 2,
                           self.resume_rect.centery - text.get_height() // 2))

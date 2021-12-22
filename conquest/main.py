# Runs game window
import pygame
import sys
import os
import ctypes

import actions
import render
import gameboard


"""
states:
    WAITING = 1
    START = 2
    TROOP_LOADOUT = 3
    COMMAND_LOADOUT = 4
    GAME = 5
    END_GAME = 6
"""

"""Init pygame modules"""
pygame.display.init()
pygame.font.init()

"""Set-up Code"""
screen_width = 1280  # 1280
screen_height = 720  # 720
default_screen_size = (screen_width, screen_height)
pygame.display.set_caption('Conquest')
icon = pygame.image.load(os.getcwd() + '/images/conquest_icon.png')
font = os.getcwd() + '/fonts/Montserrat-Regular.ttf'
pygame.display.set_icon(icon)
# Weird Stack overflow hack for setting taskbar icon on windows
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Any String Will Do")
screen = pygame.display.set_mode(default_screen_size, pygame.RESIZABLE)
fake_screen = screen.copy()
board = gameboard.create_board(fake_screen)
scale_idx = 0
scales = [1, 2, 4]
anchor = (0, 0)
state = "TROOP_LOADOUT"
# Small, Medium, and Large font sizes
fonts = [pygame.font.Font(font, 12), pygame.font.Font(font, 32), pygame.font.Font(font, 52), pygame.font.Font(font, 72)]
pygame.init()
clock = pygame.time.Clock()

"""Loop"""
while True:
    clock.tick(60)
    # Should keep anchor memory but let board snap into place if moved beyond limits
    anchor = gameboard.saturate_anchor(anchor, fake_screen, scale_idx, scales)
    state = render.update_interface(state, fake_screen, screen, board, anchor, fonts)

    for event in pygame.event.get():
        # Grab mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            buttons = pygame.mouse.get_pressed(num_buttons=5)
            if buttons[0]:  # Left Click
                print("Mouse Clicked")
                pos = pygame.mouse.get_pos()
                actions.check_user_click(fake_screen, pos, board)
            elif buttons[2]:  # Right Click
                print("Right Clicked")
                pos = pygame.mouse.get_pos()
                actions.check_user_click(fake_screen, pos, board)
            elif buttons[1]:  # Middle mouse button
                print("Scroll Wheel Clicked")
                if state == "GAME":
                    if scale_idx == 0:  # Don't even bother doing the calcs
                        continue
                    temp_board = board.copy()
                    mxi, myi = pygame.mouse.get_pos()
                    anchorxi, anchoryi = anchor[0], anchor[1]
                    held = True
                    while held:
                        mx, my = pygame.mouse.get_pos()
                        anchor = ((mx-mxi)+anchorxi, (my-myi)+anchoryi)
                        state = render.update_interface(state, fake_screen, screen, board, anchor, fonts)
                        for interrupt_event in pygame.event.get():
                            if interrupt_event.type == pygame.MOUSEBUTTONUP:
                                held = False
        elif event.type == pygame.MOUSEWHEEL:  # Middle mouse button scroll
            print("Mouse Scrolled")
            if state == "GAME":
                # If scrolling in
                if event.y == 1 and scale_idx < 2:
                    old_rect = board.get_rect()
                    board = pygame.transform.scale(board, (old_rect[2]*2, old_rect[3]*2))
                    anchor = (anchor[0]*2, anchor[1]*2)
                    scale_idx += 1
                elif event.y == -1 and scale_idx > 0:
                    old_rect = board.get_rect()
                    board = pygame.transform.scale(board, (old_rect[2]*0.5, old_rect[3]*0.5))
                    anchor = (anchor[0]*0.5, anchor[1]*0.5)
                    scale_idx -= 1
        # Grab exit X events
        elif event.type == pygame.QUIT:
            print("Quitting")
            pygame.quit()
            sys.exit(0)
        # Grab key presses
        elif event.type == pygame.KEYDOWN:
            # Esc
            if event.key == pygame.K_ESCAPE:
                print("Esc pressed")
        # Grab min/max window events
        elif event.type == pygame.VIDEORESIZE:
            print("Resizing...")
            """
            screen_content = screen
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            screen.blit(screen_content, (0, 0))
            del screen_content
            """
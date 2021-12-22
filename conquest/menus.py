# Contains info for menus in the game
import pygame

import render


def troops_menu(screen, fonts, real_screen):
    state = "TROOP_LOADOUT"
    # Just defining some numbers
    light_brown = (156, 118, 58)
    dark_brown = (59, 40, 12)
    back_color = (48, 32, 10)
    border = 10
    between = 50
    x_rat = screen.get_width() / real_screen.get_width()
    y_rat = screen.get_height() / real_screen.get_height()
    # Render the font surfaces and get their rectangles
    troops = fonts[2].render("Select Troops", 1, light_brown, back_color)
    commands = fonts[2].render("Select Commands", 1, dark_brown, back_color)
    troops_size = fonts[2].size("Select Troops")
    commands_size = fonts[2].size("Select Commands")
    troops_rect = pygame.rect.Rect(border, border, troops_size[0], troops_size[1])
    commands_rect = pygame.rect.Rect(troops_size[0] + between, border, commands_size[0], commands_size[1])

    # Check collisions with commands "button"
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    if commands_rect.collidepoint(scaled_pos):
        commands = fonts[2].render("Select Commands", 1, light_brown, back_color)

        # Check if it gets clicked
        if pygame.mouse.get_pressed(num_buttons=5)[0]:
            # Wait for the release
            while pygame.mouse.get_pressed(num_buttons=5)[0]:
                for event in pygame.event.get():
                    mouse_pos = pygame.mouse.get_pos()
                    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                    if event.type == pygame.MOUSEBUTTONUP and commands_rect.collidepoint(scaled_pos):
                        state = "COMMAND_LOADOUT"

    render.draw_background(screen, back_color)
    screen.blit(troops, (troops_rect[0], troops_rect[1]))
    screen.blit(commands, (commands_rect[0], commands_rect[1]))

    return state


def commands_menu(screen, fonts, real_screen):
    state = "COMMAND_LOADOUT"
    # Just defining some numbers
    light_brown = (156, 118, 58)
    dark_brown = (59, 40, 12)
    back_color = (48, 32, 10)
    border = 10
    between = 50
    x_rat = screen.get_width() / real_screen.get_width()
    y_rat = screen.get_height() / real_screen.get_height()
    # Render the font surfaces and get their rectangles
    troops = fonts[2].render("Select Troops", 1, dark_brown, back_color)
    commands = fonts[2].render("Select Commands", 1, light_brown, back_color)
    troops_size = fonts[2].size("Select Troops")
    commands_size = fonts[2].size("Select Commands")
    troops_rect = pygame.rect.Rect(border, border, troops_size[0], troops_size[1])
    commands_rect = pygame.rect.Rect(troops_size[0] + between, border, commands_size[0], commands_size[1])

    # Check collisions with commands "button"
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    if troops_rect.collidepoint(scaled_pos):
        troops = fonts[2].render("Select Troops", 1, light_brown, back_color)
        # Check if it gets clicked
        if pygame.mouse.get_pressed(num_buttons=5)[0]:
            # Wait for the release
            while pygame.mouse.get_pressed(num_buttons=5)[0]:
                for event in pygame.event.get():
                    mouse_pos = pygame.mouse.get_pos()
                    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                    if event.type == pygame.MOUSEBUTTONUP and troops_rect.collidepoint(scaled_pos):
                        state = "TROOP_LOADOUT"

    render.draw_background(screen, back_color)
    screen.blit(troops, (troops_rect[0], troops_rect[1]))
    screen.blit(commands, (commands_rect[0], commands_rect[1]))

    return state


def actions_menu(screen):
    # Take up right 20% and top half
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    x = screen_width*0.8
    y = 0
    width = screen_width*0.2
    height = screen_height*0.5
    line_width = 2
    pygame.draw.rect(screen, (3, 13, 46), (x, y, width, height))
    pygame.draw.line(screen, (255, 255, 255), (x-line_width, y), (x-line_width, y+height), width=line_width)


def details_menu(screen):
    # Take up right 20% and bottom half
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    x = screen_width*0.8
    y = screen_height*0.5
    width = screen_width*0.2
    height = screen_height*0.5
    line_width = 2
    # Average color of two square colors
    pygame.draw.rect(screen, (108, 79, 35), (x, y, width, height))
    pygame.draw.line(screen, (255, 255, 255), (x - line_width, y), (x - line_width, y+height), width=line_width)

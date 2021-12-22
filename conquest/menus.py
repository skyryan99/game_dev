# Contains info for menus in the game
import pygame

import render

resource_val = 1000


def troops_menu(screen, fonts, real_screen):
    state = "TROOP_LOADOUT"
    # Just defining some numbers
    global resource_val
    light_brown = (156, 118, 58)
    dark_brown = (59, 40, 12)
    back_color = (89, 60, 20)
    main_tab_color = (48, 32, 10)
    sec_tab_color = (31, 21, 7)
    border = 20
    padding = 10
    between = 50
    x_rat = screen.get_width() / real_screen.get_width()
    y_rat = screen.get_height() / real_screen.get_height()

    # Render the font surfaces and get their rectangles
    troops = fonts[2].render("Select Troops", 1, light_brown, main_tab_color)
    commands = fonts[2].render("Select Commands", 1, dark_brown, sec_tab_color)
    resources = fonts[1].render(f"Squad Gold: {resource_val}", 1, light_brown)

    troops_size = fonts[2].size("Select Troops")
    commands_size = fonts[2].size("Select Commands")
    resources_size = fonts[1].size("Squad Gold: 1000")

    troops_rect = pygame.rect.Rect(border, border, troops_size[0], troops_size[1])
    commands_rect = pygame.rect.Rect(troops_size[0] + between, border, commands_size[0], commands_size[1])
    resource_rect = pygame.rect.Rect(commands_rect[0] + commands_size[0] + between,
                                     1.5*border, resources_size[0], resources_size[1])

    troops_tab = pygame.rect.Rect(troops_rect[0] - padding, troops_rect[1] - padding,
                                  troops_rect[2] + 2*padding, troops_rect[3] + 2*padding)
    commands_tab = pygame.rect.Rect(commands_rect[0] - padding, commands_rect[1] - padding,
                                    commands_rect[2] + 2*padding, commands_rect[3] + 2*padding)
    selection_rect = pygame.rect.Rect(troops_tab[0], troops_tab[1] + troops_tab[3], screen.get_width() - border,
                                      screen.get_height() - border - troops_tab[1] - troops_tab[3] + padding)
    # Check collisions with commands "button"
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    if commands_rect.collidepoint(scaled_pos):
        commands = fonts[2].render("Select Commands", 1, light_brown, sec_tab_color)

        # Check if it gets clicked
        if pygame.mouse.get_pressed(num_buttons=5)[0]:
            # Wait for the release
            while pygame.mouse.get_pressed(num_buttons=5)[0]:
                for event in pygame.event.get():
                    mouse_pos = pygame.mouse.get_pos()
                    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                    if event.type == pygame.MOUSEBUTTONUP and commands_rect.collidepoint(scaled_pos):
                        resource_val -= 10  # Just to test the functionality
                        state = "COMMAND_LOADOUT"

    # Draw stuff
    render.draw_background(screen, back_color)  # The background
    screen.fill(main_tab_color, troops_tab)  # The background to the commands tab
    screen.fill(sec_tab_color, commands_tab)  # The background to the commands tab
    screen.fill(main_tab_color, selection_rect)  # The selection area for the troops
    screen.blit(troops, (troops_rect[0], troops_rect[1]))  # The Troops button at the top
    screen.blit(commands, (commands_rect[0], commands_rect[1]))  # The commands button at the top
    screen.blit(resources, (resource_rect[0], resource_rect[1]))  # The resource counter at the top

    return state


def commands_menu(screen, fonts, real_screen):
    state = "COMMAND_LOADOUT"
    # Just defining some numbers
    global resource_val
    light_brown = (156, 118, 58)
    dark_brown = (59, 40, 12)
    back_color = (89, 60, 20)
    main_tab_color = (48, 32, 10)
    sec_tab_color = (31, 21, 7)
    border = 20
    padding = 10
    between = 50
    x_rat = screen.get_width() / real_screen.get_width()
    y_rat = screen.get_height() / real_screen.get_height()

    # Render the font surfaces and get their rectangles
    troops = fonts[2].render("Select Troops", 1, dark_brown, sec_tab_color)
    commands = fonts[2].render("Select Commands", 1, light_brown, main_tab_color)
    resources = fonts[1].render(f"Squad Gold: {resource_val}", 1, light_brown)

    troops_size = fonts[2].size("Select Troops")
    commands_size = fonts[2].size("Select Commands")
    resources_size = fonts[1].size("Squad Gold: 1000")

    troops_rect = pygame.rect.Rect(border, border, troops_size[0], troops_size[1])
    commands_rect = pygame.rect.Rect(troops_size[0] + between, border, commands_size[0], commands_size[1])
    resource_rect = pygame.rect.Rect(commands_rect[0] + commands_size[0] + between,
                                     1.5*border, resources_size[0], resources_size[1])

    troops_tab = pygame.rect.Rect(troops_rect[0] - padding, troops_rect[1] - padding,
                                  troops_rect[2] + 2*padding, troops_rect[3] + 2*padding)
    commands_tab = pygame.rect.Rect(commands_rect[0] - padding, commands_rect[1] - padding,
                                    commands_rect[2] + 2*padding, commands_rect[3] + 2*padding)
    selection_rect = pygame.rect.Rect(troops_tab[0], troops_tab[1] + troops_tab[3], screen.get_width() - border,
                                      screen.get_height() - border - troops_tab[1] - troops_tab[3] + padding)

    # Check collisions with commands "button"
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    if troops_rect.collidepoint(scaled_pos):
        troops = fonts[2].render("Select Troops", 1, light_brown, sec_tab_color)
        # Check if it gets clicked
        if pygame.mouse.get_pressed(num_buttons=5)[0]:
            # Wait for the release
            while pygame.mouse.get_pressed(num_buttons=5)[0]:
                for event in pygame.event.get():
                    mouse_pos = pygame.mouse.get_pos()
                    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                    if event.type == pygame.MOUSEBUTTONUP and troops_rect.collidepoint(scaled_pos):
                        resource_val -= 10  # Just to test the functionality
                        state = "TROOP_LOADOUT"

    render.draw_background(screen, back_color)  # The background
    screen.fill(sec_tab_color, troops_tab)  # The background to the troops tab
    screen.fill(main_tab_color, commands_tab)  # The background to the commands tab
    screen.fill(main_tab_color, selection_rect)  # The selection area for the troops
    screen.blit(troops, (troops_rect[0], troops_rect[1]))  # The text for troops button
    screen.blit(commands, (commands_rect[0], commands_rect[1]))  # The text for commands button
    screen.blit(resources, (resource_rect[0], resource_rect[1]))  # The resource value

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

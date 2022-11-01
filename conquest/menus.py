# Contains info for menus in the game
import pygame
import entities
import render

resource_val = 1000
selected_troops = []
selected_commands = []


class Button:
    def __init__(self, row, col, width, height, spacing, entity_type):
        border_width = 2
        outer_x = (width + spacing)*col + spacing
        outer_y = (height + spacing)*row + spacing + 85
        self.outer_border = pygame.Rect(outer_x, outer_y, width, height)
        self.inner_border = pygame.Rect(outer_x + border_width, outer_y + border_width, width - 2*border_width,
                                        height - 2*border_width)
        self.entity = entity_type
        self.img_top_left = (outer_x + 3*border_width, outer_y + 3*border_width)
        self.name_top_left = (outer_x + 3*border_width + 32*5, outer_y + 3*border_width)
        self.cost_top_left = (outer_x + 3*border_width, outer_y + 4*border_width + 32*4)
        self.stats_top_left = (outer_x + 3*border_width + 32*5, outer_y + 4*border_width + 32*2)


def troops_menu(screen, fonts, real_screen):
    state = "TROOP_LOADOUT"
    # Just defining some numbers
    global resource_val
    global selected_troops
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
    troops = fonts[3].render("Select Troops", 1, light_brown, main_tab_color)
    commands = fonts[3].render("Select Commands", 1, dark_brown, sec_tab_color)
    resources = fonts[2].render(f"Squad Gold: {resource_val}", 1, light_brown)
    troop_count = fonts[4].render(f"Troops: {len(selected_troops)}/10", 1, (255, 255, 255))

    troops_size = fonts[3].size("Select Troops")
    commands_size = fonts[3].size("Select Commands")
    resources_size = fonts[2].size("Squad Gold: 1000")

    troops_rect = pygame.rect.Rect(border, border, troops_size[0], troops_size[1])
    commands_rect = pygame.rect.Rect(troops_size[0] + between, border, commands_size[0], commands_size[1])
    resource_rect = pygame.rect.Rect(commands_rect[0] + commands_size[0] + between,
                                     1.5*border, resources_size[0], resources_size[1])
    troop_count_rect = pygame.rect.Rect(resource_rect[0] - 240, screen.get_height() - 200,
                                        resource_rect[2], resource_rect[3])

    # Tabs at the top of the menu
    troops_tab = pygame.rect.Rect(troops_rect[0] - padding, troops_rect[1] - padding,
                                  troops_rect[2] + 2*padding, troops_rect[3] + 2*padding)
    commands_tab = pygame.rect.Rect(commands_rect[0] - padding, commands_rect[1] - padding,
                                    commands_rect[2] + 2*padding, commands_rect[3] + 2*padding)
    selection_rect = pygame.rect.Rect(troops_tab[0], troops_tab[1] + troops_tab[3], screen.get_width() - border,
                                      screen.get_height() - border - troops_tab[1] - troops_tab[3] + padding)

    # Buttons for troops
    buttons = [0, 1, 2, 3, 4, 5, 6]
    troop_type = [entities.Scout(), entities.FootSoldier(), entities.Halberdier(), entities.Archer(), entities.Mage(),
                  entities.Knight(), entities.Champion()]
    width = 550
    height = 200
    spacing = 40
    highlight_color = light_brown
    nonhighlighted_color = (255, 255, 255)
    color = (255, 255, 255)

    for row in [0, 1, 2, 3]:
        for col in [0, 1]:
            if col == 1 and row == 3:
                continue
            else:
                buttons[col * 4 + row] = Button(row, col, width, height, spacing, troop_type[col * 4 + row])

    selected_troops_bar_outer = pygame.Rect(1330, 125, width, (height + spacing)*4 - 40)
    selected_troops_bar_inner = pygame.Rect(1335, 130, width - 10, (height + spacing)*4 - 50)

    # Check collisions with commands "button"
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    if commands_tab.collidepoint(scaled_pos):
        commands = fonts[3].render("Select Commands", 1, light_brown, sec_tab_color)

        # Check if it gets clicked
        if pygame.mouse.get_pressed(num_buttons=5)[0]:
            # Wait for the release
            while pygame.mouse.get_pressed(num_buttons=5)[0]:
                for event in pygame.event.get():
                    mouse_pos = pygame.mouse.get_pos()
                    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                    if event.type == pygame.MOUSEBUTTONUP and commands_tab.collidepoint(scaled_pos):
                        state = "COMMAND_LOADOUT"

    # Draw stuff
    render.draw_background(screen, back_color)  # The background
    screen.fill(main_tab_color, troops_tab)  # The background to the commands tab
    screen.fill(sec_tab_color, commands_tab)  # The background to the commands tab
    screen.fill(main_tab_color, selection_rect)  # The selection area for the troops
    screen.blit(troops, (troops_rect[0], troops_rect[1]))  # The Troops button at the top
    screen.blit(commands, (commands_rect[0], commands_rect[1]))  # The commands button at the top
    screen.blit(resources, (resource_rect[0], resource_rect[1]))  # The resource counter at the top
    screen.blit(troop_count, (troop_count_rect[0], troop_count_rect[1]))  # The troops counter
    # This stuff goes on top of the other stuff so draw it after
    # Check collisions with troop buttons
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    button_hover = -1
    for i, button in enumerate(buttons):
        if button.outer_border.collidepoint(scaled_pos):
            button_hover = i

            # Check if it gets clicked
            if pygame.mouse.get_pressed(num_buttons=5)[0]:
                # Wait for the release
                while pygame.mouse.get_pressed(num_buttons=5)[0]:
                    for event in pygame.event.get():
                        mouse_pos = pygame.mouse.get_pos()
                        scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                        if event.type == pygame.MOUSEBUTTONUP and button.outer_border.collidepoint(scaled_pos):
                            if resource_val >= button.entity.cost and len(selected_troops) < 10:
                                resource_val -= button.entity.cost  # Pay for it
                                selected_troops.append(button.entity)  # Add it to the sidebar

    # Draw the buttons (sometimes highlighted)
    for i, button in enumerate(buttons):
        color = nonhighlighted_color
        if i == button_hover:
            color = highlight_color
        pygame.draw.rect(screen, color, button.outer_border)
        pygame.draw.rect(screen, (0, 0, 0), button.inner_border)
        name = fonts[2].render(button.entity.name, 1, color, (0, 0, 0))
        cost = fonts[2].render("Cost: " + str(button.entity.cost), 1, color, (0, 0, 0))
        pygame.draw.line(screen, color, (button.name_top_left[0], button.name_top_left[1] + 50),
                         (button.name_top_left[0] + 300, button.name_top_left[1] + 50))
        stats_size = fonts[1].size("STAT HEIGHT")
        # Stats listed on button
        movement = fonts[1].render("Movement: " + str(button.entity.speed), 1, color, (0, 0, 0))
        damage = fonts[1].render("Damage: " + str(button.entity.damage), 1, color, (0, 0, 0))
        health = fonts[1].render("Health: " + str(button.entity.max_health), 1, color, (0, 0, 0))
        atk_range = fonts[1].render("Range: " + str(button.entity.range), 1, color, (0, 0, 0))
        stats = [movement, damage, health, atk_range]

        screen.blit(name, button.name_top_left)
        screen.blit(cost, button.cost_top_left)
        for j, stat in enumerate(stats):
            screen.blit(stat, (button.stats_top_left[0], button.stats_top_left[1] + j*stats_size[1]))
        # Draw the stuff inside the button
        image = pygame.transform.scale(button.entity.image, (32*4, 32*4))
        screen.blit(image, button.img_top_left)

    # Draw the "troops selected" side bar
    pygame.draw.rect(screen, (255, 255, 255), selected_troops_bar_outer)
    pygame.draw.rect(screen, (0, 0, 0), selected_troops_bar_inner)
    # Now check for mouse clicks over the "troops selected" side bar to initiate a "sell back" prompt
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    for i, troop in enumerate(selected_troops):
        color = nonhighlighted_color
        baseline = 90*i
        rect = pygame.rect.Rect(selected_troops_bar_inner[0], selected_troops_bar_inner[1] + baseline,
                                selected_troops_bar_inner[2], 90)
        if rect.collidepoint(scaled_pos):
            color = highlight_color

            # Check if it gets clicked
            if pygame.mouse.get_pressed(num_buttons=5)[0]:
                # Wait for the release
                while pygame.mouse.get_pressed(num_buttons=5)[0]:
                    for event in pygame.event.get():
                        mouse_pos = pygame.mouse.get_pos()
                        scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                        if event.type == pygame.MOUSEBUTTONUP and rect.collidepoint(scaled_pos):
                            resource_val += troop.cost  # Pay for it
                            selected_troops = selected_troops[:i] + selected_troops[i + 1:]

        image = pygame.transform.scale(troop.image, (32*2, 32*2))
        movement = fonts[0].render("Movement: " + str(troop.speed), 1, color, (0, 0, 0))
        damage = fonts[0].render("Damage: " + str(troop.damage), 1, color, (0, 0, 0))
        health = fonts[0].render("Health: " + str(troop.max_health), 1, color, (0, 0, 0))
        atk_range = fonts[0].render("Range: " + str(troop.range), 1, color, (0, 0, 0))
        stats = [movement, damage, health, atk_range]
        name = fonts[1].render(troop.name, 1, color, (0, 0, 0))
        cost = fonts[1].render("Cost: " + str(troop.cost), 1, color, (0, 0, 0))
        screen.blit(name, (selected_troops_bar_inner[0] + 32*4, baseline + selected_troops_bar_inner[1] + 10))
        screen.blit(cost, (selected_troops_bar_inner[0] + 32*10, baseline + selected_troops_bar_inner[1] + 10))
        for j, stat in enumerate(stats):
            screen.blit(stat, (selected_troops_bar_inner[0] + 32*4 + j*100,
                        baseline + selected_troops_bar_inner[1] + 50))
        screen.blit(image, (selected_troops_bar_inner[0] + 25, baseline + selected_troops_bar_inner[1] + 15))

    return state


def commands_menu(screen, fonts, real_screen):
    state = "COMMAND_LOADOUT"
    # Just defining some numbers
    global resource_val
    global selected_commands
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
    troops = fonts[3].render("Select Troops", 1, dark_brown, sec_tab_color)
    commands = fonts[3].render("Select Commands", 1, light_brown, main_tab_color)
    resources = fonts[2].render(f"Squad Gold: {resource_val}", 1, light_brown)
    command_count = fonts[2].render(f"Commands: {len(selected_commands)}/4", 1, (255, 255, 255))

    troops_size = fonts[3].size("Select Troops")
    commands_size = fonts[3].size("Select Commands")
    resources_size = fonts[2].size("Squad Gold: 1000")

    troops_rect = pygame.rect.Rect(border, border, troops_size[0], troops_size[1])
    commands_rect = pygame.rect.Rect(troops_size[0] + between, border, commands_size[0], commands_size[1])
    resource_rect = pygame.rect.Rect(commands_rect[0] + commands_size[0] + between,
                                     1.5*border, resources_size[0], resources_size[1])
    command_count_rect = pygame.rect.Rect(1, 1, 1, 1)

    troops_tab = pygame.rect.Rect(troops_rect[0] - padding, troops_rect[1] - padding,
                                  troops_rect[2] + 2*padding, troops_rect[3] + 2*padding)
    commands_tab = pygame.rect.Rect(commands_rect[0] - padding, commands_rect[1] - padding,
                                    commands_rect[2] + 2*padding, commands_rect[3] + 2*padding)
    selection_rect = pygame.rect.Rect(troops_tab[0], troops_tab[1] + troops_tab[3], screen.get_width() - border,
                                      screen.get_height() - border - troops_tab[1] - troops_tab[3] + padding)

    # Buttons for commands
    buttons = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    troop_type = [entities.BattleCry(), entities.Bombard(), entities.Charge(), entities.Chastise(),
                  entities.Regenerate(), entities.ShieldWall(), entities.Stoicism(), entities.Vigilance(),
                  entities.WindsOfFate()]
    width = 800
    height = 170
    spacing = 20
    highlight_color = light_brown
    nonhighlighted_color = (255, 255, 255)
    color = (255, 255, 255)

    for row in [0, 1, 2, 3, 4]:
        for col in [0, 1]:
            if col == 1 and row == 4:
                continue
            else:
                buttons[col + 2 * row] = Button(row, col, width, height, spacing, troop_type[col + 2 * row])

    selected_commands_bar_outer = pygame.Rect(1330, 125, width, (height + spacing)*4 - 40)
    selected_commands_bar_inner = pygame.Rect(1335, 130, width - 10, (height + spacing)*4 - 50)

    # Check collisions with commands "button"
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    if troops_tab.collidepoint(scaled_pos):
        troops = fonts[3].render("Select Troops", 1, light_brown, sec_tab_color)
        # Check if it gets clicked
        if pygame.mouse.get_pressed(num_buttons=5)[0]:
            # Wait for the release
            while pygame.mouse.get_pressed(num_buttons=5)[0]:
                for event in pygame.event.get():
                    mouse_pos = pygame.mouse.get_pos()
                    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                    if event.type == pygame.MOUSEBUTTONUP and troops_tab.collidepoint(scaled_pos):
                        state = "TROOP_LOADOUT"

    render.draw_background(screen, back_color)  # The background
    screen.fill(sec_tab_color, troops_tab)  # The background to the troops tab
    screen.fill(main_tab_color, commands_tab)  # The background to the commands tab
    screen.fill(main_tab_color, selection_rect)  # The selection area for the troops
    screen.blit(troops, (troops_rect[0], troops_rect[1]))  # The text for troops button
    screen.blit(commands, (commands_rect[0], commands_rect[1]))  # The text for commands button
    screen.blit(resources, (resource_rect[0], resource_rect[1]))  # The resource value
    screen.blit(command_count, (command_count_rect[0], command_count_rect[1]))  # The troops counter
    # This stuff goes on top of the other stuff so draw it after
    # Check collisions with command buttons
    mouse_pos = pygame.mouse.get_pos()
    scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
    button_hover = -1
    for i, button in enumerate(buttons):
        if button.outer_border.collidepoint(scaled_pos):
            button_hover = i

            # Check if it gets clicked
            if pygame.mouse.get_pressed(num_buttons=5)[0]:
                # Wait for the release
                while pygame.mouse.get_pressed(num_buttons=5)[0]:
                    for event in pygame.event.get():
                        mouse_pos = pygame.mouse.get_pos()
                        scaled_pos = (mouse_pos[0] * x_rat, mouse_pos[1] * y_rat)
                        if event.type == pygame.MOUSEBUTTONUP and button.outer_border.collidepoint(scaled_pos):
                            if len(selected_commands) < 4:
                                selected_commands.append(button.entity)  # Add it to the sidebar

    # Draw the buttons (sometimes highlighted)
    for i, button in enumerate(buttons):
        color = nonhighlighted_color
        if i == button_hover:
            color = highlight_color
        pygame.draw.rect(screen, color, button.outer_border)
        pygame.draw.rect(screen, (0, 0, 0), button.inner_border)
        name = fonts[2].render(button.entity.name, 1, color, (0, 0, 0))
        cooldown = fonts[2].render("Cooldown: " + str(button.entity.cooldown), 1, color, (0, 0, 0))
        pygame.draw.line(screen, color, (button.name_top_left[0], button.name_top_left[1] + 50),
                         (button.name_top_left[0] + 300, button.name_top_left[1] + 50))

        screen.blit(name, button.name_top_left)
        screen.blit(cooldown, button.cost_top_left)

        # Draw the stuff inside the button
        image = pygame.transform.scale(button.entity.image, (32 * 2, 32 * 2))
        screen.blit(image, button.img_top_left)

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

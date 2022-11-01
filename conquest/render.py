# Draws all objects
import pygame
import menus


def draw_background(screen, color):
    screen.fill(color)


def draw_board(screen, board, anchor):
    rect = board.get_rect()
    screen.blit(board, (anchor[0], anchor[1], rect[2], rect[3]))


def draw_entities(screen, entities, cell_size, anchor, scale):
    for entity in entities:
        x = anchor[0] + scale * (entity.row * cell_size + 10)
        y = anchor[1] + scale * (entity.col * cell_size + 10)
        image = pygame.transform.scale(entity.image, (32*scale, 32*scale))
        screen.blit(image, (x, y))


def update_interface(state, fake_screen, screen, board, anchor, fonts, troops, cell_size, scale):
    color = (3, 13, 46)  # Navy blue
    if state == "WAITING":  # Waiting for another client to connect to server
        pass
    elif state == "START":  # Clients are connected and ready to play, players must ready up
        pass
    elif state == "TROOP_LOADOUT":  # Timer starts here, players select troops
        state = menus.troops_menu(fake_screen, fonts, screen)
    elif state == "COMMAND_LOADOUT":  # Players select commands
        state = menus.commands_menu(fake_screen, fonts, screen)
    elif state == "GAME":  # The main stuff. The game itself
        draw_background(fake_screen, color)
        draw_board(fake_screen, board, anchor)
        draw_entities(fake_screen, troops, cell_size, anchor, scale)
        # Draw menus on top of board
        menus.actions_menu(fake_screen)
        menus.details_menu(fake_screen)
    elif state == "ENDGAME":  # game is over, will route to an endgame menu
        pass

    # Always called last to update the entire display
    screen.blit(pygame.transform.scale(fake_screen, screen.get_rect().size), (0, 0))
    pygame.display.update()
    return state

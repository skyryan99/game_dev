# For all things clicklable in a text adventure game
import pygame
import os
import sys


def create_button(screen, text, row_num, font_type, italic=False):
    """
    row_num:
        standard screen has 4 slots for buttons. row_num specifies where the button will be placed. Ex:
        0
        1
        2
        3

    font_type:
        Black, Bold, ExtraBold, ExtraLight, Light, Medium, SemiBold, Thin, Regular

    button_size:
        Size of the button. Just to make it easy to change later
    """

    padding = 15  # pixels of padding around each button
    button_section_height = screen.get_height() * 0.68
    button_fill_color = (0, 0, 0)  # Black
    button_border_color = (255, 255, 255)  # White
    text_color = (255, 255, 255)  # White
    button_border_width = 3
    corner_radius = 5
    text_size = 22
    highlight_color = (252, 239, 164)  # Offwhite

    if font_type == 'Regular' and italic:  # Just to get around a particular naming convention in fonts folder
        font_type = "Italic"
    font = pygame.font.Font(os.getcwd() + f'/fonts/Montserrat-{font_type}.ttf', text_size)
    button_dims = font.size(text)
    button_height = button_dims[1] + 2*padding
    button_width = screen.get_width() / 2 - 2*padding

    # Create the button for realsies
    button_rect = pygame.Rect(padding, button_section_height + row_num * (button_height + padding),
                              button_width, button_height)
    border_rect = pygame.Rect(button_rect[0] - button_border_width, button_rect[1] - button_border_width,
                              button_rect[2] + 2*button_border_width, button_rect[3] + 2*button_border_width)
    button_text = font.render(text, True, text_color, button_fill_color)

    # Now draw it on the screen
    # This is the button's border
    pygame.draw.rect(screen, button_border_color, border_rect, width=button_border_width, border_radius=corner_radius)

    # This is the button fill
    pygame.draw.rect(screen, button_fill_color, button_rect, border_radius=corner_radius)

    # This is the button text
    screen.blit(button_text, (button_rect[0] + padding, button_rect[1] + padding))

    return (button_rect, border_rect, button_text, button_border_width, corner_radius, button_border_color, text_size,
            text_color, highlight_color, padding, font, text, button_fill_color, row_num)


def get_player_name(screen, clock):
    font = pygame.font.Font(os.getcwd() + '/fonts/Montserrat-SemiBold.ttf', 46)
    color_active = (44, 44, 44)
    color_passive = (0, 0, 0)
    user_text = ""
    picture = pygame.image.load(os.getcwd() + '/images/space_storm.jpg').convert()
    background = pygame.transform.scale(picture, (screen.get_width(), screen.get_height()))
    cursor_timer = 1
    example_name_size = font.size("Example Name")
    color = color_passive
    cursor_color = (255, 255, 255)
    active = False
    max_name_len = 15
    welcome_msg = "Hello there! What is your name?"
    text_size = font.size(welcome_msg)
    x = screen.get_width() / 2 - text_size[0] / 2
    y = screen.get_height() / 4
    input_rect = pygame.Rect(x, y + 2*text_size[1], screen.get_width()/2, example_name_size[1])
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(event.pos):
                    active = True
                else:
                    active = False

            if event.type == pygame.KEYDOWN:

                # Check for backspace
                if event.key == pygame.K_BACKSPACE:
                    print("Backspacing")
                    # get text input from 0 to -1 i.e. end.
                    user_text = user_text[:-1]

                # Check for done
                elif event.key == pygame.K_RETURN:

                    # user is done (if there name is at least one char)
                    if len(user_text):
                        return user_text
                # Unicode standard is used for string
                # formation
                elif len(user_text) < max_name_len:
                    print("appending: ", event.unicode)
                    user_text += event.unicode

        screen.blit(background, (0, 0))

        if active:
            cursor_timer -= 1
            color = color_active
            if cursor_timer == 0:  # If timer is 0, cursor blinks other color
                cursor_timer = 25
                if cursor_color == color_active:
                    cursor_color = (255, 255, 255)
                elif cursor_color == (0, 0, 0):
                    cursor_color = (255, 255, 255)
                else:
                    cursor_color = color_active
        else:
            color = color_passive
            cursor_color = color_passive

        cursor_x, cursor_y = font.size(user_text)
        pygame.draw.rect(screen, color, input_rect)
        text_surface = font.render(user_text, True, (255, 255, 255))
        screen.blit(font.render(welcome_msg, True, (255, 255, 255)), (x, y))
        screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
        pygame.draw.line(screen, cursor_color, (input_rect.x + cursor_x + 5, input_rect.y + 5),
                         (input_rect.x + cursor_x + 5, input_rect.y + cursor_y - 5))
        input_rect.w = max(100, text_surface.get_width() + 10)
        pygame.display.update()
        clock.tick(60)

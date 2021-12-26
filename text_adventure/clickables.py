# For all things clicklable in a text adventure game
import pygame
import os


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

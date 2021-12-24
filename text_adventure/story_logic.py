# For logic in the progression of the story
import os
import pygame
import clickables
"""Basically just a huge graph of different scenes and how they are connected.
How to arrive at each one, etc. """


def get_scene(current_scene, player_choice):
    # TEMP FOR JUST HAVING ONE SCENE
    return GiantEncounter()


def draw_scene(screen, scene):
    padding = 15
    text_size = 28
    text_body_color = (255, 255, 255)
    # Background
    picture = scene.background
    background = pygame.transform.scale(picture, (screen.get_width(), screen.get_height()))
    screen.blit(background, (0, 0))
    # Text body
    lines = []
    word_idx = 0
    line = ""
    prev_line = line
    font = pygame.font.Font(os.getcwd() + '/fonts/Montserrat-SemiBold.ttf', text_size)
    words = scene.text_body.split(" ")
    while word_idx < len(words):
        line += words[word_idx] + " "  # Add next word
        width, height = font.size(line)  # Check the new size
        if width > screen.get_width() - 2*padding:  # Compare width of line of words to screen
            lines.append(prev_line)  # If too long, add line from before last word
            line = words[word_idx] + " " # Reset
        prev_line = line
        word_idx += 1
    lines.append(line)
    # Render it
    for i, line in enumerate(lines):
        text = font.render(line, False, text_body_color)
        screen.blit(text, (padding, padding * (i + 1) + height * i))
    # Options
    buttons = []
    options = scene.options
    for i, option in enumerate(options):
        button = clickables.create_button(screen, option[0], i, option[1], option[2])
        buttons.append(button)  # Create a list of tuples with button info
    pygame.display.update()
    return buttons


class GiantEncounter:
    kind = "scene"

    def __init__(self):
        self.background = pygame.image.load(os.getcwd() + '/images/giant_encounter.jpg')
        self.text_body = "As you walk through the forest glade, the stirring of birds and pounding of hooves grabs " \
            + "your attention. You see a deer running for its life in front of you and behind it a mountain giant."
        # Form [(Text, Font_Type, Italic), ...]
        self.options = [("Back away slowly and as quietly as possible...", "ExtraLight", True),
                        ("Crouch down behind a tree trunk and watch the giant.", "Regular", False),
                        ("Shout at it to get its attention!", "ExtraBold", False),
                        ("Run away as fast as you can.", "Regular", True)]

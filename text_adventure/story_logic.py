# For logic in the progression of the story
import os
import pygame
import clickables
"""Basically just a huge graph of different scenes and how they are connected.
How to arrive at each one, etc. """

all_scenes = {"INIT": None,
              "STARTVILLAGE": None,
              "GIANTENCOUNTER": None,
              "ISOLATEDCASTLE": None
              }


def init_all_scenes():
    global all_scenes
    all_scenes["INIT"] = Init()
    all_scenes["STARTVILLAGE"] = StartVillage()
    all_scenes["GIANTENCOUNTER"] = GiantEncounter()
    all_scenes["ISOLATEDCASTLE"] = IsolatedCastle()


def get_scene(current_scene, player_choice):
    next_scene_name = current_scene.options[player_choice][3]
    return all_scenes[next_scene_name]


def draw_scene(screen, scene):
    padding = 15
    text_size = 28
    text_body_color = (255, 255, 255)
    text_outline_color = (0, 0, 0)
    text_border_thickness = 2  # Looks weird if higher than 3. Must be greater than 0
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
        text = font.render(line, True, text_body_color).convert_alpha()
        outline = font.render(line, True, text_outline_color)

        # Blit 8 times, shifted by the border thickness each time
        offsets = [(ox, oy)
                   for ox in range(-text_border_thickness, 2 * text_border_thickness, text_border_thickness)
                   for oy in range(-text_border_thickness, 2 * text_border_thickness, text_border_thickness)
                   if ox != 0 or oy != 0]
        for ox, oy in offsets:
            screen.blit(outline, (padding + ox, padding * (i + 1) + height * i + oy))
        screen.blit(text, (padding, padding * (i + 1) + height * i))


    # Options
    buttons = []
    options = scene.options
    for i, option in enumerate(options):
        i = 3 - i  # Build from bottom of screen up (for fewer than 4 options)
        button = clickables.create_button(screen, option[0], i, option[1], option[2])
        buttons.append(button)  # Create a list of tuples with button info
    pygame.display.update()
    return buttons


class Init():
    kind = "setup"

    def __init__(self):
        self.options = [("Game Loading...", "ExtraLight", True, "STARTVILLAGE")]


class GiantEncounter:
    kind = "scene"

    def __init__(self):
        self.background = pygame.image.load(os.getcwd() + '/images/giant_encounter.jpg')
        self.text_body = "As you walk through the forest glade, the stirring of birds and pounding of hooves grabs " \
            + "your attention. You see a deer running for its life in front of you and behind it a mountain giant."
        # Form [(Text, Font_Type, Italic), ...]
        self.options = [("Back away slowly and as quietly as possible...", "ExtraLight", True, "INIT"),
                        ("Crouch down behind a tree trunk and watch the giant.", "Regular", False, "INIT"),
                        ("Shout at it to get its attention!", "ExtraBold", False, "INIT"),
                        ("Run away as fast as you can.", "Regular", True, "INIT")]


class IsolatedCastle:
    kind = "scene"

    def __init__(self):
        self.background = pygame.image.load(os.getcwd() + '/images/isolated_castle.jpg')
        self.text_body = "You meander through the village and come out the other side to a vast plain. Sitting in the" \
            + " middle of it is an isolated castle. You are unsure if it is currently occupied."
        # Form [(Text, Font_Type, Italic, NextScene), ...]
        self.options = [("Continue walking through the plain towards the castle.", "Regular", False, "INIT"),
                        ("Turn back towards the village.", "Regular", False, "INIT"),
                        ("Shout obscenities into the open field.", "ExtraBold", False, "INIT")]


class StartVillage:
    kind = "scene"

    def __init__(self):
        self.background = pygame.image.load(os.getcwd() + '/images/start_village.jpg')
        self.text_body = "Welcome traveler! Before you lies the village of Thrombovor! Where will your jourmney" \
            + " take you?"
        # Form [(Text, Font_Type, Italic, NextScene), ...]
        self.options = [("Go check out the castle.", "Regular", False, "ISOLATEDCASTLE"),
                        ("Go into the forest.", "Regular", False, "GIANTENCOUNTER")]

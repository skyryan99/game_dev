# For logic in the progression of the story
import os
import pygame
import clickables
from collections import defaultdict
"""Basically just a huge graph of different scenes and how they are connected.
How to arrive at each one, etc. """

all_scenes = defaultdict()


def init_all_scenes():
    global all_scenes
    all_scenes["INIT"] = Init()
    all_scenes["WALKINGTOOFFICE1"] = WalkingToOffice1()
    all_scenes["PIOFFICE1"] = PIOffice1()
    all_scenes["PIOFFICE2A"] = PIOffice2a()
    all_scenes["PIOFFICE2B"] = PIOffice2b()
    all_scenes["PIOFFICE3A"] = PIOffice3a()
    all_scenes["PIOFFICE3B"] = PIOffice3b()


def get_scene(current_scene, player_choice):
    next_scene_name = current_scene.options[player_choice][3]
    return all_scenes[next_scene_name]


def draw_scene(screen, scene):
    padding = 12
    text_size = 30
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


class Init:
    kind = "setup"

    def __init__(self):
        self.options = [("Enter", "SemiBold", False, "WALKINGTOOFFICE1")]


class WalkingToOffice1:
    kind = "scene"

    def __init__(self):
        self.scene_num = 0
        self.background = pygame.image.load(os.getcwd() + '/images/walking_to_office_with_alcohol.webp')
        self.text_body = "I throw my shoulder into the old oak door of my house, dusting my trench coat with curls " \
            + "aged varnish. Trudging down the hallway, I balance my shopping bag full of booze while kicking the " \
            + "door closed and getting my keys out of my pocket in a way only a veteran alcohol-enthusiast can " \
            + "master. Finally, I reach my door and jostle my way in, only barely bumping my head on the cramped " \
            + "ceiling."
        # Form [(Text, Font_Type, Italic), ...]
        self.options = [("Next", "SemiBold", False, "PIOFFICE1")]


class PIOffice1:
    kind = "scene"

    def __init__(self):
        self.scene_num = 1
        self.background = pygame.image.load(os.getcwd() + '/images/pi_office_coming_back_with_alcohol.webp')
        self.text_body = " Did I say my house? It’s basically my house, but due to a technicality I actually only " \
            + "rent a so-called “coffin” apartment in a closet below the stairs of my uncle’s house. He’s not " \
            + "particularly fond of me, but I guess my \"hangdog, private eye down on his luck\" face garnered some " \
            + "scraps of sympathy."
        # Form [(Text, Font_Type, Italic, NextScene), ...]
        self.options = [("Next", "SemiBold", False, "PIOFFICE2A")]


class PIOffice2a:
    kind = "scene"

    def __init__(self):
        self.scene_num = 2
        self.background = pygame.image.load(os.getcwd() + '/images/pi_office_coming_back_with_alcohol.webp')
        self.text_body = "Anyways, for now this is only a temporary pitstop on my personal road to greatness. I’m " \
            + "sure one day pilgrims will come to this tiny musty pit of a room and bestow flower garlands on my " \
            + "combination fridge/microwave/hotpot."
        # Form [(Text, Font_Type, Italic, NextScene), ...]
        self.options = [("Priorities (alcohol).", "SemiBold", False, "PIOFFICE3A"),
                        ("God please save me from this ceaseless mediocrity.", "SemiBold", False, "PIOFFICE3B"),
                        ("Start drinking.", "SemiBold", False, "PIOFFICE2B")]


class PIOffice3a:
    kind = "scene"

    def __init__(self):
        self.scene_num = 3
        self.background = pygame.image.load(os.getcwd() + '/images/pi_office_alcohol_on_bed.jpg')
        self.text_body = "I stash my newly-gained bottles in said unholy kitchen-appliance abomination and flop " \
            + "my threadbare mattress. I pull out my phone and begin lazily searching for any social opportunities " \
            + "that could let me drink for free with people I barely know. What’s this? A client emailed me? I " \
            + "jackknife up in bed, stunned by the good fortune."

        # Form [(Text, Font_Type, Italic, NextScene), ...]
        self.options = [("CLOSE DEMO", "SemiBold", False, "INIT")]


class PIOffice3b:
    kind = "scene"

    def __init__(self):
        self.scene_num = 3
        self.background = pygame.image.load(os.getcwd() + '/images/pi_office_opening_laptop.jpg')
        self.text_body = "Filled with an extremely unusual bout of fiery motivation, I strode purposefully to my " \
            + "ancient laptop. Opening my email, I scour my inbox for any crumbs of opportunity, completely focused " \
            + "on the task at hand. Hold on. I press my left hand to my gut and investigate. Last time I felt any " \
            + "source of internal ambition this strong it turned out to be appendicitis and they had to sedate me " \
            + "the hospital. Out of the corner of my eye I see it. A client’s email!"

        # Form [(Text, Font_Type, Italic, NextScene), ...]
        self.options = [("CLOSE DEMO", "Regular", False, "INIT")]


class PIOffice2b:
    kind = "scene"

    def __init__(self):
        self.scene_num = 2
        self.background = pygame.image.load(os.getcwd() + '/images/pi_office_coming_back_with_alcohol.webp')
        self.text_body = "Man that was good shit."
        # Form [(Text, Font_Type, Italic, NextScene), ...]
        self.options = [("God please save me from this ceaseless mediocrity.", "SemiBold", False, "PIOFFICE3B")]

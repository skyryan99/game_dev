# For logic in the progression of the story
import os
import pygame
import clickables
"""Basically just a huge graph of different scenes and how they are connected.
How to arrive at ecch one, etc. """


def get_scene(current_scene, player_choice):
    # TEMP FOR JUST HAVING ONE SCENE
    return "GIANT"


def draw_scene(screen, scene):
    picture = pygame.image.load(os.getcwd() + '/images/giant_encounter.jpg')
    background = pygame.transform.scale(picture, (screen.get_width(), screen.get_height()))
    options = ["Option 1", "Option numero 2", "The Third Option", "The 4th and final option available"]
    screen.blit(background, (0, 0))
    for i, option in enumerate(options):
        clickables.create_button(screen, option, i, "Regular")
    pygame.display.update()

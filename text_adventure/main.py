import pygame
import os
import ctypes
import sys
import clickables
import story_logic

# Init shit
pygame.display.init()
pygame.font.init()
# Create window and name it
pygame.display.set_caption('Plant Adventure')
# Set icon and taskbar icon
icon = pygame.image.load(os.getcwd() + '/images/leaf_icon2.png')
pygame.display.set_icon(icon)
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PLS")
screen = pygame.display.set_mode((1280, 720))
# Background fill
screen.fill(pygame.Color(71, 71, 71))
# Set upper fps limit
clock = pygame.time.Clock()
# For testing
index = 0
scene_changed = True
current_scene = "INIT"
player_choice = 0

is_running = True
pygame.init()

while is_running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                print("Button Created")
                button_rect, border_rect, text = clickables.create_button(screen, "Test Button", index, 'ExtraBold')
                index += 1

    if scene_changed:
        current_scene = story_logic.get_scene(current_scene, player_choice)
        story_logic.draw_scene(screen, current_scene)

pygame.quit()
sys.exit(0)

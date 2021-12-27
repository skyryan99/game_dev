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
screen = pygame.display.set_mode((1280, 900))
# Background fill
screen.fill((71, 71, 71))
# Set upper fps limit
clock = pygame.time.Clock()
# For the game
name = clickables.get_player_name(screen, clock)
index = 0
scene_changed = True
current_scene = story_logic.Init()
story_logic.init_all_scenes()
player_choice = 0
buttons = []
is_running = True
pygame.init()

while is_running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                print("Escaped")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pressed = pygame.mouse.get_pressed(num_buttons=3)
            if pressed[0]:  # Left Click
                mx, my = pygame.mouse.get_pos()
                for button in buttons:
                    if button[1].collidepoint(mx, my):
                        player_choice = 3 - button[13]
                        scene_changed = True

    # Change the scene when a player picks a course of action
    if scene_changed:
        scene_changed = False
        print(player_choice)
        current_scene = story_logic.get_scene(current_scene, player_choice)
        buttons = story_logic.draw_scene(screen, current_scene)

    # Check hover for each button
    mx, my = pygame.mouse.get_pos()
    for button in buttons:
        if button[1].collidepoint(mx, my):  # Highlight color
            pygame.draw.rect(screen, button[8], button[1], width=button[3], border_radius=button[4])
            new_text_color = button[10].render(button[11], True, button[8], button[12])
            screen.blit(new_text_color, (button[0][0] + button[9], button[0][1] + button[9]))
        else:  # Regular color
            pygame.draw.rect(screen, button[5], button[1], width=button[3], border_radius=button[4])
            screen.blit(button[2], (button[0][0] + button[9], button[0][1] + button[9]))
        pygame.display.update(button[1])


pygame.quit()
sys.exit(0)

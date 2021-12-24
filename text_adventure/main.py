import pygame
import os
import ctypes

# Create window and name it
pygame.display.set_caption('Plant Adventure')
# Set icon and taskbar icon
icon = pygame.image.load(os.getcwd() + '/images/leaf_icon2.png')
pygame.display.set_icon(icon)
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PLS")
window_surface = pygame.display.set_mode((1280, 720))
# Background fill
background = pygame.Surface((1280, 720))
background.fill(pygame.Color(0, 0, 0))

# Set upper fps limit
clock = pygame.time.Clock()

is_running = True
pygame.init()

while is_running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

    window_surface.blit(background, (0, 0))

    pygame.display.update()

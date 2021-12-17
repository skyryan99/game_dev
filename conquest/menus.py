# Contains info for menus in the game
import pygame


def troops_menu(screen):
    pass


def commands_menu(screen):
    pass


def actions_menu(screen):
    # Take up right 20% and top half
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    x = screen_width*0.8
    y = 0
    width = screen_width*0.2
    height = screen_height*0.5
    line_width = 2
    pygame.draw.rect(screen, (3, 13, 46), (x, y, width, height))
    pygame.draw.line(screen, (255, 255, 255), (x-line_width, y), (x-line_width, y+height), width=line_width)


def details_menu(screen):
    # Take up right 20% and bottom half
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    x = screen_width*0.8
    y = screen_height*0.5
    width = screen_width*0.2
    height = screen_height*0.5
    line_width = 2
    # Average color of two square colors
    pygame.draw.rect(screen, (108, 79, 35), (x, y, width, height))
    pygame.draw.line(screen, (255, 255, 255), (x - line_width, y), (x - line_width, y+height), width=line_width)

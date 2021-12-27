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


def get_player_name():
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


index = 0
scene_changed = True
current_scene = story_logic.Init()
story_logic.init_all_scenes()
name = get_player_name()
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

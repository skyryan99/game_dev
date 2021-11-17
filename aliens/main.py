import pygame
import random
from pygame import mixer

pygame.mixer.init()
pygame.font.init()
"""Object classes"""


class BigText:
    def __init__(self, size, x, y):
        self.font = pygame.font.Font('fonts/Montserrat-SemiBold.ttf', size)
        self.X = x
        self.Y = y
        self.value = 0


class Player:
    def __init__(self):
        self.Img = pygame.image.load('images/player_ship.png')
        self.speed = 0.3
        self.height = 64
        self.width = 64
        self.X = (screen_width / 2) - (self.width / 2)
        self.Y = screen_height - self.height
        self.Delta_x = 0

    def move(self):
        self.X = min(max(0, self.X + self.Delta_x), screen_width - self.width)


def spawn_alien(new_alien_x):
    for an_alien in aliens:
        # Check top row aliens for their X pos
        if an_alien.Y == an_alien.height / 2 and abs(new_alien_x - an_alien.X) < an_alien.width:
            return 0
    return new_alien_x


class Alien:
    def __init__(self, speed, jump):
        self.Img = pygame.image.load('images/alien_ship.png')
        self.speed = speed
        self.height = 64
        self.width = 64
        self.X = spawn_alien(random.randint(0, screen_width - 2 * self.width))
        self.Y = self.height / 2
        self.Delta_x = self.speed
        self.Delta_y = jump
        self.state = "MOVE"

    def move(self):
        if self.state == "EXPLODE":
            self.X = -100  # Just out of bounds
            self.Y = -100
            explosion_sound = mixer.Sound('sounds/explosion.wav')
            explosion_sound.set_volume(0.2)
            explosion_sound.play()
            self.state = "MOVE"
            return
        self.X = self.X + self.Delta_x
        # If it hits the sides
        if self.X >= (screen_width - self.width) or self.X <= 0:
            self.Y += self.Delta_y
            self.Delta_x *= -1


class Bullet:
    def __init__(self):
        self.Img = pygame.image.load('images/bullet.png')
        self.speed = 0.6
        self.height = 32
        self.width = 32
        self.X = -100  # Just out of bounds
        self.Y = -100
        self.Delta_y = 10
        self.state = "READY"
        self.num_aliens = 0

    def fire(self):
        # Can't fire if already fired
        if self.state == "FIRE":
            return
        self.state = "FIRE"
        self.X = player.X + (self.width / 2)
        self.Y = player.Y - (self.height / 2)
        bullet_sound = mixer.Sound('sounds/laser.wav')
        bullet_sound.play()
        bullet_sound.set_volume(0.2)

    def move(self):
        # Doesn't appear if not fired
        if self.state == "READY":
            self.X = -100  # Just out of bounds
            self.Y = -100
            return
        self.Y -= self.speed
        # Check if bullet missed
        if self.Y <= -self.height:
            self.state = "READY"


class Explosion:
    def __init__(self, x, y):
        self.Img = pygame.image.load('images/explosion.png')
        self.X = x
        self.Y = y
        self.height = 64
        self.width = 64
        self.timer = 500

    def run_explosion(self):
        if self.timer == 0:
            self.X = -100
            self.Y = -100
            return
        self.timer -= 1


"""Set-up code"""
screen_width = 800
screen_height = 600

# Title
pygame.display.set_caption("Aliens")
# Icon
icon = pygame.image.load('images/spaceship_icon.png')
pygame.display.set_icon(icon)
# Screen Size and background
screen = pygame.display.set_mode((screen_width, screen_height))
background = pygame.image.load('images/background.jpg')
# Background sound
mixer.music.load('sounds/background.wav')
mixer.music.play(-1)
mixer.music.set_volume(0.1)
# Create Objects
player = Player()
bullet = Bullet()
aliens = []
timer = 1
game_end = False
end_timer = 10000
score = BigText(22, 10, 10)
explosion_img = pygame.image.load('images/explosion.png')
explosion = Explosion(-100, -100)
# Init the pygame
pygame.init()


# Object 1 should be the object above Object 2
def check_collisions(object1, object2, proximity):
    x1 = object1.X + object1.width / 2  # middle of object
    x2 = object2.X + object2.width / 2  # middle of object
    y1 = object1.Y + object1.height  # bottom of object
    y2 = object2.Y  # top of object
    dist_squared = pow(x2 - x1, 2) + pow(y2 - y1, 2)
    if proximity == "CLOSE" and dist_squared < 100:
        return True
    elif proximity == "FAR" and dist_squared < 1600:
        return True
    return False


def populate_aliens(timer, alien_speed, alien_jump):
    if timer == 0 and bullet.num_aliens < max_enemies:
        aliens.append(Alien(alien_speed, alien_jump))
        bullet.num_aliens += 1


def explode_alien(explosion, alien):
    explosion = Explosion(alien.X, alien.Y)
    return explosion


button1 = pygame.Rect(int(screen_width / 4), int(3 * screen_height / 12), int(screen_width / 2), int(screen_height / 6))
button1_text = BigText(45, int(21 * screen_width / 48), int(7 * screen_height / 24))
button1_text.value = "Easy"
button2 = pygame.Rect(int(screen_width / 4), int(6 * screen_height / 12), int(screen_width / 2), int(screen_height / 6))
button2_text = BigText(45, int(19 * screen_width / 48), int(13 * screen_height / 24))
button2_text.value = "Medium"
button3 = pygame.Rect(int(screen_width / 4), int(9 * screen_height / 12), int(screen_width / 2), int(screen_height / 6))
button3_text = BigText(45, int(21 * screen_width / 48), int(19 * screen_height / 24))
button3_text.value = "Hard"
title = BigText(65, int(9 * screen_width / 24), int(screen_height / 12))
title.value = "Aliens"
title_render = title.font.render(title.value, True, (255, 255, 190))
"""Start Menu"""
while True:
    """Draw all the buttons"""
    screen.blit(background, (0, 0))
    # screen.fill((60, 100, 180))  # Solid color background if desired
    screen.fill((0, 0, 102), button1)
    screen.fill((0, 0, 102), button2)
    screen.fill((0, 0, 102), button3)
    button1_render = button1_text.font.render(button1_text.value, True, (255, 255, 190))
    button2_render = button2_text.font.render(button2_text.value, True, (255, 255, 190))
    button3_render = button3_text.font.render(button3_text.value, True, (255, 255, 190))

    screen.blit(title_render, (title.X, title.Y))
    """Check the cursor and mouse clicks"""
    mouse_pos = pygame.mouse.get_pos()
    is_pressed = pygame.mouse.get_pressed()[0]
    # Check first button
    if button1.collidepoint(mouse_pos):
        button1_render = button1_text.font.render(button1_text.value, True, (174, 174, 130))
        screen.blit(icon, (button1_text.X - 60, button1_text.Y + 16))
        if is_pressed:
            max_enemies = 12
            spawn_rate = 2000
            alien_speed = 0.2
            alien_jump = 74
            break
    elif button2.collidepoint(mouse_pos):
        button2_render = button2_text.font.render(button2_text.value, True, (174, 174, 130))
        screen.blit(icon, (button2_text.X - 60, button2_text.Y + 16))
        if is_pressed:
            max_enemies = 16
            spawn_rate = 800
            alien_speed = 0.3
            alien_jump = 88
            break
    elif button3.collidepoint(mouse_pos):
        button3_render = button3_text.font.render(button3_text.value, True, (174, 174, 130))
        screen.blit(icon, (button3_text.X - 60, button3_text.Y + 16))
        if is_pressed:
            max_enemies = 20
            spawn_rate = 400
            alien_speed = 0.7
            alien_jump = 108
            break
    for event in pygame.event.get():
        # Exit if 'X' on window is pressed
        if event.type == pygame.QUIT:
            exit(0)
    screen.blit(button1_render, (button1_text.X, button1_text.Y))
    screen.blit(button2_render, (button2_text.X, button2_text.Y))
    screen.blit(button3_render, (button3_text.X, button3_text.Y))

    pygame.display.update()

"""Gameplay Loop"""
while True:
    if game_end:
        if end_timer > 9000:
            screen.blit(explosion_img, (player.X, player.Y))
            pygame.display.update()
            end_timer -= 1
        else:
            for event in pygame.event.get():
                # Exit if 'X' on window is pressed
                if event.type == pygame.QUIT:
                    exit(0)
            end_timer -= 1
            game_over1 = BigText(100, screen_width / 10, screen_height / 10)
            game_over2 = BigText(100, screen_width / 10, int(screen_height / 2))
            game_over1.value = 'GAME OVER'
            game_over2.value = 'SCORE: ' + str(score.value)
            value = game_over1.font.render(game_over1.value, True, (255, 255, 255))
            value2 = game_over2.font.render(game_over2.value, True, (255, 255, 255))
            screen.blit(background, (0, 0))
            screen.blit(value, (game_over1.X, game_over1.Y))
            screen.blit(value2, (game_over2.X, game_over2.Y))
            pygame.display.update()
        if end_timer == 0:
            exit(0)

    else:
        # Background
        screen.blit(background, (0, 0))

        if timer == 0:
            timer = spawn_rate
        timer -= 1
        # Check Events
        for event in pygame.event.get():
            # Exit if 'X' on window is pressed
            if event.type == pygame.QUIT:
                exit(0)
            # If Key is being pressed
            if event.type == pygame.KEYDOWN:
                # "A" moves left
                if event.key == pygame.K_a:
                    player.Delta_x -= player.speed
                # "D" moves right
                if event.key == pygame.K_d:
                    player.Delta_x += player.speed
                # " " fires a bullet
                if event.key == pygame.K_SPACE:
                    bullet.fire()
            # When key is released
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    player.Delta_x += player.speed
                if event.key == pygame.K_d:
                    player.Delta_x -= player.speed
        populate_aliens(timer, alien_speed, alien_jump)
        # Get player location
        player.move()
        # Draw player icon
        screen.blit(player.Img, (player.X, player.Y))
        # Get alien location
        for alien in aliens:
            alien.move()
            screen.blit(alien.Img, (alien.X, alien.Y))
        # Get Bullet location
        bullet.move()
        # Draw Bullet
        screen.blit(bullet.Img, (bullet.X, bullet.Y))
        # Check collisions for player
        for alien in aliens:
            if check_collisions(alien, player, "CLOSE"):
                explode_sound = mixer.Sound('sounds/explosion.wav')
                explode_sound.set_volume(0.1)
                explode_sound.play()
                game_end = True
                continue
            if check_collisions(alien, bullet, "FAR"):
                bullet.state = "READY"
                alien.state = "EXPLODE"
                explosion = explode_alien(explosion, alien)
                bullet.num_aliens -= 1
                score.value += 1
        # Update and draw explosion
        explosion.run_explosion()
        screen.blit(explosion.Img, (explosion.X, explosion.Y))
        # Update score
        update = score.font.render("Score: " + str(score.value), True, (255, 255, 255))
        screen.blit(update, (score.X, score.Y))
        # Update display
        pygame.display.update()

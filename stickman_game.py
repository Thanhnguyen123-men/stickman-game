import pygame
import sys
import random
from math import copysign
import os

# ---------------- Config ----------------
WIDTH, HEIGHT = 800, 480
FPS = 60
GRAVITY = 0.9
PLAYER_SPEED = 5
JUMP_SPEED = -15
BULLET_SPEED = 12
ENEMY_SPEED_MIN = 1.0
ENEMY_SPEED_MAX = 3.0
SPAWN_CHANCE = 0.01  # per frame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 191, 255)
GROUND_GRAY = (200, 200, 200)
GROUND_STRIPE = (170, 170, 170)
DARK_SKY = (180, 220, 255)

pygame.init()
FONT = pygame.font.SysFont(None, 28)

# ---------------- Helper ----------------
def resource_path(filename):
    """Get absolute path to resource, works for PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)

# ---------------- Player ----------------
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.alive = True
        self.shoot_cooldown = 0

        # Load image and resize
        self.image = pygame.image.load(resource_path("player.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (20, 50))
        self.width = 20
        self.height = 50

    def rect(self):
        return pygame.Rect(self.x - self.width//2, self.y - self.height, self.width, self.height)

    def update(self, keys):
        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.vx = PLAYER_SPEED
        if keys[pygame.K_UP] and self.on_ground:
            self.vy = JUMP_SPEED
            self.on_ground = False

        self.x += self.vx
        self.vy += GRAVITY
        self.y += self.vy

        # Screen bounds
        self.x = max(10, min(WIDTH-10, self.x))

        # Ground
        ground_y = HEIGHT - 40
        if self.y >= ground_y:
            self.y = ground_y
            self.vy = 0
            self.on_ground = True

        # Cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def draw(self, surf):
        surf.blit(self.image, (self.x - self.width//2, self.y - self.height))

# ---------------- Bullet ----------------
class Bullet:
    def __init__(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir
        self.speed = BULLET_SPEED
        self.life = 80

        self.image = pygame.image.load(resource_path("bullet.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (14, 6))

    def rect(self):
        return pygame.Rect(self.x, self.y - 3, 14, 6)

    def update(self):
        self.x += self.dir * self.speed
        self.life -= 1

    def draw(self, surf):
        surf.blit(self.image, (self.x, self.y - 3))

# ---------------- Enemy ----------------
class Enemy:
    def __init__(self, x, y, w=30, h=36, speed=2.0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = speed
        self.dir = -1 if x > WIDTH//2 else 1
        self.alive = True

        self.image = pygame.image.load(resource_path("enemy.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (w, h))

    def rect(self):
        return pygame.Rect(self.x, self.y - self.h, self.w, self.h)

    def update(self):
        self.x += self.dir * self.speed
        if self.x < 0:
            self.x = 0
            self.dir *= -1
        if self.x > WIDTH - self.w:
            self.x = WIDTH - self.w
            self.dir *= -1

    def draw(self, surf):
        surf.blit(self.image, (self.x, self.y - self.h))

# ---------------- Game ----------------
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Stickman Game")
        self.clock = pygame.time.Clock()

        # Load background
        self.background = pygame.image.load(resource_path("background.png")).convert()
        self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))

        self.reset()

    def reset(self):
        self.player = Player(WIDTH//2, HEIGHT - 40)
        self.bullets = []
        self.enemies = [Enemy(random.randint(20, WIDTH-60), HEIGHT-40, speed=random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)) for _ in range(3)]
        self.score = 0
        self.start_ticks = pygame.time.get_ticks()
        self.game_over = False

    def spawn_enemy(self):
        side = random.choice(['left', 'right'])
        x = 0 if side == 'left' else WIDTH-30
        dir = 1 if side == 'left' else -1
        e = Enemy(x, HEIGHT-40, speed=random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX))
        e.dir = dir
        self.enemies.append(e)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and self.game_over:
                    self.reset()
                if event.key == pygame.K_SPACE and not self.game_over:
                    if self.player.shoot_cooldown <= 0:
                        keys = pygame.key.get_pressed()
                        dir = -1 if keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT] else 1
                        bx = self.player.x + int(copysign(self.player.width//2 + 8, dir))
                        by = int(self.player.y - self.player.height + 2*10 + 10)
                        self.bullets.append(Bullet(bx, by, dir))
                        self.player.shoot_cooldown = 12

    def update(self):
        keys = pygame.key.get_pressed()
        if not self.game_over:
            self.player.update(keys)
            for b in self.bullets[:]:
                b.update()
                if b.life <= 0 or b.x < -50 or b.x > WIDTH+50:
                    self.bullets.remove(b)
            for e in self.enemies[:]:
                e.update()

            # bullet hits enemy
            for b in self.bullets[:]:
                for e in self.enemies[:]:
                    if b.rect().colliderect(e.rect()):
                        try: self.enemies.remove(e)
                        except: pass
                        try: self.bullets.remove(b)
                        except: pass
                        self.score += 10
                        break

            # player hits enemy
            for e in self.enemies:
                if self.player.rect().colliderect(e.rect()):
                    self.game_over = True
                    self.player.alive = False

            self.score = (pygame.time.get_ticks() - self.start_ticks)//1000 + self.score
            if random.random() < SPAWN_CHANCE:
                self.spawn_enemy()

    def draw_ground(self):
        ground_y = HEIGHT - 40
        pygame.draw.rect(self.screen, GROUND_GRAY, (0, ground_y, WIDTH, 40))
        for i in range(0, WIDTH, 40):
            pygame.draw.rect(self.screen, GROUND_STRIPE, (i+10, ground_y+14, 20, 4))

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_ground()
        self.player.draw(self.screen)
        for b in self.bullets:
            b.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)

        score_surf = FONT.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_surf, (10, 10))

        if self.game_over:
            over_surf = FONT.render("GAME OVER - Press R to restart", True, (200,40,40))
            rect = over_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(over_surf, rect)

        pygame.display.flip()

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

if __name__ == "__main__":
    Game().run()

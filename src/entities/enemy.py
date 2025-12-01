# src/entities/enemy.py
import pygame
from config import ENEMY_SIZE


class Enemy:
    def __init__(self, x, y, speed, max_hp=30):
        self.pos = pygame.Vector2(x, y)
        self.speed = speed
        self.state = "moving"  # "moving" or "attacking"
        self.max_hp = max_hp
        self.hp = max_hp
        self.is_dead = False
        self.attack_range = 50
        # for drawing / collisions
        self.size = 24
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def get_rect(self):
        rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
        rect.center = self.pos
        return rect

    def update(self, dt: float, target_rect: pygame.Rect):
        if self.is_dead:
            return

        # --- move toward target center (both X and Y) ---
        tx, ty = target_rect.center
        dx = tx - self.pos.x
        dy = ty - self.pos.y

        # distance to target
        dist_sq = dx * dx + dy * dy

        # close enough to attack?
        if dist_sq <= self.attack_range * self.attack_range:
            self.state = "attacking"
            # when attacking, we don't move; Game will apply damage
        else:
            self.state = "moving"
            dist = dist_sq**0.5
            if dist > 0:
                # normalized direction
                self.pos.x += (dx / dist) * self.speed * dt
                self.pos.y += (dy / dist) * self.speed * dt

        # sync rect to pos for rendering/collision
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def take_damage(self, amount: float):
        self.hp -= amount
        if self.hp <= 0:
            self.is_dead = True

    def draw(self, screen):
        # --- enemy body ---
        pygame.draw.rect(screen, (200, 50, 50), self.rect)

        # --- HP BAR ABOVE ENEMY ---
        bar_width = 30
        bar_height = 4
        offset_y = -14

        x = int(self.pos.x - bar_width / 2)
        y = int(self.pos.y + offset_y)

        pygame.draw.rect(screen, (80, 0, 0), (x, y, bar_width, bar_height))

        if self.max_hp > 0:
            ratio = max(0.0, self.hp / self.max_hp)
        else:
            ratio = 0.0

        pygame.draw.rect(
            screen,
            (0, 220, 0),
            (x, y, int(bar_width * ratio), bar_height),
        )

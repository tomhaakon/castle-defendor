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

    def get_rect(self):
        rect = pygame.Rect(0, 0, ENEMY_SIZE, ENEMY_SIZE)
        rect.center = self.pos
        return rect

    def update(self, dt, castle_rect):
        if self.is_dead:
            return

        if self.state == "moving":
            self.pos.y += self.speed * dt

            rect = self.get_rect()
            if rect.colliderect(castle_rect):
                self.state = "attacking"
                self.pos.y = castle_rect.top - ENEMY_SIZE / 2

    def take_damage(self, amount):
        if self.is_dead:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True

    def draw(self, surface, font=None):
        if self.is_dead:
            return

        rect = self.get_rect()
        color = (50, 200, 50) if self.state == "attacking" else (200, 50, 50)
        pygame.draw.rect(surface, color, rect)

        if font is not None:
            txt = font.render(str(int(self.hp)), True, (255, 255, 255))
            txt_rect = txt.get_rect(center=(rect.centerx, rect.top - 10))
            surface.blit(txt, txt_rect)

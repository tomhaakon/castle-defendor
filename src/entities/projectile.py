import pygame
from entities.damage_number import DamageNumber


class Projectile:
    def __init__(
        self,
        pos,
        velocity,
        damage,
        radius=5,
        max_distance=250,
        color=(255, 255, 0),
        crit=False,
    ):
        self.pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.damage = damage
        self.radius = radius
        self.max_distance = max_distance
        self.color = color
        self.is_dead = False
        self.crit = crit

    def update(self, dt, enemies, damage_numbers):
        if self.is_dead:
            return

        # move
        self.pos += self.velocity * dt

        # remove projectile if travel to far
        if self.pos.distance_to(self.start_pos) >= self.max_distance:
            self.is_dead = True
            return

        # collision with enemies
        for enemy in enemies:
            if enemy.is_dead:
                continue
            if enemy.get_rect().collidepoint(self.pos.x, self.pos.y):
                enemy.take_damage(self.damage)

                enemy_rect = enemy.get_rect()
                color = (255, 255, 0) if self.crit else (255, 80, 80)

                damage_numbers.append(
                    DamageNumber(enemy_rect.midtop, self.damage, color)
                )
                self.is_dead = True
                break

    def draw(self, surface):
        if self.is_dead:
            return
        pygame.draw.circle(
            surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius
        )

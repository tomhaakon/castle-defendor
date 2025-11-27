import pygame
import random

from entities.projectile import Projectile

from config import DEFENCE_STATS


class Defence:
    def __init__(self, x, y, defence_type="archer", level=1):
        self.pos = pygame.Vector2(x, y)
        self.defence_type = defence_type
        self.level = level

        stats = DEFENCE_STATS[defence_type]

        self.base_damage = stats["damage"]
        self.base_range = stats["range"]

        self.base_cooldown = stats["cooldown"]
        self.base_projectile_speed = stats["proj_speed"]
        self.projectile_color = stats["color"]
        self.base_cost = stats["base_cost"]
        self.crit_chance = stats["crit_chance"]
        self.crit_multiplier = stats["crit_multiplier"]

        self.time_since_last_shot = 0.0

    def recalculate_stats(self):
        # scale based on level
        self.damage = self.base_damage * (1.0 + 0.3 * (self.level - 1))
        self.range = self.base_range * (1.0 + 0.1 * (self.level - 1))

        self.attack_cooldown = max(
            0.15, self.base_cooldown * (1.0 - 0.07 * (self.level - 1))
        )

        self.projectile_speed = self.base_projectile_speed * (
            1.0 + 0.1 * (self.level - 1)
        )

    def upgrade(self):
        self.level += 1
        self.recalculate_stats()

    def get_upgrade_cost(self) -> int:
        return int(self.base_cost * self.level)

    def update(self, dt, enemies, projectiles):
        # cd
        self.time_since_last_shot += dt
        if self.time_since_last_shot < self.base_cooldown:
            return

        # find enemy in  range
        target = None
        for enemy in enemies:
            if enemy.is_dead:
                continue

            if self.pos.distance_to(enemy.pos) <= self.base_range:
                target = enemy
                break

        if target is None:
            return

        # fire projectile
        direction = target.pos - self.pos
        if direction.length_squared() == 0:
            return

        direction = direction.normalize()
        velocity = direction * self.base_projectile_speed

        is_crit = random.random() < self.crit_chance
        dmg = self.base_damage * (self.crit_multiplier if is_crit else 1.0)

        projectiles.append(
            Projectile(
                self.pos,
                velocity,
                dmg,
                max_distance=self.base_range,
                color=self.projectile_color,
                crit=is_crit,
            )
        )
        self.time_since_last_shot = 0.0

    def draw(self, surface):
        # rect = pygame.Rect(0, 0, 30, 30)
        # rect.center = self.pos
        # pygame.draw.rect(surface, (80, 160, 220), rect, border_radius=4)
        pass

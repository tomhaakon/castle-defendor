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

        self.max_hp = stats.get("max_hp", 50)
        self.hp = self.max_hp

        self.size = 32
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # --- shake / recoil state (used by UI to shake icon) ---
        self.shake_time = 0.0
        self.shake_duration = 0.12  # seconds
        self.shake_magnitude = 2  # pixels (used in UI)

    def take_damage(self, amount: float):
        self.hp = max(0.0, self.hp - amount)

    def is_dead(self) -> bool:
        return self.hp <= 0

    def recalculate_stats(self):
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
        # decay shake timer every frame
        if self.shake_time > 0:
            self.shake_time = max(0.0, self.shake_time - dt)

        # cooldown
        self.time_since_last_shot += dt
        if self.time_since_last_shot < self.base_cooldown:
            return

        # find enemy in range
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

        aoe_radius = 60 if self.defence_type == "mage" else 0.0

        projectiles.append(
            Projectile(
                self.pos,
                velocity,
                dmg,
                max_distance=self.base_range,
                color=self.projectile_color,
                crit=is_crit,
                area_radius=aoe_radius,
            )
        )

        # reset cooldown and start shake
        self.time_since_last_shot = 0.0
        self.shake_time = self.shake_duration

    def draw(self, screen):
        # just HP bar (no square; icons are drawn in UI slots)
        bar_width = 40
        bar_height = 5
        offset_y = -55

        x = int(self.pos.x - bar_width / 2)
        y = int(self.pos.y + offset_y)

        if self.max_hp > 0:
            ratio = max(0.0, self.hp / self.max_hp)
        else:
            ratio = 0.0

        pygame.draw.rect(
            screen,
            (0, 220, 0),
            (x, y, int(bar_width * ratio), bar_height),
        )

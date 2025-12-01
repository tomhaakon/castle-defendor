import pygame
from entities.damage_number import DamageNumber
from entities.aoe_effect import AoeEffect  # <-- make sure this file/class exists


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
        source_type: str = "archer",
        area_radius: float = 0.0,
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
        self.area_radius = area_radius
        self.source_type = source_type

    def update(self, dt, enemies, damage_numbers, aoe_effects):
        if self.is_dead:
            return

        # move
        self.pos += self.velocity * dt

        # remove projectile if it travels too far
        if self.pos.distance_to(self.start_pos) >= self.max_distance:
            self.is_dead = True
            return

        # === AOE PROJECTILE (e.g. mage) ===
        if self.area_radius > 0:
            # first, see if we hit *any* enemy this frame
            impact = False
            for enemy in enemies:
                if enemy.is_dead:
                    continue
                if enemy.get_rect().collidepoint(self.pos.x, self.pos.y):
                    impact = True
                    break

            if not impact:
                return

            # spawn visual AoE circle at impact point
            aoe_effects.append(AoeEffect(self.pos.x, self.pos.y, self.area_radius))

            # damage all enemies within radius
            for enemy in enemies:
                if enemy.is_dead:
                    continue

                dx = enemy.pos.x - self.pos.x
                dy = enemy.pos.y - self.pos.y
                dist_sq = dx * dx + dy * dy  # correct distance squared

                if dist_sq <= self.area_radius * self.area_radius:
                    enemy.take_damage(self.damage)

                    enemy_rect = enemy.get_rect()
                    color = (255, 255, 0) if self.crit else (255, 80, 80)
                    damage_numbers.append(
                        DamageNumber(enemy_rect.midtop, self.damage, color)
                    )

            self.is_dead = True
            return

        # === NORMAL SINGLE-TARGET PROJECTILE ===
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

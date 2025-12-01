# entities/aoe_effect.py
import pygame


class AoeEffect:
    def __init__(self, x: float, y: float, radius: float, lifetime: float = 0.25):
        self.pos = pygame.math.Vector2(x, y)
        self.radius = radius
        self.lifetime = lifetime
        self.age = 0.0
        self.dead = False

    def update(self, dt: float):
        self.age += dt
        if self.age >= self.lifetime:
            self.dead = True

    def is_dead(self) -> bool:
        return self.dead

    def draw(self, screen: pygame.Surface):
        # Fade out over time
        t = max(0.0, min(1.0, 1.0 - self.age / self.lifetime))
        alpha = int(180 * t)

        # Draw on a temporary surface to get alpha
        diameter = int(self.radius * 2)
        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)

        # soft blue-ish circle, tweak color as you like
        pygame.draw.circle(
            surf,
            (100, 180, 255, alpha),
            (self.radius, self.radius),
            self.radius,
        )

        screen.blit(
            surf,
            (self.pos.x - self.radius, self.pos.y - self.radius),
        )

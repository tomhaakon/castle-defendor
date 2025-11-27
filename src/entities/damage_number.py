import pygame


class DamageNumber:
    def __init__(self, pos, amount, color=(255, 80, 80)):
        self.pos = pygame.Vector2(pos)
        self.amount = amount
        self.color = color
        self.lifetime = 1.6
        self.age = 0.0
        self.velocity = pygame.Vector2(0, -60)
        self.alpha = 255

    def update(self, dt):
        self.age += dt
        self.pos += self.velocity * dt

        t = self.age / self.lifetime

        self.alpha = max(0, int(255 * (1 - t)))

    def is_dead(self):
        return self.age >= self.lifetime or self.alpha <= 0

    def draw(self, surface, font):
        if self.alpha <= 0:
            return

        text_surf = font.render(str(int(self.amount)), True, self.color)
        text_surf.set_alpha(self.alpha)
        rect = text_surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        surface.blit(text_surf, rect)

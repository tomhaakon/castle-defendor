import pygame
from config import WIDTH, HEIGHT


class ActionBar:
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font = font  # used for gold amount text

        # === Container ===
        self.hotbar_container_color = (255, 255, 0)
        hotbar_container_size = pygame.Vector2(60, 180)

        x = WIDTH - hotbar_container_size.x - 20
        y = HEIGHT - hotbar_container_size.y - 280

        self.hotbar_container = pygame.Rect(
            x, y, hotbar_container_size.x, hotbar_container_size.y
        )

        # === Icon layout ===
        self.icon_size = (80, 80)  # how big icons will be drawn
        self.icon_spacing = 10

        # === Load icon images ===
        # (change paths/names to match your actual files)
        self.img_shop = pygame.image.load("assets/ui/icon_shop.png").convert_alpha()
        self.img_gold = pygame.image.load("assets/ui/icon_gold.png").convert_alpha()
        self.img_next = pygame.image.load(
            "assets/ui/icon_next_wave.png"
        ).convert_alpha()

        # Scale icons to a consistent size
        self.img_shop = pygame.transform.scale(self.img_shop, self.icon_size)
        self.img_gold = pygame.transform.scale(self.img_gold, self.icon_size)
        self.img_next = pygame.transform.scale(self.img_next, self.icon_size)

        # === Build icon rects & metadata ===
        self.icons = []
        self._create_icons()

    def _create_icons(self):
        """Create rects & metadata for shop, gold, next wave icons."""
        cx = self.hotbar_container.x + 10
        cy = self.hotbar_container.y + 10

        # SHOP ICON
        self.icons.append(
            {
                "name": "shop",
                "rect": pygame.Rect(cx, cy, *self.icon_size),
                "image": self.img_shop,
                "type": "button",
            }
        )

        # GOLD ICON
        cy += self.icon_size[1] + self.icon_spacing
        self.icons.append(
            {
                "name": "gold",
                "rect": pygame.Rect(cx, cy, *self.icon_size),
                "image": self.img_gold,
                "type": "display",
            }
        )

        # NEXT WAVE ICON
        cy += self.icon_size[1] + self.icon_spacing
        self.icons.append(
            {
                "name": "next_wave",
                "rect": pygame.Rect(cx, cy, *self.icon_size),
                "image": self.img_next,
                "type": "button",
            }
        )

    # ---------- INPUT ----------
    def handle_click(self, mouse_pos) -> str | None:
        """Return the name of the icon that was clicked, or None."""
        for icon in self.icons:
            if icon["rect"].collidepoint(mouse_pos):
                print(f"{icon['name']} icon clicked")
                return icon["name"]
        return None

    # ---------- DRAW ----------
    def draw(self, gold_amount: int):
        # Draw background container
        for icon in self.icons:
            rect = icon["rect"]
            img = icon["image"]
            self.screen.blit(img, rect)

            # Special handling for gold: draw the amount underneath
            if icon["name"] == "gold":
                text_surf = self.font.render(str(gold_amount), True, (0, 0, 0))
                text_rect = text_surf.get_rect(midtop=(rect.centerx, rect.bottom + 2))
                self.screen.blit(text_surf, text_rect)

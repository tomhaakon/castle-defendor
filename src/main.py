import pygame

# -----------------------------
# CONFIG / CONSTANTS
# -----------------------------
WIDTH, HEIGHT = 1280, 720
FPS = 60

BOTTOM_FRACTION = 1 / 4  # bottom quarter is castle
ENEMY_SIZE = 40
BASE_ENEMY_SPEED = 120


DEFENCE_STATS = {
    "archer": {
        "damage": 8,
        "range": 300,
        "cooldown": 0.4,
        "proj_speed": 450,
        "color": (255, 255, 0),
    },
    "cannon": {
        "damage": 25,
        "range": 220,
        "cooldown": 1.1,
        "proj_speed": 350,
        "color": (200, 200, 200),
    },
    "mage": {
        "damage": 12,
        "range": 280,
        "cooldown": 0.7,
        "proj_speed": 400,
        "color": (150, 80, 255),
    },
}

DEFENCE_TYPES = ["archer", "cannon", "mage"]


# -----------------------------
# ENEMY CLASS
# -----------------------------
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
        """Update enemy movement and collision with castle."""
        if self.is_dead:
            return

        if self.state == "moving":
            # move down
            self.pos.y += self.speed * dt

            rect = self.get_rect()
            if rect.colliderect(castle_rect):
                self.state = "attacking"
                # snap to top of castle
                self.pos.y = castle_rect.top - ENEMY_SIZE / 2

    def take_damage(self, amount):
        if self.is_dead:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True

    def draw(self, surface):
        if self.is_dead:
            return

        rect = self.get_rect()
        if self.state == "attacking":
            color = (50, 200, 50)  # green
        else:
            color = (200, 50, 50)  # red
        pygame.draw.rect(surface, color, rect)

        # hp text on top
        font = pygame.font.SysFont(None, 18)
        txt = font.render(str(int(self.hp)), True, (255, 255, 255))
        txt_rect = txt.get_rect(center=(rect.centerx, rect.top - 10))
        surface.blit(txt, txt_rect)


# -----------------------------
# DEFENCE CLASS
# -----------------------------


class Defence:
    def __init__(self, x, y, defence_type="archer"):
        self.pos = pygame.Vector2(x, y)
        self.defence_type = defence_type

        stats = DEFENCE_STATS[defence_type]

        self.damage = stats["damage"]
        self.range = stats["range"]

        self.attack_cooldown = stats["cooldown"]
        self.projectile_speed = stats["proj_speed"]
        self.projectile_color = stats["color"]

        self.time_since_last_shot = 0.0

    def update(self, dt, enemies, projectiles):
        # cd
        self.time_since_last_shot += dt
        if self.time_since_last_shot < self.attack_cooldown:
            return

        # find enemy in  range
        target = None
        for enemy in enemies:
            if enemy.is_dead:
                continue

            if self.pos.distance_to(enemy.pos) <= self.range:
                target = enemy
                break

        if target is None:
            return

        # fire projectile
        direction = target.pos - self.pos
        if direction.length_squared() == 0:
            return

        direction = direction.normalize()
        velocity = direction * self.projectile_speed

        projectiles.append(
            Projectile(self.pos, velocity, self.damage, max_distance=self.range)
        )
        self.time_since_last_shot = 0.0

    def draw(self, surface):
        rect = pygame.Rect(0, 0, 30, 30)
        rect.center = self.pos
        pygame.draw.rect(surface, (80, 160, 220), rect, border_radius=4)


# -----------------------------
# PROJECTILE  CLASS
# -----------------------------
class Projectile:
    def __init__(
        self, pos, velocity, damage, radius=5, max_distance=250, color=(255, 255, 0)
    ):
        self.pos = pygame.Vector2(pos)
        self.start_pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.damage = damage
        self.radius = radius
        self.max_distance = max_distance
        self.color = color
        self.is_dead = False

    def update(self, dt, enemies):
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
                self.is_dead = True
                break

    def draw(self, surface):
        if self.is_dead:
            return
        pygame.draw.circle(
            surface, (255, 255, 0), (int(self.pos.x), int(self.pos.y)), self.radius
        )


# -----------------------------
# GAME CLASS
# -----------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("CastleDefend0r")

        self.clock = pygame.time.Clock()
        self.running = True

        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 72)

        self.slot_labels = ["slot_1", "slot_2", "slot_3", "slot_4", "slot_5"]

        # wave / enemies
        self.enemies: list[Enemy] = []
        self.wave_number = 0

        # castle hp
        self.castle_max_hp = 100.0
        self.castle_hp = self.castle_max_hp

        # dps per attacking enemy
        self.castle_damage_per_second_per_enemy = 5.0

        # game state
        self.is_game_over = False

        # defence
        self.defences: list[Defence] = []
        self.projectiles: list[Projectile] = []

        self.slot_defences: list[Defence | None] = [None] * len(self.slot_labels)
        self.selected_slot: int | None = None

        self.init_defence()

    # ---------- RECT HELPERS ----------
    def get_spawn_rect(self):
        spawn_width = WIDTH - 100
        spawn_height = 80
        x = (WIDTH - spawn_width) // 2
        y = 0
        return pygame.Rect(x, y, spawn_width, spawn_height)

    def get_castle_rect(self):
        bottom_height = int(HEIGHT * BOTTOM_FRACTION)
        top_height = HEIGHT - bottom_height
        return pygame.Rect(0, top_height, WIDTH, bottom_height)

    def get_wave_button_rect(self):
        castle_rect = self.get_castle_rect()
        button_width = 220
        button_height = 50
        x = WIDTH - button_width - 20
        y = castle_rect.top + 20
        return pygame.Rect(x, y, button_width, button_height)

    # ---------- SLOT GEOMETRY -----
    def get_slot_rects(self):
        width, height = self.screen.get_size()
        bottom_height = int(height * BOTTOM_FRACTION)
        top_height = height - bottom_height

        hud_y = top_height
        hud_height = bottom_height

        num_slots = len(self.slot_labels)

        slot_width = 100
        slot_height = 100
        margin_x = 40

        if num_slots > 1:
            spacing = (width - 2 * margin_x - num_slots * slot_width) // (num_slots - 1)
        else:
            spacing = 0

        base_y = hud_y + (hud_height - slot_height) // 2
        y_offsets = [30, 15, 0, 15, 30]

        rects = []
        for i in range(num_slots):
            x = margin_x + i * (slot_width + spacing)
            y = base_y + y_offsets[i % len(y_offsets)]
            rects.append(pygame.Rect(x, y, slot_width, slot_height))

        return rects

    def get_slot_index_at_pos(self, pos):
        for i, rect in enumerate(self.get_slot_rects()):
            if rect.collidepoint(pos):
                return i
        return None

    def cycle_slot_defence_type(self, slot_index: int):
        """Right-click: change the defence type in this slot (archer/cannon/mage)."""
        defence = self.slot_defences[slot_index]

        # If slot is empty, create a default one (archer)
        if defence is None:
            slot_rects = self.get_slot_rects()
            castle_rect = self.get_castle_rect()
            rect = slot_rects[slot_index]
            x = rect.centerx
            y = castle_rect.top + 40
            self.slot_defences[slot_index] = Defence(x, y, defence_type="archer")
        else:
            # Cycle to next type
            current_type = defence.defence_type
            try:
                idx = DEFENCE_TYPES.index(current_type)
            except ValueError:
                idx = 0
            new_type = DEFENCE_TYPES[(idx + 1) % len(DEFENCE_TYPES)]

            # Rebuild the defence with same position but new type
            x, y = defence.pos.x, defence.pos.y
            self.slot_defences[slot_index] = Defence(x, y, defence_type=new_type)

        # Refresh positions + flat list
        self.update_defence_positions_from_slots()

    # ---------- DEFENCE ---------
    def init_defence(self):
        slot_rects = self.get_slot_rects()
        castle_rect = self.get_castle_rect()

        for i, rect in enumerate(slot_rects):
            x = rect.centerx
            y = castle_rect.top + 40
            defence = Defence(x, y)
            self.slot_defences[i] = defence

        self.defences = [d for d in self.slot_defences if d is not None]

    def update_defence_positions_from_slots(self):
        slot_rects = self.get_slot_rects()
        castle_rect = self.get_castle_rect()

        for i, defence in enumerate(self.slot_defences):
            if defence is not None:
                defence.pos.x = slot_rects[i].centerx
                defence.pos.y = castle_rect.top + 40

        self.defences = [d for d in self.slot_defences if d is not None]

    # ---------- WAVES ----------
    def spawn_wave(self):

        if self.is_game_over:
            return

        if not self.can_spawn_wave():
            print("Cannot spawn wave: game over or incoming wave")
            return

        self.wave_number += 1
        spawn_rect = self.get_spawn_rect()

        num_enemies = 3 + self.wave_number * 2
        speed_base = BASE_ENEMY_SPEED + self.wave_number * 10

        for i in range(num_enemies):
            x = spawn_rect.left + (i + 0.5) * (spawn_rect.width / num_enemies)
            y = spawn_rect.bottom + ENEMY_SIZE / 2
            enemy = Enemy(x, y, speed_base)
            self.enemies.append(enemy)

    def can_spawn_wave(self) -> bool:

        if self.is_game_over:
            return False
        if len(self.enemies) > 0:
            return False

        return True

    # ---------- MAIN LOOP ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    # ---------- EVENTS ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_SPACE:
                    if self.can_spawn_wave():
                        self.spawn_wave()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos

                # Right click: change defence type in slot
                if event.button == 3:
                    slot_index = self.get_slot_index_at_pos(mouse_pos)
                    if slot_index is not None:
                        self.cycle_slot_defence_type(slot_index)
                    return

                # Left click: wave button or slot select / swap
                if event.button == 1:
                    # Wave button click?
                    if self.get_wave_button_rect().collidepoint(mouse_pos):
                        if self.can_spawn_wave():
                            self.spawn_wave()
                        return

                    # Slot click?
                    slot_index = self.get_slot_index_at_pos(mouse_pos)
                    if slot_index is not None:
                        if self.selected_slot is None:
                            # select this slot
                            self.selected_slot = slot_index
                        else:
                            # swap defences between slots
                            a = self.selected_slot
                            b = slot_index
                            self.slot_defences[a], self.slot_defences[b] = (
                                self.slot_defences[b],
                                self.slot_defences[a],
                            )
                            self.selected_slot = None
                            self.update_defence_positions_from_slots()

    # ---------- UPDATE ----------
    def update(self, dt):
        castle_rect = self.get_castle_rect()

        if not self.is_game_over:

            # update enemies and calc dmg
            damage_this_frame = 0.0
            for enemy in self.enemies:
                enemy.update(dt, castle_rect)

                if enemy.state == "attacking" and self.castle_hp > 0:
                    damage_this_frame += self.castle_damage_per_second_per_enemy * dt

            # apply dmg
            if damage_this_frame > 0:
                self.castle_hp = max(0.0, self.castle_hp - damage_this_frame)

            if self.castle_hp <= 0:
                self.castle_hp = 0
                self.is_game_over = True

            for defence in self.defences:
                defence.update(dt, self.enemies, self.projectiles)

            for proj in self.projectiles:
                proj.update(dt, self.enemies)

            self.projectiles = [p for p in self.projectiles if not p.is_dead]
            self.enemies = [e for e in self.enemies if not e.is_dead]

            # later: remove dead enemies

    # ---------- DRAW ----------
    def draw(self):
        self.draw_background(self.screen)
        self.draw_spawn_area(self.screen)
        self.draw_slots(self.screen, self.font, self.slot_labels)

        castle_rect = self.get_castle_rect()
        pygame.draw.rect(self.screen, (120, 120, 150), castle_rect, width=1)

        self.draw_castle_hp(self.screen, self.font)
        self.draw_wave_button(self.screen, self.font, self.wave_number)

        for defence in self.defences:
            defence.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for projectile in self.projectiles:
            projectile.draw(self.screen)

        if self.is_game_over:
            self.draw_game_overlay(self.screen)

        pygame.display.flip()

    # ---------- DRAW HELPERS ----------
    @staticmethod
    def draw_background(screen):
        bottom_height = int(HEIGHT * BOTTOM_FRACTION)
        top_height = HEIGHT - bottom_height

        pygame.draw.rect(screen, (80, 80, 80), pygame.Rect(0, 0, WIDTH, top_height))
        pygame.draw.rect(
            screen,
            (50, 50, 50),
            pygame.Rect(0, top_height, WIDTH, bottom_height),
        )

    def draw_spawn_area(self, screen):
        rect = self.get_spawn_rect()
        pygame.draw.rect(screen, (100, 60, 60), rect)

    def draw_wave_button(self, screen, font, wave_number):
        rect = self.get_wave_button_rect()

        if self.can_spawn_wave():
            bg_color = (100, 100, 130)
            text_color = (255, 255, 255)
            label = f"Next wave ({wave_number +1}) - SPACE"
        else:
            bg_color = (60, 60, 80)
            text_color = (180, 180, 180)
            label = "Wave incoming.."

        pygame.draw.rect(screen, bg_color, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, width=2)

        text_surf = font.render(label, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def draw_castle_hp(self, screen, font):
        castle_rect = self.get_castle_rect()

        bar_width = 300
        bar_height = 20
        x = 20
        y = castle_rect.top + 20

        # background
        outline_rect = pygame.Rect(x, y, bar_width, bar_height)
        pygame.draw.rect(screen, (0, 0, 0), outline_rect, width=2)

        # fill hp part
        ratio = 0 if self.castle_max_hp == 0 else self.castle_hp / self.castle_max_hp
        fill_width = int(bar_width * ratio)
        fill_rect = pygame.Rect(x + 1, y + 1, max(0, fill_width - 2), bar_height - 2)

        # color
        r = int(200 * (1 - ratio))
        g = int(200 * ratio)
        color = (r, g, 0)
        pygame.draw.rect(screen, color, fill_rect)

        # text
        hp_text = f"Castle:HO {int(self.castle_hp)}/{int(self.castle_max_hp)}"
        text_surf = font.render(hp_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(midleft=(x, y - 8))
        screen.blit(text_surf, text_rect)

    def draw_game_overlay(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # semi-transparent black
        screen.blit(overlay, (0, 0))

        # big text
        text_surf = self.big_font.render("GAME OVER", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))

        screen.blit(text_surf, text_rect)

        # small hint

        small = self.font.render("Press ESC to quit", True, (220, 220, 220))
        small_rect = small.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))

        screen.blit(small, small_rect)

    def draw_slots(self, screen, font, labels):
        slot_rects = self.get_slot_rects()

        for i, (label, rect) in enumerate(zip(labels, slot_rects)):
            defence = self.slot_defences[i]
            has_defence = defence is not None

            fill_color = (150, 150, 180) if has_defence else (120, 120, 120)

            if has_defence:
                fill_color = (140, 140, 170)

            if self.selected_slot == i:
                border_color = (255, 255, 0)
                border_width = 3
            else:
                border_color = (0, 0, 0)
                border_width = 2

            pygame.draw.rect(screen, fill_color, rect)
            pygame.draw.rect(screen, border_color, rect, width=border_width)

            label_surf = font.render(label, True, (220, 220, 220))
            label_rect = label_surf.get_rect(midleft=(rect.left + 8, rect.top + 12))
            screen.blit(label_surf, label_rect)

            if has_defence:
                icon_rect = pygame.Rect(0, 0, 32, 32)
                icon_rect.center = rect.center
                pygame.draw.rect(
                    screen, defence.projectile_color, icon_rect, border_radius=6
                )
                pygame.draw.rect(screen, (0, 0, 0), icon_rect, width=1, border_radius=6)

                type_letter = {
                    "archer": "A",
                    "cannon": "C",
                    "mage": "M",
                }.get(defence.defence_type, "?")

                icon_text = font.render(type_letter, True, (0, 0, 0))
                icon_text_rect = icon_text.get_rect(center=icon_rect.center)
                screen.blit(icon_text, icon_text_rect)


# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    game = Game()
    game.run()

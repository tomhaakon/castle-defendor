# src/core/game.py
import pygame
from pygame.time import wait

from config import (
    WIDTH,
    HEIGHT,
    FPS,
    BOTTOM_FRACTION,
    DEFENCE_STATS,
    DEFENCE_TYPES,
    BASE_ENEMY_SPEED,
    ENEMY_SIZE,
    GOLD_PER_KILL,
    GOLD_PER_WAVE_CLEAR,
)
from entities.enemy import Enemy
from entities.defence import Defence
from entities.projectile import Projectile
from entities.damage_number import DamageNumber

from ui.slots import (
    compute_slot_rects,
    get_slot_index_at_pos,
    draw_slots as draw_slots_ui,
    build_slot_menu,
    draw_slot_menu as draw_slot_menu_ui,
)
from ui.hud import (
    draw_background,
    draw_castle_hp,
    draw_damage_numbers,
    draw_game_overlay,
    draw_gold,
    draw_spawn_area,
    draw_wave_button,
)
from ui.shop import draw_shop_popup, get_shop_popup_layout


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
        self.swap_source_slot: int | None = None

        self.slot_menu_open: bool = False
        self.slot_menu_slot: int | None = None
        self.slot_menu_items: list[tuple[str, pygame.Rect]] = []

        self.init_defence()

        self.gold = 200
        self.damage_numbers: list[DamageNumber] = []

        self.owned_defences: list[tuple[str, int]] = []

        self.choose_defence_menu_open: bool = False
        self.choose_defence_menu_slot: int | None = None
        self.choose_defence_menu_items: list[tuple[str, pygame.Rect, int]] = []

        self.shop_open: bool = False

    def try_buy_defence(self, defence_type: str):
        cost = DEFENCE_STATS[defence_type]["shop_cost"]
        if self.gold < cost:
            print("Not enoguh gold")
            return

        self.gold -= cost
        self.owned_defences.append((defence_type, 1))
        print("bought new defence", defence_type, "Lv1")

    def open_slot_menu(self, slot_index: int):
        self.slot_menu_open = True
        self.slot_menu_slot = int(slot_index)
        self.selected_slot = slot_index

        slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))
        slot_rect = slot_rects[slot_index]

        labels: list[str] = []
        defence = self.slot_defences[slot_index]

        if defence is None:
            labels.append("Add")
        else:
            # swap always the same
            labels.append("Swap")

            # upgrade → show price
            upg_cost = defence.get_upgrade_cost()
            labels.append(f"Upgrade ({upg_cost}g)")

            # withdraw
            labels.append("Withdraw")

        self.slot_menu_items = build_slot_menu(slot_rect, labels)

    def close_slot_menu(self):
        self.slot_menu_open = False
        self.slot_menu_slot = None
        self.slot_menu_items = []

    #        self.selected_slot = None

    def open_choose_defence_menu(self, slot_index: int):
        """Popup listing owned_defences to place into this slot."""
        if not self.owned_defences:
            print("No owned defences to place.")
            return

        self.choose_defence_menu_open = True
        self.choose_defence_menu_slot = slot_index
        self.choose_defence_menu_items = []

        slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))
        base_rect = slot_rects[slot_index]

        item_width = 140
        item_height = 24
        padding = 4

        # place menu to the right of the slot
        x = base_rect.right + 8
        y = base_rect.top

        for i, (dtype, level) in enumerate(self.owned_defences):
            # temporary Defence just to ask for its upgrade cost
            temp_def = Defence(0, 0, defence_type=dtype, level=level)
            upg_cost = temp_def.get_upgrade_cost()

            label = f"{dtype.capitalize()} Lv{level}"
            r = pygame.Rect(x, y + i * (item_height + padding), item_width, item_height)
            self.choose_defence_menu_items.append((label, r, i))

    def close_choose_defence_menu(self):
        self.choose_defence_menu_open = False
        self.choose_defence_menu_slot = None
        self.choose_defence_menu_items = []

    def handle_slot_menu_choice(self, slot_index: int, label: str):
        if label == "Swap":
            self.swap_source_slot = slot_index
            self.selected_slot = slot_index
            self.close_slot_menu()
            return

        if label.startswith("Upgrade"):
            self.selected_slot = slot_index
            self.upgrade_selected_slot()
            self.selected_slot = None
            self.close_slot_menu()
            return

        if label == "Withdraw":
            if 0 <= slot_index < len(self.slot_defences):
                defence = self.slot_defences[slot_index]
                if defence is not None:
                    # add its type back to owned list
                    self.owned_defences.append((defence.defence_type, defence.level))
                    # remove from slot
                    self.slot_defences[slot_index] = None
                    self.update_defence_positions_from_slots()

            if self.selected_slot == slot_index:
                self.selected_slot = None

            if self.swap_source_slot == slot_index:
                self.swap_source_slot = None

            self.close_slot_menu()
            return

        if label == "Add":
            self.selected_slot = slot_index
            self.close_slot_menu()
            self.open_choose_defence_menu(slot_index)
            return

    def draw_choose_defence_menu(self, screen):
        if not self.choose_defence_menu_open:
            return

        for label, rect, _owned_index in self.choose_defence_menu_items:
            pygame.draw.rect(screen, (70, 70, 100), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, width=1)

            text_surf = self.font.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

    def draw_slot_menu(self, screen):
        if not self.slot_menu_open:
            return
        draw_slot_menu_ui(screen, self.font, self.slot_menu_items)

    def upgrade_selected_slot(self):
        if self.selected_slot is None:
            return

        defence = self.slot_defences[self.selected_slot]
        if defence is None:
            return

        cost = defence.get_upgrade_cost()
        if self.gold < cost:
            print("Not enough gold for upgrade:", cost)
            return

        self.gold -= cost
        defence.upgrade()
        print(
            f"Upgraded {defence.defence_type} to level {defence.level}, spent {cost} gold (remaining {self.gold})"
        )

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
        y = castle_rect.top - 70
        return pygame.Rect(x, y, button_width, button_height)

    def get_shop_button_rect(self):
        width = 140
        height = 45
        x = WIDTH - 200  # left side of screen
        y = HEIGHT - height - 120  # bottom-left corner

        return pygame.Rect(x, y, width, height)

    # ---------- SLOT GEOMETRY -----

    def cycle_slot_defence_type(self, slot_index: int):
        """Right-click: change the defence type in this slot (archer/cannon/mage)."""
        defence = self.slot_defences[slot_index]

        # If slot is empty, create a default one (archer)
        if defence is None:
            slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))
            rect = slot_rects[slot_index]
            x = rect.centerx
            y = rect.centery
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
            level = defence.level
            self.slot_defences[slot_index] = Defence(
                x, y, defence_type=new_type, level=level
            )

        # Refresh positions + flat list
        self.update_defence_positions_from_slots()

    # ---------- DEFENCE ---------
    def init_defence(self):
        slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))

        for i, rect in enumerate(slot_rects):
            x = rect.centerx
            y = rect.centery
            defence_type = "archer"

            defence = Defence(x, y, defence_type=defence_type)
            self.slot_defences[i] = defence

        self.defences = [d for d in self.slot_defences if d is not None]

    def update_defence_positions_from_slots(self):
        slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))

        for i, defence in enumerate(self.slot_defences):
            if defence is not None:
                rect = slot_rects[i]

                defence.pos.x = rect.centerx
                defence.pos.y = rect.centery

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

        num_enemies = 1 + self.wave_number * 2
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

    def handle_shop_popup_click(self, mouse_pos):
        # if shop isn't open, nothing to do
        if not self.shop_open:
            return

        popup_rect, shop_rects, owned_rects, close_rect = get_shop_popup_layout(
            self.owned_defences
        )

        # close button
        if close_rect.collidepoint(mouse_pos):
            self.shop_open = False
            return

        # click outside popup -> close
        if not popup_rect.collidepoint(mouse_pos):
            self.shop_open = False
            return

        # shop area
        for dtype, rect in shop_rects.items():
            if rect.collidepoint(mouse_pos):
                self.try_buy_defence(dtype)
                return

        # owned area (for now just select / do nothing special,
        # you can extend later)
        for owned_index, rect in owned_rects:
            if rect.collidepoint(mouse_pos):
                dtype, level = self.owned_defences[owned_index]
                print(f"Clicked owned defence: {dtype} Lv{level}")
                return

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
                if event.key == pygame.K_u:
                    self.upgrade_selected_slot()
                # NEW: toggle shop popup
                if event.key == pygame.K_i:
                    self.shop_open = not self.shop_open
                    # when opening shop, close other menus
                    if self.shop_open:
                        self.close_slot_menu()
                        self.close_choose_defence_menu()
                        self.swap_source_slot = None
                        self.selected_slot = None

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos

                if event.button == 1:
                    # If shop popup is open, it has priority for clicks
                    if self.shop_open:
                        self.handle_shop_popup_click(mouse_pos)
                        return

                    # shop buttton
                    if self.get_shop_button_rect().collidepoint(mouse_pos):
                        self.shop_open = True
                        self.close_slot_menu()
                        self.close_choose_defence_menu()
                        self.swap_source_slot = None
                        self.selected_slot = None
                        return

                    # 1) If choose-defence menu is open, handle it FIRST (modal)
                    if self.choose_defence_menu_open:
                        clicked_any = False
                        for label, rect, owned_index in self.choose_defence_menu_items:
                            if rect.collidepoint(mouse_pos):
                                clicked_any = True
                                if self.choose_defence_menu_slot is not None:
                                    slot_index = self.choose_defence_menu_slot
                                    # place new Defence in that slot
                                    slot_rects = compute_slot_rects(
                                        self.screen, len(self.slot_labels)
                                    )
                                    srect = slot_rects[slot_index]

                                    dtype, level = self.owned_defences[owned_index]
                                    new_def = Defence(
                                        srect.centerx,
                                        srect.centery,
                                        defence_type=dtype,
                                        level=level,
                                    )
                                    self.slot_defences[slot_index] = new_def
                                    self.update_defence_positions_from_slots()
                                    # remove from owned list
                                    del self.owned_defences[owned_index]

                                self.close_choose_defence_menu()
                                self.selected_slot = None
                                return

                        # clicked outside choose menu -> just close it and stop
                        self.close_choose_defence_menu()
                        self.selected_slot = None
                        return

                    # 3) Wave button
                    if self.get_wave_button_rect().collidepoint(mouse_pos):
                        if self.can_spawn_wave():
                            self.spawn_wave()

                        self.close_slot_menu()
                        self.swap_source_slot = None
                        self.selected_slot = None
                        return

                    # 4) Swap target selection
                    if self.swap_source_slot is not None:
                        slot_rects = compute_slot_rects(
                            self.screen, len(self.slot_labels)
                        )
                        slot_index = get_slot_index_at_pos(slot_rects, mouse_pos)

                        if slot_index is not None:
                            if slot_index == self.swap_source_slot:
                                # clicked same slot => cancel swap
                                self.swap_source_slot = None
                                self.selected_slot = None
                            else:
                                # perform swap
                                a = self.swap_source_slot
                                b = slot_index
                                self.slot_defences[a], self.slot_defences[b] = (
                                    self.slot_defences[b],
                                    self.slot_defences[a],
                                )
                                self.swap_source_slot = None
                                self.selected_slot = None

                            self.close_slot_menu()
                            return
                        else:
                            # clicked somewhere else -> cancel swap + close menu
                            self.swap_source_slot = None
                            self.selected_slot = None
                            self.close_slot_menu()
                            return

                    # 5) Slot popup menu (Swap / Upgrade / Destroy / Add)
                    if self.slot_menu_open:
                        for label, rect in self.slot_menu_items:
                            if rect.collidepoint(mouse_pos):
                                if self.slot_menu_slot is not None:
                                    self.handle_slot_menu_choice(
                                        self.slot_menu_slot, label
                                    )
                                return
                        # clicked outside menu -> close
                        self.close_slot_menu()
                        self.selected_slot = None

                    # 6) Normal slot click (open menu)
                    slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))
                    slot_index = get_slot_index_at_pos(slot_rects, mouse_pos)

                    if slot_index is not None:
                        self.open_slot_menu(slot_index)
                        return

                    # Clicked somewhere else -> reset
                    self.swap_source_slot = None
                    self.selected_slot = None
                    self.close_slot_menu()
                    return

                # Right click here

    # ---------- UPDATE ----------
    def update(self, dt):
        castle_rect = self.get_castle_rect()

        if not self.is_game_over:

            had_enemies_before = len(self.enemies) > 0

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

            alive_before = sum(1 for e in self.enemies if not e.is_dead)

            for proj in self.projectiles:
                proj.update(dt, self.enemies, self.damage_numbers)

            for dn in self.damage_numbers:
                dn.update(dt)
            self.damage_numbers = [dn for dn in self.damage_numbers if not dn.is_dead()]

            alive_after = sum(1 for e in self.enemies if not e.is_dead)
            killed_this_frame = alive_before - alive_after
            if killed_this_frame > 0:
                self.gold += killed_this_frame * GOLD_PER_KILL

            self.projectiles = [p for p in self.projectiles if not p.is_dead]
            self.enemies = [e for e in self.enemies if not e.is_dead]

            if had_enemies_before and len(self.enemies) == 0 and not self.is_game_over:
                bonus = GOLD_PER_WAVE_CLEAR * max(1, self.wave_number)
                self.gold += bonus

    # ---------- DRAW ----------
    def draw(self):
        draw_background(self.screen)
        draw_spawn_area(self.screen, self.get_spawn_rect())

        slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))
        draw_slots_ui(
            self.screen,
            self.font,
            self.slot_labels,
            self.slot_defences,
            self.selected_slot,
            slot_rects,
        )

        castle_rect = self.get_castle_rect()
        pygame.draw.rect(self.screen, (120, 120, 150), castle_rect, width=1)

        self.draw_castle_hp(self.screen, self.font)
        self.draw_gold(self.screen, self.font)
        self.draw_wave_button(self.screen, self.font, self.wave_number)
        self.draw_shop_button(self.screen, self.font)

        for defence in self.defences:
            defence.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for projectile in self.projectiles:
            projectile.draw(self.screen)

        draw_damage_numbers(self.screen, self.font, self.damage_numbers)

        self.draw_slot_menu(self.screen)
        self.draw_choose_defence_menu(self.screen)

        draw_shop_popup(self.screen, self.font, self.shop_open, self.owned_defences)

        if self.is_game_over:
            draw_game_overlay(self.screen, self.font, self.big_font)

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

    def draw_shop_button(self, screen, font):
        rect = self.get_shop_button_rect()

        pygame.draw.rect(screen, (100, 150, 80), rect)  # green-ish
        pygame.draw.rect(screen, (0, 0, 0), rect, width=2)

        label = "Open Shop (I)"
        surf = font.render(label, True, (255, 255, 255))
        text_rect = surf.get_rect(center=rect.center)
        screen.blit(surf, text_rect)

    def draw_spawn_area(self, screen):
        rect = self.get_spawn_rect()
        pygame.draw.rect(screen, (100, 60, 60), rect)

    def draw_wave_button(self, screen, font, wave_number):
        rect = self.get_wave_button_rect()

        if self.can_spawn_wave():
            bg_color = (100, 100, 130)
            text_color = (255, 255, 255)
            label = f"Ready for next wave! ({wave_number +1})"
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
        slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))
        draw_slots_ui(
            screen,
            font,
            labels,
            self.slot_defences,
            self.selected_slot,
            slot_rects,
        )

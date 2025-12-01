# src/core/game.py
import pygame
from pygame.time import wait

import ui.action_bar

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

        self.fields_bg = pygame.image.load("assets/fields.png").convert()
        self.castle_wall_img = pygame.image.load(
            "assets/castle_wall_img.png"
        ).convert_alpha()

        # compute playfield height once
        castle_rect = self.get_castle_rect()

        playfield_height = castle_rect.top
        self.fields_bg_scaled = pygame.transform.smoothscale(
            self.fields_bg, (WIDTH, playfield_height)
        )
        self.init_defence()

        self.gold = 200
        self.damage_numbers: list[DamageNumber] = []

        self.owned_defences: list[tuple[str, int]] = []

        self.choose_defence_menu_open: bool = False
        self.choose_defence_menu_slot: int | None = None
        self.choose_defence_menu_items: list[tuple[str, pygame.Rect, int]] = []

        self.shop_open: bool = False

        self.action_bar = ui.action_bar.ActionBar(self.screen, self.font)

    def get_nearest_defence(self, enemy) -> Defence | None:
        living_defences = [d for d in self.defences if not d.is_dead()]

        if not living_defences:
            return None

        def sqr_dist(d: Defence):
            dx = enemy.pos.x - d.pos.x
            dy = enemy.pos.y - d.pos.y
            return dx * dx + dy * dy

        return min(living_defences, key=sqr_dist)

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
        print()

    # ---------- RECT HELPERS ----------
    def get_spawn_rect(self):
        spawn_width = WIDTH - 100
        spawn_height = 80
        x = (WIDTH - spawn_width) // 2
        y = 0
        return pygame.Rect(x, y, spawn_width, spawn_height)

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

                    clicked_icon = self.action_bar.handle_click(mouse_pos)
                    if clicked_icon == "shop":
                        self.shop_open = True
                        # maybe also close other menus, etc.
                        return

                    if clicked_icon == "next_wave":
                        if self.can_spawn_wave():
                            self.spawn_wave()
                        return

                    if clicked_icon == "gold":
                        print(f"Current gold: {self.gold}")
                        # or later, open some stats/tooltip
                        return

                    # If shop popup is open, it has priority for clicks
                    if self.shop_open:
                        self.handle_shop_popup_click(mouse_pos)
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
            damage_to_castle = 0.0
            damage_per_enemy = self.castle_damage_per_second_per_enemy

            for enemy in self.enemies:
                # ---- 1) Find nearest target among ALL defences + castle ----
                ex, ey = enemy.pos.x, enemy.pos.y

                # start with castle as default target
                castle_cx, castle_cy = castle_rect.center
                best_dist_sqr = (ex - castle_cx) ** 2 + (ey - castle_cy) ** 2
                best_target_kind = "castle"
                best_target_def = None
                target_x, target_y = castle_cx, castle_cy

                # check each living defence
                for d in self.defences:
                    if d.is_dead():
                        continue
                    dx = ex - d.pos.x
                    dy = ey - d.pos.y
                    dist_sqr = dx * dx + dy * dy
                    if dist_sqr < best_dist_sqr:
                        best_dist_sqr = dist_sqr
                        best_target_kind = "defence"
                        best_target_def = d
                        target_x, target_y = d.pos.x, d.pos.y

                # ---- 2) Move enemy toward the chosen target ----
                target_rect = pygame.Rect(0, 0, 10, 10)
                target_rect.center = (target_x, target_y)

                enemy.update(dt, target_rect)

                # ---- 3) Apply damage if the enemy is in attacking state ----
                if enemy.state == "attacking":
                    if best_target_kind == "defence" and best_target_def is not None:
                        best_target_def.take_damage(damage_per_enemy * dt)
                    elif best_target_kind == "castle" and self.castle_hp > 0:
                        damage_to_castle += damage_per_enemy * dt

            if damage_to_castle > 0:
                self.castle_hp = max(0.0, self.castle_hp - damage_to_castle)

            if self.castle_hp <= 0:
                self.castle_hp = 0
                self.is_game_over = True

            for i, d in enumerate(self.slot_defences):
                if d is not None and d.is_dead():
                    self.slot_defences[i] = None

            self.defences = [d for d in self.defences if not d.is_dead()]

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

        # Layout rects
        hp_bar_rect = self.get_hp_bar_rect()
        castle_rect = self.get_castle_rect()
        playfield_rect = pygame.Rect(0, 0, WIDTH, castle_rect.top)

        # Background that matches these rects
        draw_background(self.screen, castle_rect, hp_bar_rect)

        # --- Tile fields.png in the playfield without stretching ---
        tex = self.fields_bg
        tw, th = tex.get_width(), tex.get_height()

        for y in range(0, playfield_rect.height, th):
            for x in range(0, playfield_rect.width, tw):
                self.screen.blit(tex, (x, y))

        ttw, tth = self.castle_wall_img.get_width(), self.castle_wall_img.get_height()

        for y in range(castle_rect.y, castle_rect.bottom, tth):
            for x in range(castle_rect.x, castle_rect.right, ttw):
                self.screen.blit(self.castle_wall_img, (x, y))

        # Spawn area on top of background
        #    draw_spawn_area(self.screen, self.get_spawn_rect())

        slot_rects = compute_slot_rects(self.screen, len(self.slot_labels))

        draw_slots_ui(
            self.screen,
            self.font,
            self.slot_labels,
            self.slot_defences,
            self.selected_slot,
            slot_rects,
        )

        pygame.draw.rect(self.screen, (120, 120, 150), castle_rect, width=1)

        # --- Castle HP full-width at bottom ---
        draw_castle_hp(
            self.screen,
            self.font,
            self.castle_hp,
            self.castle_max_hp,
            hp_bar_rect,
        )

        selected_defence = (
            self.slot_defences[self.selected_slot]
            if self.selected_slot is not None
            else None
        )

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

        # show upcoming wave under the button
        self.action_bar.draw(self.gold, self.wave_number + 1)
        pygame.display.flip()

    # ---------- DRAW HELPERS ----------

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

    # ---------- RECT HELPERS ----------
    # ---------- RECT HELPERS ----------
    def get_hp_bar_rect(self):
        """Bottom-most row: full-width castle HP bar."""
        bar_height = 44
        return pygame.Rect(0, HEIGHT - bar_height, WIDTH, bar_height)

    def get_castle_rect(self):
        """Castle area sits directly above the HP bar."""
        castle_height = 140  # tweak if you want it taller/shorter
        hp_bar_rect = self.get_hp_bar_rect()
        y = hp_bar_rect.top - castle_height
        return pygame.Rect(0, y, WIDTH, castle_height)

# src/ui/slots.py
import pygame
from config import HEIGHT, WIDTH


def compute_slot_rects(screen: pygame.Surface, num_slots: int) -> list[pygame.Rect]:
    """
    Compute a horizontal row of slot rects, centered on X,
    but placed higher up on the screen (above the castle area).
    """
    slot_width = 70
    slot_height = 70
    gap = WIDTH / 7

    total_width = num_slots * slot_width + (num_slots - 1) * gap
    start_x = (WIDTH - total_width) // 2

    # --- vertical placement ---
    # We know from the new layout in Game:
    # hp_bar_height = 24
    # ui_row_height = 40
    # castle_height = 120
    hp_bar_height = 24
    ui_row_height = 40
    castle_height = 120
    margin_from_bottom = -50

    # castle_rect.top = HEIGHT - (hp + ui + castle)
    castle_top = HEIGHT - (hp_bar_height + ui_row_height + castle_height)

    # place slots ABOVE the castle, with some margin
    row_y = castle_top - slot_height - margin_from_bottom

    rects: list[pygame.Rect] = []
    x = start_x
    for _ in range(num_slots):
        rects.append(pygame.Rect(x, row_y, slot_width, slot_height))
        x += slot_width + gap

    return rects


def get_slot_index_at_pos(
    slot_rects: list[pygame.Rect], pos: tuple[int, int]
) -> int | None:
    """Return the index of the first slot rect containing pos, or None."""
    for i, rect in enumerate(slot_rects):
        if rect.collidepoint(pos):
            return i
    return None


def draw_slots(
    screen: pygame.Surface,
    font: pygame.font.Font,
    labels: list[str],
    slot_defences: list,
    selected_slot: int | None,
    slot_rects: list[pygame.Rect],
):
    """Draw the HUD slots, defence icons and levels."""
    for i, (label, rect) in enumerate(zip(labels, slot_rects)):
        defence = slot_defences[i]
        has_defence = defence is not None

        fill_color = (150, 150, 180) if has_defence else (120, 120, 120)

        if has_defence:
            fill_color = (140, 140, 170)

        if selected_slot == i:
            border_color = (255, 255, 0)
            border_width = 3
        else:
            border_color = (0, 0, 0)
            border_width = 2

        pygame.draw.rect(screen, fill_color, rect)
        pygame.draw.rect(screen, border_color, rect, width=border_width)

        # slot label top-left
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

            level_text = font.render(f"Lv{defence.level}", True, (255, 255, 255))
            lvl_rect = level_text.get_rect(midbottom=(rect.centerx, rect.bottom - 6))
            screen.blit(level_text, lvl_rect)


def build_slot_menu(
    slot_rect: pygame.Rect, labels: list[str]
) -> list[tuple[str, pygame.Rect]]:
    """Given a slot rect and labels, return menu items (label, rect) for a popup."""
    item_width = 140
    item_height = 26
    padding = 4

    # position menu above the slot by default
    x = slot_rect.left
    y = slot_rect.top - (item_height + padding) * len(labels) - 8

    # if it would go off top of screen, move it below slot instead
    if y < 0:
        y = slot_rect.bottom + 8

    items: list[tuple[str, pygame.Rect]] = []
    for i, label in enumerate(labels):
        r = pygame.Rect(x, y + i * (item_height + padding), item_width, item_height)
        items.append((label, r))
    return items


def draw_slot_menu(
    screen: pygame.Surface,
    font: pygame.font.Font,
    menu_items: list[tuple[str, pygame.Rect]],
):
    """Draw the small popup menu with the given (label, rect) items."""
    for label, rect in menu_items:
        pygame.draw.rect(screen, (60, 60, 80), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, width=1)

        text_surf = font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

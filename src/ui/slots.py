# src/ui/slots.py
import pygame
from config import HEIGHT, WIDTH
import random

# --- Defence icons (loaded once) ---
ICON_SIZE = (100, 100)
ARCHER_ICON = pygame.image.load("assets/archer_up.png")
ARCHER_ICON = pygame.transform.scale(ARCHER_ICON, ICON_SIZE)

CANNON_ICON = pygame.image.load("assets/canon_up.png")
CANNON_ICON = pygame.transform.scale(CANNON_ICON, ICON_SIZE)

MAGE_ICON = pygame.image.load("assets/mage_up.png")
MAGE_ICON = pygame.transform.scale(MAGE_ICON, ICON_SIZE)

SLOT_ICON = pygame.image.load("assets/slot_spot.png")
SLOT_ICON = pygame.transform.scale(SLOT_ICON, ICON_SIZE)


DEFENCE_ICONS = {
    "archer": ARCHER_ICON,
    "cannon": CANNON_ICON,
    "mage": MAGE_ICON,
}


def compute_slot_rects(screen: pygame.Surface, num_slots: int) -> list[pygame.Rect]:
    """
    Compute a horizontal row of slot rects, centered on X,
    but placed higher up on the screen (above the castle area).
    These rects are used both for drawing and clicking.
    """
    slot_width, slot_height = ICON_SIZE  # ⬅️ match the visual icon size
    gap = WIDTH / 7  # can tweak if icons get too close

    total_width = num_slots * slot_width + (num_slots - 1) * gap
    start_x = (WIDTH - total_width) // 2

    hp_bar_height = 24
    ui_row_height = 40
    castle_height = 120

    castle_top = HEIGHT - (hp_bar_height + ui_row_height + castle_height)

    # place slots ABOVE the castle, with some margin
    row_y = castle_top - 80

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
        # make the clickable area a bit larger than the visual rect
        hit_rect = rect.inflate(20, 20)  # +10 px on each side
        if hit_rect.collidepoint(pos):
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

        if slot_defences[i] is None:

            # Slot label
            label_surf = font.render(label, True, (220, 220, 220))
            label_rect = label_surf.get_rect(midleft=(rect.left + 25, rect.top + 35))
            screen.blit(label_surf, label_rect)

        if defence is not None:
            # try to get a sprite for this defence type
            icon_surf = DEFENCE_ICONS.get(defence.defence_type)

            # base icon center
            cx, cy = rect.center

            # small jitter if this defence recently fired
            if getattr(defence, "shake_time", 0) > 0:
                jx = random.randint(-defence.shake_magnitude, defence.shake_magnitude)
                jy = random.randint(-defence.shake_magnitude, defence.shake_magnitude)
            else:
                jx = jy = 0

            if icon_surf is not None:
                icon_rect = icon_surf.get_rect(center=(cx + jx, cy + jy))
                screen.blit(icon_surf, icon_rect)
            else:
                # fallback: colored box, if no icon defined
                icon_rect = pygame.Rect(0, 0, 32, 32)
                icon_rect.center = (cx + jx, cy + jy)
                pygame.draw.rect(
                    screen, defence.projectile_color, icon_rect, border_radius=6
                )
                pygame.draw.rect(screen, (0, 0, 0), icon_rect, width=1, border_radius=6)

            # level text above the defence icon
            level_text = font.render(f"Lv{defence.level}", True, (255, 255, 255))
            lvl_rect = level_text.get_rect(midbottom=(rect.centerx, rect.bottom - 110))
            screen.blit(level_text, lvl_rect)


def build_slot_menu(
    slot_rect: pygame.Rect, labels: list[str]
) -> list[tuple[str, pygame.Rect]]:
    item_width = 140
    item_height = 26
    padding = 4

    # position menu above the slot by default
    x = slot_rect.left
    y = slot_rect.top - (item_height + padding) * len(labels) - 8

    # if it would go off top of screen, move it below slot instead
    if y < 0:
        y = slot_rect.bottom + 8

    # --- clamp horizontally so it stays on screen, away from action bar edge ---
    margin = 8
    if x + item_width > WIDTH - margin:
        x = WIDTH - item_width - margin
    if x < margin:
        x = margin

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


def draw_slot_spots(screen: pygame.Surface, slot_rects: list[pygame.Rect]):
    """Draw only the slot background (slot spot image) for each slot."""
    ox = 0
    oy = 35
    for rect in slot_rects:
        spot_rect = SLOT_ICON.get_rect(center=(rect.centerx + ox, rect.centery + oy))
        screen.blit(SLOT_ICON, spot_rect)


def get_defence_icon(defence_type: str | None) -> pygame.Surface:
    if defence_type is None:
        return SLOT_ICON
    return DEFENCE_ICONS.get(defence_type, SLOT_ICON)


def build_stat_lines(defence) -> list[str]:
    if defence is None:
        return ["Empty slot", "Pick a defence to place here."]

    return [
        f"Type: {defence.defence_type.title()}",
        f"Level: {defence.level}",
        f"Damage: {defence.base_damage}",
        f"Range: {defence.base_range}",
        f"Cooldown: {defence.base_cooldown:.2f}s",
        f"Projectile speed: {defence.base_projectile_speed}",
        f"Crit: {int(defence.crit_chance * 100)}% x{defence.crit_multiplier}",
        f"Max HP: {defence.max_hp}",
    ]


def build_slot_popup(
    slot_rect: pygame.Rect,
    defence,
    buttons: list[str],
    extra_lines: list[str] | None = None,
):
    """Prepare geometry for the detailed slot popup."""

    icon_surf = get_defence_icon(getattr(defence, "defence_type", None))

    padding = 16
    popup_width = 460
    icon_area_width = 140
    icon_area_height = 140
    button_width = 190
    button_height = 34
    button_spacing = 8

    stats_lines = build_stat_lines(defence)
    if extra_lines:
        stats_lines.extend(extra_lines)

    button_area_height = (
        len(buttons) * (button_height + button_spacing) - button_spacing
        if buttons
        else 0
    )
    stats_area_height = len(stats_lines) * 20
    content_height = max(icon_area_height, button_area_height) + padding + stats_area_height
    popup_height = padding * 2 + content_height

    x = slot_rect.centerx - popup_width // 2
    x = max(10, min(x, WIDTH - popup_width - 10))
    y = slot_rect.top - popup_height - 12
    if y < 10:
        y = slot_rect.bottom + 12

    popup_rect = pygame.Rect(x, y, popup_width, popup_height)

    icon_rect = icon_surf.get_rect()
    icon_rect.center = (
        popup_rect.left + padding + icon_area_width // 2,
        popup_rect.top + padding + icon_area_height // 2,
    )

    buttons_rects: list[tuple[str, pygame.Rect]] = []
    right_x = popup_rect.left + padding + icon_area_width + padding
    right_y = popup_rect.top + padding

    for i, label in enumerate(buttons):
        r = pygame.Rect(
            right_x,
            right_y + i * (button_height + button_spacing),
            button_width,
            button_height,
        )
        buttons_rects.append((label, r))

    stats_start_y = popup_rect.top + padding + max(icon_area_height, button_area_height) + padding

    return {
        "rect": popup_rect,
        "icon": icon_surf,
        "icon_rect": icon_rect,
        "buttons": buttons_rects,
        "stats": stats_lines,
        "stats_start_y": stats_start_y,
    }


def draw_slot_popup(
    screen: pygame.Surface,
    font: pygame.font.Font,
    popup_data: dict,
):
    rect: pygame.Rect = popup_data["rect"]
    pygame.draw.rect(screen, (40, 42, 60), rect, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), rect, width=2, border_radius=8)

    # icon side
    icon = popup_data["icon"]
    icon_rect: pygame.Rect = popup_data["icon_rect"]
    pygame.draw.rect(
        screen, (58, 60, 80), (icon_rect.left - 8, icon_rect.top - 8, 156, 156), 0, 8
    )
    pygame.draw.rect(
        screen, (15, 15, 25), (icon_rect.left - 8, icon_rect.top - 8, 156, 156), 2, 8
    )
    screen.blit(icon, icon_rect)

    # buttons
    for label, brect in popup_data["buttons"]:
        pygame.draw.rect(screen, (70, 72, 98), brect, border_radius=4)
        pygame.draw.rect(screen, (10, 10, 15), brect, width=1, border_radius=4)
        text_surf = font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=brect.center)
        screen.blit(text_surf, text_rect)

    # stats
    y = popup_data["stats_start_y"]
    for line in popup_data["stats"]:
        text_surf = font.render(line, True, (230, 230, 230))
        text_rect = text_surf.get_rect(left=rect.left + 24, top=y)
        screen.blit(text_surf, text_rect)
        y += 20

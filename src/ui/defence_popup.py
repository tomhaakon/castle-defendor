"""UI helpers for showing a detailed defence popup."""
from __future__ import annotations

import pygame

from config import HEIGHT, WIDTH
from ui.slots import DEFENCE_ICONS, SLOT_ICON

POPUP_WIDTH = 560
POPUP_HEIGHT = 320
BUTTON_WIDTH = 210
BUTTON_HEIGHT = 38
BUTTON_GAP = 10


class PopupLayout:
    def __init__(
        self,
        popup_rect: pygame.Rect,
        close_rect: pygame.Rect,
        icon_rect: pygame.Rect,
        buttons: list[tuple[str, str, pygame.Rect, bool]],
        stats_origin: tuple[int, int],
    ) -> None:
        self.popup_rect = popup_rect
        self.close_rect = close_rect
        self.icon_rect = icon_rect
        self.buttons = buttons
        self.stats_origin = stats_origin


def build_defence_popup_layout(defence, slot_label: str, can_upgrade: bool) -> PopupLayout:
    popup_rect = pygame.Rect(0, 0, POPUP_WIDTH, POPUP_HEIGHT)
    popup_rect.center = (WIDTH // 2, HEIGHT // 2)

    close_rect = pygame.Rect(popup_rect.right - 28, popup_rect.top + 16, 16, 16)

    icon_rect = pygame.Rect(0, 0, 180, 180)
    icon_rect.midleft = (popup_rect.left + 36 + icon_rect.width // 2, popup_rect.centery)

    buttons: list[tuple[str, str, pygame.Rect, bool]] = []
    button_x = icon_rect.right + 30
    button_y = popup_rect.top + 46

    if defence is None:
        add_rect = pygame.Rect(button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        buttons.append(("add", "Add defence", add_rect, True))
    else:
        upgrade_rect = pygame.Rect(button_x, button_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        remove_rect = pygame.Rect(
            button_x, button_y + (BUTTON_HEIGHT + BUTTON_GAP), BUTTON_WIDTH, BUTTON_HEIGHT
        )
        sell_rect = pygame.Rect(
            button_x,
            button_y + 2 * (BUTTON_HEIGHT + BUTTON_GAP),
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
        )
        buttons.append(("upgrade", "Upgrade", upgrade_rect, can_upgrade))
        buttons.append(("remove", "Remove from slot", remove_rect, True))
        buttons.append(("sell", "Sell", sell_rect, True))

    stats_origin = (
        button_x,
        button_y + len(buttons) * (BUTTON_HEIGHT + BUTTON_GAP) + 14,
    )

    return PopupLayout(popup_rect, close_rect, icon_rect, buttons, stats_origin)


def draw_button(screen: pygame.Surface, font: pygame.font.Font, label: str, rect: pygame.Rect, enabled: bool):
    bg = (105, 115, 150) if enabled else (70, 70, 90)
    pygame.draw.rect(screen, bg, rect, border_radius=6)
    pygame.draw.rect(screen, (0, 0, 0), rect, width=2, border_radius=6)

    color = (255, 255, 255) if enabled else (180, 180, 180)
    surf = font.render(label, True, color)
    surf_rect = surf.get_rect(center=rect.center)
    screen.blit(surf, surf_rect)


def draw_icon(screen: pygame.Surface, icon_rect: pygame.Rect, defence):
    if defence is None:
        slot_surf = pygame.transform.smoothscale(SLOT_ICON, icon_rect.size)
        screen.blit(slot_surf, icon_rect)
        return

    icon = DEFENCE_ICONS.get(defence.defence_type)
    if icon is None:
        pygame.draw.rect(screen, (50, 50, 70), icon_rect, border_radius=8)
        return

    scaled = pygame.transform.smoothscale(icon, icon_rect.size)
    screen.blit(scaled, icon_rect)


def format_stats(defence) -> list[str]:
    if defence is None:
        return ["Empty slot", "Place a defence to see its stats."]

    lines = [
        f"Level: {defence.level}",
        f"Damage: {defence.base_damage}",
        f"Range: {defence.base_range}",
        f"Cooldown: {defence.base_cooldown:.2f}s",
        f"Projectile speed: {defence.base_projectile_speed}",
        f"Crit: {int(defence.crit_chance * 100)}% x{defence.crit_multiplier}",
        f"HP: {int(defence.hp)}/{int(defence.max_hp)}",
    ]
    return lines


def draw_defence_popup(
    screen: pygame.Surface,
    font: pygame.font.Font,
    defence,
    slot_label: str,
    layout: PopupLayout,
    gold: int,
):
    pygame.draw.rect(screen, (15, 15, 25), screen.get_rect())

    pygame.draw.rect(screen, (45, 45, 70), layout.popup_rect, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), layout.popup_rect, width=2, border_radius=10)

    pygame.draw.rect(screen, (120, 70, 70), layout.close_rect, border_radius=4)
    pygame.draw.line(
        screen,
        (10, 10, 10),
        layout.close_rect.topleft,
        layout.close_rect.bottomright,
        width=2,
    )
    pygame.draw.line(
        screen,
        (10, 10, 10),
        layout.close_rect.topright,
        layout.close_rect.bottomleft,
        width=2,
    )

    title = f"{slot_label.capitalize()} — {defence.defence_type.capitalize()}" if defence else f"{slot_label.capitalize()} — Empty"
    title_surf = font.render(title, True, (255, 255, 255))
    title_rect = title_surf.get_rect(midtop=(layout.popup_rect.centerx, layout.popup_rect.top + 14))
    screen.blit(title_surf, title_rect)

    draw_icon(screen, layout.icon_rect, defence)

    upgrade_cost = defence.get_upgrade_cost() if defence is not None else None

    for action, label, rect, enabled in layout.buttons:
        button_label = label
        if action == "upgrade" and upgrade_cost is not None:
            button_label = f"Upgrade ({upgrade_cost}g)"
            enabled = enabled and gold >= upgrade_cost
        draw_button(screen, font, button_label, rect, enabled)

    stats_lines = format_stats(defence)
    x, y = layout.stats_origin
    for line in stats_lines:
        surf = font.render(line, True, (230, 230, 230))
        screen.blit(surf, (x, y))
        y += 22

    if defence is not None and upgrade_cost is not None:
        hint = f"Next upgrade cost: {upgrade_cost}g"
        hint_color = (200, 180, 120) if gold >= upgrade_cost else (200, 120, 120)
        hint_surf = font.render(hint, True, hint_color)
        screen.blit(hint_surf, (layout.popup_rect.left + 22, layout.popup_rect.bottom - 32))

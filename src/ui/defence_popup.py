import pygame
from dataclasses import dataclass

from config import WIDTH, HEIGHT, DEFENCE_STATS
from ui.slots import DEFENCE_ICONS


@dataclass
class DefencePopupLayout:
    popup_rect: pygame.Rect
    icon_rect: pygame.Rect
    button_rects: list[tuple[str, str, pygame.Rect]]
    stats_origin: tuple[int, int]
    icon_col_width: int
    stats_col_width: int


def calculate_defence_snapshot(defence) -> dict:
    stats = DEFENCE_STATS[defence.defence_type]
    level = defence.level

    damage = stats["damage"] * (1.0 + 0.3 * (level - 1))
    attack_range = stats["range"] * (1.0 + 0.1 * (level - 1))
    cooldown = max(0.15, stats["cooldown"] * (1.0 - 0.07 * (level - 1)))
    projectile_speed = stats["proj_speed"] * (1.0 + 0.1 * (level - 1))

    snapshot = {
        "level": level,
        "damage": damage,
        "range": attack_range,
        "cooldown": cooldown,
        "projectile_speed": projectile_speed,
        "crit_chance": stats["crit_chance"] * 100,
        "crit_multiplier": stats["crit_multiplier"],
        "hp": defence.hp,
        "max_hp": stats.get("max_hp", defence.max_hp),
        "upgrade_cost": defence.get_upgrade_cost(),
        "sell_value": int(stats["base_cost"] * level * 0.5),
    }
    return snapshot


def build_defence_popup_layout(defence) -> DefencePopupLayout:
    popup_width = int(WIDTH * 0.55)
    popup_height = int(HEIGHT * 0.35)

    icon_col_width = int(popup_width * 0.4)
    stats_col_width = int(popup_width * 0.4)
    button_col_width = popup_width - icon_col_width - stats_col_width

    popup_rect = pygame.Rect(0, 0, popup_width, popup_height)
    popup_rect.center = (WIDTH // 2, HEIGHT // 2 - 20)

    icon = DEFENCE_ICONS.get(defence.defence_type)
    if icon is None:
        icon_rect = pygame.Rect(
            popup_rect.left + 16,
            popup_rect.top + 36,
            icon_col_width - 32,
            popup_height - 72,
        )
    else:
        icon_rect = icon.get_rect()
        icon_rect.center = (
            popup_rect.left + icon_col_width // 2,
            popup_rect.top + popup_height // 2 + 6,
        )

    button_size = 16
    button_gap = 12
    button_x = popup_rect.left + icon_col_width + stats_col_width + (
        button_col_width - button_size
    ) // 2
    button_y = popup_rect.top + 70

    snapshot = calculate_defence_snapshot(defence)

    button_rects: list[tuple[str, str, pygame.Rect]] = [
        (
            "upgrade",
            "↑",
            pygame.Rect(button_x, button_y, button_size, button_size),
        ),
        (
            "remove",
            "✕",
            pygame.Rect(
                button_x,
                button_y + (button_size + button_gap),
                button_size,
                button_size,
            ),
        ),
        (
            "sell",
            "$",
            pygame.Rect(
                button_x,
                button_y + 2 * (button_size + button_gap),
                button_size,
                button_size,
            ),
        ),
    ]

    stats_origin = (
        popup_rect.left + icon_col_width + 20,
        popup_rect.top + 68,
    )

    return DefencePopupLayout(
        popup_rect=popup_rect,
        icon_rect=icon_rect,
        button_rects=button_rects,
        stats_origin=stats_origin,
        icon_col_width=icon_col_width,
        stats_col_width=stats_col_width,
    )


def draw_defence_popup(screen, font, defence, layout: DefencePopupLayout):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    pygame.draw.rect(screen, (28, 32, 48), layout.popup_rect, border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), layout.popup_rect, width=2, border_radius=10)

    title_text = f"{defence.defence_type.title()} (Lv{defence.level})"
    title_surf = font.render(title_text, True, (255, 255, 255))
    title_rect = title_surf.get_rect(
        midtop=(layout.popup_rect.centerx, layout.popup_rect.top + 10)
    )
    screen.blit(title_surf, title_rect)

    icon = DEFENCE_ICONS.get(defence.defence_type)
    if icon is not None:
        screen.blit(icon, layout.icon_rect)
    else:
        pygame.draw.rect(screen, (100, 100, 140), layout.icon_rect, border_radius=6)

    snapshot = calculate_defence_snapshot(defence)

    icon_button_font = pygame.font.SysFont(None, max(14, font.get_height() - 10))
    for action, label, rect in layout.button_rects:
        base_color = (80, 110, 160) if action == "upgrade" else (70, 90, 120)
        pygame.draw.rect(screen, base_color, rect, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), rect, width=1, border_radius=4)

        text_surf = icon_button_font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    tooltip_lines = [
        f"Upgrade ({snapshot['upgrade_cost']}g)",
        "Remove from slot",
        f"Sell ({snapshot['sell_value']}g)",
    ]
    tooltip_font = pygame.font.SysFont(None, max(14, font.get_height() - 6))
    tooltip_x = layout.button_rects[0][2].centerx
    tooltip_y = layout.popup_rect.top + 24
    for line in tooltip_lines:
        text_surf = tooltip_font.render(line, True, (210, 210, 230))
        text_rect = text_surf.get_rect(centerx=tooltip_x, y=tooltip_y)
        screen.blit(text_surf, text_rect)
        tooltip_y += text_rect.height + 2

    stats_x, stats_y = layout.stats_origin
    stats_font = pygame.font.SysFont(None, max(16, font.get_height() - 6))
    stats_lines = [
        f"HP: {int(snapshot['hp'])}/{int(snapshot['max_hp'])}",
        f"Damage: {snapshot['damage']:.1f}",
        f"Range: {snapshot['range']:.0f}",
        f"Cooldown: {snapshot['cooldown']:.2f}s",
        f"Projectile Speed: {snapshot['projectile_speed']:.0f}",
        f"Crit: {snapshot['crit_chance']:.0f}% x{snapshot['crit_multiplier']:.1f}",
    ]

    for i, line in enumerate(stats_lines):
        text_surf = stats_font.render(line, True, (230, 230, 230))
        text_rect = text_surf.get_rect(topleft=(stats_x, stats_y + i * 20))
        screen.blit(text_surf, text_rect)

    separator_x1 = layout.popup_rect.left + layout.icon_col_width
    separator_x2 = separator_x1 + layout.stats_col_width
    separator_top = layout.popup_rect.top + 24
    separator_bottom = layout.popup_rect.bottom - 24
    pygame.draw.line(
        screen,
        (52, 60, 82),
        (separator_x1, separator_top),
        (separator_x1, separator_bottom),
        width=2,
    )
    pygame.draw.line(
        screen,
        (52, 60, 82),
        (separator_x2, separator_top),
        (separator_x2, separator_bottom),
        width=2,
    )

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
    popup_width = 520
    popup_height = 260

    popup_rect = pygame.Rect(0, 0, popup_width, popup_height)
    popup_rect.center = (WIDTH // 2, HEIGHT // 2 - 20)

    icon = DEFENCE_ICONS.get(defence.defence_type)
    if icon is None:
        icon_rect = pygame.Rect(popup_rect.left + 20, popup_rect.top + 20, 120, 120)
    else:
        icon_rect = icon.get_rect(topleft=(popup_rect.left + 20, popup_rect.top + 20))

    button_width = 200
    button_height = 36
    button_x = icon_rect.right + 24
    button_y = popup_rect.top + 24

    snapshot = calculate_defence_snapshot(defence)

    button_rects: list[tuple[str, str, pygame.Rect]] = [
        (
            "upgrade",
            f"Upgrade ({snapshot['upgrade_cost']}g)",
            pygame.Rect(button_x, button_y, button_width, button_height),
        ),
        (
            "remove",
            "Remove from slot",
            pygame.Rect(
                button_x, button_y + (button_height + 10), button_width, button_height
            ),
        ),
        (
            "sell",
            f"Sell ({snapshot['sell_value']}g)",
            pygame.Rect(
                button_x,
                button_y + 2 * (button_height + 10),
                button_width,
                button_height,
            ),
        ),
    ]

    stats_origin = (button_x, button_y + 3 * (button_height + 10) + 20)

    return DefencePopupLayout(
        popup_rect=popup_rect,
        icon_rect=icon_rect,
        button_rects=button_rects,
        stats_origin=stats_origin,
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

    for action, label, rect in layout.button_rects:
        base_color = (80, 110, 160) if action == "upgrade" else (70, 90, 120)
        pygame.draw.rect(screen, base_color, rect, border_radius=6)
        pygame.draw.rect(screen, (0, 0, 0), rect, width=1, border_radius=6)

        text_surf = font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    stats_x, stats_y = layout.stats_origin
    stats_lines = [
        f"HP: {int(snapshot['hp'])}/{int(snapshot['max_hp'])}",
        f"Damage: {snapshot['damage']:.1f}",
        f"Range: {snapshot['range']:.0f}",
        f"Cooldown: {snapshot['cooldown']:.2f}s",
        f"Projectile Speed: {snapshot['projectile_speed']:.0f}",
        f"Crit: {snapshot['crit_chance']:.0f}% x{snapshot['crit_multiplier']:.1f}",
    ]

    for i, line in enumerate(stats_lines):
        text_surf = font.render(line, True, (230, 230, 230))
        text_rect = text_surf.get_rect(topleft=(stats_x, stats_y + i * 22))
        screen.blit(text_surf, text_rect)

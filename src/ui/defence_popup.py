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
    popup_width = max(480, int(WIDTH * 0.6))
    padding = 16
    title_space = 40
    center = (WIDTH // 2, HEIGHT // 2 - 20)

    usable_width = popup_width - 2 * padding
    portrait_width = int(usable_width * 0.4)  # 2/5 for portrait
    stats_width = int(usable_width * 0.4)  # 2/5 for stats
    buttons_width = usable_width - portrait_width - stats_width  # 1/5 for buttons

    icon = DEFENCE_ICONS.get(defence.defence_type)
    if icon is None:
        icon_rect = pygame.Rect(0, 0, 96, 96)
    else:
        icon_rect = icon.get_rect().copy()

    button_size = 16
    button_spacing = 14

    snapshot = calculate_defence_snapshot(defence)

    # Predict content height to size the popup before positioning
    stats_line_height = 18
    stats_height = stats_line_height * 6
    buttons_height = 3 * button_size + 2 * button_spacing
    content_height = max(icon_rect.height, stats_height, buttons_height)
    popup_height = title_space + content_height + padding

    popup_rect = pygame.Rect(0, 0, popup_width, popup_height)
    popup_rect.center = center

    content_top = popup_rect.top + title_space
    portrait_area_left = popup_rect.left + padding
    icon_rect.center = (
        portrait_area_left + portrait_width // 2,
        content_top + content_height // 2,
    )

    stats_origin_x = portrait_area_left + portrait_width + padding
    stats_origin = (stats_origin_x, content_top)

    button_area_x = stats_origin_x + stats_width + padding
    button_rects: list[tuple[str, str, pygame.Rect]] = [
        (
            "upgrade",
            f"Upgrade ({snapshot['upgrade_cost']}g)",
            pygame.Rect(
                button_area_x + buttons_width - button_size,
                content_top,
                button_size,
                button_size,
            ),
        ),
        (
            "remove",
            "Remove from slot",
            pygame.Rect(
                button_area_x + buttons_width - button_size,
                content_top + (button_size + button_spacing),
                button_size,
                button_size,
            ),
        ),
        (
            "sell",
            f"Sell ({snapshot['sell_value']}g)",
            pygame.Rect(
                button_area_x + buttons_width - button_size,
                content_top + 2 * (button_size + button_spacing),
                button_size,
                button_size,
            ),
        ),
    ]

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

    stats_font = pygame.font.SysFont(None, max(font.get_height() - 6, 12))

    for action, label, rect in layout.button_rects:
        base_color = (90, 130, 190) if action == "upgrade" else (70, 90, 120)
        pygame.draw.rect(screen, base_color, rect, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), rect, width=1, border_radius=4)

        abbrev = label[0].upper()
        abbrev_surf = stats_font.render(abbrev, True, (255, 255, 255))
        abbrev_rect = abbrev_surf.get_rect(center=rect.center)
        screen.blit(abbrev_surf, abbrev_rect)

        label_surf = stats_font.render(label, True, (220, 220, 220))
        label_rect = label_surf.get_rect(right=rect.left - 6, centery=rect.centery)
        screen.blit(label_surf, label_rect)

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
        text_surf = stats_font.render(line, True, (230, 230, 230))
        text_rect = text_surf.get_rect(topleft=(stats_x, stats_y + i * 18))
        screen.blit(text_surf, text_rect)

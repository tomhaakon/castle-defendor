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
    stats_width: int


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
    popup_width = int(WIDTH * 0.6)
    popup_height = 320

    popup_rect = pygame.Rect(0, 0, popup_width, popup_height)
    popup_rect.center = (WIDTH // 2, HEIGHT // 2 - 20)

    content_padding = 24
    title_offset = 56

    content_left = popup_rect.left + content_padding
    content_top = popup_rect.top + title_offset
    content_width = popup_width - 2 * content_padding

    icon_col_width = int(content_width * 0.4)
    stats_col_width = int(content_width * 0.4)
    button_col_width = content_width - icon_col_width - stats_col_width

    icon = DEFENCE_ICONS.get(defence.defence_type)
    if icon is None:
        icon_rect = pygame.Rect(0, 0, icon_col_width - 12, icon_col_width - 12)
        icon_rect.topleft = (content_left + 6, content_top)
    else:
        icon_rect = icon.get_rect()
        icon_rect.topleft = (
            content_left + (icon_col_width - icon_rect.width) // 2,
            content_top,
        )

    button_size = 16
    button_spacing = 12
    button_x = content_left + icon_col_width + stats_col_width + (
        button_col_width - button_size
    ) // 2
    button_y = content_top

    button_rects: list[tuple[str, str, pygame.Rect]] = [
        (
            "upgrade",
            "Upgrade",
            pygame.Rect(button_x, button_y, button_size, button_size),
        ),
        (
            "remove",
            "Remove",
            pygame.Rect(
                button_x, button_y + (button_size + button_spacing), button_size, button_size
            ),
        ),
        (
            "sell",
            "Sell",
            pygame.Rect(
                button_x,
                button_y + 2 * (button_size + button_spacing),
                button_size,
                button_size,
            ),
        ),
    ]

    stats_origin = (content_left + icon_col_width + 12, content_top)

    return DefencePopupLayout(
        popup_rect=popup_rect,
        icon_rect=icon_rect,
        button_rects=button_rects,
        stats_origin=stats_origin,
        stats_width=stats_col_width - 24,
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

    stats_font_size = max(14, font.get_height() - 6)
    stats_font = pygame.font.Font(None, stats_font_size)

    button_font_size = max(12, font.get_height() - 10)
    button_font = pygame.font.Font(None, button_font_size)

    for action, label, rect in layout.button_rects:
        base_color = (80, 110, 160) if action == "upgrade" else (70, 90, 120)
        pygame.draw.rect(screen, base_color, rect, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), rect, width=1, border_radius=4)

        symbol = {
            "upgrade": "U",
            "remove": "X",
            "sell": "$",
        }.get(action, label[:1])

        text_surf = button_font.render(symbol, True, (255, 255, 255))
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
        f"Upgrade: {snapshot['upgrade_cost']}g",
        f"Sell: {snapshot['sell_value']}g",
    ]

    wrapped_lines: list[str] = []
    for line in stats_lines:
        words = line.split()
        if not words:
            continue

        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if stats_font.size(candidate)[0] <= layout.stats_width:
                current = candidate
            else:
                wrapped_lines.append(current)
                current = word
        wrapped_lines.append(current)

    line_height = stats_font.get_linesize()
    for i, line in enumerate(wrapped_lines):
        text_surf = stats_font.render(line, True, (230, 230, 230))
        text_rect = text_surf.get_rect(topleft=(stats_x, stats_y + i * line_height))
        screen.blit(text_surf, text_rect)

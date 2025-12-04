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
    popup_width = int(WIDTH * 0.55)
    popup_height = 260

    popup_rect = pygame.Rect(0, 0, popup_width, popup_height)
    popup_rect.center = (WIDTH // 2, HEIGHT // 2 - 20)

    # width proportions: 2/5 portrait, 2/5 stats, 1/5 buttons
    portrait_width = int(popup_width * 0.4)
    stats_width = int(popup_width * 0.4)
    buttons_width = popup_width - portrait_width - stats_width
    content_top = popup_rect.top + 56
    inner_pad = 16

    icon = DEFENCE_ICONS.get(defence.defence_type)
    icon_size = min(portrait_width - 2 * inner_pad, 140)
    if icon is None:
        icon_rect = pygame.Rect(
            popup_rect.left + (portrait_width - icon_size) // 2,
            content_top,
            icon_size,
            icon_size,
        )
    else:
        icon_rect = icon.get_rect()
        icon_rect.size = (
            min(icon_rect.width, icon_size),
            min(icon_rect.height, icon_size),
        )
        icon_rect.topleft = (
            popup_rect.left + (portrait_width - icon_rect.width) // 2,
            content_top + max(0, (icon_size - icon_rect.height) // 2),
        )

    snapshot = calculate_defence_snapshot(defence)

    button_size = 16
    button_x = popup_rect.left + portrait_width + stats_width + inner_pad
    button_y = content_top
    button_gap = 18
    button_rects: list[tuple[str, str, pygame.Rect]] = []
    for i, (action, label) in enumerate(
        [
            ("upgrade", f"Upgrade ({snapshot['upgrade_cost']}g)"),
            ("remove", "Remove from slot"),
            ("sell", f"Sell ({snapshot['sell_value']}g)"),
        ]
    ):
        rect = pygame.Rect(
            button_x + (buttons_width - inner_pad - button_size) // 2,
            button_y + i * (button_size + button_gap),
            button_size,
            button_size,
        )
        button_rects.append((action, label, rect))

    stats_origin = (
        popup_rect.left + portrait_width + inner_pad,
        content_top,
    )

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
        scaled_icon = pygame.transform.smoothscale(icon, layout.icon_rect.size)
        screen.blit(scaled_icon, layout.icon_rect)
    else:
        pygame.draw.rect(screen, (100, 100, 140), layout.icon_rect, border_radius=6)

    snapshot = calculate_defence_snapshot(defence)

    stat_font = pygame.font.SysFont(None, max(14, font.get_height() - 6))
    button_font = pygame.font.SysFont(None, 14)

    for action, label, rect in layout.button_rects:
        base_color = (80, 110, 160) if action == "upgrade" else (70, 90, 120)
        pygame.draw.rect(screen, base_color, rect, border_radius=4)
        pygame.draw.rect(screen, (0, 0, 0), rect, width=1, border_radius=4)

        text_surf = button_font.render(label, True, (230, 230, 230))
        text_rect = text_surf.get_rect(midleft=(rect.right + 8, rect.centery))
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

    line_height = stat_font.get_linesize() + 2
    for i, line in enumerate(stats_lines):
        text_surf = stat_font.render(line, True, (230, 230, 230))
        text_rect = text_surf.get_rect(topleft=(stats_x, stats_y + i * line_height))
        screen.blit(text_surf, text_rect)

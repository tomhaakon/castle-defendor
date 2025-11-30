# src/ui/hud.py
import pygame

from config import BOTTOM_FRACTION, HEIGHT, WIDTH


def draw_background(
    screen: pygame.Surface,
    castle_rect: pygame.Rect,
    hp_bar_rect: pygame.Rect,
) -> None:
    """
    Draw the background using the same layout as Game:
    - top area (play field)
    - castle area
    - UI row
    - HP bar row
    """

    # Play field = everything above the castle
    playfield_rect = pygame.Rect(0, 0, WIDTH, castle_rect.top)
    pygame.draw.rect(screen, (80, 80, 80), playfield_rect)

    # Castle background
    pygame.draw.rect(screen, (60, 60, 90), castle_rect)

    # HP bar background
    pygame.draw.rect(screen, (20, 20, 20), hp_bar_rect)


def draw_wave_button(
    screen: pygame.Surface,
    font: pygame.font.Font,
    can_spawn_wave: bool,
    wave_number: int,
    button_rect: pygame.Rect,
) -> None:
    if can_spawn_wave:
        bg_color = (100, 100, 130)
        text_color = (255, 255, 255)
        label = f"Ready for next wave! ({wave_number + 1})"
    else:
        bg_color = (60, 60, 80)
        text_color = (180, 180, 180)
        label = "Wave incoming.."

    pygame.draw.rect(screen, bg_color, button_rect)
    pygame.draw.rect(screen, (0, 0, 0), button_rect, width=2)

    text_surf = font.render(label, True, text_color)
    text_rect = text_surf.get_rect(center=button_rect.center)
    screen.blit(text_surf, text_rect)


def draw_castle_hp(
    screen: pygame.Surface,
    font: pygame.font.Font,
    castle_hp: float,
    castle_max_hp: float,
    bar_rect: pygame.Rect,
) -> None:
    """Draw a full-width HP bar in the bottom row."""

    # background row
    pygame.draw.rect(screen, (20, 20, 20), bar_rect)

    # inner bar padding
    inner_padding_x = 0
    inner_padding_y = 0

    inner_width = bar_rect.width - inner_padding_x * 2
    inner_height = bar_rect.height - inner_padding_y * 2

    ratio = 0 if castle_max_hp == 0 else castle_hp / castle_max_hp
    fill_width = int(inner_width * ratio)

    # outline
    outline_rect = pygame.Rect(
        bar_rect.left,
        bar_rect.top,
        inner_width,
        inner_height,
    )
    pygame.draw.rect(screen, (0, 0, 0), outline_rect, width=2)

    # fill
    r = int(200 * (1 - ratio))
    g = int(200 * ratio)
    color = (r, g, 0)

    fill_rect = pygame.Rect(
        outline_rect.left + 1,
        outline_rect.top + 1,
        max(0, fill_width - 2),
        outline_rect.height - 2,
    )
    pygame.draw.rect(screen, color, fill_rect)

    # text centered in the row
    hp_text = f"Castle HP {int(castle_hp)}/{int(castle_max_hp)}"
    text_surf = font.render(hp_text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=bar_rect.center)
    screen.blit(text_surf, text_rect)


def draw_gold(
    screen: pygame.Surface,
    font: pygame.font.Font,
    gold: int,
    selected_defence,
    ui_row_rect: pygame.Rect,
) -> None:
    """Show gold + upgrade hint in the UI row (above HP bar)."""

    # Gold text on the left side of the row
    text = f"Gold: {gold}"
    surf = font.render(text, True, (255, 215, 0))
    rect = surf.get_rect(midleft=(ui_row_rect.centerx, ui_row_rect.centery))
    screen.blit(surf, rect)

    # Upgrade hint on the right side of the row
    if selected_defence is not None:
        cost = selected_defence.get_upgrade_cost()
        hint = (
            f"U: Upgrade {selected_defence.defence_type} "
            f"(Lv{selected_defence.level}) for {cost}g"
        )
    else:
        hint = ""

    hint_surf = font.render(hint, True, (230, 230, 230))
    hint_rect = hint_surf.get_rect(
        midright=(ui_row_rect.right - 20, ui_row_rect.centery)
    )
    screen.blit(hint_surf, hint_rect)


def draw_game_overlay(
    screen: pygame.Surface,
    font: pygame.font.Font,
    big_font: pygame.font.Font,
) -> None:
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    text_surf = big_font.render("GAME OVER", True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
    screen.blit(text_surf, text_rect)

    small = font.render("Press ESC to quit", True, (220, 220, 220))
    small_rect = small.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    screen.blit(small, small_rect)


def draw_damage_numbers(
    screen: pygame.Surface, font: pygame.font.Font, damage_numbers: list
) -> None:
    for damage_number in damage_numbers:
        damage_number.draw(screen, font)

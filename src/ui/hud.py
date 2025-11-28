# src/ui/hud.py
import pygame

from config import BOTTOM_FRACTION, HEIGHT, WIDTH


def draw_background(screen: pygame.Surface) -> None:
    """Draw the two-tone background separating the playfield and HUD."""
    bottom_height = int(HEIGHT * BOTTOM_FRACTION)
    top_height = HEIGHT - bottom_height

    pygame.draw.rect(screen, (80, 80, 80), pygame.Rect(0, 0, WIDTH, top_height))
    pygame.draw.rect(
        screen,
        (50, 50, 50),
        pygame.Rect(0, top_height, WIDTH, bottom_height),
    )


def draw_spawn_area(screen: pygame.Surface, spawn_rect: pygame.Rect) -> None:
    pygame.draw.rect(screen, (100, 60, 60), spawn_rect)


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
    castle_rect: pygame.Rect,
) -> None:
    bar_width = 300
    bar_height = 20
    x = 20
    y = castle_rect.top + 20

    outline_rect = pygame.Rect(x, y, bar_width, bar_height)
    pygame.draw.rect(screen, (0, 0, 0), outline_rect, width=2)

    ratio = 0 if castle_max_hp == 0 else castle_hp / castle_max_hp
    fill_width = int(bar_width * ratio)
    fill_rect = pygame.Rect(x + 1, y + 1, max(0, fill_width - 2), bar_height - 2)

    r = int(200 * (1 - ratio))
    g = int(200 * ratio)
    color = (r, g, 0)
    pygame.draw.rect(screen, color, fill_rect)

    hp_text = f"Castle:HO {int(castle_hp)}/{int(castle_max_hp)}"
    text_surf = font.render(hp_text, True, (255, 255, 255))
    text_rect = text_surf.get_rect(midleft=(x, y - 8))
    screen.blit(text_surf, text_rect)


def draw_gold(
    screen: pygame.Surface,
    font: pygame.font.Font,
    gold: int,
    selected_defence,
) -> None:
    text = f"Gold: {gold}"
    surf = font.render(text, True, (255, 215, 0))
    rect = surf.get_rect(topright=(WIDTH - 20, 20))
    screen.blit(surf, rect)

    if selected_defence is not None:
        cost = selected_defence.get_upgrade_cost()
        hint = (
            f"U: Upgrade {selected_defence.defence_type} "
            f"(Lv{selected_defence.level}) for {cost}g"
        )
    else:
        hint = ""

    hint_surf = font.render(hint, True, (230, 230, 230))
    hint_rect = hint_surf.get_rect(topright=(WIDTH - 20, 45))
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

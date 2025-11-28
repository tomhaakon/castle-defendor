# src/ui/shop.py
import pygame

from config import DEFENCE_STATS, HEIGHT, WIDTH
from entities.defence import Defence


def get_shop_popup_layout(owned_defences: list[tuple[str, int]]):
    """Return geometry for the shop popup:
    - popup_rect
    - shop_item_rects: dict[str, Rect]
    - owned_item_rects: list[tuple[int, Rect]] (index in owned_defences, rect)
    - close_rect: Rect for the 'X' button
    """
    popup_width = 520
    popup_height = 320
    popup_x = (WIDTH - popup_width) // 2
    popup_y = (HEIGHT - popup_height) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

    close_size = 24
    close_rect = pygame.Rect(
        popup_rect.right - close_size - 8,
        popup_rect.top + 8,
        close_size,
        close_size,
    )

    inner_pad = 16
    inner_rect = popup_rect.inflate(-2 * inner_pad, -2 * inner_pad)

    column_gap = 20
    col_width = (inner_rect.width - column_gap) // 2

    shop_col_rect = pygame.Rect(
        inner_rect.left,
        inner_rect.top + 30,
        col_width,
        inner_rect.height - 30,
    )

    owned_col_rect = pygame.Rect(
        inner_rect.left + col_width + column_gap,
        inner_rect.top + 30,
        col_width,
        inner_rect.height - 30,
    )

    shop_item_rects: dict[str, pygame.Rect] = {}
    item_h = 28
    item_pad = 6
    shop_types = ["archer", "cannon", "mage"]
    for i, dtype in enumerate(shop_types):
        r = pygame.Rect(
            shop_col_rect.left,
            shop_col_rect.top + i * (item_h + item_pad),
            shop_col_rect.width,
            item_h,
        )
        shop_item_rects[dtype] = r

    owned_item_rects: list[tuple[int, pygame.Rect]] = []
    for i, _dtype in enumerate(owned_defences):
        r = pygame.Rect(
            owned_col_rect.left,
            owned_col_rect.top + i * (item_h + item_pad),
            owned_col_rect.width,
            item_h,
        )
        owned_item_rects.append((i, r))

    return popup_rect, shop_item_rects, owned_item_rects, close_rect


def draw_shop_popup(
    screen: pygame.Surface,
    font: pygame.font.Font,
    shop_open: bool,
    owned_defences: list[tuple[str, int]],
):
    if not shop_open:
        return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    popup_rect, shop_rects, owned_rects, close_rect = get_shop_popup_layout(
        owned_defences
    )

    pygame.draw.rect(screen, (40, 40, 70), popup_rect)
    pygame.draw.rect(screen, (0, 0, 0), popup_rect, width=2)

    pygame.draw.rect(screen, (100, 60, 60), close_rect)
    pygame.draw.rect(screen, (0, 0, 0), close_rect, width=1)
    x_surf = font.render("X", True, (255, 255, 255))
    x_rect = x_surf.get_rect(center=close_rect.center)
    screen.blit(x_surf, x_rect)

    inner_pad = 16
    title_shop = font.render("Shop", True, (255, 255, 255))
    title_owned = font.render("Owned", True, (255, 255, 255))

    screen.blit(title_shop, (popup_rect.left + inner_pad, popup_rect.top + inner_pad))
    screen.blit(
        title_owned,
        (
            popup_rect.centerx + 10,
            popup_rect.top + inner_pad,
        ),
    )

    for dtype, rect in shop_rects.items():
        cost = DEFENCE_STATS[dtype]["shop_cost"]
        pygame.draw.rect(screen, (70, 70, 110), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, width=1)

        label = f"Buy {dtype.capitalize()} ({cost}g)"
        text_surf = font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    if not owned_defences:
        none_text = font.render("(none)", True, (180, 180, 180))
        if owned_rects:
            _, first_rect = owned_rects[0]
            screen.blit(none_text, (first_rect.left, first_rect.top))
    else:
        for idx, rect in owned_rects:
            dtype, level = owned_defences[idx]
            pygame.draw.rect(screen, (60, 100, 60), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, width=1)

            temp_def = Defence(0, 0, defence_type=dtype, level=level)
            upg_cost = temp_def.get_upgrade_cost()

            label = f"{dtype.capitalize()} Lv{level}"
            text_surf = font.render(label, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)


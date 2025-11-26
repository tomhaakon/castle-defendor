import pygame


def main():
    pygame.init()

    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("CastleDefend0r")

    clock = pygame.time.Clock()
    running = True
    dt = 0

    slot_labels = ["slot_1", "slot_2", "slot_3", "slot_4", "slot_5"]

    font = pygame.font.SysFont(None, 24)

    # enemy setup
    enemies = []
    wave_number = 0
    enemy_size = 40
    base_enemy_speed = 120

    while running:
        dt = clock.tick(60) / 1000

        # 1 handle events
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if keys[pygame.K_ESCAPE]:
                running = False
            if keys[pygame.K_SPACE]:
                wave_number += 1
                spawn_wave(enemies, wave_number, screen, enemy_size, base_enemy_speed)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                if get_wave_button_rect(screen).collidepoint(mouse_pos):
                    wave_number += 1
                    spawn_wave(
                        enemies, wave_number, screen, enemy_size, base_enemy_speed
                    )

        # draw
        draw_background(screen)
        draw_slots(screen, font, slot_labels)
        draw_spawn_area(screen)

        castle_rect = get_castle_rect(screen)

        # castle outline
        pygame.draw.rect(screen, (120, 120, 150), castle_rect, width=1)

        draw_wave_button(screen, font, wave_number)

        # update & draw enemies
        update_and_draw_enemies(screen, enemies, dt, castle_rect, enemy_size)

        pygame.display.flip()

    pygame.quit()


def spawn_wave(enemies, wave_number, screen, enemy_size, base_speed):
    spawn_rect = get_spawn_rect(screen)

    num_enemies = 3 + wave_number * 2

    for i in range(num_enemies):
        # spread enemies evenly across spawn pos
        x = spawn_rect.left + (i + 0.5) * (spawn_rect.width / num_enemies)
        y = spawn_rect.bottom + enemy_size / 2

        enemy = {
            "pos": pygame.Vector2(x, y),
            "speed": base_speed + wave_number * 10,
            "state": "moving",
        }
        enemies.append(enemy)


def update_and_draw_enemies(screen, enemies, dt, castle_rect, enemy_size):
    for enemy in enemies:
        pos = enemy["pos"]
        state = enemy["state"]
        speed = enemy["speed"]

        enemy_rect = pygame.Rect(0, 0, enemy_size, enemy_size)
        enemy_rect.center = pos

        if state == "moving":
            # move down
            pos.y += speed * dt
            enemy_rect.center = pos

            # check collision
            if enemy_rect.colliderect(castle_rect):
                enemy["state"] = "attacking"
                # snap to castle
                pos.y = castle_rect.top - enemy_size / 3

                enemy_rect.center = pos

        # change color
        if enemy["state"] == "attacking":
            color = (50, 200, 50)
        else:
            color = (200, 50, 50)

        pygame.draw.rect(screen, color, enemy_rect)


def get_spawn_rect(screen):
    WIDTH, HEIGHT = screen.get_size()

    spawn_width = WIDTH - 100
    spawn_height = 80

    x = (WIDTH - spawn_width) // 2
    y = 0  # top

    return pygame.Rect(x, y, spawn_width, spawn_height)


def draw_spawn_area(screen):
    rect = get_spawn_rect(screen)
    pygame.draw.rect(screen, (100, 60, 60), rect)
    return rect


def get_castle_rect(screen):
    WIDTH, HEIGHT = screen.get_size()
    bottom_height = HEIGHT // 4

    top_height = HEIGHT - bottom_height

    return pygame.Rect(0, top_height, WIDTH, bottom_height)


def get_wave_button_rect(screen):
    WIDTH, HEIGHT = screen.get_size()
    bottom_height = HEIGHT // 4
    top_height = HEIGHT - bottom_height

    button_width = 220
    button_height = 50
    x = WIDTH - button_width - 20
    y = top_height + 20

    return pygame.Rect(x, y, button_width, button_height)


def draw_wave_button(screen, font, wave_number):
    rect = get_wave_button_rect(screen)

    pygame.draw.rect(screen, (100, 100, 130), rect)
    pygame.draw.rect(screen, (0, 0, 0), rect, width=2)

    label = f"Next wave ({wave_number + 1}) - SPACE"
    text_surf = font.render(label, True, (255, 255, 255))
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)


def draw_slots(screen, font, labels):

    width, height = screen.get_size()
    bottom_height = height // 4
    top_height = height - bottom_height

    hud_y = top_height
    hud_height = bottom_height

    num_slots = len(labels)

    # Slot visual settings
    slot_width = 100
    slot_height = 100
    margin_x = 40

    if num_slots > 1:
        spacing = (width - 2 * margin_x - num_slots * slot_width) // (num_slots - 1)

    else:
        spacing = 0

    # base y, aprox middle
    base_y = hud_y + (hud_height - slot_height) // 2

    # offets of slots
    y_offsets = [30, 15, 0, 15, 30]

    for i, label in enumerate(labels):
        x = margin_x + i * (slot_width + spacing)

        # apply arch
        y = base_y + y_offsets[i % len(y_offsets)]

        rect = pygame.Rect(x, y, slot_width, slot_height)

        # fill slot
        pygame.draw.rect(screen, (120, 120, 120), rect)
        # outline
        pygame.draw.rect(screen, (0, 0, 0), rect, width=2)

        # text

        text_surf = font.render(label, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)


def draw_background(screen):
    WIDTH, HEIGHT = screen.get_size()
    bottom_height = HEIGHT // 4
    top_height = HEIGHT - bottom_height

    pygame.draw.rect(screen, (80, 80, 80), pygame.Rect(0, 0, WIDTH, top_height))

    pygame.draw.rect(
        screen, (50, 50, 50), pygame.Rect(0, top_height, WIDTH, bottom_height)
    )


if __name__ == "__main__":
    main()

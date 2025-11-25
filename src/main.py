import pygame


def main():
    pygame.init()

    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("CastleDefend0r")

    bottom_height = 180
    top_height = 540

    top_gray = (80, 80, 80)
    bottom_gray = (50, 50, 50)

    clock = pygame.time.Clock()
    running = True
    dt = 0

    player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

    while running:
        # 1 handle events
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if keys[pygame.K_ESCAPE]:
            running = False

        pygame.draw.rect(screen, top_gray, pygame.Rect(0, 0, 1280, top_height))

        pygame.draw.rect(
            screen, bottom_gray, pygame.Rect(0, top_height, 1280, bottom_height)
        )

        pygame.display.flip()

        dt = clock.tick(60) / 1000

    pygame.quit()


if __name__ == "__main__":
    main()

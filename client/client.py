import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame

import game
import connect_screen
import consts


def init_pygame() -> pygame.Surface:
    """
    Use: starts pygame with and return the new screen
    """
    pygame.init()
    screen = pygame.display.set_mode((consts.WIDTH, consts.HEIGHT))
    pygame.display.set_caption(consts.GAME_NAME)
    pygame.display.set_icon(pygame.image.load(consts.PLAYER_IMG))

    return screen


if __name__ == "__main__":
    screen = init_pygame()

    connection_screen = connect_screen.ConnectScreen(screen)
    connection_screen.run()

    my_game = game.Game(connection_screen.sock, connection_screen.addr, connection_screen.full_screen)
    my_game.run()

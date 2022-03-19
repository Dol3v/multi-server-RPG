import pygame

from connect_screen import ConnectScreen
from game import Game
from consts import *


def init_pygame() -> pygame.Surface:

    """
    Use: starts pygame with and return the new screen
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(GAME_NAME)
    pygame.display.set_icon(pygame.image.load(PLAYER_IMG))

    return screen
    


if __name__ == "__main__":

    screen = init_pygame()

    connection_screen = ConnectScreen(screen)
    connection_screen.run()

    game = Game(connection_screen.sock, connection_screen.addr, connection_screen.full_screen)
    game.run()

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

    stage = ConnectScreen(screen)
    stage.run()

    stage = Game(stage.sock, stage.addr, stage.full_screen)
    stage.run()

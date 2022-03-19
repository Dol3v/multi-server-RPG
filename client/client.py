from connect_screen import ConnectScreen
from game import Game
import pygame
from consts import *


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.full_screen = False
        pygame.display.set_caption(GAME_NAME)
        pygame.display.set_icon(pygame.image.load(PLAYER_IMG))
        stage = ConnectScreen(self.screen)
        stage.run()

        stage = Game(stage.sock, stage.addr, stage.full_screen)
        stage.run()


if __name__ == "__main__":
    App()

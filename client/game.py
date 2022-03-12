import socket
import sys

import pygame

from level import Level
from consts import *


class Game:
    def __init__(self, conn: socket.socket):

        # general setup
        pygame.init()
        self.conn = conn
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("MMORPG Game")
        pygame.display.set_icon(pygame.image.load('idle_down.png'))
        self.clock = pygame.time.Clock()

        self.level = Level()

    def run(self):

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # send()

            self.screen.fill('black')
            self.level.run()
            pygame.display.update()
            self.clock.tick(FPS)

import socket
import sys

import pygame

from map import Map
from consts import *

class Game:
    def __init__(self, conn: socket.socket, server_addr: tuple):

        # communication 
        self.conn = conn
        # timeout of 0.5 seconds
        self.conn.settimeout(0.5)
        self.server_addr = server_addr


        # pygame globals
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(GAME_NAME)
        pygame.display.set_icon(pygame.image.load(PLAYER_IMG))
        self.clock = pygame.time.Clock()

        # logic
        self.level = Map(self)

    def run(self):

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()


            # run level
            self.screen.fill('black')
            self.level.run()
            pygame.display.flip()
            self.clock.tick(FPS)




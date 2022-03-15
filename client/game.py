import socket
import sys

import pygame

from map import Map
from consts import *
from connectscreen import ConnectScreen

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
        self.full_screen = False
        pygame.display.set_caption(GAME_NAME)
        pygame.display.set_icon(pygame.image.load(PLAYER_IMG))
        self.clock = pygame.time.Clock()

        # logic
        self.current_screen = ConnectScreen(self)

    def run(self):
        while True:
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        if self.full_screen:
                            self.screen = self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        else:
                            self.screen = self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                        self.full_screen = not self.full_screen

            self.screen.fill("black")
            self.current_screen.run(event_list)
            pygame.display.update()
            self.clock.tick(FPS)




import socket
import sys

import pygame

from level import Level
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
        pygame.display.set_caption("MMORPG Game")
        pygame.display.set_icon(pygame.image.load('idle_down.png'))
        self.clock = pygame.time.Clock()

        # logic
        self.level = Level()

    def server_handler(self):
        """
        Use: communicate with the server over UDP.
        """
        try:
            # sending location and actions
            self.conn.sendto(b"location", self.server_addr)

            # receive server update
            data, addr = self.conn.recvfrom(1024)
            print(f"Data: {data}\nFrom: {addr}")
        except TimeoutError:
            print("Timeout")
        

    def run(self):

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()


            # run level
            self.screen.fill('black')
            self.level.run()
            pygame.display.update()
            self.clock.tick(FPS)

            # server synchronization 
            self.server_handler()


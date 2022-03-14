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
        pygame.display.set_caption(GAME_NAME)
        pygame.display.set_icon(pygame.image.load(PLAYER_IMG))
        self.clock = pygame.time.Clock()

        self.player_img = pygame.image.load(PLAYER_IMG)

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
        
    # ------------------------------------------------------------------
    def render_client(self, x: int, y: int):
        """
        Use: print client by the given x and y
        """
        self.screen.blit(self.player_img, self.player_img.get_rect(center=(x, y)))

    
    def render_clients(self, clients_info: list):
        """
        Use: prints the other clients by the given info about them
        """
        for client in clients_info:
            render_client(client[0][1])
    # ------------------------------------------------------------------


    def run(self):

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()


            # run level
            self.screen.fill('black')
            self.render_client(0, 0)
            self.level.run()
            pygame.display.flip()
            self.clock.tick(FPS)

            # server synchronization 
            self.server_handler()




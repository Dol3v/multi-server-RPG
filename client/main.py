import pygame
import sys

from level import Level
from settings import *
from connectscreen import ConnectScreen


class Game:
    def __init__(self):

        # general setup
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.full_screen = False
        pygame.display.set_caption("MMORPG Game")
        pygame.display.set_icon(pygame.image.load('assets/idle_down.png'))
        self.clock = pygame.time.Clock()
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
            self.current_screen.run(event_list)
            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    game.run()

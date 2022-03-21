import pygame

from consts import *


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(*groups)
        # get the directory of this file

        self.image = pygame.image.load(TREE_IMG).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)

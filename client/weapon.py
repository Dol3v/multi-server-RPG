import pygame
import numpy as np

from consts import *

class Weapon(pygame.sprite.Sprite):
    def __init__(self, player, groups, vec):
        super().__init__(groups)
        self.sword = pygame.image.load(SWORD_IMG)
        self.image = pygame.Surface((self.sword.get_width(), self.sword.get_height()), pygame.SRCALPHA)

        angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        self.sword = pygame.transform.rotate(self.sword, angle)
        self.image = pygame.transform.rotate(self.image, angle)

        self.image.blit(self.sword, (0, 0))

        # self.image.fill("red")

        self.rect = self.image.get_rect(center=player.rect.center + pygame.math.Vector2(60 * vec[0], (60 * vec[1] + 3)))

import math
from typing import Tuple

import pygame
import numpy as np
from consts import *


class Weapon(pygame.sprite.Sprite):
    def __init__(self, groups, weapon_type, rarity):
        super().__init__(*groups)
        self.weapon_type = weapon_type
        self.rarity = rarity
        self.texture = pygame.image.load(f"assets/weapons/{weapon_type}/full.png")

        self.original_texture = pygame.image.load(f"assets/weapons/{weapon_type}/full.png")
        self.original_image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)

        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        # angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        # self.sword = pygame.transform.rotate(self.sword, angle)
        # self.image = pygame.transform.rotate(self.image, angle)

    def draw_weapon(self, player):
        center_x = WIDTH // 2
        center_y = HEIGHT // 2

        mouse_pos = pygame.mouse.get_pos()

        vec_x = (mouse_pos[0] - center_x)
        vec_y = (mouse_pos[1] - center_y)

        vec = self.normalize_vec(vec_x, vec_y)
        angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        self.texture = pygame.transform.rotate(self.original_texture, angle)
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.image.blit(self.texture, (0, 0))
        self.rect = self.image.get_rect(
            center=player.rect.center + pygame.math.Vector2(60 * vec[0], (60 * vec[1] + 3)))

    def normalize_vec(self, x, y) -> Tuple[float, float]:
        factor = math.sqrt(x ** 2 + y ** 2)
        if factor == 0:
            return 0, -0.1
        return x / factor, y / factor

    def attack(self, player):
        pass

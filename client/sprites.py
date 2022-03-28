"""Every sprite or group class for the client"""
"""
TODO: merge the weapon classes with the Player class
"""

import pygame

from consts import *
from common.consts import SCREEN_WIDTH, SCREEN_HEIGHT

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(*groups)
        # get the directory of this file

        self.image = pygame.image.load(TREE_IMG).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)


class FollowingCameraGroup(pygame.sprite.Group):
    def __init__(self):
        # general setup
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = SCREEN_WIDTH / 2
        self.half_height = SCREEN_HEIGHT / 2
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        # getting the offset
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        # for spr in self.sprites():
        for sprite in sorted(self.sprites(), key=lambda spr: spr.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)


class Entity(pygame.sprite.Sprite):
    def __init__(self, groups, x, y):
        super().__init__(*groups)
        self.x = x
        self.y = y
        self.texture = pygame.image.load(PLAYER_IMG)
        self.draw_player_entity()

    def move_to(self, x, y):
        self.x = x
        self.y = y

    def draw_player_entity(self):
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()),
                                    pygame.SRCALPHA)

        self.image.blit(self.texture, (0, 0))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.draw_player_entity()

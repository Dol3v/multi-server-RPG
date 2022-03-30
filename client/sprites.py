"""Every sprite or group class for the client"""
"""
TODO: merge the weapon classes with the Player class
"""

import pygame

from graphics import Animation
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

        # creating the floor
        self.floor_surface = pygame.image.load('assets/map1.jpg')
        self.floor_rect = self.floor_surface.get_rect(topleft=(0, 0))

    def custom_draw(self, player):
        # getting the offset
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        if self.offset.x < 0:
            self.offset.x = 0
        if self.offset.y < 0:
            self.offset.y = 0

        # drawing the floor
        floor_offset_pos = self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surface, floor_offset_pos)

        # for spr in self.sprites():
        for sprite in sorted(self.sprites(), key=lambda spr: spr.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)


class Entity(pygame.sprite.Sprite):
    def __init__(self, groups, x, y, direction):
        super().__init__(*groups)
        self.x = x
        self.y = y

        self.last_x = x
        self.last_y = y
        self.texture = pygame.image.load("assets/character/knight/knight.png").convert_alpha()
        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * PLAYER_SIZE_MULTIPLIER,
                                                             self.texture.get_height() * PLAYER_SIZE_MULTIPLIER))

        self.original_texture = self.texture.copy()

        self.direction = direction
        self.draw_entity()

    def move_to(self, x, y):
        self.last_x = self.x
        self.last_y = self.y
        self.x = x
        self.y = y

    def draw_entity(self):
        pass

    def update(self):
        self.draw_entity()


class PlayerEntity(Entity):
    def __init__(self, groups, x, y, direction):
        super().__init__(groups, x, y, direction)
        self.texture = pygame.image.load("assets/character/knight/knight.png").convert_alpha()
        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * PLAYER_SIZE_MULTIPLIER,
                                                             self.texture.get_height() * PLAYER_SIZE_MULTIPLIER))
        self.original_texture = self.texture.copy()

        self.direction = direction

        self.animation = Animation(
            [
                pygame.image.load("assets/character/knight/move_0.png"),
                pygame.image.load("assets/character/knight/move_1.png"),
                pygame.image.load("assets/character/knight/move_2.png")
            ],
            10
        )

        self.draw_entity()

    def draw_entity(self):
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()),
                                    pygame.SRCALPHA)

        self.image.blit(self.texture, (0, 0))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update_player_animation(self):
        if self.last_x != self.x or self.last_y != self.y:
            print("should to animation")
            frame = self.animation.get_next_frame()
            if self.direction[0] < 0:
                frame = pygame.transform.flip(frame, True, False)
            frame = pygame.transform.scale(frame, (frame.get_width() * PLAYER_SIZE_MULTIPLIER,
                                                   frame.get_height() * PLAYER_SIZE_MULTIPLIER))
            self.texture = frame

        else:
            if self.direction[0] < 0:
                self.texture = pygame.transform.flip(self.original_texture, True, False)
            else:
                self.texture = self.original_texture

    def update(self):
        self.draw_entity()
        self.update_player_animation()

import datetime
import time

import pygame
import numpy as np
import abc

from common.utils import get_bounding_box
from consts import *
from common.consts import PROJECTILE_SPEED, ARROW_OFFSET_FACTOR, SCREEN_HEIGHT, SCREEN_WIDTH


def get_weapon_type(tool_id: int) -> str | None:
    for weapon_type in weapon_data:
        if weapon_data[weapon_type]["id"] == tool_id:
            return weapon_type
    return None


class Hand(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(*groups)

        self.texture = pygame.image.load("assets/character/knight/knight_hand.png")
        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * (PLAYER_SIZE_MULTIPLIER - 0.5),
                                                             self.texture.get_height() * (PLAYER_SIZE_MULTIPLIER - 0.5))
                                              )
        self.original_texture = self.texture.copy()

        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.original_image = self.image.copy()

        self.rect = self.image.get_rect()

    def draw_hand(self, player):
        vec = player.get_direction_vec()

        angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        self.image = pygame.transform.rotate(self.original_image, angle)
        self.image.blit(pygame.transform.rotate(self.texture, angle), (0, 0))
        self.rect = self.image.get_rect(
            center=player.rect.center + pygame.math.Vector2(45 * vec[0], (45 * vec[1] + 3)))

    def hide(self):
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.rect = self.image.get_rect()


class Item(pygame.sprite.Sprite):
    def __init__(self, visible_sprites, weapon_type, rarity, flip_item=True, add_to_sprite_group=True):
        super().__init__()
        self.visible_sprites = visible_sprites
        if add_to_sprite_group:
            self.start_drawing()

        self.weapon_type = weapon_type
        self.rarity = rarity
        self.texture = pygame.image.load(f"assets/weapons/{weapon_type}/full.png")

        self.icon = pygame.transform.scale(self.texture, (32, 32))
        self.flip_item = flip_item

        data = weapon_data.get(weapon_type)

        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * data["size_multiplier"],
                                                             self.texture.get_height() * data["size_multiplier"]))

        self.original_texture = self.texture.copy()
        hand = pygame.image.load("assets/character/knight/knight_hand.png")
        hand = pygame.transform.scale(hand, (hand.get_width() * (PLAYER_SIZE_MULTIPLIER - 0.5),
                                             hand.get_height() * (PLAYER_SIZE_MULTIPLIER - 0.5)))

        self.is_ranged = data.get("is_ranged")
        self.damage = data.get("damage")
        self.cooldown = data.get("cooldown")

        hand_position = data.get("hand_position")

        self.original_texture.blit(hand, (hand_position[0], hand_position[1]))

        self.original_image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

        # angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        # self.sword = pygame.transform.rotate(self.sword, angle)
        # self.image = pygame.transform.rotate(self.image, angle)

    def draw_item(self, player):
        vec = player.get_direction_vec()

        angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        self.texture = self.original_texture

        if vec[0] < 0 and self.flip_item:
            self.texture = pygame.transform.flip(self.original_texture, True, False)

        self.texture = pygame.transform.rotate(self.texture, angle)
        self.image = pygame.transform.rotate(self.original_image, angle)

        self.image.blit(self.texture, (0, 0))
        self.rect = self.image.get_rect(
            center=player.rect.center + pygame.math.Vector2(60 * vec[0], (60 * vec[1] + 3)))

    def hide(self):
        self.remove(self.visible_sprites)

    def start_drawing(self):
        self.add(self.visible_sprites)

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

        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()))
        self.original_image = self.image.copy()

        self.rect = self.image.get_rect()

    def draw_weapon(self, player):
        vec = player.get_direction_vec()

        angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        self.image = pygame.transform.rotate(self.original_image, angle)
        self.image.blit(self.texture, (0, 0))
        self.rect = self.image.get_rect(
            center=player.rect.center + pygame.math.Vector2(45 * vec[0], (45 * vec[1] + 3)))

    def hide(self):
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.rect = self.image.get_rect()


class Weapon(pygame.sprite.Sprite):
    def __init__(self, groups, weapon_type, rarity, flip_weapon=True):
        super().__init__(*groups)
        self.weapon_type = weapon_type
        self.rarity = rarity
        self.texture = pygame.image.load(f"assets/weapons/{weapon_type}/full.png")

        self.icon = pygame.transform.scale(self.texture, (32, 32))
        self.flip_weapon = flip_weapon

        self.original_texture = pygame.image.load(f"assets/weapons/{weapon_type}/full.png")
        hand = pygame.image.load("assets/character/knight/knight_hand.png")
        hand = pygame.transform.scale(hand, (hand.get_width() * (PLAYER_SIZE_MULTIPLIER - 0.5),
                                             hand.get_height() * (PLAYER_SIZE_MULTIPLIER - 0.5)))

        data = weapon_data.get(weapon_type)

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

    def draw_weapon(self, player):
        vec = player.get_direction_vec()

        angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        self.texture = self.original_texture

        if vec[0] < 0 and self.flip_weapon:
            self.texture = pygame.transform.flip(self.original_texture, True, False)

        self.texture = pygame.transform.rotate(self.texture, angle)
        self.image = pygame.transform.rotate(self.original_image, angle)

        self.image.blit(self.texture, (0, 0))
        self.rect = self.image.get_rect(
            center=player.rect.center + pygame.math.Vector2(60 * vec[0], (60 * vec[1] + 3)))

    def hide(self):
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    @abc.abstractmethod
    def attack(self, player):
        return


class RangeWeapon(Weapon):
    def __init__(self, groups, obstacle_sprites, map_collision, weapon_type, rarity):
        super().__init__(groups, weapon_type, rarity)
        self.groups = groups
        self.map_collision = map_collision
        self.projectile_texture = pygame.image.load(f"assets/weapons/{weapon_type}/projectile.png")
        self.obstacle_sprites = obstacle_sprites
        self.is_ranged = True

    def attack(self, player):
        Projectile((*self.groups, self.obstacle_sprites), self.map_collision, player.rect.centerx, player.rect.centery,
                   self.projectile_texture, PROJECTILE_SPEED, player.get_direction_vec(), 200)
        pass


class Projectile(pygame.sprite.Sprite):
    def __init__(self, groups, map_collision, x, y, texture, speed, vec, ttl):
        super().__init__(*groups)
        self.groups = groups
        self.map_collision = map_collision
        self.x = x + ARROW_OFFSET_FACTOR * vec[0]
        self.y = y + ARROW_OFFSET_FACTOR * vec[1]
        self.texture = texture
        self.speed = speed
        self.vec = vec
        self.angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))
        self.ttl = ttl
        self.loops = 0

        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.texture = pygame.transform.rotate(self.texture, self.angle)
        self.image = pygame.transform.rotate(self.image, self.angle)
        self.image.blit(self.texture, (0, 0))
        self.draw_projectile()

    def draw_projectile(self):
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def check_collision(self):
        for sprite in self.groups[1]:
            if sprite != self and sprite.rect.colliderect(self.rect) and not isinstance(sprite, Projectile):
                self.kill()
        for _, rect in self.map_collision.intersect(get_bounding_box((self.rect.x, self.rect.y),
                                                                  SCREEN_HEIGHT, SCREEN_WIDTH)):
            if rect.colliderect(self.rect):
                self.kill()

    def move_projectile(self):
        self.x += self.vec[0] * self.speed
        self.y += self.vec[1] * self.speed

    def update(self):
        if self.loops > self.ttl:
            self.kill()
        self.check_collision()
        self.move_projectile()
        self.draw_projectile()
        self.loops += 1

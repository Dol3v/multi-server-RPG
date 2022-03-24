"""Every sprite or group class for the client"""
"""
TODO: merge the weapon classes with the Entity class
"""
import pygame
import math
import numpy as np
import abc

from typing import Tuple

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
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        mouse_pos = pygame.mouse.get_pos()

        vec_x = (mouse_pos[0] - center_x)
        vec_y = (mouse_pos[1] - center_y)

        vec = normalize_vec(vec_x, vec_y)

        angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        self.texture = pygame.transform.rotate(self.original_texture, angle)
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.image.blit(self.texture, (0, 0))
        self.rect = self.image.get_rect(
            center=player.rect.center + pygame.math.Vector2(60 * vec[0], (60 * vec[1] + 3)))

    @staticmethod
    def normalize_vec(x, y) -> Tuple[float, float]:
        factor = math.sqrt(x ** 2 + y ** 2)
        if factor == 0:
            return 0, -0.1
        return x / factor, y / factor

    @abc.abstractmethod
    def attack(self, player):
        return


class RangeWeapon(Weapon):
    def __init__(self, groups, obstacle_sprites, weapon_type, rarity):
        super().__init__(*groups, weapon_type, rarity)
        self.groups = groups
        self.projectile_texture = pygame.image.load(f"assets/weapons/{weapon_type}/projectile.png")
        self.obstacle_sprites = obstacle_sprites

    def attack(self, player):
        center_x = WIDTH // 2
        center_y = HEIGHT // 2

        mouse_pos = pygame.mouse.get_pos()

        vec_x = (mouse_pos[0] - center_x)
        vec_y = (mouse_pos[1] - center_y)

        vec = normalize_vec(vec_x, vec_y)

        Projectile([*self.groups, self.obstacle_sprites], player.rect.centerx, player.rect.centery,
                   self.projectile_texture, 4, vec, 200)
        pass


class Projectile(pygame.sprite.Sprite):
    def __init__(self, groups, x, y, texture, speed, vec, ttl):
        super().__init__(*groups)
        self.groups = groups
        self.x = x + 100 * vec[0]
        self.y = y + 100 * vec[1]
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

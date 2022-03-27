import pygame
import numpy as np
import abc
from common.consts import SCREEN_HEIGHT, SCREEN_WIDTH
from common.utils import normalize_vec


def get_weapon_type(tool_id: int) -> str:
    if tool_id == 0:
        return None
    if tool_id == 1:
        return "sword"
    if tool_id == 2:
        return "axe"
    if tool_id == 3:
        return "bow"


class Weapon(pygame.sprite.Sprite):
    def __init__(self, groups, weapon_type, rarity):
        super().__init__(*groups)
        self.weapon_type = weapon_type
        self.rarity = rarity
        self.texture = pygame.image.load(f"assets/weapons/{weapon_type}/full.png")

        self.icon = pygame.transform.scale(self.texture, (32, 32))

        self.original_texture = pygame.image.load(f"assets/weapons/{weapon_type}/full.png")
        self.original_image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        # angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        # self.sword = pygame.transform.rotate(self.sword, angle)
        # self.image = pygame.transform.rotate(self.image, angle)

    def draw_weapon(self, player):
        vec = player.get_direction_vec()

        angle = -(180 - np.rad2deg(np.arctan2(vec[0], vec[1])))

        self.texture = pygame.transform.rotate(self.original_texture, angle)
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
    def __init__(self, groups, obstacle_sprites, weapon_type, rarity):
        super().__init__(groups, weapon_type, rarity)
        self.groups = groups
        self.projectile_texture = pygame.image.load(f"assets/weapons/{weapon_type}/projectile.png")
        self.obstacle_sprites = obstacle_sprites

    def attack(self, player):
        Projectile([*self.groups, self.obstacle_sprites], player.rect.centerx, player.rect.centery,
                   self.projectile_texture, 4, player.get_direction_vec(), 200)
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

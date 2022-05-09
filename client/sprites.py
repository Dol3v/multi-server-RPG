"""Every sprite or group class for the client"""

import numpy as np
import pygame

from common.consts import SCREEN_WIDTH, SCREEN_HEIGHT, EntityType

try:
    import client_consts as consts
    import graphics
    import items
except ModuleNotFoundError:
    from client import client_consts as consts
    from client import graphics
    from client import items

"""
TODO: merge the weapon classes with the Player class
"""


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, obstacle_group, rect: pygame.Rect):
        super().__init__(obstacle_group)
        self.image = None
        self.rect = rect


class Tile(pygame.sprite.Sprite):
    def __init__(self, groups, pos, image):
        super().__init__(*groups)
        # get the directory of this file
        self.image = image

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
    def __init__(self, groups, entity_type, x, y, direction):
        super().__init__(*groups)
        self.x = x
        self.y = y

        self.entity_type = entity_type

        self.health = consts.MAX_HEALTH

        self.last_x = x
        self.last_y = y

        self.scale_size = consts.ENTITY_DATA[entity_type][3]

        self.draw_hp = consts.ENTITY_DATA[entity_type][4]

        if entity_type == "player":
            return

        self.texture = pygame.image.load("assets/" + consts.ENTITY_DATA[entity_type][0]).convert_alpha()
        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * self.scale_size,
                                                             self.texture.get_height() * self.scale_size))
        self.animation_ticks = 0  # Animation running delay so it won't look buggy
        anim = []

        for path in consts.ENTITY_DATA[entity_type][1]:
            anim.append(pygame.image.load("assets/" + path))

        self.animation = graphics.Animation(anim, consts.ENTITY_DATA[entity_type][2])

        if self.animation.is_empty():
            self.animation = graphics.Animation([self.texture.copy()], consts.ENTITY_DATA[entity_type][2])

        self.original_texture = self.texture.copy()

        self.direction = direction
        self.draw_entity()

    def move_to(self, x, y):
        self.last_x = self.x
        self.last_y = self.y
        self.x = x
        self.y = y
        if (self.last_x != self.x) or (self.last_y != self.y):
            self.animation_ticks = 0

    def draw_entity(self):
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()),
                                    pygame.SRCALPHA)

        self.image.blit(self.texture, (0, 0))
        if self.draw_hp:
            self.image.fill((255, 0, 0),
                            (0, 0, (self.texture.get_width()) * (self.health / consts.MAX_HEALTH),
                             self.texture.get_height() * 0.02))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.update_entity_animation()
        self.draw_entity()
        if self.animation_ticks < 10:
            self.animation_ticks += 1

    def update_entity_animation(self):
        # Movement
        if (self.last_x != self.x or self.last_y != self.y) or (self.animation_ticks < 10):
            frame = self.animation.get_next_frame()
            if self.direction[0] < 0:
                frame = pygame.transform.flip(frame, True, False)
            frame = pygame.transform.scale(frame, (frame.get_width() * self.scale_size,
                                                   frame.get_height() * self.scale_size))
            self.texture = frame

            if self.entity_type == EntityType.PROJECTILE:
                angle = -(180 - np.rad2deg(np.arctan2(self.direction[0], self.direction[1])))
                self.texture = pygame.transform.rotate(self.texture, angle)

        else:
            if self.entity_type != EntityType.PROJECTILE:
                if self.direction[0] < 0:
                    self.texture = pygame.transform.flip(self.original_texture, True, False)
                else:
                    self.texture = self.original_texture


class PlayerEntity(Entity):
    def __init__(self, groups, x, y, direction, tool_id, map_collision):
        super().__init__(groups, EntityType.PLAYER, x, y, direction)
        self.texture = pygame.image.load("assets/character/knight/knight.png").convert_alpha()
        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * consts.PLAYER_SIZE_MULTIPLIER,
                                                             self.texture.get_height() * consts.PLAYER_SIZE_MULTIPLIER))
        self.original_texture = self.texture.copy()
        self.direction = direction

        self.visible_sprites = (groups[1],)
        self.obstacles_sprites = (groups[0],)
        self.tool_id = 0
        self.hand = items.Hand(self.visible_sprites)
        self.map_collision = map_collision
        self.update_tool(tool_id)

        self.groups = groups

        self.animation = graphics.Animation(
            [
                pygame.image.load("assets/character/knight/move_0.png"),
                pygame.image.load("assets/character/knight/move_1.png"),
                pygame.image.load("assets/character/knight/move_2.png")
            ],
            10
        )

        self.draw_entity()

    def get_direction_vec(self):
        return self.direction

    def update_player_animation(self):
        # Hand Movements
        self.hand.draw_weapon(self)

        # Movement
        if self.last_x != self.x or self.last_y != self.y:
            frame = self.animation.get_next_frame()
            if self.direction[0] < 0:
                frame = pygame.transform.flip(frame, True, False)
            frame = pygame.transform.scale(frame, (frame.get_width() * consts.PLAYER_SIZE_MULTIPLIER,
                                                   frame.get_height() * consts.PLAYER_SIZE_MULTIPLIER))
            self.texture = frame

        else:
            if self.direction[0] < 0:
                self.texture = pygame.transform.flip(self.original_texture, True, False)
            else:
                self.texture = self.original_texture

    def update_tool(self, tool_id):
        self.tool_id = tool_id
        self.hand.kill()

        if tool_id == 0:
            self.hand = items.Hand(self.visible_sprites)
            return
        for item in consts.weapon_data.keys():
            if consts.weapon_data[item]["id"] == tool_id:
                self.hand = items.Item(self.visible_sprites, item, "rare")
                return

    def update(self):
        self.draw_entity()
        self.hand.draw(self)
        self.update_entity_animation()

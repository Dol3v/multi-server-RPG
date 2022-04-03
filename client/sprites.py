"""Every sprite or group class for the client"""
"""
TODO: merge the weapon classes with the Player class
"""

from graphics import Animation
from weapons import *


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

        self.last_x = x
        self.last_y = y

        self.scale_size = entity_data[entity_type][3]

        if entity_type == "player":
            return

        self.texture = pygame.image.load("assets/entity/" + entity_data[entity_type][0]).convert_alpha()
        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * self.scale_size,
                                                             self.texture.get_height() * self.scale_size))

        self.animation = Animation(entity_data[entity_type][1], entity_data[entity_type][2])

        if self.animation.is_empty():
            self.animation = Animation([self.texture.copy()], entity_data[entity_type][2])

        self.original_texture = self.texture.copy()

        self.direction = direction
        self.draw_entity()

    def move_to(self, x, y):
        self.last_x = self.x
        self.last_y = self.y
        self.x = x
        self.y = y

    def draw_entity(self):
        self.image = pygame.Surface((self.texture.get_width(), self.texture.get_height()),
                                    pygame.SRCALPHA)

        self.image.blit(self.texture, (0, 0))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.update_entity_animation()
        self.draw_entity()

    def update_entity_animation(self):
        # Movement


        if self.last_x != self.x or self.last_y != self.y:
            frame = self.animation.get_next_frame()
            if self.direction[0] < 0:
                frame = pygame.transform.flip(frame, True, False)
            frame = pygame.transform.scale(frame, (frame.get_width() * self.scale_size,
                                                   frame.get_height() * self.scale_size))
            self.texture = frame

            if self.entity_type == ARROW_TYPE:
                angle = -(180 - np.rad2deg(np.arctan2(self.direction[0], self.direction[1])))
                self.texture = pygame.transform.rotate(self.texture,angle)

        else:
            if self.entity_type != ARROW_TYPE:
                if self.direction[0] < 0:
                    self.texture = pygame.transform.flip(self.original_texture, True, False)
                else:
                    self.texture = self.original_texture


class PlayerEntity(Entity):
    def __init__(self, groups, x, y, direction, tool_id, map_collision):
        super().__init__(groups, "player", x, y, direction, 1)
        self.texture = pygame.image.load("assets/character/knight/knight.png").convert_alpha()
        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * PLAYER_SIZE_MULTIPLIER,
                                                             self.texture.get_height() * PLAYER_SIZE_MULTIPLIER))
        self.original_texture = self.texture.copy()
        self.direction = direction

        self.visible_sprites = (groups[1],)
        self.obstacles_sprites = (groups[0],)
        self.tool_id = 0
        self.hand = Hand(self.visible_sprites)
        self.map_collision = map_collision
        self.update_tool(tool_id)

        self.groups = groups

        self.animation = Animation(
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

    def update_tool(self, tool_id):
        self.tool_id = tool_id
        self.hand.kill()
        match tool_id:
            case 0:
                self.hand = Hand(self.visible_sprites)
            case 1:
                self.hand = Weapon(self.visible_sprites, "sword", "rare")
            case 2:
                self.hand = Weapon(self.visible_sprites, "axe", "rare")
            case 3:
                self.hand = RangeWeapon(self.visible_sprites, self.obstacles_sprites, self.map_collision,
                                        "bow", "rare")

    def update(self):
        self.draw_entity()
        self.hand.draw_weapon(self)
        self.update_entity_animation()


class EntityBoots(Entity):
    def __init__(self, groups, x, y, direction):
        super().__init__(groups, x, y, direction)
        self.texture = pygame.image.load("assets/mobs/Big demon/big_demon_idle_anim_f0.png").convert_alpha()
        self.texture = pygame.transform.scale(self.texture, (self.texture.get_width() * PLAYER_SIZE_MULTIPLIER,
                                                             self.texture.get_height() * PLAYER_SIZE_MULTIPLIER))
        self.original_texture = self.texture.copy()
        self.direction = direction

        self.visible_sprites = (groups[1],)
        self.obstacles_sprites = (groups[0],)
        self.groups = groups

        self.animation = Animation(
            [
                pygame.image.load("assets/mobs/Big demon/big_demon_run_anim_f0.png"),
                pygame.image.load("assets/mobs/Big demon/big_demon_run_anim_f1.png"),
                pygame.image.load("assets/mobs/Big demon/big_demon_run_anim_f2.png"),
                pygame.image.load("assets/mobs/Big demon/big_demon_run_anim_f3.png")
            ],
            10
        )

        self.draw_entity()

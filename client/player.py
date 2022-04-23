"""Player class..."""
from typing import List, Tuple

import pygame

from common.consts import SPEED, SCREEN_HEIGHT, SCREEN_WIDTH
from common.utils import normalize_vec, get_bounding_box
from items import *
from consts import *
from graphics import Animation, Inventory


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, map_collision, display_surface):
        super().__init__(*groups)
        # self.image = pygame.image.load(PLAYER_IMG).convert_alpha()
        self.map_collision = map_collision
        self.image = pygame.image.load("assets/character/knight/knight.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * PLAYER_SIZE_MULTIPLIER,
                                                         self.image.get_height() * PLAYER_SIZE_MULTIPLIER))
        self.original_image = self.image.copy()
        self.display_surface = display_surface

        self.inv = Inventory()
        self.inv.set_item_in_slot(5, Item(groups[0], "health_potion", "rare", False, False))
        self.inv.set_item_in_slot(20, Item(groups[0], "sword", "rare", False, False))
        self.inv.set_item_in_slot(25, Item(groups[0], "shmulik_mahak", "rare", True, False))

        self.moving_animation = Animation(
            [pygame.image.load("assets/character/knight/move_0.png"),
             pygame.image.load("assets/character/knight/move_1.png"),
             pygame.image.load("assets/character/knight/move_2.png")],
            10
        )

        self.rect = self.image.get_rect(center=pos)

        self.looking_direction = "RIGHT"

        self.direction = pygame.math.Vector2()
        self.speed = SPEED
        self.max_health = MAX_HEALTH
        self.current_health = self.max_health
        self.obstacle_sprites = obstacle_sprites
        self.attack_cooldown = pygame.time.get_ticks()
        self.attacking = False
        self.is_typing = False
        self.is_inv_open = True

        self.hand = Hand(groups)

        self.hotbar: List[Item | None] = self.inv.get_hotbar_items()
        self.current_hotbar_slot = 0

    def input(self):
        if self.is_typing:
            self.direction.x = 0
            self.direction.y = 0
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            if pygame.time.get_ticks() < self.attack_cooldown:
                self.direction.x = 0
                self.direction.y = 0
                return
            self.direction.y = -1
        elif keys[pygame.K_s]:
            if pygame.time.get_ticks() < self.attack_cooldown:
                self.direction.x = 0
                self.direction.y = 0
                return
            self.direction.y = 1
        else:
            self.direction.y = 0
        if keys[pygame.K_d]:
            if pygame.time.get_ticks() < self.attack_cooldown:
                self.direction.x = 0
                self.direction.y = 0
                return
            self.direction.x = 1
        elif keys[pygame.K_a]:
            if pygame.time.get_ticks() < self.attack_cooldown:
                self.direction.x = 0
                self.direction.y = 0
                return
            self.direction.x = -1
        else:
            self.direction.x = 0

        if pygame.mouse.get_pressed()[0]:  # Check if the mouse is clicked
            if not self.hotbar[self.current_hotbar_slot]:
                return
            item = self.hotbar[self.current_hotbar_slot]
            if not self.attacking:
                if self.attack_cooldown < pygame.time.get_ticks():
                    self.attacking = True
                    self.attack_cooldown = pygame.time.get_ticks() + item.cooldown
        else:
            self.attacking = False

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()
        self.rect.x += self.direction.x * speed
        if self.rect.x < 0:
            self.rect.x = 0
        self.collision('horizontal')

        self.rect.y += self.direction.y * speed
        if self.rect.y < 0:
            self.rect.y = 0

        self.collision('vertical')

    # self.rect.center += self.direction*speed

    def collision(self, direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.direction.x > 0:  # moving right
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0:  # moving left
                        self.rect.left = sprite.rect.right
            for _, rect in self.map_collision.intersect(get_bounding_box((self.rect.x, self.rect.y),
                                                                         SCREEN_HEIGHT, SCREEN_WIDTH)):
                if rect.colliderect(self.rect):
                    if self.direction.x > 0:  # moving right
                        self.rect.right = rect.left
                    if self.direction.x < 0:  # moving left
                        self.rect.left = rect.right

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.direction.y > 0:  # moving down
                        self.rect.bottom = sprite.rect.top
                    if self.direction.y < 0:  # moving up
                        self.rect.top = sprite.rect.bottom
            for _, rect in self.map_collision.intersect(get_bounding_box((self.rect.x, self.rect.y),
                                                                         SCREEN_HEIGHT, SCREEN_WIDTH)):
                if rect.colliderect(self.rect):
                    if self.direction.y > 0:  # moving down
                        self.rect.bottom = rect.top
                    if self.direction.y < 0:  # moving up
                        self.rect.top = rect.bottom

    def get_screen_location(self):
        half_width = SCREEN_WIDTH / 2
        half_height = SCREEN_HEIGHT / 2
        return [self.rect.centerx - half_width, self.rect.centery - half_height]

    def draw_main_item(self):
        item = self.hotbar[self.current_hotbar_slot]
        if item:
            print(item)
            item.draw_item(self)
            self.hand.hide()
        else:
            self.hand.draw_hand(self)

    def set_item_in_slot(self, slot, item):
        self.inv.items[slot] = item

    def get_item_in_slot(self, slot) -> Item:
        return self.inv.items[slot]

    def remove_item_in_slot(self, slot):
        if self.inv.items[slot]:
            self.inv.items[slot].kill()
            self.inv.items[slot] = None

    def get_direction_vec(self) -> Tuple[float, float]:
        center_x = self.rect.centerx
        center_y = self.rect.centery

        if center_x > SCREEN_WIDTH // 2:
            center_x = SCREEN_WIDTH // 2

        if center_y > SCREEN_HEIGHT // 2:
            center_y = SCREEN_HEIGHT // 2

        mouse_pos = pygame.mouse.get_pos()

        vec_x = (mouse_pos[0] - center_x)
        vec_y = (mouse_pos[1] - center_y)

        return normalize_vec(vec_x, vec_y)

    def update_looking_direction(self):
        vec = self.get_direction_vec()
        if vec[0] >= 0:  # Check if looking x is positive (pointing on the right side of the screen)
            self.looking_direction = "RIGHT"
        else:
            self.looking_direction = "LEFT"

    def update_player_animation(self):
        if self.direction.x == 0 and self.direction.y == 0:
            if self.looking_direction == "RIGHT":
                self.image = self.original_image.copy()

            if self.looking_direction == "LEFT":
                self.image = pygame.transform.flip(self.original_image, True, False)
            return

        if self.looking_direction == "LEFT":
            frame = self.moving_animation.get_next_frame()
            frame = pygame.transform.flip(frame, True, False)
            frame = pygame.transform.scale(frame, (frame.get_width() * PLAYER_SIZE_MULTIPLIER,
                                                   frame.get_height() * PLAYER_SIZE_MULTIPLIER))
            self.image = frame

        if self.looking_direction == "RIGHT":
            frame = self.moving_animation.get_next_frame()
            frame = pygame.transform.scale(frame, (frame.get_width() * PLAYER_SIZE_MULTIPLIER,
                                                   frame.get_height() * PLAYER_SIZE_MULTIPLIER))
            self.image = frame

    def update(self):
        self.input()
        self.move(self.speed)
        self.update_hotbar()
        self.draw_main_item()
        self.update_looking_direction()
        self.update_player_animation()

    def update_hotbar(self):
        self.current_hotbar_slot = self.inv.current_hotbar_slot
        self.hotbar = self.inv.get_hotbar_items()

    def draw_inventory(self, event_list):
        if self.is_inv_open:
            self.inv.draw_inventory(self.display_surface)
            self.inv.update(event_list)

"""Player class..."""
from typing import List

import pygame

from common.consts import SPEED, SCREEN_WIDTH, SCREEN_HEIGHT
from weapons import Weapon
from consts import *


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites):
        super().__init__(*groups)
        self.image = pygame.image.load(PLAYER_IMG).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)

        self.direction = pygame.math.Vector2()
        self.speed = SPEED
        self.max_health = MAX_HEALTH
        self.current_health = self.max_health
        self.obstacle_sprites = obstacle_sprites
        self.attack_cooldown = pygame.time.get_ticks()
        self.attacking = False
        self.is_typing = False

        self.hotbar: List[Weapon | None] = [None] * 6
        self.current_slot = 0

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
            if not self.attacking:
                if self.attack_cooldown < pygame.time.get_ticks():
                    self.attacking = True
                    self.attack_cooldown = pygame.time.get_ticks() + ATTACK_COOLDOWN
        else:
            self.attacking = False

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()
        self.rect.x += self.direction.x * speed
        self.collision('horizontal')
        self.rect.y += self.direction.y * speed
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

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.direction.y > 0:  # moving down
                        self.rect.bottom = sprite.rect.top
                    if self.direction.y < 0:  # moving up
                        self.rect.top = sprite.rect.bottom

    def get_screen_location(self):
        half_width = SCREEN_WIDTH / 2
        half_height = SCREEN_HEIGHT / 2
        return [self.rect.centerx - half_width, self.rect.centery - half_height]

    def draw_main_weapon(self):
        weapon = self.hotbar[self.current_slot]
        if weapon:
            weapon.draw_weapon(self)

    def set_weapon_in_slot(self, slot, weapon: Weapon):
        self.hotbar[slot] = weapon

    def get_weapon_in_slot(self, slot) -> Weapon:
        return self.hotbar[slot]

    def remove_weapon_in_slot(self, slot):
        if self.hotbar[slot]:
            self.hotbar[slot].kill()
            self.hotbar[slot] = None

    def next_slot(self):
        current_weapon = self.hotbar[self.current_slot]
        if current_weapon:
            current_weapon.hide()

        if self.current_slot + 1 < len(self.hotbar):
            self.current_slot += 1
        else:
            self.current_slot = 0

    def previous_slot(self):
        current_weapon = self.hotbar[self.current_slot]
        if current_weapon:
            current_weapon.hide()

        if self.current_slot - 1 > -1:
            self.current_slot -= 1
        else:
            self.current_slot = len(self.hotbar) - 1

    def update(self):
        self.input()
        self.move(self.speed)
        self.draw_main_weapon()

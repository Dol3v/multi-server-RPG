import pygame
from consts import *


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

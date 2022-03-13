import pygame
from settings import *
from tile import Tile
from player import Player


class Level:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.visible_sprites = YSortCameraGroup()
        self.obstacles_sprites = pygame.sprite.Group()

        self.health_background = pygame.image.load("assets/health/health_background.png")
        self.health_background = pygame.transform.scale(self.health_background, (self.health_background.get_width() * 4,
                                                                                 self.health_background.get_height() * 4))

        self.health_bar = pygame.image.load("assets/health/health_bar.png")
        self.health_bar = pygame.transform.scale(self.health_bar, (self.health_bar.get_width() * 4,
                                                                   self.health_bar.get_height() * 4))

        self.create_map()

    def create_map(self):
        for row_index, row in enumerate(WORLD_MAP):
            for col_index, col in enumerate(row):
                x = col_index * TILESIZE
                y = row_index * TILESIZE
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacles_sprites])
                if col == 'p':
                    self.player = Player((x, y), [self.visible_sprites], self.obstacles_sprites)

    def run(self, event_list):
        self.display_surface.fill("black")
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update()
        self.draw_health_bar()

    def draw_health_bar(self):
        self.display_surface.blit(self.health_background, (WIDTH * 0, HEIGHT * 0.895))

        width = (self.player.current_health / self.player.max_health) * self.health_bar.get_width() # Health Percentage
        new_bar = pygame.transform.scale(self.health_bar, (width, self.health_bar.get_height()))
        self.display_surface.blit(new_bar, (WIDTH * 0.06, HEIGHT * 0.94))


class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self):
        # general setup
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        # getting the offset
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        # for sprite in self.sprites():
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)

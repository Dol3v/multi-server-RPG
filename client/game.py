import pygame
import socket
import math
import sys
from typing import Tuple, List

# to import from a dir
sys.path.append('../')

from common.protocol import generate_client_message, parse_server_message

from consts import *
from player import Player
from tile import Tile
from weapon import Weapon

class Game:
    def __init__(self, conn: socket.socket, server_addr: tuple, full_screen):
        # init sprites
        self.display_surface = pygame.display.get_surface()
        self.visible_sprites = FollowingCameraGroup()
        self.obstacles_sprites = pygame.sprite.Group()
        self.attack_sprite = None

        # player init
        self.player = None  
        self.player_img = pygame.image.load(PLAYER_IMG)

        # generate map
        self.create_map()

        self.full_screen = full_screen
        self.running = False
        self.clock = pygame.time.Clock()

        # communication
        self.conn = conn
        self.conn.settimeout(0.5)
        self.server_addr = server_addr

        # Health bar init
        self.health_background = pygame.image.load(HEALTH_BACKGROUND_IMG)
        self.health_background = pygame.transform.scale(self.health_background, (self.health_background.get_width() * 4,
                                                                                 self.health_background.get_height() * 4))
        self.health_bar = pygame.image.load(HEALTH_BAR_IMG)
        self.health_bar = pygame.transform.scale(self.health_bar, (self.health_bar.get_width() * 4,
                                                                   self.health_bar.get_height() * 4))


    def server_update(self):
        """
        Use: communicate with the server over UDP.
        """
        try:
            # sending location and actions
            x = self.player.rect.centerx
            y = self.player.rect.centery

            self.conn.sendto(generate_client_message(x, y), self.server_addr)

            # receive server update
            packet, addr = self.conn.recvfrom(1024)

            if addr == self.server_addr:

                entity_locations = parse_server_message(packet)
                self.render_clients(entity_locations)

        except TimeoutError:
            print("Timeout")

    # ------------------------------------------------------------------
    def render_client(self, x: int, y: int):
        """
        Use: print client by the given x and y (Global locations)
        """
        screen_location = self.player.get_screen_location()
        new_x = x - screen_location[0]  # Returns relative location x to the screen
        new_y = y - screen_location[1]  # Returns relative location y to the screen
        self.display_surface.blit(self.player_img, self.player_img.get_rect(center=(new_x, new_y)))

    def render_clients(self, client_locations: List[Tuple[int, int]]):
        """
        Use: prints the other clients by the given info about them
        """
        for client_pos in client_locations:
            self.render_client(*client_pos)

    # ------------------------------------------------------------------

    def create_map(self):
        for row_index, row in enumerate(WORLD_MAP):
            for col_index, col in enumerate(row):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacles_sprites])
                if col == 'p':
                    self.player = Player((x, y), [self.visible_sprites], self.obstacles_sprites,
                                         self.create_attack, self.destroy_attack)

    def create_attack(self):
        center_x = WIDTH // 2
        center_y = HEIGHT // 2

        mouse_pos = pygame.mouse.get_pos()

        vec_x = (mouse_pos[0] - center_x)
        vec_y = (mouse_pos[1] - center_y)

        vec = self.normalize(vec_x, vec_y)

        self.attack_sprite = Weapon(self.player, [self.visible_sprites], vec)

    def destroy_attack(self):
        if self.attack_sprite:
            self.attack_sprite.kill()
        self.attack_sprite = None

    @staticmethod
    def normalize(x, y) -> Tuple[float, float]:
        factor = math.sqrt(x ** 2 + y ** 2)
        return x / factor, y / factor

    def run(self):
        self.running = True

        while self.running:
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        if self.full_screen:
                            pygame.display.set_mode((WIDTH, HEIGHT))
                        else:
                            pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                        self.full_screen = not self.full_screen
            self.display_surface.fill("black")
            self.visible_sprites.custom_draw(self.player)
            self.visible_sprites.update()
            self.draw_health_bar()
            self.server_update()
            pygame.display.update()
            self.clock.tick(FPS)

    def draw_health_bar(self):
        self.display_surface.blit(self.health_background, (WIDTH * 0, HEIGHT * 0.895))

        width = (self.player.current_health / self.player.max_health) * self.health_bar.get_width()  # Health Percentage
        new_bar = pygame.transform.scale(self.health_bar, (width, self.health_bar.get_height()))
        self.display_surface.blit(new_bar, (WIDTH * 0.06, HEIGHT * 0.94))


class FollowingCameraGroup(pygame.sprite.Group):
    def __init__(self):
        # general setup
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = WIDTH / 2
        self.half_height = HEIGHT / 2
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        # getting the offset
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        # for spr in self.sprites():
        for sprite in sorted(self.sprites(), key=lambda spr: spr.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)

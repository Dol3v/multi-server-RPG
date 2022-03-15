import pygame

from player import Player
from consts import *
from tile import Tile


class Map:
    def __init__(self, game):
        self.player = None  # FIXME: where do u update self.player lol (temp to create new commit, will be removed)
        self.display_surface = pygame.display.get_surface()
        self.visible_sprites = FollowingCameraGroup()
        self.obstacles_sprites = pygame.sprite.Group()
        self.player_img = pygame.image.load(PLAYER_IMG)
        self.create_map()
        self.conn = game.conn
        self.server_addr = game.server_addr

    def server_handler(self):
        """
        Use: communicate with the server over UDP.
        """
        try:
            # sending location and actions
            self.conn.sendto(b"location", self.server_addr)

            # receive server update
            data, addr = self.conn.recvfrom(1024)
            print(f"Data: {data}\nFrom: {addr}")
        except TimeoutError:
            print("Timeout")

    # ------------------------------------------------------------------
    def render_client(self, x: int, y: int):
        """
        Use: print client by the given x and y (Global locations)
        """
        screen_location = self.player.get_screen_location();
        new_x = x - screen_location[0]  # Returns relative location x to the screen
        new_y = y - screen_location[1]  # Returns relative location y to the screen
        self.display_surface.blit(self.player_img, self.player_img.get_rect(center=(new_x, new_y)))

    def render_clients(self, clients_info: list):
        """
        Use: prints the other clients by the given info about them
        """
        for client in clients_info:
            self.render_client(client[0][1])

    # ------------------------------------------------------------------

    def create_map(self):
        for row_index, row in enumerate(WORLD_MAP):
            for col_index, col in enumerate(row):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacles_sprites])
                if col == 'p':
                    self.player = Player((x, y), [self.visible_sprites], self.obstacles_sprites)

    def run(self,event_list):
        self.display_surface.fill("black")
        self.visible_sprites.custom_draw(self.player)
        self.visible_sprites.update()
        self.render_client(150, 150)
        self.server_handler()


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
        print(f"X: {player.rect.centerx}\nY: {player.rect.centery}")

        # for spr in self.sprites():
        for sprite in sorted(self.sprites(), key=lambda spr: spr.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)

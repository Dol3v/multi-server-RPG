"""Game loop and communication with the server"""
import queue
import socket
import sys
import threading
import pygame
from typing import Tuple, List

# to import from a dir
sys.path.append('../')

from common.consts import RECV_CHUNK, SCREEN_WIDTH, SCREEN_HEIGHT
from consts import *
from networking import generate_client_message, parse_server_message
from player import Player
from sprites import Entity, Tile, FollowingCameraGroup




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
        self.server_addr = server_addr

        # Health bar init
        self.health_background = pygame.image.load(HEALTH_BACKGROUND_IMG)
        self.health_background = pygame.transform.scale(self.health_background, (self.health_background.get_width() * 4,
                                                                                 self.health_background.get_height() * 4))
        self.health_bar = pygame.image.load(HEALTH_BAR_IMG)
        self.health_bar = pygame.transform.scale(self.health_bar, (self.health_bar.get_width() * 4,
                                                                   self.health_bar.get_height() * 4))

        self.hot_bar = pygame.image.load("assets/hot_bar.png")
        self.hot_bar = pygame.transform.scale(self.hot_bar,
                                              (self.hot_bar.get_width() * 2, self.hot_bar.get_height() * 2))

        self.entities = {}
        self.recv_queue = queue.Queue()
        self.seqn = 0
        # [msg, attack, attack_dir, equipped_id]
        self.actions = [b'', False, 0.0, 0] 

    def receiver(self):
        while True:
            self.recv_queue.put(self.conn.recvfrom(RECV_CHUNK))

    def server_update(self):
        """
        Use: communicate with the server over UDP.
        """
        # sending location and actions
        self.update_player_actions("Sup everyone", 1)
        self.conn.sendto(generate_client_message(self.seqn, self.player.rect.centerx, self.player.rect.centery, self.actions), self.server_addr)
        self.seqn += 1

        # receive server update
        try:
            packet, addr = self.recv_queue.get(block=False)
        except queue.Empty:
            return

        if addr == self.server_addr:
            data, entity_locations = parse_server_message(packet)
            self.render_clients(entity_locations)
            self.update_player_status(data)

    def update_player_status(self, data: list) -> None:
        """
        Use: update player status by the server message
        """
        # self.player.hotbar
        tools = data[:3]

        # update client position only when the server says so
        if (data[3] != -1 and data[4] != -1):
            self.player.rect.centerx = data[3]
            self.player.rect.centery = data[4]

        self.player.current_health = data[-1]

    def update_player_actions(self, chat: str, equipped_id: int) -> None:
        """
        Use: update player actions to send
        """
        self.actions[CHAT] = chat.encode()
        print(self.actions[CHAT])
        self.actions[ATTACK] = self.player.attacking
        # BUG: This may cause some problems
        # TODO: change to ff in the format
        self.actions[ATTACK_DIR] = 0.0#self.player.direction.rotate()

        self.actions[EQUIPPED_ID] = equipped_id


    def render_clients(self, client_locations: List[Tuple[int, int]]) -> None:
        """
        Use: prints the other clients by the given info about them

        #TODO: Remove entities that died (or left if player)
                (For server, add "died" flag)
                [(1, 3, sword), (2, 4, axe), (4, 3, bow)]
                [(1, 3, sword), (2, 4, axe, died) (4, 3, bow)]
        """

        for entity_id, pos in enumerate(client_locations):
            if entity_id in self.entities:
                self.entities.get(entity_id).move_to(*pos)
            else:
                self.entities[entity_id] = Entity([self.obstacles_sprites, self.visible_sprites], *pos)


    def create_map(self) -> None:
        """
        Use:
        """
        for row_index, row in enumerate(WORLD_MAP):
            for col_index, col in enumerate(row):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacles_sprites])
                if col == 'p':
                    self.player = Player((x, y), [self.visible_sprites], self.obstacles_sprites)

    def run(self) -> None:
        """
        Use: game loop
        """
        self.running = True
        # starts the receiving thread 
        recv_thread = threading.Thread(target=self.receiver)
        recv_thread.start()

        # Game loop
        while self.running:
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        if self.full_screen:
                            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                        else:
                            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                        self.full_screen = not self.full_screen

            # sprite update
            self.display_surface.fill("black")
            self.visible_sprites.custom_draw(self.player)
            self.visible_sprites.update()
            self.draw_health_bar()
            self.draw_hot_bar()
            self.server_update()
            pygame.display.update()
            self.clock.tick(FPS)


    def draw_health_bar(self):
        """
        Use: draw health bar by self.player.current_health
        """
        self.display_surface.blit(self.health_background, (SCREEN_WIDTH * 0, SCREEN_HEIGHT * 0.895))

        width = (self.player.current_health / self.player.max_health) * self.health_bar.get_width()  # Health Percentage
        new_bar = pygame.transform.scale(self.health_bar, (width, self.health_bar.get_height()))
        self.display_surface.blit(new_bar, (SCREEN_WIDTH * 0.06, SCREEN_HEIGHT * 0.94))

    def draw_hot_bar(self):
        """
        Use: draw the tool's menu by the tools received from the server
        """
        width = (WIDTH - self.hot_bar.get_width()) / 2
        self.display_surface.blit(self.hot_bar,(width,HEIGHT * 0.9))



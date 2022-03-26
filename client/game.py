"""Game loop and communication with the server"""
import queue
import random
import socket
import sys
import threading
import pygame
from typing import Tuple, List

# to import from a dir
sys.path.append('../')

from graphics import ChatBox
from common.consts import RECV_CHUNK, SCREEN_WIDTH, SCREEN_HEIGHT, VALID_POS, Pos, MIN_HEALTH
from consts import *
from networking import generate_client_message, parse_server_message
from player import Player
from sprites import Entity, FollowingCameraGroup, Tile


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
        # [msg, dir_bit, attack, attack_dir, equipped_id]
        self.actions = [b'', 0, False, 0.0, 0.0, 0] 
        self.chat_msg = ""

        self.is_showing_chat = False
        self.chat = ChatBox(0, 0, 300, 150, pygame.font.SysFont("arial", 15))

    def receiver(self):
        while True:
            self.recv_queue.put(self.conn.recvfrom(RECV_CHUNK))

    def server_update(self):
        """
        Use: communicate with the server over UDP.
        """
        # update server
        self.update_player_actions()
        update_packet = generate_client_message(self.seqn, self.player.rect.centerx, self.player.rect.centery, self.actions)
        self.conn.sendto(update_packet, self.server_addr)
        self.seqn += 1

        # receive server update
        try:
            packet, addr = self.recv_queue.get(block=False)
        except queue.Empty:
            return

        if addr == self.server_addr:
            (*tools, x, y, health), entities = parse_server_message(packet)
            # update graphics and status
            self.render_clients(entities)
            self.update_player_status(tools, (x, y), health)

    def update_player_status(self, tools: list, valid_pos: Pos, health: int) -> None:
        """
        Use: update player status by the server message
        """
        # self.player.hotbar

        # update client position only when the server says so
        if (valid_pos != VALID_POS):
            self.player.rect.centerx = valid_pos[0]
            self.player.rect.centery = valid_pos[1]

        if health >= MIN_HEALTH:
            self.player.current_health = health

    def update_player_actions(self) -> None:
        """
        Use: update player actions to send
        """
        self.actions[CHAT] = self.chat_msg.encode()
        self.actions[ATTACK] = self.player.attacking
        # BUG: This may cause some problems
        # TODO: change to ff in the format
        self.actions[ATTACK_DIR] = 0.0  # self.player.direction.rotate()

        self.actions[EQUIPPED_ID] = 1  # equipped_id

    def render_clients(self, entities: List[Tuple[int, int]]) -> None:
        """
        Use: prints the other clients by the given info about them

        #TODO: Remove entities that died (or left if player)
                (For server, add "died" flag)
                [(1, 3, sword), (2, 4, axe), (4, 3, bow)]
                [(1, 3, sword), (2, 4, axe, died) (4, 3, bow)]
        """

        for entity_id,  entity_info in enumerate(entities):

            entity_type, pos, entity_dir = entity_info

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

                if event.type == pygame.MOUSEBUTTONDOWN and self.is_showing_chat:
                    self.player.is_typing = self.chat.has_collision(*pygame.mouse.get_pos())

                if event.type == pygame.KEYDOWN:
                    if self.player.is_typing:
                        if event.key == pygame.K_TAB:  # Check if closes the chat
                            self.player.is_typing = not self.player.is_typing
                            self.is_showing_chat = not self.is_showing_chat

                        elif event.key == pygame.K_RETURN:  # Check if enter is clicked and sends the message
                            self.chat.add_message(self.chat_msg)
                            self.chat_msg = ""
                            self.player.is_typing = not self.player.is_typing

                        elif event.key == pygame.K_BACKSPACE:
                            if len(self.chat_msg) > 0:
                                self.chat_msg = self.chat_msg[:-1]

                        else:  # Check if typing a key
                            self.chat_msg += event.unicode
                    else:
                        if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            if self.full_screen:
                                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                            else:
                                pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                            self.full_screen = not self.full_screen
                        if event.key == pygame.K_TAB:
                            self.is_showing_chat = not self.is_showing_chat

            # sprite update
            self.display_surface.fill("black")
            self.visible_sprites.custom_draw(self.player)
            self.visible_sprites.update()
            self.draw_health_bar()
            self.draw_hot_bar()
            self.draw_chat(event_list)
            self.server_update()
            pygame.display.update()
            self.clock.tick(FPS)

    def draw_chat(self, event_list):
        if self.is_showing_chat:
            self.chat.render_chat(self.display_surface, self.chat_msg)
            self.chat.update(event_list)

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
        width = (SCREEN_WIDTH - self.hot_bar.get_width()) / 2
        self.display_surface.blit(self.hot_bar, (width, SCREEN_HEIGHT * 0.9))

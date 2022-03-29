"""Game loop and communication with the server"""
import queue
import socket
import sys
import threading
import weapons
from typing import Tuple, List

# to import from a dir
sys.path.append('../')

from graphics import ChatBox
from common.consts import *
from consts import *
from networking import generate_client_message, parse_server_message
from player import Player
from sprites import Entity, FollowingCameraGroup, Tile
from weapons import *


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

        self.inv = pygame.image.load("assets/inventory.png")
        self.inv = pygame.transform.scale(self.inv, (self.inv.get_width() * 2.5, self.inv.get_height() * 2.5))
        self.inv.set_alpha(150)

        self.entities = {}
        self.recv_queue = queue.Queue()
        self.seqn = 0

        self.actions = [b'', 0, False, 0.0, 0.0, 0]
        """[message, direction, did attack, attack directions, selected slot]"""

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
        update_packet = generate_client_message(self.seqn, self.player.rect.centerx, self.player.rect.centery,
                                                self.actions)
        self.conn.sendto(update_packet, self.server_addr)
        self.seqn += 1

        # receive server update
        try:
            packet, addr = self.recv_queue.get(block=False)
        except queue.Empty:
            return

        if addr == self.server_addr:
            (*tools, chat_msg, x, y, health), entities = parse_server_message(packet)
            print(x, y, health)
            for i, tool_id in enumerate(tools):  # I know its ugly code but I don't care enough to change it lmao
                weapon_type = weapons.get_weapon_type(tool_id)

                if weapon_type:
                    player_weapon = self.player.get_weapon_in_slot(i)

                    if player_weapon:
                        if player_weapon.weapon_type != weapon_type or player_weapon.rarity != "rare":

                            weapon = Weapon([self.visible_sprites], weapon_type, "rare")
                            if weapon.is_ranged:
                                weapon.kill()
                                weapon = RangeWeapon([self.visible_sprites], self.obstacles_sprites,
                                                     weapon_type, "rare")

                            self.player.remove_weapon_in_slot(i)
                            self.player.set_weapon_in_slot(i, weapon)
                    else:
                        weapon = Weapon([self.visible_sprites], weapon_type, "rare")
                        if weapon.is_ranged:
                            weapon.kill()
                            weapon = RangeWeapon([self.visible_sprites], self.obstacles_sprites,
                                                 weapon_type, "rare")

                        self.player.set_weapon_in_slot(i, weapon)
                else:
                    self.player.set_weapon_in_slot(i, None)

            # update graphics and status
            self.render_clients(entities)
            self.update_player_status(tools, (x, y), health)

    def update_player_status(self, tools: list, valid_pos: Pos, health: int) -> None:
        """
        Use: update player status by the server message
        """
        # update client position only when the server says so
        if valid_pos != DEFAULT_POS_MARK:
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
        self.actions[ATTACK_DIR_X], self.actions[ATTACK_DIR_Y] = self.player.get_direction_vec()
        self.actions[SELECTED_SLOT] = self.player.current_slot

    def render_clients(self, entities: List[Tuple[int, tuple, tuple]]) -> None:
        """
        Use: prints the other clients by the given info about them

        #TODO: Remove players that died (or left if player)
                (For server, add "died" flag)
                [(1, 3, sword), (2, 4, axe), (4, 3, bow)]
                [(1, 3, sword), (2, 4, axe, died) (4, 3, bow)]
        """
        for index, entity_info in enumerate(entities):
            entity_type, pos, entity_dir = entity_info
            if entity_type != PLAYER_TYPE:
                continue
            if index in self.entities:
                self.entities.get(index).move_to(*pos)
            else:
                self.entities[index] = Entity([self.obstacles_sprites, self.visible_sprites], *pos)

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
                if event.type == pygame.MOUSEWHEEL:
                    if event.y > 0:
                        self.player.previous_slot()
                    elif event.y < 0:
                        self.player.next_slot()

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
                        if event.key == pygame.K_e:
                            self.player.is_inv_open = not self.player.is_inv_open

            # sprite update
            self.display_surface.fill("black")
            self.visible_sprites.custom_draw(self.player)
            self.visible_sprites.update()
            self.draw_health_bar()
            self.draw_hot_bar()
            self.draw_chat(event_list)
            self.draw_inventory()
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
        hot_bar = self.hot_bar.copy()

        for i, weapon in enumerate(self.player.hotbar):

            surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            if i == self.player.current_slot:
                surface.fill((0, 0, 0, 100))

            if weapon:

                if weapon.is_ranged:
                    surface.blit(pygame.transform.rotate(weapon.icon, -90), (0, 0))
                else:
                    surface.blit(weapon.icon, (0, 0))
            hot_bar.blit(surface, (16 + 36 * i, 18))
            # (16 + 36 * i, 18)

        self.display_surface.blit(hot_bar, (width, SCREEN_HEIGHT * 0.9))

    def draw_inventory(self):
        if self.player.is_inv_open:
            x = SCREEN_WIDTH - self.inv.get_width()
            y = 0
            self.display_surface.blit(self.inv, (x, y))

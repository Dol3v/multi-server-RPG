"""Game loop and communication with the server"""
import base64
import queue
import sys
import threading
from typing import List

import weapons

# to import from a dir
sys.path.append('../')

from graphics import ChatBox
from common.consts import *
from networking import *
from sprites import PlayerEntity, FollowingCameraGroup, Entity
from weapons import *
from map_manager import *


class Game:
    def __init__(self, conn: socket.socket, server_addr: tuple, player_uuid: str, shared_key: bytes, full_screen,
                 initial_pos: tuple):
        # misc networking
        self.entities = {}
        self.recv_queue = queue.Queue()
        self.seqn = 0
        self.fernet = Fernet(base64.urlsafe_b64encode(shared_key))

        # init sprites
        self.can_recv: bool = False
        self.display_surface = pygame.display.get_surface()
        self.visible_sprites = FollowingCameraGroup()
        self.obstacles_sprites = pygame.sprite.Group()
        self.attack_sprite = None

        self.map = Map()
        self.map.add_layer(Layer("assets/map/animapa_test.csv", TilesetData("assets/map/new_props.png",
                                                                            "assets/map/new_props.tsj")))
        self.map_collision = Index((0, 0, self.visible_sprites.floor_surface.get_width(),
                                    self.visible_sprites.floor_surface.get_height()))
        self.map.load_collision_objects_to(self.map_collision)

        # player init
        self.player = Player(initial_pos, (self.visible_sprites,), self.obstacles_sprites, self.map_collision)
        self.player_img = pygame.image.load(PLAYER_IMG)
        self.player_uuid = player_uuid

        self.map = Map()
        self.map.add_layer(Layer("assets/map/animapa_test.csv", TilesetData("assets/map/new_props.png",
                                                                            "assets/map/new_props.tsj")))
        self.map.load_collision_objects_to(self.map_collision)

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

        # inventory init
        self.inv = pygame.image.load("assets/inventory.png")
        self.inv = pygame.transform.scale(self.inv, (self.inv.get_width() * 2.5, self.inv.get_height() * 2.5))
        self.inv.set_alpha(150)

        self.chat_msg = ""
        self.msg_to_send = ""

        self.is_showing_chat = True
        self.chat = ChatBox(0, 0, 300, 150, pygame.font.SysFont("arial", 15))

    @property
    def x(self):
        return self.player.rect.centerx

    @property
    def y(self):
        return self.player.rect.centery

    def receiver(self):
        while not self.can_recv:
            ...
        while True:
            self.recv_queue.put(self.conn.recvfrom(UDP_RECV_CHUNK))

    def server_update(self):
        """communicate with the server over UDP."""
        if self.msg_to_send:
            self.chat_msg = self.msg_to_send
            self.msg_to_send = ""
        update_packet = generate_client_routine_message(self.player_uuid, self.seqn, self.x, self.y,
                                                        self.player, self.chat_msg, self.fernet)
        self.conn.sendto(update_packet, self.server_addr)
        self.seqn += 1

        # receive server update
        try:
            packet, addr = self.recv_queue.get(block=False)
        except queue.Empty:
            return

        if addr != self.server_addr:
            return
        contents = parse_message(packet, self.fernet)
        pos, tools, health, entities = tuple(contents["valid_pos"]), contents["tools"], contents["health"], \
                                       contents["entities"]

        print(f"{pos=} {health=} {tools=}")
        for i, tool_id in enumerate(tools):  # I know its ugly code but I don't care enough to change it lmao
            weapon_type = weapons.get_weapon_type(tool_id)

            if weapon_type:
                player_weapon = self.player.get_weapon_in_slot(i)

                if player_weapon:
                    if player_weapon.weapon_type != weapon_type or player_weapon.rarity != "rare":

                        weapon = Weapon((self.visible_sprites,), weapon_type, "rare")
                        if weapon.is_ranged:
                            weapon.kill()
                            weapon = RangeWeapon([self.visible_sprites], self.obstacles_sprites, self.map_collision,
                                                 weapon_type, "rare")

                        self.player.remove_weapon_in_slot(i)
                        self.player.set_weapon_in_slot(i, weapon)
                else:
                    weapon = Weapon((self.visible_sprites,), weapon_type, "rare")
                    if weapon.is_ranged:
                        weapon.kill()
                        weapon = RangeWeapon((self.visible_sprites,), self.obstacles_sprites, self.map_collision,
                                             weapon_type, "rare")

                    self.player.set_weapon_in_slot(i, weapon)
            else:
                self.player.set_weapon_in_slot(i, None)

        # update graphics and status

        self.render_entities(entities)
        self.update_player_status(pos, health)

    def update_player_status(self, valid_pos: Pos, health: int) -> None:
        """update player status by the server message"""

        # update client position only when the server says so
        if valid_pos != DEFAULT_POS_MARK:
            self.player.rect.centerx = valid_pos[0]
            self.player.rect.centery = valid_pos[1]

        if health >= MIN_HEALTH:
            self.player.current_health = health
        else:
            print("ded")
            self.running = False
            # TODO: start here login screen
            pygame.quit()
            sys.exit(0)

    def render_entities(self, entities: List[dict]) -> None:
        """
        Use: prints the other clients by the given info about them
        """
        print("-" * 10)
        for entity in entities:
            entity_type, entity_uuid, pos, entity_dir = entity["type"], entity["uuid"], entity["pos"], entity["dir"]
            print(f"received entity {entity_uuid=} {entity_type=} {pos=} {entity_dir=}")
            if entity_uuid in self.entities.keys():
                print("entity in keys, updating")
                self.entities[entity_uuid].direction = entity_dir
                self.entities[entity_uuid].move_to(*pos)

                if entity_type == EntityType.PLAYER and self.entities[entity_uuid].tool_id != entity["tool"]:
                    self.entities[entity_uuid].update_tool(entity["tool"])
            else:
                if entity_type == EntityType.PLAYER:
                    print("creating player")
                    self.entities[entity_uuid] = PlayerEntity((self.obstacles_sprites, self.visible_sprites), *pos,
                                                              entity_dir, entity["tool"], self.map_collision)
                else:
                    print(f"creating entity of type={entity_type}")
                    self.entities[entity_uuid] = Entity((self.obstacles_sprites, self.visible_sprites), entity_type,
                                                        *pos, entity_dir)

        remove_entities = []
        received_uuids = list(map(lambda info: info["uuid"], entities))
        print(f"{received_uuids=}")
        print(f"keys={self.entities.keys()}")
        for entity_uuid in self.entities.keys():
            if entity_uuid not in received_uuids:
                print(f"killing uuid={entity_uuid}")
                self.entities[entity_uuid].kill()
                remove_entities.append(entity_uuid)

        for entity_uuid in remove_entities:
            self.entities.pop(entity_uuid)

    def run(self):
        """
        Use: game loop
        """
        self.running = True
        # starts the receiving thread
        recv_thread = threading.Thread(target=self.receiver)
        recv_thread.start()
        self.draw_map()

        # Game loop
        while self.running:
            event_list = pygame.event.get()
            self.draw_chat(event_list)
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
                            self.msg_to_send = self.chat_msg
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
            self.server_update()
            self.can_recv = True
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

    def draw_map(self):
        for layer in self.map.layers:
            layer.draw_layer(self.visible_sprites)

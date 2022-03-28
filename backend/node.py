import functools
import logging
import sys
import threading
import time
from collections import defaultdict

from pyqtree import Index

# to import from a dir
sys.path.append('../')

from common.consts import *
from common.utils import *
from collision import *
from networking import generate_server_message, parse_client_message
from consts import WEAPON_DATA, ARM_LENGTH_MULTIPLIER


class Node:

    def __init__(self, port) -> None:
        self.node_ip = SERVER_IP  # socket.gethostbyname(socket.gethostname())
        self.address = (self.node_ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.players = defaultdict(lambda: Player())

        self.spindex = Index(bbox=(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
        """Quadtree for collision/range detection. Player keys are tuples `(type, data)`, with the type being
        projectile/player/mob, and data being other stuff that are relevant. Contains address of client for player
        players."""

        # Starts the node
        self.run()

    @functools.cached_property
    def addrs(self) -> Iterable[Addr]:
        return self.players.keys()

    def in_range(self, pos: Pos, width: int, height: int) -> list:
        """Returns all stuff in range of the bounding box."""
        return self.spindex.intersect(get_bounding_box(pos, height, width))

    def entities_in_range(self, entity_addr, bbox: Tuple[int, int, int, int]):
        """Returns all players in a given bounding box that are not the player itself."""
        return map(lambda addr: self.players[addr], filter(lambda addr: addr != entity_addr,
                                                           self.spindex.intersect(bbox)))

    def entities_in_rendering_range(self, entity: Player, entity_addr: Addr) -> Iterable[Player]:
        """Returns all players that are within render distance of each other.
        """
        return self.entities_in_range(entity_addr, get_bounding_box(entity.pos, SCREEN_HEIGHT, SCREEN_WIDTH))

    def entities_in_melee_attack_range(self, entity: Player, entity_addr: Addr, melee_range: int):
        """Returns all enemy players that are in the attack range (i.e. in the general direction of the player
        and close enough)."""
        weapon_x, weapon_y = int(entity.pos[0] + ARM_LENGTH_MULTIPLIER * entity.direction[0]),\
                             int(entity.pos[1] + ARM_LENGTH_MULTIPLIER * entity.direction[1])
        logging.debug(f"pos={entity.pos}, dir={entity.direction}, weapon={weapon_x, weapon_y}")
        return self.entities_in_range(entity_addr, (weapon_x - melee_range // 2, weapon_y - melee_range // 2,
                                                    weapon_x + melee_range // 2, weapon_y + melee_range // 2))

    def update_location(self, player_pos: Pos, seqn: int, entity: Player, addr: Addr) -> Pos:
        """Updates the player location in the server and returns location data to be sent to the client.
        Additionally, adds the client to ``self.players`` if it wasn't there already.

        :param entity: player to update
        :param player_pos: position of player given by the client
        :param seqn: sequence number given by the client
        :param addr: address of client
        :returns:``DEFAULT_POS_MARK`` if the client position is fine, or the server-side-calculated pos for the client
        otherwise.
        """
        # if the received packet is dated then update player
        secure_pos = DEFAULT_POS_MARK
        if invalid_movement(entity, player_pos, seqn) or seqn != entity.last_updated + 1:
            secure_pos = self.players[addr].pos
        else:
            # update player location in quadtree
            self.spindex.remove(addr, get_bounding_box(entity.pos, CLIENT_HEIGHT, CLIENT_WIDTH))
            # if packet is not outdated, update player stats
            entity.pos = player_pos
            entity.last_updated = seqn

            self.spindex.insert(addr, get_bounding_box(entity.pos, CLIENT_HEIGHT, CLIENT_WIDTH))
        return secure_pos

    def update_hp(self, player: Player, inventory_slot: int, addr: Addr):
        """Updates hp of players in case of attack.

        :param player: player entity with updated position
        :param inventory_slot: slot index of player
        :param addr: address of client"""

        # check for cooldown and update it accordingly
        if player.current_cooldown != -1:
            if player.current_cooldown + player.last_time_attacked > (new := time.time()):
                logging.debug(f"COOLDOWN {player.current_cooldown} prevented attack by {addr=}")
                return
            logging.debug(f"COOLDOWN {player.current_cooldown} passed, {new=}, old={player.last_time_attacked}")
            player.current_cooldown = -1
        try:
            tool = player.tools[inventory_slot]
            weapon_data = WEAPON_DATA[tool]
        except KeyError:
            logging.info(f"Invalid slot index/tool given by {addr=}")
            return
        if weapon_data['is_melee']:
            players_in_range = self.entities_in_melee_attack_range(player, addr, weapon_data['melee_attack_range'])
            # resetting cooldown
            player.current_cooldown = weapon_data['cooldown']
            player.last_time_attacked = time.time()

            for player in players_in_range:
                player.health -= weapon_data['damage']
                if player.health < 0:
                    player.health = 0
                logging.info(f"Updated player health to {player.health}")
        else:
            ...

    def update_client(self, addr: Addr, secure_pos: Pos) -> None:
        """
        Use: sends server message to the client
        """
        new_chat = ""
        entity = self.players[addr]

        entities_array = flatten(
            map(lambda e: (e.entity_type, *e.pos, *e.direction), self.entities_in_rendering_range(entity, addr)))
        # generate and send message
        update_packet = generate_server_message(entity.tools, new_chat, secure_pos, entity.health, entities_array)
        self.server_sock.sendto(update_packet, addr)

    def handle_client(self):
        """
        Use: communicate with client
        """
        while True:
            try:
                data, addr = self.server_sock.recvfrom(RECV_CHUNK)
                client_msg = parse_client_message(data)
                if not client_msg:
                    continue

                seqn, x, y, chat, _, attacked, *attack_dir, slot_index = parse_client_message(data)
                player_pos = x, y
                if addr not in self.addrs:
                    self.spindex.insert(addr, get_bounding_box(player_pos, CLIENT_HEIGHT, CLIENT_WIDTH))
                    self.players[addr].pos = player_pos

                entity = self.players[addr]
                if seqn <= entity.last_updated:
                    logging.info(f"Got outdated packet from {addr=}")
                    continue

                entity.direction = attack_dir   # TODO: check if normalized
                secure_pos = self.update_location(player_pos, seqn, entity, addr)
                if attacked:
                    logging.info(f"Player {addr} tried to attack")
                    self.update_hp(entity, slot_index, addr)
                self.update_client(addr, secure_pos)
            except Exception as e:
                logging.exception(e)

    def run(self) -> None:
        """
        Use: starts node threads
        """

        self.server_sock.bind(self.address)
        logging.info(f"Binded to address {self.address}")

        try:
            for i in range(THREADS_COUNT):
                # starts handlers threads
                client_thread = threading.Thread(target=self.handle_client)
                client_thread.start()

        except Exception as e:
            logging.exception(f"{e}")


def invalid_movement(entity: Player, player_pos: Pos, seqn: int) -> bool:
    """
    Use: check if a given player movement is valid
    """
    return entity.last_updated != -1 and not moved_reasonable_distance(
        player_pos, entity.pos, seqn - entity.last_updated)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.INFO)
    Node(SERVER_PORT)

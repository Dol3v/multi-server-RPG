import functools
import itertools
import logging
import sched
import sys
import threading
from collections import defaultdict
from typing import Any

from pyqtree import Index

# to import from a dir

sys.path.append('../')

from common.consts import *
from common.utils import *
from collision import *
from consts import WEAPON_DATA, ARM_LENGTH_MULTIPLIER, FRAME_TIME, MAX_SLOT
from entities import *
from networking import generate_server_message, parse_client_message

EntityData = Tuple[int, str, int, int, float, float, int]
"""type, uuid, x, y, direction in x, direction in y"""


class Node:

    def __init__(self, port) -> None:
        self.node_ip = socket.gethostbyname(socket.gethostname())
        self.address = (self.node_ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.players = defaultdict(lambda: Player())
        self.bots: defaultdict[str, Bot] = defaultdict(lambda: Bot())
        self.projectiles: defaultdict[str, Projectile] = defaultdict(lambda: Projectile())

        self.spindex = Index(bbox=(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
        """Quadtree for collision/range detection. Player keys are tuples `(type, uuid)`, with the type being
        projectile/player/mob, and the uuid being, well, the uuid."""

        # Starts the node
        self.run()

    @functools.cached_property
    def addrs(self) -> Iterable[Addr]:
        return self.players.keys()

    @property
    def entities(self) -> defaultdict[str, Entity]:
        return self.players | self.bots | self.players

    def get_data_from_entity(self, entity_data: Tuple[int, Any]) -> EntityData:
        """Retrieves data about an entity from its quadtree identifier: kind & other data (id/address).

        :returns: flattened tuple of kind, position and direction"""
        tool_id = EMPTY_SLOT
        if entity_data[0] == PLAYER_TYPE:
            chosen_iterable = self.players
        elif entity_data[0] == PROJECTILE_TYPE:
            chosen_iterable = self.projectiles
        elif entity_data[0] == BOT_TYPE:
            chosen_iterable = self.bots
        else:
            raise ValueError(f"Invalid entity type {entity_data[0]} given, with identifier {entity_data[1]}")
        entity = chosen_iterable[entity_data[1]]
        if entity_data[0] == PLAYER_TYPE:
            tool_id = entity.tools[entity.slot]
        elif entity_data[0] == BOT_TYPE:
            tool_id = entity.weapon
        return entity_data[0], entity.uuid.encode(), *entity.pos, *entity.direction, tool_id

    def attackable_in_range(self, entity_addr: Addr, bbox: Tuple[int, int, int, int]) -> Iterable[Attackable]:
        return map(lambda data: self.bots[data[1]] if data[0] == BOT_TYPE else self.players[data[1]],
                   filter(lambda data: data[1] != entity_addr and data[0] != PROJECTILE_TYPE,
                          self.spindex.intersect(bbox)))

    def entities_in_rendering_range(self, entity: Player, player_addr: Addr) -> Iterable[EntityData]:
        """Returns all players that are within render distance of each other."""
        return map(self.get_data_from_entity, filter(lambda data: data[1] != player_addr,
                                                     self.spindex.intersect(
                                                         get_bounding_box(entity.pos, SCREEN_HEIGHT, SCREEN_WIDTH))))

    def entities_in_melee_attack_range(self, entity: Player, entity_addr: Addr, melee_range: int):
        """Returns all enemy players that are in the attack range (i.e. in the general direction of the player
        and close enough)."""
        weapon_x, weapon_y = int(entity.pos[0] + ARM_LENGTH_MULTIPLIER * entity.direction[0]), \
                             int(entity.pos[1] + ARM_LENGTH_MULTIPLIER * entity.direction[1])
        return self.attackable_in_range(entity_addr, (weapon_x - melee_range // 2, weapon_y - melee_range // 2,
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
            self.spindex.remove((PLAYER_TYPE, addr), get_bounding_box(entity.pos, CLIENT_HEIGHT, CLIENT_WIDTH))
            # if packet is not outdated, update player stats
            entity.pos = player_pos
            entity.last_updated = seqn

            self.spindex.insert((PLAYER_TYPE, addr), get_bounding_box(entity.pos, CLIENT_HEIGHT, CLIENT_WIDTH))
        return secure_pos

    def update_hp(self, player: Player, inventory_slot: int, addr: Addr):
        """Updates hp of players in case of attack.

        :param player: player entity with updated position
        :param inventory_slot: slot index of player
        :param addr: address of client"""
        logging.debug(f"Player {addr} tried to attack")
        # check for cooldown and update it accordingly
        if player.current_cooldown != -1:
            if player.current_cooldown + player.last_time_attacked > (new := time.time()):
                logging.debug(f"COOLDOWN {player.current_cooldown} prevented attack by {addr=}")
                return
            logging.info(f"COOLDOWN {player.current_cooldown} passed, {new=}, old={player.last_time_attacked}")
            player.current_cooldown = -1
        try:
            tool = player.tools[inventory_slot]
            weapon_data = WEAPON_DATA[tool]
        except KeyError:
            logging.info(f"Invalid slot index/tool given by {addr=}")
            return
        player.current_cooldown = weapon_data['cooldown'] * FRAME_TIME
        if weapon_data['is_melee']:
            attackable_in_range = self.entities_in_melee_attack_range(player, addr, weapon_data['melee_attack_range'])
            # resetting cooldown
            player.last_time_attacked = time.time()

            for attackable in attackable_in_range:
                attackable.health -= weapon_data['damage']
                if attackable.health < 0:
                    attackable.health = 0
                logging.debug(f"Updated entity health to {attackable.health}")
        else:
            player.current_cooldown = weapon_data['cooldown'] * FRAME_TIME
            player.last_time_attacked = time.time()
            # adding into saved data
            projectile = Projectile(pos=(int(player.pos[0] + ARROW_OFFSET_FACTOR * player.direction[0]),
                                         int(player.pos[1] + ARROW_OFFSET_FACTOR * player.direction[1])),
                                    direction=player.direction, damage=weapon_data['damage'])
            self.projectiles[projectile.uuid] = projectile
            self.spindex.insert((PROJECTILE_TYPE, projectile.uuid),
                                get_bounding_box(projectile.pos, PROJECTILE_HEIGHT, PROJECTILE_WIDTH))
            logging.info(f"Added projectile {projectile}")

    def update_client(self, addr: Addr, secure_pos: Pos):
        """
        Use: sends server message to the client
        """
        new_chat = ""
        player = self.players[addr]
        entities_array = flatten(self.entities_in_rendering_range(player, addr))
        # generate and send message
        update_packet = generate_server_message(player.tools, new_chat, secure_pos, player.health, entities_array)
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
                if slot_index > MAX_SLOT or slot_index < 0:
                    continue

                if addr not in self.addrs:
                    self.spindex.insert((PLAYER_TYPE, addr), get_bounding_box(player_pos, CLIENT_HEIGHT, CLIENT_WIDTH))
                    self.players[addr].pos = player_pos

                entity = self.players[addr]
                if seqn <= entity.last_updated:
                    logging.info(f"Got outdated packet from {addr=}")
                    continue

                entity.direction = attack_dir  # TODO: check if normalized
                secure_pos = self.update_location(player_pos, seqn, entity, addr)

                entity.slot = slot_index
                if attacked:
                    self.update_hp(entity, slot_index, addr)
                self.update_client(addr, secure_pos)
            except Exception as e:
                logging.exception(e)

    def server_controlled_entities_update(self, s, projectiles, bots: List[Bot]):
        """
        Use: update all projectiles and bots positions inside a loop
        """
        # projectile handling
        to_remove = []
        for projectile in projectiles.values():
            collided = False
            intersection = self.spindex.intersect(get_bounding_box(projectile.pos, PROJECTILE_HEIGHT, PROJECTILE_WIDTH))
            if intersection:
                for kind, identifier in intersection:
                    if kind == PLAYER_TYPE:
                        player = self.players[identifier]
                        logging.info(f"Projectile {projectile} hit a player {player}")
                        player.health -= projectile.damage
                        if player.health < MIN_HEALTH:
                            player.health = MIN_HEALTH
                        logging.debug(f"Updated player {identifier} health to {player.health}")
                        to_remove.append(projectile)
                        collided = True
                        # TODO: add wall collision
            if not collided:
                self.spindex.remove((PROJECTILE_TYPE, projectile.uuid), get_bounding_box(projectile.pos,
                                                                                         PROJECTILE_HEIGHT,
                                                                                         PROJECTILE_WIDTH))
                self.projectiles[projectile.uuid].pos = projectile.pos[0] + \
                                                        int(PROJECTILE_SPEED * projectile.direction[0]), projectile.pos[
                                                            1] + \
                                                        int(PROJECTILE_SPEED * projectile.direction[1])
                self.spindex.insert((PROJECTILE_TYPE, projectile.uuid), get_bounding_box(projectile.pos,
                                                                                         PROJECTILE_HEIGHT,
                                                                                         PROJECTILE_WIDTH))
        # print(list(self.projectiles.values()))
        for projectile in to_remove:
            self.projectiles.pop(projectile.uuid)
            self.spindex.remove((PROJECTILE_TYPE, projectile.uuid), get_bounding_box(projectile.pos,
                                                                                     PROJECTILE_HEIGHT,
                                                                                     PROJECTILE_WIDTH))
        s.enter(FRAME_TIME, 1, self.server_controlled_entities_update, (s, projectiles, bots,))

    def start_location_update(self):
        """
        Use: starts the schedular and the function
        """
        s = sched.scheduler(time.time, time.sleep)
        s.enter(FRAME_TIME, 1, self.server_controlled_entities_update, (s, self.projectiles, self.bots,))
        s.run()

    def run(self) -> None:
        """
        Use: starts node threads
        """

        self.server_sock.bind(self.address)
        logging.info(f"Binded to address {self.address}")

        try:
            threading.Thread(target=self.start_location_update).start()
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
    Node(NODE_PORT)

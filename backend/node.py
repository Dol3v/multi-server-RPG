import logging
import queue
import sched
import sys
import threading
import time
from collections import defaultdict
from typing import Dict

import numpy as np
from cryptography.fernet import InvalidToken
from pyqtree import Index

# to import from a dir
from client.map_manager import Map, Layer, TilesetData

sys.path.append('../')

from common.consts import *
from common.utils import *
from collision import *
from consts import WEAPON_DATA, ARM_LENGTH_MULTIPLIER, FRAME_TIME, MAX_SLOT, ROOT_SERVER2SERVER_PORT, MOB_SIGHT_HEIGHT, \
    MOB_SIGHT_WIDTH, MOB_ERROR_TERM, RANGED_OFFSET
from entities import *
from networking import generate_server_message, parse_client_message

EntityData = Tuple[int, str, int, int, float, float, int]
"""type, uuid, x, y, direction in x, direction in y"""


class Node:

    def __init__(self, port):
        # TODO: uncomment when coding on prod
        # self.node_ip = socket.gethostbyname(socket.gethostname())
        self.node_ip = "127.0.0.1"
        self.address = (self.node_ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.root_sock = socket.socket()
        # TODO: remove when actually deploying exe
        time.sleep(1)
        self.root_sock.connect((ROOT_IP, ROOT_SERVER2SERVER_PORT))

        self.players: Dict[str, Player] = {}
        self.mobs: Dict[str, Mob] = {}
        self.projectiles: defaultdict[str, Projectile] = defaultdict(lambda: Projectile())

        self.spindex = Index(bbox=(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
        """Quadtree for collision/range detection. Player keys are tuples `(type, uuid)`, with the type being
        projectile/player/mob, and the uuid being, well, the uuid."""

        self.send_queue = queue.Queue()
        self.recv_queue = queue.Queue()

        self.socket_dict = defaultdict(lambda: self.server_sock)
        self.socket_dict[(ROOT_IP, ROOT_PORT)] = self.root_sock

        self.load_map()
        # Starts the node
        self.generate_mobs()
        self.run()

    @property
    def entities(self) -> Dict[str, Entity]:
        return self.players | self.mobs | self.projectiles

    @property
    def server_controlled(self) -> Dict[str, ServerControlled]:
        return self.mobs | self.projectiles

    @staticmethod
    def get_mob_stop_distance(mob: Mob) -> float:
        return 0.5 * (np.sqrt(BOT_HEIGHT ** 2 + BOT_WIDTH ** 2) + np.sqrt(CLIENT_HEIGHT ** 2 + CLIENT_WIDTH ** 2)) + \
               (RANGED_OFFSET if mob.weapon == BOW else 0)

    def get_data_from_entity(self, entity_data: Tuple[int, str]) -> EntityData:
        """Retrieves data about an entity from its quadtree identifier: kind & other data (id/address).

        :returns: flattened tuple of kind, position and direction"""
        entity = self.entities[entity_data[1]]
        tool_id = EMPTY_SLOT
        if entity_data[0] == PLAYER_TYPE:
            tool_id = entity.tools[entity.slot]
        elif entity_data[0] == MOB_TYPE:
            tool_id = entity.weapon
        return entity_data[0], entity.uuid.encode(), *entity.pos, *entity.direction, tool_id

    def attackable_in_range(self, entity_uuid: str, bbox: Tuple[int, int, int, int]) -> Iterable[Combatant]:
        return map(lambda data: self.mobs[data[1]] if data[0] == MOB_TYPE else self.players[data[1]],
                   filter(lambda data: data[1] != entity_uuid and data[0] != ARROW_TYPE,
                          self.spindex.intersect(bbox)))

    def entities_in_rendering_range(self, entity: Player) -> Iterable[EntityData]:
        """Returns all players that are within render distance of each other."""
        return map(self.get_data_from_entity, filter(lambda data: data[1] != entity.uuid and data[0] != OBSTACLE_TYPE,
                                                     self.spindex.intersect(
                                                         get_bounding_box(entity.pos, SCREEN_HEIGHT, SCREEN_WIDTH))))

    def entities_in_melee_attack_range(self, entity: Combatant, melee_range: int) \
            -> Iterable[Combatant]:
        """Returns all enemy players that are in the attack range (i.e. in the general direction of the player
        and close enough)."""
        weapon_x, weapon_y = int(entity.pos[0] + ARM_LENGTH_MULTIPLIER * entity.direction[0]), \
                             int(entity.pos[1] + ARM_LENGTH_MULTIPLIER * entity.direction[1])
        return self.attackable_in_range(entity.uuid, (weapon_x - melee_range // 2, weapon_y - melee_range // 2,
                                                      weapon_x + melee_range // 2, weapon_y + melee_range // 2))

    def players_in_range(self, pos: Pos, width: int, height: int) -> Iterable[Pos]:
        intersecting = self.spindex.intersect(get_bounding_box(pos, height, width))
        filtered = filter(lambda data: data[0] == PLAYER_TYPE, intersecting)
        mapped = list(map(lambda data: self.entities[data[1]].pos, filtered))
        return mapped

    def load_map(self):
        """Loads the map"""
        game_map = Map()
        game_map.add_layer(Layer("../client/assets/map/animapa_test.csv",
                                 TilesetData("../client/assets/map/new_props.png",
                                             "../client/assets/map/new_props.tsj")))
        game_map.load_collision_objects_to(self.spindex)

    @staticmethod
    def get_entity_bounding_box(pos: Pos, entity_type: int):
        width, height = -1, -1
        if entity_type == PLAYER_TYPE:
            width, height = CLIENT_WIDTH, CLIENT_HEIGHT
        elif entity_type == ARROW_TYPE:
            width, height = PROJECTILE_WIDTH, PROJECTILE_HEIGHT
        elif entity_type == MOB_TYPE:
            width, height = BOT_WIDTH, BOT_HEIGHT
        else:
            raise ValueError("Non-existent type entered to get_entity_bounding_box")
        return get_bounding_box(pos, height, width)

    def get_collidables_with(self, pos: Pos, entity_uuid: str, *, kind: int) -> Iterable[Tuple[int, str]]:
        return filter(lambda data: data[1] != entity_uuid, self.spindex.intersect(
            self.get_entity_bounding_box(pos, kind)))

    def update_entity_location(self, entity: Entity, new_location: Pos, kind: int):
        self.spindex.remove((kind, entity.uuid), self.get_entity_bounding_box(entity.pos, kind))
        # are both necessary? prob not, but I'm not gonna take the risk
        entity.pos = new_location
        self.entities[entity.uuid].pos = new_location
        self.spindex.insert((kind, entity.uuid), self.get_entity_bounding_box(entity.pos, kind))

    def update_mob_directions(self, mob: Mob):
        """Updates mob's attacking/movement directions, and updates whether he is currently tracking a player."""
        in_range = self.players_in_range(mob.pos, MOB_SIGHT_WIDTH, MOB_SIGHT_HEIGHT)
        mob.direction = -1, -1  # used to reset calculations each iteration
        if not in_range:
            mob.on_player = False
            mob.direction = 0.0, 0.0
            return
        print("on player")
        nearest_player_pos = min(in_range,
                                 key=lambda pos: (mob.pos[0] - pos[0]) ** 2 + (mob.pos[1] - pos[1]) ** 2)
        mob.on_player = True
        if np.sqrt(((mob.pos[0] - nearest_player_pos[0]) ** 2 + (mob.pos[1] - nearest_player_pos[1]) ** 2)) <= \
                self.get_mob_stop_distance(mob) + MOB_ERROR_TERM:
            print(f"mob uuid={mob.uuid} is within stop distance")
            mob.direction = 0.0, 0.0
        dir_x, dir_y = nearest_player_pos[0] - mob.pos[0], nearest_player_pos[1] - mob.pos[1]
        dir_x, dir_y = normalize_vec(dir_x, dir_y)
        mob.attacking_direction = dir_x, dir_y
        if mob.direction != (0., 0.):
            mob.direction = dir_x * MOB_SPEED, dir_y * MOB_SPEED

    def melee_attack(self, attacker: Combatant, weapon_data: dict):
        attackable_in_range = self.entities_in_melee_attack_range(attacker,
                                                                  weapon_data['melee_attack_range'])
        # resetting cooldown
        attacker.last_time_attacked = time.time()

        for attackable in attackable_in_range:
            attackable.health -= weapon_data['damage']
            if attackable.health < 0:
                attackable.health = 0
            logging.debug(f"Updated entity health to {attackable.health}")

    def ranged_attack(self, attacker: Combatant, weapon_data: dict):
        attacker.current_cooldown = weapon_data['cooldown'] * FRAME_TIME
        attacker.last_time_attacked = time.time()
        # adding into saved data
        projectile = Projectile(pos=(int(attacker.pos[0] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[0]),
                                     int(attacker.pos[1] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[1])),
                                direction=attacker.attacking_direction, damage=weapon_data['damage'])
        self.projectiles[projectile.uuid] = projectile
        self.spindex.insert((ARROW_TYPE, projectile.uuid),
                            get_bounding_box(projectile.pos, PROJECTILE_HEIGHT, PROJECTILE_WIDTH))
        logging.info(f"Added projectile {projectile}")

    def attack(self, attacker: Combatant, weapon: int):
        """Attacks using data from ``attacker``.

        :param attacker: attacker
        :param weapon: attacking weapon id"""
        weapon_data = WEAPON_DATA[weapon]
        if attacker.current_cooldown != -1:
            if attacker.current_cooldown + attacker.last_time_attacked > (new := time.time()):
                return
            logging.info(f"[attack] cooldown={attacker.current_cooldown} passed, {new=}")
            attacker.current_cooldown = -1
        attacker.current_cooldown = weapon_data['cooldown'] * FRAME_TIME
        if weapon_data['is_melee']:
            self.melee_attack(attacker, weapon_data)
        else:
            self.ranged_attack(attacker, weapon_data)

    def update_location(self, player_pos: Pos, seqn: int, player: Player) -> Pos:
        """Updates the player location in the server and returns location data to be sent to the client.

        :param player: player to update
        :param player_pos: position of player given by the client
        :param seqn: sequence number given by the client
        :returns: ``DEFAULT_POS_MARK`` if the client position is fine, or the server-side-calculated pos for the client
        otherwise.
        """
        # if the received packet is dated then update player
        secure_pos = DEFAULT_POS_MARK
        if self.invalid_movement(player, player_pos, seqn) or seqn != player.last_updated + 1:
            logging.info(
                f"[update] invalid movement of {player.uuid=} from {player.pos} to {player_pos}. {seqn=}, {player.last_updated=}")
            secure_pos = self.players[player.uuid].pos
        else:
            self.update_entity_location(player, player_pos, PLAYER_TYPE)
        return secure_pos

    def update_client(self, player_uuid: str, secure_pos: Pos):
        """sends server message to the client"""
        new_chat = ""
        player = self.players[player_uuid]
        entities_array = flatten(self.entities_in_rendering_range(player))
        # generate and send message
        update_packet = generate_server_message(player.tools, new_chat, secure_pos, player.health, entities_array)
        self.server_sock.sendto(update_packet, player.addr)

    def handle_client(self):
        """communicate with client"""
        while True:
            try:
                data, addr = self.server_sock.recvfrom(RECV_CHUNK)
                player_uuid = data[:UUID_SIZE].decode()
                try:
                    data = self.players[player_uuid].fernet.decrypt(data[UUID_SIZE:])
                except InvalidToken:
                    logging.warning(f"[security] player {addr=} sent non-matching uuid={player_uuid}")
                    continue
                client_msg = parse_client_message(data)
                if not client_msg:
                    continue
                seqn, x, y, chat, _, attacked, *attack_dir, slot_index = parse_client_message(data)
                player_pos = x, y
                if slot_index > MAX_SLOT or slot_index < 0:
                    continue

                player = self.players[player_uuid]
                if seqn <= player.last_updated != 0:
                    logging.info(f"Got outdated packet from {addr=}")
                    continue

                player.attacking_direction = attack_dir  # TODO: check if normalized
                secure_pos = self.update_location(player_pos, seqn, player)

                player.slot = slot_index
                if attacked:
                    self.attack(player, player.tools[player.slot])
                self.update_client(player.uuid, secure_pos)
                player.last_updated = seqn
            except Exception as e:
                logging.exception(e)

    def server_controlled_entities_update(self, s, projectiles, bots):
        """update all projectiles and bots positions inside a loop"""
        # projectile handling
        to_remove = []
        for projectile in projectiles.values():
            projectile.ttl -= 1
            intersection = self.get_collidables_with(projectile.pos, projectile.uuid, kind=ARROW_TYPE)
            if intersection:
                for kind, identifier in intersection:
                    if kind == ARROW_TYPE:
                        continue
                    if kind == PLAYER_TYPE:
                        player = self.players[identifier]
                        logging.info(f"Projectile {projectile} hit a player {player}")
                        player.health -= projectile.damage
                        if player.health < MIN_HEALTH:
                            player.health = MIN_HEALTH
                        logging.debug(f"Updated player {identifier} health to {player.health}")
                    to_remove.append(projectile)
                    break
            if projectile.ttl == 0:
                to_remove.append(projectile)
                continue

            self.update_entity_location(projectile,
                                        (projectile.pos[0] + int(PROJECTILE_SPEED * projectile.direction[0]),
                                         projectile.pos[1] + int(PROJECTILE_SPEED * projectile.direction[1])),
                                        ARROW_TYPE)
        for projectile in to_remove:
            self.projectiles.pop(projectile.uuid)
            self.spindex.remove((ARROW_TYPE, projectile.uuid), get_bounding_box(projectile.pos,
                                                                                PROJECTILE_HEIGHT,
                                                                                PROJECTILE_WIDTH))
            logging.info(f"[update] removed projectile {projectile.uuid}")
        for mob in self.mobs.values():
            self.update_mob_directions(mob)
            colliding = self.get_collidables_with(mob.pos, mob.uuid, kind=MOB_TYPE)
            if colliding:
                for kind, identifier in colliding:
                    if kind == ARROW_TYPE:
                        continue
                    mob.direction = 0., 0.  # TODO: refactor a bit into update_mob_directions
            if mob.on_player:
                self.attack(mob, mob.weapon)
            self.update_entity_location(mob, (mob.pos[0] + int(mob.direction[0] * MOB_SPEED),
                                              mob.pos[1] + int(mob.direction[1] * MOB_SPEED)),
                                        MOB_TYPE)
        s.enter(FRAME_TIME, 1, self.server_controlled_entities_update, (s, projectiles, bots,))

    def start_location_update(self):
        """starts the schedular and the function"""
        s = sched.scheduler(time.time, time.sleep)
        s.enter(FRAME_TIME, 1, self.server_controlled_entities_update, (s, self.projectiles, self.mobs,))
        s.run()

    def root_receiver(self):
        while True:
            data = self.root_sock.recv(RECV_CHUNK)
            shared_key, player_uuid = data[:SHARED_KEY_SIZE], data[SHARED_KEY_SIZE:SHARED_KEY_SIZE + UUID_SIZE].decode()
            ip, port = deserialize_addr(data[SHARED_KEY_SIZE + UUID_SIZE:])
            logging.info(f"[login] notified player {player_uuid=} with addr={(ip, port)} is about to join")
            initial_pos = self.get_available_position(PLAYER_TYPE)

            self.players[player_uuid] = Player(uuid=player_uuid, addr=(ip, port),
                                               fernet=Fernet(base64.urlsafe_b64encode(shared_key)),
                                               pos=initial_pos)

            self.spindex.insert((PLAYER_TYPE, player_uuid),
                                get_bounding_box(initial_pos, CLIENT_HEIGHT, CLIENT_WIDTH))

    def get_available_position(self, kind: int) -> Pos:
        """Generates a position on the map, such that the bounding box of an entity of type ``kind``
           doesn't intersect with any existing object on the map.

        :param kind: entity type
        :returns: available position"""
        pos_x, pos_y = int(np.random.uniform(0, WORLD_WIDTH)), int(np.random.uniform(0, WORLD_HEIGHT))

        while len(self.spindex.intersect(self.get_entity_bounding_box((pos_x, pos_y), kind))) != 0:
            pos_x, pos_y = int(np.random.uniform(0, WORLD_WIDTH)), int(np.random.uniform(0, WORLD_HEIGHT))
        return pos_x, pos_y

    def generate_mobs(self):
        # """Generate the mobs object with a random positions"""
        # for _ in range(MOB_COUNT):
        #     mob = Mob()
        #     mob.pos = self.get_available_position(MOB_TYPE)
        #     mob.weapon = random.randint(MIN_WEAPON_NUMBER, MAX_WEAPON_NUMBER)
        #     self.mobs[mob.uuid] = mob
        mob = Mob()
        mob.pos = (2500, 1700)
        # mob.weapon = random.randint(MIN_WEAPON_NUMBER, MAX_WEAPON_NUMBER)
        mob.weapon = BOW
        self.mobs[mob.uuid] = mob
        self.spindex.insert((MOB_TYPE, mob.uuid), self.get_entity_bounding_box(mob.pos, MOB_TYPE))

    def run(self) -> None:
        """starts node threads"""
        self.server_sock.bind(self.address)
        logging.info(f"Binded to address {self.address}")

        try:
            threading.Thread(target=self.start_location_update).start()
            threading.Thread(target=self.root_receiver).start()
            for _ in range(THREADS_COUNT):
                # starts handlers threads
                client_thread = threading.Thread(target=self.handle_client)
                client_thread.start()

        except Exception as e:
            logging.exception(f"{e}")

    def invalid_movement(self, entity: Player, player_pos: Pos, seqn: int) -> bool:
        """
        Use: check if a given player movement is valid
        """
        return entity.last_updated != -1 and (not moved_reasonable_distance(
            player_pos, entity.pos, seqn - entity.last_updated) or
                                              not is_empty(
                                                  self.get_collidables_with(player_pos, entity.uuid, kind=PLAYER_TYPE)))


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.WARNING)
    Node(NODE_PORT)

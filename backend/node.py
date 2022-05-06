import logging
import queue
import sys
import threading
import time
from collections import defaultdict
from typing import Set

from pyqtree import Index

# to import from a dir
# from backend.logic.attacks import attack
from backend.database import SqlDatabase, DB_PASS
from backend.database.database_utils import update_user_info
from backend.logic.collision import invalid_movement
from backend.logic.entity_logic import EntityManager, Player, Mob
from common.message_type import MessageType

sys.path.append('../')

from common.consts import *
from common.utils import *
from backend_consts import MAX_SLOT, ROOT_SERVER2SERVER_PORT

from backend.networks.networking import parse_message_from_client, \
    generate_routine_message, S2SMessageType, generate_status_message

from backend.logic.server_controlled_entities import server_entities_handler
from client.map_manager import Map, Layer, TilesetData


class Node:
    """Server that receive and transfer data to the clients and root server"""

    def __init__(self, port, db_conn: SqlDatabase):
        # TODO: uncomment when coding on prod
        # self.node_ip = socket.gethostbyname(socket.gethostname())
        self.node_ip = "127.0.0.1"
        self.address = (self.node_ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.root_sock = socket.socket()
        self.db = db_conn
        # TODO: remove when actually deploying exe
        # root_ip = enter_ip("Enter root's IP: ")

        self.send_queue = queue.Queue()
        self.recv_queue = queue.Queue()

        self.socket_dict = defaultdict(lambda: self.server_sock)
        self.socket_dict[(ROOT_IP, ROOT_PORT)] = self.root_sock

        self.dead_clients: Set[str] = set()
        self.should_join: Set[str] = set()
        self.entities_manager = EntityManager(create_map())
        self.generate_mobs()
        # Starts the node
        self.run()

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
        if invalid_movement(player, player_pos, seqn, self.entities_manager) or seqn != player.last_updated_seqn + 1:
            logging.info(
                f"[update] invalid movement of {player.uuid=} from {player.pos} to {player_pos}. {seqn=}"
                f", {player.last_updated_seqn=}")
            secure_pos = self.entities_manager.players[player.uuid].pos
        else:
            self.entities_manager.update_entity_location(player, player_pos)
        return secure_pos

    def kill_player(self, player: Player):
        logging.info(f"killing {player!r}")
        self.server_sock.sendto(generate_status_message(MessageType.DIED_SERVER, player.fernet), player.addr)
        self.entities_manager.remove_entity(player)
        update_user_info(self.db, player)
        self.dead_clients.add(player.uuid)

    def update_client(self, player: Player, secure_pos: Pos):
        """Sends server message to the client"""
        entities_array = self.entities_manager.get_entities_in_range(
            get_bounding_box(player.pos, SCREEN_HEIGHT, SCREEN_WIDTH),
            entity_filter=lambda _, entity_uuid: entity_uuid != player.uuid
        )
        # generate and send message
        update_packet = generate_routine_message(secure_pos, player, entities_array)
        self.server_sock.sendto(update_packet, player.addr)
        logging.debug(f"[debug] sent message to client {player.uuid=}")

    def routine_message_handler(self, player_uuid: str, contents: dict):
        """Handles messages of type `MessageType.ROUTINE_CLIENT`."""
        if player_uuid in self.should_join:
            player = self.entities_manager.pop(player_uuid, EntityType.PLAYER)
            player.last_updated_time = time.time()
            logging.info(f"adding {player=!r} to the game")
            self.entities_manager.add_entity(player)
            self.should_join.remove(player_uuid)

        if player_uuid in self.dead_clients:
            return

        try:
            player_pos, seqn, chat, attack_dir, slot_index, clicked_mouse, did_swap = tuple(contents["pos"]), contents[
                "seqn"], \
                                                                                      contents["chat"], contents["dir"], \
                                                                                      contents["slot"], contents[
                                                                                          "is_attacking"], \
                                                                                      contents["did_swap"]
            swap_indices = (-1, -1)
            if did_swap:
                swap_indices = contents["swap"]
        except KeyError:
            logging.warning(f"[security] invalid message given by {player_uuid=}")
            return

        if slot_index > MAX_SLOT or slot_index < 0:
            return

        player = self.entities_manager.players[player_uuid]
        logging.debug(f"{player=} sent a routine message")
        if seqn <= player.last_updated_seqn != 0:
            logging.info(f"Got outdated packet from {player_uuid=}")
            return

        if player.health <= MIN_HEALTH:
            self.kill_player(player)
            return

        player.attacking_direction = attack_dir
        player.new_message = chat
        secure_pos = self.update_location(player_pos, seqn, player)

        if did_swap:
            player.inventory[swap_indices[0]], player.inventory[swap_indices[1]] = player.inventory[swap_indices[1]], \
                                                                                   player.inventory[swap_indices[0]]
            logging.info(f"{player=!r} swaped inventory slot {swap_indices[0]} with slot {swap_indices[1]}")
        player.slot = slot_index
        if clicked_mouse:
            player.item.on_click(player, self.entities_manager)

        # self.broadcast_clients(player.uuid)
        self.update_client(player, secure_pos)
        player.last_updated_seqn = seqn
        player.last_updated_time = time.time()

    def closed_game_handler(self, player_uuid: str):
        logging.info(f"player {player_uuid} exited the game.")
        if player := self.entities_manager.get(player_uuid, EntityType.PLAYER):
            self.entities_manager.remove_entity(player)
            update_user_info(self.db, player)

    def client_handler(self):
        """Communicate with client"""
        while True:
            data, addr = self.server_sock.recvfrom(RECV_CHUNK)
            data = parse_message_from_client(data, self.entities_manager)
            if not data:
                continue
            try:
                message_type = MessageType(data["contents"]["id"])
                client_uuid = data["uuid"]
            except KeyError as e:
                logging.warning(f"[security] invalid message, no id/uuid present {data=}, {e=}")
                continue
            except ValueError as e:
                logging.warning(f"[security] invalid id, {data=}, {e=}")
                continue

            match message_type:
                case MessageType.ROUTINE_CLIENT:
                    self.routine_message_handler(client_uuid, data["contents"])
                case MessageType.CLOSED_GAME_CLIENT:
                    self.closed_game_handler(client_uuid)
                case _:
                    logging.warning(f"[security] no handler present for {message_type=}, {data=}")

    def handle_player_prelogin(self, data: dict):
        """Handles the root message of a player that is going to join.

        :param data: data of message sent from root
        """
        try:
            shared_key, player_uuid, initial_pos, ip, port = base64.b64decode(data["key"]), data["uuid"], \
                                                             data["initial_pos"], data["client_ip"], data["client_port"]
            logging.info(f"[login] notified player {player_uuid=} with addr={(ip, port)} is about to join")

            self.should_join.add(player_uuid)
            if data["is_login"]:
                self.entities_manager.add_to_dict(Player(uuid=player_uuid, addr=(ip, port),
                                                         fernet=Fernet(base64.urlsafe_b64encode(shared_key)),
                                                         pos=initial_pos, slot=data["initial_slot"],
                                                         health=data["initial_hp"], inventory=data["initial_inventory"])
                                                  )
            else:
                self.entities_manager.add_to_dict(Player(uuid=player_uuid, addr=(ip, port),
                                                         fernet=Fernet(base64.urlsafe_b64encode(shared_key)),
                                                         pos=initial_pos))
            if player_uuid in self.dead_clients:
                self.dead_clients.remove(player_uuid)
        except KeyError as e:
            logging.warning(f"[error] invalid message from root message, {data=}, {e=}")

    def root_handler(self):
        """Receive new clients from the root infinitely
        NOTE: add msg_type
        """
        while True:
            try:
                data = json.loads(self.root_sock.recv(RECV_CHUNK))
                match S2SMessageType(data["id"]):
                    case S2SMessageType.PLAYER_LOGIN:
                        self.handle_player_prelogin(data)
            except KeyError | ValueError as e:
                logging.warning(f"[error] prelogin message from root has an invalid format, {data=}, {e=}")

    def generate_mobs(self):
        """Generate the mobs object with a random positions"""
        for _ in range(MOB_COUNT):
            mob = Mob()
            mob.pos = self.entities_manager.get_available_position(EntityType.MOB)
            mob.weapon = SWORD  # random.randint(MIN_WEAPON_NUMBER, MAX_WEAPON_NUMBER)
            self.entities_manager.add_entity(mob)
            logging.info(f"added mob {mob!r}")

    def run(self):
        """Starts node threads and bind & connect sockets"""
        self.server_sock.bind(self.address)
        self.root_sock.connect((ROOT_IP, ROOT_SERVER2SERVER_PORT))  # may case the bug
        logging.info(f"bound to address {self.address}")

        threading.Thread(target=server_entities_handler, args=(self.entities_manager,)).start()
        threading.Thread(target=self.root_handler).start()
        for _ in range(THREADS_COUNT):
            # starts handlers threads
            client_thread = threading.Thread(target=self.client_handler)
            client_thread.start()


def create_map():
    """Create a new quadtree and loads the map

    :returns: spindex: the quadtree
    """
    spindex = Index(bbox=(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
    game_map = Map()
    game_map.add_layer(Layer("../client/assets/map/animapa_test.csv",
                             TilesetData("../client/assets/map/new_props.png",
                                         "../client/assets/map/new_props.tsj")))
    game_map.load_collision_objects_to(spindex)

    return spindex


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s %(threadName)s:%(thread)d - %(message)s", level=logging.INFO)
    db = SqlDatabase("127.0.0.1", DB_PASS)
    Node(NODE_PORT, db)

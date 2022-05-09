import logging
import queue
import sys
import threading
import time
from collections import defaultdict
from typing import Set, Dict

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

from backend.networks.networking import decrypt_client_packet, \
    generate_routine_message, generate_status_message, S2SMessageType, craft_message

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
        self.queue = queue.Queue()
        # TODO: remove when actually deploying exe
        # root_ip = enter_ip("Enter root's IP: ")

        self.root_send_queue = queue.Queue()
        self.root_recv_queue = queue.Queue()

        self.socket_dict = defaultdict(lambda: self.server_sock)
        self.socket_dict[(ROOT_IP, ROOT_PORT)] = self.root_sock

        self.dead_clients: Set[str] = set()
        self.should_join: Dict[str, Player] = {}
        self.entities_manager = EntityManager(create_map())
        self.generate_mobs()
        # Starts the node
        self.run()

    def receiver(self):
        while True:
            try:
                self.queue.put(self.server_sock.recvfrom(RECV_CHUNK))
            except ConnectionError:
                continue

    def root_sender(self):
        while True:
            message = self.root_send_queue.get()
            self.root_sock.send(json.dumps(message).encode())
            logging.info(f"sent to root {message=}")

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
            secure_pos = self.entities_manager.players[player.uuid].pos
        else:
            self.entities_manager.update_entity_location(player, player_pos)
        return secure_pos

    def handle_player_termination(self, player: Player):
        self.entities_manager.remove_entity(player)
        update_user_info(self.db, player)
        self.dead_clients.add(player.uuid)
        self.root_send_queue.put({"status": S2SMessageType.PLAYER_DISCONNECTED, "uuid": player.uuid})
        self.server_sock.sendto(generate_status_message(MessageType.DIED_SERVER, player.fernet), player.addr)

    def kill_player(self, player: Player):
        logging.info(f"killing {player!r}")
        self.handle_player_termination(player)

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
            player = self.should_join.pop(player_uuid)
            self.entities_manager.add_entity(player)

        if player_uuid in self.dead_clients:
            return

        try:
            player_pos, seqn, attack_dir, slot_index, clicked_mouse, did_swap, using_skill = tuple(contents["pos"]), \
                                                                                             contents["seqn"], \
                                                                                             contents["dir"], \
                                                                                             contents["slot"], \
                                                                                             contents["is_attacking"], \
                                                                                             contents["did_swap"], \
                                                                                             contents["using_skill"]
            swap_indices = (-1, -1)
            if did_swap:
                swap_indices = contents["swap"]
        except KeyError:
            logging.warning(f"[security] invalid message given by {player_uuid=}")
            return

        if slot_index > MAX_SLOT or slot_index < 0:
            return

        player = self.entities_manager.players[player_uuid]
        logging.debug(f"{player=} sent a routine message, {contents=}")
        if seqn <= player.last_updated_seqn != 0:
            logging.info(f"Got outdated packet from {player_uuid=}")
            return

        if player.health <= MIN_HEALTH:
            self.kill_player(player)
            return

        player.attacking_direction = attack_dir
        secure_pos = self.update_location(player_pos, seqn, player)

        if did_swap:
            player.inventory[swap_indices[0]], player.inventory[swap_indices[1]] = player.inventory[
                                                                                       swap_indices[1]], \
                                                                                   player.inventory[swap_indices[0]]
            logging.info(f"{player=!r} swapped inventory slot {swap_indices[0]} with slot {swap_indices[1]}")
        player.slot = slot_index
        if clicked_mouse:
            player.item.on_click(player, self.entities_manager)

        if using_skill:
            player.skill.on_click(player, self.entities_manager)

        player.last_updated_seqn = seqn
        player.last_updated_time = time.time()

        bags = self.entities_manager.get_entities_in_range(
            get_entity_bounding_box(player.pos, player.kind),
            entity_filter=lambda entity_type, _: entity_type == EntityType.BAG
        )
        for bag in bags:
            player.fill_inventory(bag)
            self.entities_manager.remove_entity(bag)

        # self.broadcast_clients(player.uuid)
        self.update_client(player, secure_pos)

    def closed_game_handler(self, player_uuid: str):
        if player := self.entities_manager.get(player_uuid, EntityType.PLAYER):
            logging.info(f"player {player_uuid} exited the game.")
            self.handle_player_termination(player)

    def handle_should_join(self, player_uuid: str) -> Player | None:
        logging.info(f"player uuid={player_uuid} joined")
        player = self.should_join[player_uuid]
        self.should_join.pop(player_uuid)
        self.entities_manager.add_entity(player)
        self.root_send_queue.put({"status": S2SMessageType.PLAYER_CONNECTED, "uuid": player_uuid})
        return player

    def client_handler(self):
        """Communicate with client"""
        while True:
            data, addr = self.queue.get()
            parsed_packet = json.loads(data)

            if not (player_uuid := parsed_packet.get("uuid", None)):
                logging.warning(f"[security] invalid packet {data=}")
                continue

            # sus
            if player_uuid in self.dead_clients:
                continue

            player = self.handle_should_join(player_uuid) if player_uuid in self.should_join.keys() else \
                self.entities_manager.get(player_uuid, EntityType.PLAYER)

            if not player:
                logging.warning(f"player uuid={player_uuid} couldn't be found")
                continue

            data = decrypt_client_packet(parsed_packet, player.fernet)
            if not data:
                continue
            try:
                message_type = MessageType(data["contents"]["id"])
            except KeyError as e:
                logging.warning(f"[security] invalid message, no id/uuid present {data=}, {e=}")
                continue
            except ValueError as e:
                logging.warning(f"[security] invalid id, {data=}, {e=}")
                continue

            if player := self.entities_manager.players.get(parsed_packet["uuid"], None):
                with player.lock:
                    match message_type:
                        case MessageType.ROUTINE_CLIENT:
                            self.routine_message_handler(player_uuid, data["contents"])
                        case MessageType.CHAT_PACKET:
                            self.chat_handler(player_uuid, data["contents"])
                        case MessageType.CLOSED_GAME_CLIENT:
                            self.closed_game_handler(player_uuid)
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

            if data["is_login"]:
                new_health = data["initial_hp"]
                if new_health == 0:
                    new_health = MAX_HEALTH

                self.should_join[player_uuid] = Player(uuid=player_uuid, addr=(ip, port),
                                                       fernet=Fernet(base64.urlsafe_b64encode(shared_key)),
                                                       pos=initial_pos, slot=data["initial_slot"],
                                                       health=new_health, inventory=data["initial_inventory"])

            else:  # on signup
                self.should_join[player_uuid] = Player(uuid=player_uuid, addr=(ip, port),
                                                       fernet=Fernet(base64.urlsafe_b64encode(shared_key)),
                                                       pos=initial_pos)
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

    def chat_handler(self, player_uuid: str, contents: dict):
        """Broadcast clients new messages to each other."""
        try:
            new_message = contents["new_message"]
        except KeyError:
            logging.warning(f"[error] new_message is not a field in {contents=}")
            return

        for uuid_to_broadcast in self.entities_manager.players:
            if player_uuid != uuid_to_broadcast:
                player = self.entities_manager.get(uuid_to_broadcast, EntityType.PLAYER)
                self.server_sock.sendto(craft_message(MessageType.CHAT_PACKET, {"new_message": new_message}
                                                      , player.fernet), player.addr)
                # TODO: update root server

    def generate_mobs(self):
        """Generate the mobs object with a random positions"""
        for _ in range(MOB_COUNT):
            mob = Mob()
            mob.pos = self.entities_manager.get_available_position(EntityType.MOB)
            self.entities_manager.add_entity(mob)
            logging.info(f"added mob {mob!r}")

    def run(self):
        """Starts node threads and bind & connect sockets"""
        self.server_sock.bind(self.address)
        self.root_sock.connect((ROOT_IP, ROOT_SERVER2SERVER_PORT))  # may case the bug
        logging.info(f"bound to address {self.address}")

        threading.Thread(target=self.receiver).start()
        threading.Thread(target=server_entities_handler, args=(self.entities_manager,)).start()
        threading.Thread(target=self.root_handler).start()
        threading.Thread(target=self.root_sender).start()
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

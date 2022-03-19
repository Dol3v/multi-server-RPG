import logging, socket, sys, threading
from typing import Tuple

# to import from a dir
sys.path.append('../')

from collision import players_are_colliding
from consts import *
from client.consts import WIDTH, HEIGHT
from common.consts import CLIENT_FORMAT, CLIENT_WIDTH, CLIENT_HEIGHT, MESSAGE_ENDIANESS
from common.utils import *


class Node:

    def __init__(self, ip, port):
        self.address = (ip, port)
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # timeout of 0.5 seconds
        # self.server_sock.settimeout(0.5)
        self.entities = {}
        # Starts the node
        self.run()

    @staticmethod
    def parse_client_message(contents: bytes) -> tuple | None:
        return parse(CLIENT_FORMAT, contents)

    def entities_within_render_distance_of(self, player_pos: Pos):
        """Returns all entities that are within render distance of each other."""

        def within_render_distance(pos1: Pos, pos2: Pos) -> bool:
            return (0 <= abs(pos1[0] - pos2[0]) < WIDTH // 2 + CLIENT_WIDTH) and \
                   (0 <= abs(pos1[1] - pos2[1]) < HEIGHT // 2 + CLIENT_HEIGHT)  # NOTE: really should be client_height/2

        return filter(lambda pos: within_render_distance(player_pos, pos) and pos != player_pos,
                      self.entities.values())

    def encode_entity_locations_for_player(self, player_pos: Pos) -> bytes | None:
        # converts list of tuples into a list
        entities_pos = flatten(self.entities_within_render_distance_of(player_pos))
        msg_format = MESSAGE_ENDIANESS + "l" + "l" * len(entities_pos)
        try:
            return struct.pack(msg_format, len(entities_pos) // 2, *entities_pos)
        except struct.error:
            return None

    @staticmethod
    def get_colliding_entities_with(player_pos: Pos, *, entities_to_check: Iterable[Pos]):
        """Returns all entities that collided with a given player."""
        # would have refactored players_are_colliding into an inner function, but it'll prob be more complicated in the
        # future
        # TODO: optimize the sh*t out of this routine
        return filter(lambda pos: players_are_colliding(pos, player_pos), entities_to_check)

    def handle_clients(self):
        """
        Use: communicate with client
        """
        while True:
            try:
                data, addr = self.server_sock.recvfrom(1024)
                # update current player data
                player_pos = self.parse_client_message(data)
                if not player_pos:
                    continue
                logging.debug(f"Received position {player_pos} from {addr=}")
                self.entities[addr] = player_pos

                # some collision checks
                within_render_distance = self.entities_within_render_distance_of(player_pos)
                colliding_players = list(self.get_colliding_entities_with(player_pos,
                                                                          entities_to_check=within_render_distance))
                # print(colliding_players, player_pos, self.entities.values())
                if len(colliding_players) == 1:
                    print("Collision")
                update_msg = self.encode_entity_locations_for_player(player_pos)
                if not update_msg:
                    continue
                logging.debug(f"Sent positions {list(within_render_distance)} to {addr=}")
                self.server_sock.sendto(update_msg, addr)

            except Exception as e:
                logging.error(e)

    def run(self):
        """
        Use: starts node threads
        """

        self.server_sock.bind(self.address)
        try:
            for i in range(THREADS_COUNT):
                # starts thread per client
                client_thread = threading.Thread(target=self.handle_clients)
                client_thread.start()

        except Exception as e:
            logging.exception(f"{e}")


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(thread)d - %(message)s", level=logging.WARNING)
    Node(SERVER_IP, SERVER_PORT)

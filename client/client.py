"""Runs the client stages"""
import os
import signal
import sys

from common.utils import get_random_port

sys.path.append('../')
from common.consts import SCREEN_WIDTH, SCREEN_HEIGHT

import pygame
import game
import connect_screen
from client_consts import GAME_NAME, PLAYER_IMG

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'


def init_pygame() -> pygame.Surface:
    """
    Use: starts pygame with and return the new screen
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(GAME_NAME)
    pygame.display.set_icon(pygame.image.load(PLAYER_IMG))

    return screen


def main():
    # signal.signal(signal.SIGINT, game.on_game_exit)
    # signal.signal(signal.SIGTERM, game.on_game_exit)
    while True:
        screen = init_pygame()
        connection_screen = connect_screen.ConnectScreen(screen, 10000)
        connection_screen.run()
        if not connection_screen.sock:
            print("Login/Signup failed")
            return

        my_game = game.Game(connection_screen.sock, connection_screen.game_server_addr,
                            connection_screen.received_player_uuid, connection_screen.shared_key,
                            connection_screen.full_screen, connection_screen.initial_pos)
        pygame.init()
        my_game.run()


if __name__ == "__main__":
    main()

"""Connection screen login and signup"""
import base64
import socket
import sys
import platform

import pygame.transform

# to import from a dir
from networking import do_ecdh, get_login_response, send_credentials
from common.utils import is_valid_ip

sys.path.append('../')
from consts import *
from common.consts import NODE_PORT, SCREEN_HEIGHT, ROOT_PORT
from graphics import *


class ConnectScreen:
    def __init__(self, screen, port: int):
        """Remove port later, currently stays for debugging before login"""
        self.received_player_uuid = None
        self.game_server_addr = None
        self.shared_key = None
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.screen = screen
        self.login_bg = pygame.transform.scale(pygame.image.load(LOGIN_BACKGROUND), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.register_bg = pygame.transform.scale(pygame.image.load(REGISTER_BACKGROUND), (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.running = False
        self.full_screen = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if platform.system() == "Windows":
            self.sock.bind(("127.0.0.1", port))
        self.clock = pygame.time.Clock()

        self.is_login_screen = True

        big_font = pygame.font.SysFont("arial", 45)
        big_font.set_bold(True)

        self.tip_box = TipBox(0, SCREEN_HEIGHT * 0.8, pygame.font.SysFont("arial", 30), 5)

        self.login_group = pygame.sprite.Group(
            Text(0, SCREEN_HEIGHT * 0.1, "Login to server!", big_font).position_center(),

            Text(0, SCREEN_HEIGHT * 0.20, "Enter Server's IP", pygame.font.SysFont("arial", 25)).position_center(),
            LimitedTextBox(0, SCREEN_HEIGHT * 0.25, 250, pygame.font.SysFont("arial", 35), 15).position_center(),

            Text(0, SCREEN_HEIGHT * 0.35, "Enter Username", pygame.font.SysFont("arial", 25)).position_center(),
            LimitedTextBox(0, SCREEN_HEIGHT * 0.40, 250, pygame.font.SysFont("arial", 35), 15).position_center(),

            Text(0, SCREEN_HEIGHT * 0.50, "Enter Password", pygame.font.SysFont("arial", 25)).position_center(),
            LimitedTextBox(0, SCREEN_HEIGHT * 0.55, 250, pygame.font.SysFont("arial", 35), 15).position_center(),

            ConnectButton(0, SCREEN_HEIGHT * 0.70, 200, 50, CONNECT_BUTTON_IMG, self).position_center(),
            MoveScreenButton(0, SCREEN_HEIGHT * 0.8, 150, 40, REGISTER_BUTTON_IMG, self).position_center()
        )

        self.register_group = pygame.sprite.Group(
            Text(0, SCREEN_HEIGHT * 0.1, "Register To Server", big_font).position_center(),

            Text(0, SCREEN_HEIGHT * 0.20, "Enter Server's IP", pygame.font.SysFont("arial", 25)).position_center(),
            LimitedTextBox(0, SCREEN_HEIGHT * 0.25, 250, pygame.font.SysFont("arial", 35), 15).position_center(),

            Text(0, SCREEN_HEIGHT * 0.35, "Enter Username", pygame.font.SysFont("arial", 25)).position_center(),
            LimitedTextBox(0, SCREEN_HEIGHT * 0.40, 250, pygame.font.SysFont("arial", 35), 15).position_center(),

            Text(0, SCREEN_HEIGHT * 0.50, "Enter Password", pygame.font.SysFont("arial", 25)).position_center(),
            LimitedTextBox(0, SCREEN_HEIGHT * 0.55, 250, pygame.font.SysFont("arial", 35), 15).position_center(),

            RegisterButton(0, SCREEN_HEIGHT * 0.70, 200, 50, REGISTER_BUTTON_IMG, self).position_center(),
            MoveScreenButton(0, SCREEN_HEIGHT * 0.8, 150, 40, LOGIN_BUTTON_IMG, self).position_center()
        )

        anim = [None] * 40
        for i in range(40):
            anim[i] = pygame.image.load(f"assets/loading_animation/l-{i}.png")

        self.loading_animation = Animation(anim, 40)
        self.is_loading_animation = False

    def run(self):
        self.running = True

        while self.running:

            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        if self.full_screen:
                            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                        else:
                            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                        self.full_screen = not self.full_screen

            bg = self.login_bg
            if not self.is_login_screen:
                bg = self.register_bg

            self.screen.blit(bg, bg.get_rect())

            group = self.login_group
            if not self.is_login_screen:
                group = self.register_group

            group.update(event_list)
            if not self.is_loading_animation:
                group.draw(self.screen)
            else:
                self.run_loading_animation()
                text = Text(0, SCREEN_HEIGHT * 0.75, "Some Useful Tips:", pygame.font.SysFont("arial", 30))
                text.position_center()
                new_group = pygame.sprite.Group(self.tip_box, text)
                new_group.update(event_list)
                new_group.draw(self.screen)

            pygame.display.update()
            self.clock.tick(FPS)

    def run_loading_animation(self):
        if self.is_loading_animation:
            frame = self.loading_animation.get_next_frame()
            frame = pygame.transform.scale(frame, (SCREEN_WIDTH * 0.375, SCREEN_HEIGHT * 0.5))
            x = (SCREEN_WIDTH - frame.get_width()) / 2
            y = (SCREEN_HEIGHT - frame.get_height()) / 2
            self.screen.blit(frame, (x, y))

    def get_sprite_by_position(self, position):
        group = self.login_group
        if not self.is_login_screen:
            group = self.register_group

        for index, spr in enumerate(group):
            if index == position:
                return spr
        return False

    def connect_to_server(self, ip, username, password, is_login: bool = False):
        if not is_valid_ip(ip):
            print(f"Invalid ip {ip}")
            return
        self.running = False
        with socket.socket() as conn:
            try:
                conn.connect((ip, ROOT_PORT))
                print("Connected")
            except OSError:
                print(f"Couldn't connect to ip {ip}")
                return
            self.shared_key = do_ecdh(conn)
            print(f"Did ecdh, key={self.shared_key}")
            send_credentials(username, password, conn, self.shared_key, self.sock.getsockname(), is_login)
            ip, user_uuid, success, error_message = get_login_response(conn)
            self.game_server_addr = (ip, NODE_PORT)
            self.received_player_uuid = user_uuid

            if not success:
                print(error_message)
                self.sock = None


class ConnectButton(Button):
    def __init__(self, x, y, width, height, image_path, connect_screen):
        super().__init__(x, y, width, height, image_path)
        self.connect_screen = connect_screen

    def update(self, event_list):
        self.render_button()
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):

                    self.connect_screen.is_loading_animation = True
                    ip = self.connect_screen.get_sprite_by_position(2).text
                    username = self.connect_screen.get_sprite_by_position(4).text
                    password = self.connect_screen.get_sprite_by_position(6).text
                    if ip == "":
                        ip = '127.0.0.1'
                        self.connect_screen.running = False  # Debug TODO remove this shit later

                    self.connect_screen.connect_to_server(ip, username, password, is_login=True)


class RegisterButton(Button):
    def __init__(self, x, y, width, height, image_path, connect_screen):
        super().__init__(x, y, width, height, image_path)
        self.connect_screen = connect_screen

    def update(self, event_list):
        self.render_button()
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    self.connect_screen.is_loading_animation = True
                    ip = self.connect_screen.get_sprite_by_position(2).text
                    username = self.connect_screen.get_sprite_by_position(4).text
                    password = self.connect_screen.get_sprite_by_position(6).text
                    if ip == "":
                        ip = '127.0.0.1'
                    # Send register packet to the server and wait for response
                    self.connect_screen.connect_to_server(ip, username, password, is_login=False)


class MoveScreenButton(Button):  # Button to change between loading and registration screen
    def __init__(self, x, y, width, height, image_path, connect_screen):
        super().__init__(x, y, width, height, image_path)
        self.connect_screen = connect_screen

    def update(self, event_list):
        self.render_button()
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    self.connect_screen.is_login_screen = not self.connect_screen.is_login_screen

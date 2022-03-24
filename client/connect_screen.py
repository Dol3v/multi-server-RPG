"""Connection screen login and signup"""
import socket
import sys

import pygame.transform

# to import from a dir
sys.path.append('../')
from consts import CONNECTION_SCREEN_IMG, CONNECT_BUTTON_IMG, FPS
from common.consts import SERVER_PORT, SCREEN_HEIGHT
from graphics import *


class ConnectScreen:
    def __init__(self, screen, port: int):
        """Remove port later, currently stays for debugging before login"""
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.screen = screen
        self.background = pygame.transform.scale(pygame.image.load(CONNECTION_SCREEN_IMG),
                                                 (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.running = False
        self.full_screen = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = None
        self.clock = pygame.time.Clock()

        server_ip = Text(0, SCREEN_HEIGHT * 0.20, "Enter Server's IP", pygame.font.SysFont("arial", 25))
        server_ip.position_center()

        input_box = LimitedTextBox(0, SCREEN_HEIGHT * 0.25, 250, pygame.font.SysFont("arial", 35), 15)
        input_box.position_center()

        username = Text(0, SCREEN_HEIGHT * 0.35, "Enter Username", pygame.font.SysFont("arial", 25))
        username.position_center()

        username_input = LimitedTextBox(0, SCREEN_HEIGHT * 0.40, 250, pygame.font.SysFont("arial", 35), 15)
        username_input.position_center()

        password = Text(0, SCREEN_HEIGHT * 0.50, "Enter Password", pygame.font.SysFont("arial", 25))
        password.position_center()

        password_input = LimitedTextBox(0, SCREEN_HEIGHT * 0.55, 250, pygame.font.SysFont("arial", 35), 15)
        password_input.position_center()

        connect_btn = ConnectButton(0, SCREEN_HEIGHT * 0.70, 200, 50, CONNECT_BUTTON_IMG, self)
        connect_btn.position_center()

        self.tip_box = TipBox(0, SCREEN_HEIGHT * 0.8, pygame.font.SysFont("arial", 30), 5)

        self.group = pygame.sprite.Group(server_ip, input_box, username, username_input,
                                         password, password_input, connect_btn)
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

            self.screen.blit(self.background, self.background.get_rect())
            self.group.update(event_list)
            if not self.is_loading_animation:
                self.group.draw(self.screen)
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
        for index, spr in enumerate(self.group):
            if index == position:
                return spr
        return False

    def connect_to_server(self, ip, username, password):
        self.running = False
        self.addr = (ip, SERVER_PORT)  # TODO: complete


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
                    ip = self.connect_screen.get_sprite_by_position(1).text
                    username = self.connect_screen.get_sprite_by_position(3).text
                    password = self.connect_screen.get_sprite_by_position(5).text
                    if ip == "":
                        ip = '127.0.0.1'
                    self.connect_screen.connect_to_server(ip, username, password)

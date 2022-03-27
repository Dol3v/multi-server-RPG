"""Connection screen login and signup"""
import socket
import sys

import pygame.transform

# to import from a dir
sys.path.append('../')
from consts import *
from common.consts import SERVER_PORT, SCREEN_HEIGHT
from graphics import *


class ConnectScreen:
    def __init__(self, screen, port: int):
        """Remove port later, currently stays for debugging before login"""
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.screen = screen
        self.login_bg = pygame.transform.scale(pygame.image.load(LOGIN_BACKGROUND), (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.register_bg = pygame.transform.scale(pygame.image.load(REGISTER_BACKGROUND), (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.running = False
        self.full_screen = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 10000))
        self.addr = None
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
                    ip = self.connect_screen.get_sprite_by_position(2).text
                    username = self.connect_screen.get_sprite_by_position(4).text
                    password = self.connect_screen.get_sprite_by_position(6).text
                    if ip == "":
                        ip = '127.0.0.1'
                    self.connect_screen.connect_to_server(ip, username, password)  # Login player to the server


class RegisterButton(Button):
    def __init__(self, x, y, width, height, image_path, connect_screen):
        super().__init__(x, y, width, height, image_path)
        self.connect_screen = connect_screen

    def update(self, event_list):
        self.render_button()
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    print("Registered lmao")
                    self.connect_screen.is_loading_animation = True
                    ip = self.connect_screen.get_sprite_by_position(1).text
                    username = self.connect_screen.get_sprite_by_position(3).text
                    password = self.connect_screen.get_sprite_by_position(5).text
                    if ip == "":
                        ip = '127.0.0.1'
                    # Send register packet to the server and wait for response
                    # TODO: Dolev or reem do the register stuff lmao


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

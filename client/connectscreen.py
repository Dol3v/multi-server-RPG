import pygame.transform

from py_utils import *
from consts import *


class ConnectScreen:
    def __init__(self, game):
        self.width = WIDTH
        self.height = HEIGHT
        self.screen = game.screen
        self.background = pygame.transform.scale(pygame.image.load("assets/background.jpg"), (WIDTH, HEIGHT))

        server_ip = Text(0, HEIGHT * 0.20, "Enter Server's IP", pygame.font.SysFont("arial", 25))
        server_ip.position_center()

        input_box = LimitedTextBox(0, HEIGHT * 0.25, 250, pygame.font.SysFont("arial", 35), 15)
        input_box.position_center()

        username = Text(0, HEIGHT * 0.35, "Enter Username", pygame.font.SysFont("arial", 25))
        username.position_center()

        username_input = LimitedTextBox(0, HEIGHT * 0.40, 250, pygame.font.SysFont("arial", 35), 15)
        username_input.position_center()

        password = Text(0, HEIGHT * 0.50, "Enter Password", pygame.font.SysFont("arial", 25))
        password.position_center()

        password_input = LimitedTextBox(0, HEIGHT * 0.55, 250, pygame.font.SysFont("arial", 35), 15)
        password_input.position_center()

        connect_btn = ConnectButton(0, HEIGHT * 0.70, 200, 50, "assets/connect_btn.png", game)
        connect_btn.position_center()

        self.tip_box = TipBox(0, HEIGHT * 0.8, pygame.font.SysFont("arial", 30), 5)

        self.group = pygame.sprite.Group(server_ip, input_box, username, username_input,
                                         password, password_input, connect_btn)
        anim = [None] * 40
        for i in range(40):
            anim[i] = pygame.image.load(f"assets/loading_animation/l-{i}.png")

        self.loading_animation = Animation(anim, 40)
        self.is_loading_animation = False

    def run(self, event_list):
        self.screen.blit(self.background, self.background.get_rect())
        self.group.update(event_list)
        if not self.is_loading_animation:
            self.group.draw(self.screen)
        else:
            self.run_loading_animation()
            text = Text(0, HEIGHT * 0.75, "Some Useful Tips:", pygame.font.SysFont("arial", 30))
            text.position_center()
            new_group = pygame.sprite.Group(self.tip_box, text)
            new_group.update(event_list)
            new_group.draw(self.screen)

    def run_loading_animation(self):
        if self.is_loading_animation:
            frame = self.loading_animation.get_next_frame()
            frame = pygame.transform.scale(frame, (WIDTH * 0.375, HEIGHT * 0.5))
            x = (WIDTH - frame.get_width()) / 2
            y = (HEIGHT - frame.get_height()) / 2
            self.screen.blit(frame, (x, y))

    def get_sprite_by_position(self, position):
        for index, spr in enumerate(self.group):
            if index == position:
                return spr
        return False

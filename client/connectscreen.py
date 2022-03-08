from py_utils import *
from settings import *


class ConnectScreen:
    def __init__(self, screen):
        self.width = WIDTH
        self.height = HEIGHT
        self.screen = screen
        self.background = pygame.transform.scale(pygame.image.load("background.jpg"), (WIDTH, HEIGHT))
        input_box = LimitedTextBox(0, HEIGHT * 0.30, 250, pygame.font.SysFont("arial", 35), 15)
        input_box.position_center()

        connect_btn = ConnectButton(0, HEIGHT * 0.45, 200, 50, "connect_btn.png")
        connect_btn.position_center()

        self.group = pygame.sprite.Group(input_box, connect_btn)

    def run(self, event_list):
        self.screen.blit(self.background, self.background.get_rect())
        self.group.update(event_list)
        self.group.draw(self.screen)

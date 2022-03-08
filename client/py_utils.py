import pygame
from settings import *


class TextInputBox(pygame.sprite.Sprite):
    def __init__(self, x, y, w, font):
        super().__init__()
        self.color = (0, 0, 0)
        self.backcolor = None
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.width = w
        self.font = font
        self.active = False
        self.text = ""
        self.height = None
        self.render_text()

    def position_center(self):
        self.pos = ((WIDTH - self.width) / 2, self.y)
        self.render_text()

    def render_text(self):
        t_surf = self.font.render(self.text, True, self.color, self.backcolor)

        if not self.height:
            self.height = t_surf.get_height() + 10

        self.image = pygame.Surface((max(self.width, t_surf.get_width() + 10), self.height),
                                    pygame.SRCALPHA)

        self.width = self.image.get_width()
        self.pos = ((WIDTH - self.width) / 2, self.y)

        background = pygame.image.load("text-box.png")
        background = pygame.transform.scale(background,
                                            (max(self.width, t_surf.get_width() + 10), self.height))

        self.image.blit(background, background.get_rect())

        font_size = self.font.size(self.text)

        x = (max(self.width, t_surf.get_width() + 10) - font_size[0]) / 2
        y = (self.height - font_size[1]) / 2

        self.image.blit(t_surf, (x, y))
        self.rect = self.image.get_rect(topleft=self.pos)

    def update(self, event_list):
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos)
            if event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.render_text()


class LimitedTextBox(TextInputBox):
    def __init__(self, x, y, w, font, character_limit: int):
        super().__init__(x, y, w, font)
        self.character_limit = character_limit

    def update(self, event_list):
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos)
            if event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if len(self.text) < self.character_limit:
                        self.text += event.unicode
                self.render_text()


class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, image_path):
        super().__init__()
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.width = width
        self.height = height
        self.image = pygame.transform.scale(pygame.image.load(image_path), (width, height))
        self.render_button()

    def position_center(self):
        self.pos = ((WIDTH - self.width) / 2, self.y)
        self.render_button()

    def render_button(self):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        surface.blit(self.image, self.image.get_rect())
        self.rect = surface.get_rect(topleft=self.pos)


class ConnectButton(Button):
    def __init__(self, x, y, width, height, image_path):
        super().__init__(x, y, width, height, image_path)

    def update(self, event_list):
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    print("Clicked")

"""Grphics utils for login screen and more"""
import random
import pygame

from common.consts import SCREEN_WIDTH


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
        self.pos = ((SCREEN_WIDTH - self.width) / 2, self.y)
        self.render_text()
        return self

    def render_text(self):
        t_surf = self.font.render(self.text, True, self.color, self.backcolor)

        if not self.height:
            self.height = t_surf.get_height() + 10

        self.image = pygame.Surface((max(self.width, t_surf.get_width() + 10), self.height),
                                    pygame.SRCALPHA)

        self.width = self.image.get_width()
        self.pos = ((SCREEN_WIDTH - self.width) / 2, self.y)

        background = pygame.image.load("assets/text-box.png")
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


class Text(pygame.sprite.Sprite):
    def __init__(self, x, y, text, font, color=(255, 255, 255), backcolor=None):
        super().__init__()
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.text = text
        self.font = font
        self.color = color
        self.backcolor = backcolor
        self.width = 0
        self.render_text()

    def position_center(self):
        self.pos = ((SCREEN_WIDTH - self.width) / 2, self.y)
        self.render_text()
        return self

    def render_text(self):
        t_surf = self.font.render(self.text, True, self.color, self.backcolor)
        self.image = pygame.Surface((t_surf.get_width(), t_surf.get_height()),
                                    pygame.SRCALPHA)
        self.width = t_surf.get_width()
        self.image.fill((0, 0, 0, 100))
        self.image.blit(t_surf, (0, 0))
        self.rect = self.image.get_rect(topleft=self.pos)

    def update(self, event_list):
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
        self.pos = ((SCREEN_WIDTH - self.width) / 2, self.y)
        self.render_button()
        return self

    def render_button(self):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        surface.blit(self.image, self.image.get_rect())
        self.rect = surface.get_rect(topleft=self.pos)


class Animation:
    """A class to simplify the act of adding animations to sprites."""

    def __init__(self, frames, fps, loops=-1):
        """
        The argument frames is a list of frames in the correct order;
        fps is the frames per second of the animation;
        loops is the number of times the animation will loop (a value of -1
        will loop indefinitely).
        """
        self.frames = frames
        self.fps = fps
        self.frame = 0
        self.timer = None
        self.loops = loops
        self.loop_count = 0
        self.done = False

    def get_next_frame(self):
        """
        Advance the frame if enough time has elapsed and the animation has
        not finished looping.
        """
        now = pygame.time.get_ticks()
        if not self.timer:
            self.timer = now
        if not self.done and now - self.timer > 1000.0 / self.fps:
            self.frame = (self.frame + 1) % len(self.frames)
            if not self.frame:
                self.loop_count += 1
                if self.loops != -1 and self.loop_count >= self.loops:
                    self.done = True
                    self.frame -= 1
            self.timer = now
        return self.frames[self.frame]

    def reset(self):
        """Set frame, timer, and loop status back to the initialized state."""
        self.frame = 0
        self.timer = None
        self.loop_count = 0
        self.done = False


class TipBox(pygame.sprite.Sprite):
    def __init__(self, x, y, font, seconds_per_tip):
        super().__init__()
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.font = font
        self.seconds_per_tip = seconds_per_tip

        with open("assets/tips.txt") as f:
            self.tips = [line.rstrip('\n') for line in f]

        self.tip = random.choice(self.tips)
        self.now = pygame.time.get_ticks()
        self.timer = None
        self.width = 0
        self.render_text()

    def render_text(self):
        t_surf = self.font.render(self.tip, True, (0, 0, 0), None)
        self.width = t_surf.get_width()
        self.pos = ((SCREEN_WIDTH - self.width) / 2, self.y)

        self.image = pygame.Surface((t_surf.get_width(), t_surf.get_height()),
                                    pygame.SRCALPHA)
        self.width = t_surf.get_width()
        self.image.blit(t_surf, (0, 0))
        self.rect = self.image.get_rect(topleft=self.pos)

    def update(self, event_list):
        self.now = pygame.time.get_ticks()

        if not self.timer:
            self.timer = pygame.time.get_ticks()

        if self.now - self.timer > 1000 * self.seconds_per_tip:
            print("Changed!")

            random_tip = self.tip
            while self.tip == random_tip:
                self.tip = random.choice(self.tips)
            self.timer = self.now
        self.render_text()

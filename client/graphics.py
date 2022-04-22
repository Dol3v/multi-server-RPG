"""Grphics utils for login screen and more"""
import random
from typing import List

import pygame
import math

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

    def is_empty(self):
        return len(self.frames) == 0


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

            random_tip = self.tip
            while self.tip == random_tip:
                self.tip = random.choice(self.tips)
            self.timer = self.now
        self.render_text()


class ChatBox:
    def __init__(self, x, y, width, height, font, text_color=(255, 255, 255)):
        super().__init__()
        self.x = x
        self.y = y
        self.scroll_height = 0
        self.width = width
        self.height = height
        self.font = font
        self.background_color = (82, 82, 82, 100)
        self.text_color = text_color
        self.history = []
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.message_surface = pygame.Surface((0, 0), pygame.SRCALPHA)
        self.load_message_surface()
        self.at_bottom = True

        self.text_area = None

    def add_message(self, message: str):
        if message == "":
            return
        self.history.append(message)
        self.message_surface = self.combine_surfaces(self.message_surface, self.generate_surface(message))
        if self.at_bottom:
            self.jump_to_new_message()

    def load_message_surface(self):
        for msg in self.history:
            self.message_surface = self.combine_surfaces(self.message_surface, self.generate_surface(msg))

    def render_chat(self, surface, current_message):

        self.image.fill(self.background_color)
        self.image.blit(self.message_surface, (0, self.scroll_height))

        current_message_surf = self.generate_surface(current_message)

        text_surface = pygame.Surface((self.width, current_message_surf.get_height()), pygame.SRCALPHA)
        text_surface.fill((255, 255, 255, 150))
        text_surface.blit(current_message_surf, (0, 0))
        self.text_area = text_surface.copy()
        surface.blit(self.combine_surfaces(self.image, text_surface), (self.x, self.y))

    def update(self, event_list):
        keys = pygame.key.get_pressed()
        if self.message_surface.get_height() > self.image.get_height():
            if keys[pygame.K_UP]:
                if self.scroll_height < 0:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.scroll_height += 4
                    else:
                        self.scroll_height += 2
                    self.at_bottom = False

            if keys[pygame.K_DOWN]:
                if self.image.get_height() + abs(self.scroll_height) < self.message_surface.get_height():
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.scroll_height -= 4
                    else:
                        self.scroll_height -= 2
                else:
                    self.at_bottom = True

    def jump_to_new_message(self):
        if self.message_surface.get_height() > self.height:
            self.scroll_height = self.image.get_height() - self.message_surface.get_height()
            self.at_bottom = True

    def generate_surface(self, message: str):
        full_surface = self.font.render(message, True, self.text_color, None)

        if full_surface.get_width() > self.width:
            surface = pygame.Surface((0, 0), pygame.SRCALPHA)
            loops_amount = math.ceil(full_surface.get_width() / self.width)

            # t_surf = self.font.render(self.tip, True, (0, 0, 0), None)
            index = 0
            characters = list(message)
            for i in range(loops_amount):
                current_msg = ""
                rendered_text = self.font.render(current_msg, True, self.text_color, None)
                while index < len(characters) and rendered_text.get_width() < self.width:
                    current_msg += characters[index]
                    index += 1
                    rendered_text = self.font.render(current_msg, True, self.text_color, None)

                index -= 1
                current_msg = current_msg[:-1]
                surface = self.combine_surfaces(surface, self.font.render(current_msg, True, self.text_color, None))
            return surface
        else:
            return full_surface

    def has_collision(self, x, y) -> bool:
        return self.combine_surfaces(self.image, self.text_area).get_rect(topleft=(self.x, self.y)).collidepoint(x, y)

    def combine_surfaces(self, f_surf, s_surf):
        # Create a surface and pass the sum of the widths.
        # Also, pass pg.SRCALPHA to make the surface transparent.
        result = pygame.Surface((self.width, f_surf.get_height() + s_surf.get_height()), pygame.SRCALPHA)

        # Blit the first two surfaces onto the third.
        result.blit(f_surf, (0, 0))
        result.blit(s_surf, (0, f_surf.get_height()))
        return result


class Inventory:
    def __init__(self):
        size_multiplier = 3
        self.inv = pygame.image.load("assets/inventory.png")
        self.inv = pygame.transform.scale(self.inv, (self.inv.get_width() * size_multiplier,
                                                     self.inv.get_height() * size_multiplier))
        self.starting_x = 8 * size_multiplier
        self.starting_y = 8 * size_multiplier
        self.x_offset = 2 * size_multiplier
        self.y_offest = 2 * size_multiplier

        self.rows = 4
        self.columns = 9

        self.icon_size = 16 * size_multiplier
        self.items = [None] * (self.rows * self.columns)
        self.icon_rects: List[pygame.Rect | None] = [None] * (self.rows * self.columns)
        self.init_icon_rects()
        self.current_hotbar_slot = 0
        self.has_hovered_slot = False
        self.hovered_slot = -1
        self.selected_slot = -1
        self.move = [-1, -1]

    def init_icon_rects(self):
        for y in range(self.rows):  # Rows
            for x in range(self.columns):  # Columns
                index = y * 9 + x
                self.icon_rects[index] = pygame.Rect(

                    (SCREEN_WIDTH - self.inv.get_width()) + self.starting_x + self.icon_size * x + self.x_offset * x,
                    self.starting_y + self.icon_size * y + self.y_offest * y,
                    self.icon_size, self.icon_size)

    def draw_inventory(self, surface):
        inv = self.inv.copy()

        for y in range(self.rows):  # Rows
            for x in range(self.columns):  # Columns
                index = y * self.columns + x
                item = self.items[index]

                if self.has_hovered_slot:
                    if index == self.hovered_slot:
                        pygame.draw.rect(surface, (255, 255, 255, 100),
                                         pygame.Rect((SCREEN_WIDTH - self.inv.get_width()) +
                                                     self.starting_x + self.icon_size * x + self.x_offset * x,
                                                     self.starting_y + self.icon_size * y + self.y_offest * y,
                                                     self.icon_size, self.icon_size))

                if index == self.selected_slot:
                    pygame.draw.rect(surface, (100, 200, 50, 100),
                                     pygame.Rect((SCREEN_WIDTH - self.inv.get_width()) +
                                                 self.starting_x + self.icon_size * x + self.x_offset * x,
                                                 self.starting_y + self.icon_size * y + self.y_offest * y,
                                                 self.icon_size, self.icon_size))

                if item:
                    icon = pygame.transform.scale(item.icon, (self.icon_size, self.icon_size))
                    inv.blit(icon, (
                        self.starting_x + self.icon_size * x + self.x_offset * x,
                        self.starting_y + self.icon_size * y + self.y_offest * y
                    ))
        inv.set_alpha(200)
        surface.blit(inv, (SCREEN_WIDTH - inv.get_width(), 0))

    def update(self, event_list):
        mouse_pos = pygame.mouse.get_pos()
        has_collision_rect = False
        index = 0
        for rect in self.icon_rects:
            if rect.collidepoint(mouse_pos):
                has_collision_rect = True
                self.hovered_slot = index
                break
            index += 1
        self.has_hovered_slot = has_collision_rect

        for event in event_list:
            if event.type == pygame.MOUSEBUTTONUP:
                if has_collision_rect:
                    if self.selected_slot == -1 and self.items[index]:
                        self.selected_slot = index
                    else:
                        # Note selected_slot = seleceted slot
                        # Note index = new slot
                        self.swap_items(self.selected_slot, index)
                        self.move = [self.selected_slot, index]
                        self.selected_slot = -1

    def set_item_in_slot(self, slot, item):
        self.items[slot] = item

    def get_hotbar_items(self):
        return self.items[:9]

    def next_hotbar_slot(self):
        hotbar = self.get_hotbar_items()
        current_item = hotbar[self.current_hotbar_slot]
        if current_item:
            current_item.hide()

        if self.current_hotbar_slot + 1 < len(hotbar):
            self.current_hotbar_slot += 1
        else:
            self.current_hotbar_slot = 0

        if hotbar[self.current_hotbar_slot]:
            hotbar[self.current_hotbar_slot].start_drawing()

    def previous_hotbar_slot(self):
        hotbar = self.get_hotbar_items()
        current_item = hotbar[self.current_hotbar_slot]
        if current_item:
            current_item.hide()

        if self.current_hotbar_slot - 1 > -1:
            self.current_hotbar_slot -= 1
        else:
            self.current_hotbar_slot = len(hotbar) - 1

        if hotbar[self.current_hotbar_slot]:
            hotbar[self.current_hotbar_slot].start_drawing()

    def swap_items(self, index_one: int, index_two: int):
        if index_one == index_two:
            return
        if index_one == self.current_hotbar_slot:
            if self.get_hotbar_items()[index_one]:
                self.get_hotbar_items()[index_one].hide()
        if index_two == self.current_hotbar_slot:
            if self.get_hotbar_items()[index_two]:
                self.get_hotbar_items()[index_two].hide()
        self.items[index_one], self.items[index_two] = self.items[index_two], self.items[index_one]

        if index_one == self.current_hotbar_slot:
            if self.items[index_one]:
                self.items[index_one].start_drawing()
        if index_two == self.current_hotbar_slot:
            if self.items[index_two]:
                self.items[index_two].start_drawing()

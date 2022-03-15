import pygame
import os
from consts import *

class Tile(pygame.sprite.Sprite):
	def __init__(self,pos,groups):
		super().__init__(groups)
		# base_path = os.path.dirname(__file__)
		# print(base_path)
		# needed_path = os.path.join(base_path,'/graphics/tree.PNG')
		# print(needed_path)
		# open('C:\\Networks\\client\\test.txt')
		# print('done open')

		# get the directory of this file

		self.image = pygame.image.load("assets/tree.png").convert_alpha()
		self.rect = self.image.get_rect(topleft = pos)

import pygame
import os
from settings import*

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
		source_file_dir = os.path.dirname(os.path.abspath(__file__))
		fond_img_path = os.path.join(source_file_dir, 'tree.png')
		self.image = pygame.image.load(fond_img_path).convert_alpha()
		self.rect = self.image.get_rect(topleft = pos)

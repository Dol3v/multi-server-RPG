import pygame, sys, os
from pygame.locals import *
pygame.init()
screen = pygame.display.set_mode((100, 100))

player = pygame.image.load("idle_down.png")
player.convert()

while True:
    screen.blit(player, (10, 10))
    pygame.display.flip()

pygame.quit()

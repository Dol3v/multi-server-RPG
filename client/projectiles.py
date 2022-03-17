import pygame,sys

class Player (pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((100,100))
        self.image.fill((255,255,255))
        self.rect = self.image.get_rect(center = (screen_width/2,screen_height/2))

    def update(self):
        self.rect.center = pygame.mouse.get_pos()
    def create_bullet(self):
        return Bullet (pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1])


class Bullet (pygame.sprite.Sprite):
    def __init__(self,pos_x,pos_y):
        super().__init__()
        self.image = pygame.Surface((50,10)) # change this to image.loade
        self.image.fill((255,0,0))
        self.rect =self.image.get_rect(center = (pos_x,pos_y))
    def update(self):
        self.rect.x += 5 # this is what countrels the projectile dir
        if self.rect.x >= screen_width +200: # this is ehat kills it better to change it to some kind of timeout
            self.kill()



#basic shit
pygame.init()
clock =pygame.time.Clock()
screen_width , screen_height = 800,800
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.mouse.set_visible(False)

player = Player()
player_group = pygame.sprite.Group()
player_group.add(player)

bullet_group = pygame.sprite.Group()

while True:
    for event in pygame.event.get():
        if event.type ==pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            bullet_group.add(player.create_bullet())



    #drawing
    screen.fill((30,30,30))
    bullet_group.draw(screen)
    player_group.draw(screen)
    player_group.update()
    bullet_group.update()
    pygame.display.flip()
    clock.tick(120)

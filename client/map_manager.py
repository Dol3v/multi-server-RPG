import json
from csv import reader

import pygame
from pyqtree import Index

from client import consts
from common.utils import get_bounding_box
from common.consts import OBSTACLE_TYPE

try:
    from sprites import Tile
except ModuleNotFoundError:
    from client.sprites import Tile


def import_csv_layer(path):
    layer = []
    with open(path) as level_map:
        layout = reader(level_map, delimiter=",")
        for row in layout:
            layer.append(row)
        return layer


class MapTile:
    def __init__(self, tile_image):
        self.image = tile_image
        self.has_collision = False
        self.collision_objects = []

    def add_collision_rect(self, x, y, width, height):
        self.has_collision = True
        self.collision_objects.append(pygame.Rect((x, y), (width, height)))

    def get_collision_objects(self):
        return self.collision_objects.copy()


class TilesetData:
    def __init__(self, image, data):
        self.image = pygame.image.load(image)
        self.tiles = {-1: None}
        self.data = json.load(open(data))
        self.init_tiles()

    def init_tiles(self):
        tile_id = 0
        for y_cord in range(8):
            for x_cord in range(8):
                map_tile = MapTile(
                    self.image.subsurface((x_cord * 64, y_cord * 64, 64, 64))
                )
                if len(self.data["tiles"]) != 0:
                    for tile in self.data["tiles"]:
                        if tile["id"] == tile_id:

                            objectgroup = tile["objectgroup"]

                            for collision in objectgroup["objects"]:
                                height = int(collision["height"])
                                width = int(collision["width"])
                                x = int(collision["x"])
                                y = int(collision["y"])
                                map_tile.add_collision_rect(x, y, width, height)
                self.tiles[tile_id] = map_tile
                tile_id += 1

    def get_tile(self, tile_id) -> MapTile | None:
        return self.tiles[tile_id]


class Layer:
    def __init__(self, csv_file_path, tileset: TilesetData):
        self.layer_grid = import_csv_layer(csv_file_path)
        self.tileset = tileset
        self.collision_objects = []

    def load_collision_objects(self):
        for y in range(len(self.layer_grid)):
            for x in range(len(self.layer_grid[0])):
                tile_id = int(self.layer_grid[y][x])
                if tile_id != -1:
                    tile = self.tileset.get_tile(tile_id)
                    if tile.has_collision:
                        for rect in tile.get_collision_objects():
                            rect.x += x * consts.TILE_SIZE
                            rect.y += y * consts.TILE_SIZE
                            self.collision_objects.append(rect)

    def draw_layer(self, visible_sprites):
        for y in range(len(self.layer_grid)):
            for x in range(len(self.layer_grid[0])):
                tile_id = int(self.layer_grid[y][x])
                if tile_id != -1:
                    tile = self.tileset.get_tile(tile_id)
                    Tile((visible_sprites,), (x * consts.TILE_SIZE, y * consts.TILE_SIZE), tile.image)


class Map:
    def __init__(self):
        self.collision_objects = []
        self.layers = []

    def add_layer(self, layer: Layer):
        self.layers.append(layer)

    def load_collision_objects_to(self, quadtree: Index):
        self.collision_objects = []
        for layer in self.layers:
            layer.load_collision_objects()
            self.collision_objects.extend(layer.collision_objects)

            for obj in layer.collision_objects:
                quadtree.insert((OBSTACLE_TYPE, obj), get_bounding_box((obj.x, obj.y), obj.height, obj.width))

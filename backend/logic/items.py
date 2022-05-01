import abc
import logging
import time
from dataclasses import dataclass
from typing import Type, Dict

from backend.backend_consts import FRAME_TIME
from backend.logic.entities import Entity, Combatant, Projectile
from backend.logic.entities_management import EntityManager
from common.consts import EntityType, MIN_HEALTH, ARROW_OFFSET_FACTOR, SWORD, AXE, BOW, MAHAK


@dataclass
class Item:
    """An in-game item"""
    type: int

    def on_click(self, clicked_by: Entity, manager: EntityManager):
        """Handles a click on the item.

        :param clicked_by: entity who clicked on the item
        :param manager: entity manager"""
        ...


@dataclass
class Weapon(Item):
    """An in-game weapon."""
    cooldown: int
    damage: int

    def on_click(self, clicked_by: Combatant, manager: EntityManager):
        self.use_to_attack(clicked_by, manager)
        clicked_by.last_time_attacked = time.time()
        clicked_by.current_cooldown = self.cooldown * FRAME_TIME

    @abc.abstractmethod
    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        """Attack using this weapon."""
        ...


@dataclass
class MeleeWeapon(Weapon):
    melee_attack_range: int

    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        in_range = manager.entities_in_melee_attack_range(attacker, self.melee_attack_range)
        for kind, attackable in in_range:
            if kind == EntityType.MOB == attackable.kind:
                continue  # mobs shouldn't attack mobs
            attackable.health -= self.damage
            if attackable.health <= MIN_HEALTH:
                manager.remove_entity(attackable, kind)
                logging.info(f"killed {attackable=}")
            logging.info(f"updated entity health to {attackable.health}")


@dataclass
class RangedWeapon(Weapon):
    projectile_class: Type[Projectile]
    """Projectile type to be shot. Can be any class which inherits from `Projectile`."""

    def use_to_attack(self, attacker: Combatant, manager: EntityManager):
        projectile = self.projectile_class(
            pos=(int(attacker.pos[0] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[0]),
                 int(attacker.pos[1] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[1])))
        manager.add_entity(projectile.kind, projectile.uuid, projectile.pos, projectile.height,
                           projectile.width)
        with manager.projectile_lock:
            manager.projectiles[projectile.uuid] = projectile
            logging.info(f"added projectile {projectile}")


_item_pool: Dict[int, Item] = {
    SWORD: MeleeWeapon(type=SWORD, cooldown=100, damage=15, melee_attack_range=100),
    AXE: MeleeWeapon(type=AXE, cooldown=300, damage=40, melee_attack_range=150),
    BOW: RangedWeapon(type=BOW, cooldown=400, damage=30, projectile_class=Projectile),
    MAHAK: RangedWeapon(type=MAHAK, cooldown=200, damage=100, projectile_class=Projectile)
}


def get_item(kind: int) -> Item:
    return _item_pool[kind]

import logging
import time

from backend.consts import FRAME_TIME, WEAPON_DATA
from backend.logic.entities import Combatant, Projectile
from backend.logic.entities_management import EntityManager
from common.consts import MIN_HEALTH, ARROW_OFFSET_FACTOR, PROJECTILE_HEIGHT, PROJECTILE_WIDTH, EntityType


def melee_attack(entities_manager: EntityManager, attacker: Combatant, weapon_data: dict):
    attackable_in_range = entities_manager.entities_in_melee_attack_range(attacker,
                                                                          weapon_data['melee_attack_range'])
    # resetting cooldown
    attacker.last_time_attacked = time.time()

    for kind, attackable in attackable_in_range:
        attackable.health -= weapon_data['damage']
        if attackable.health <= MIN_HEALTH:
            entities_manager.remove_entity(attackable, kind)
            logging.debug(f"[debug] killed {attackable=}")
        logging.debug(f"Updated entity health to {attackable.health}")


def ranged_attack(entities_manager: EntityManager, attacker: Combatant, weapon_data: dict):
    attacker.current_cooldown = weapon_data['cooldown'] * FRAME_TIME
    attacker.last_time_attacked = time.time()
    # adding into saved data
    projectile = Projectile(pos=(int(attacker.pos[0] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[0]),
                                 int(attacker.pos[1] + ARROW_OFFSET_FACTOR * attacker.attacking_direction[1])),
                            direction=attacker.attacking_direction, damage=weapon_data['damage'])
    entities_manager.add_entity(EntityType.ARROW, projectile.uuid,
                                projectile.pos, PROJECTILE_HEIGHT, PROJECTILE_WIDTH)
    with entities_manager.projectile_lock:
        entities_manager.projectiles[projectile.uuid] = projectile
    logging.info(f"Added projectile {projectile}")


def attack(entities_manager: EntityManager, attacker: Combatant, weapon: int):
    """Attacks using data from `attacker`.

    :param entities_manager: object with all players and server entity data
    :param attacker: the attacking entity data
    :param weapon: the weapon the attacker using
    NOTE: the attacker can be an arrow (that's why we use weapon: int)
    """

    if attacker.uuid in entities_manager.players.keys():
        logging.debug("[debug] player is attacking")
    weapon_data = WEAPON_DATA[weapon]

    if attacker.current_cooldown != -1:
        if attacker.current_cooldown + attacker.last_time_attacked > (new := time.time()):
            return
        logging.info(f"[attack] cooldown={attacker.current_cooldown} passed, {new=}")
        attacker.current_cooldown = -1
    attacker.current_cooldown = weapon_data['cooldown'] * FRAME_TIME
    logging.debug(f"[debug] attacker={attacker.uuid} is attacking")

    if weapon_data['is_melee']:
        melee_attack(entities_manager, attacker, weapon_data)
    else:
        ranged_attack(entities_manager, attacker, weapon_data)

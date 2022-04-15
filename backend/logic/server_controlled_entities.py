import logging
import sched
import time

from backend.consts import FRAME_TIME
from backend.logic.attacks import attack
from backend.logic.entities import Combatant
from backend.logic.entities_management import EntityManager
from common.consts import EntityType, MIN_HEALTH, PROJECTILE_SPEED, MOB_SPEED


def server_controlled_entities_update(entities_manager: EntityManager, s):
    """update all projectiles and bots positions inside a loop"""
    # BUGFIX: sometimes this functions just freezes
    to_remove = []
    with entities_manager.projectile_lock:
        for projectile in entities_manager.projectiles.values():
            projectile.ttl -= 1
            if projectile.ttl == 0:
                logging.debug(f"[debug] gonna remove uuid={projectile.uuid}, ttl=0")
                to_remove.append(projectile)
                continue

            intersection = entities_manager.get_collidables_with(projectile.pos, projectile.uuid, kind=EntityType.ARROW)
            should_remove = False
            if intersection:
                for kind, identifier in intersection:
                    if kind == EntityType.ARROW:
                        continue
                    if kind == EntityType.PLAYER or kind == EntityType.MOB:
                        combatant: Combatant = entities_manager.entities[identifier]
                        logging.info(f"Projectile {projectile} hit {combatant}")
                        should_remove = True
                        combatant.health -= projectile.damage
                        if combatant.health <= MIN_HEALTH:
                            logging.info(f"[update] killed {combatant=}")
                            # remove entity on
                            entities_manager.remove_entity(combatant, kind)
                        logging.debug(f"Updated player {identifier} health to {combatant.health}")
                if should_remove:
                    to_remove.append(projectile)
                    logging.debug(f"[debug] gonna remove uuid={projectile.uuid}, nonzero intersection")
                    continue

            entities_manager.update_entity_location(projectile,
                                                    (projectile.pos[0] + int(PROJECTILE_SPEED * projectile.direction[0]),
                                         projectile.pos[1] + int(PROJECTILE_SPEED * projectile.direction[1])),
                                                    EntityType.ARROW)
    for projectile in to_remove:
        entities_manager.remove_entity(projectile, EntityType.ARROW)
        logging.info(f"[update] removed projectile {projectile.uuid}")

    with entities_manager.mob_lock:
        for mob in entities_manager.mobs.values():
            entities_manager.update_mob_directions(mob)
            colliding = entities_manager.get_collidables_with(mob.pos, mob.uuid, kind=EntityType.MOB)

            for kind, identifier in colliding:
                if kind == EntityType.ARROW:
                    continue
                mob.direction = 0., 0.  # TODO: refactor a bit into update_mob_directions

            if mob.on_player:
                attack(entities_manager, mob, mob.weapon)
            entities_manager.update_entity_location(mob, (mob.pos[0] + int(mob.direction[0] * MOB_SPEED),
                                                          mob.pos[1] + int(mob.direction[1] * MOB_SPEED)),
                                                    EntityType.MOB)

    s.enter(FRAME_TIME, 1, server_controlled_entities_update, (entities_manager, s,))


def server_entities_handler(entities_manager):
    """Starts the schedular and update entities functions"""
    s = sched.scheduler(time.time, time.sleep)
    s.enter(FRAME_TIME, 1, server_controlled_entities_update, (entities_manager, s,))
    s.run()

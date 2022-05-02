import logging
import sched
import time

from backend.backend_consts import FRAME_TIME
from backend.logic.entity_logic import EntityManager, Combatant
from common.consts import EntityType, MIN_HEALTH, PROJECTILE_SPEED, MOB_SPEED


def server_controlled_entities_update(entities_manager: EntityManager, s):
    """update all projectiles and bots positions inside a loop"""
    # BUGFIX: deadlock when two mobs merge
    update_projectiles(entities_manager)
    update_mobs(entities_manager)
    s.enter(FRAME_TIME, 1, server_controlled_entities_update, (entities_manager, s,))


def update_projectiles(entities_manager: EntityManager):
    """Update projectile position, ttl and existence.
       In addition, lowers entities HP, and kill them if needed
       """
    to_remove = []
    with entities_manager.projectile_lock:
        for projectile in entities_manager.projectiles.values():
            projectile.ttl -= 1
            if projectile.ttl == 0:
                logging.debug(f"[debug] gonna remove uuid={projectile.uuid}, ttl=0")
                to_remove.append(projectile)
                continue

            intersection = entities_manager.get_collidables_with(projectile.pos, projectile.uuid,
                                                                 kind=EntityType.PROJECTILE)
            should_remove = False
            if intersection:
                for kind, identifier in intersection:
                    if kind == EntityType.PROJECTILE:
                        continue
                    if kind == EntityType.PLAYER or kind == EntityType.MOB:
                        combatant: Combatant = entities_manager.get(identifier, EntityType.MOB)
                        logging.info(f"Projectile {projectile} hit {combatant}")
                        should_remove = True
                        combatant.health -= projectile.damage
                        if combatant.health <= MIN_HEALTH:
                            logging.info(f"[update] killed {combatant=}")
                            # remove entity on
                            entities_manager.remove_entity(combatant)
                        logging.debug(f"Updated player {identifier} health to {combatant.health}")
                if should_remove:
                    to_remove.append(projectile)
                    logging.debug(f"[debug] gonna remove uuid={projectile.uuid}, nonzero intersection")
                    continue

            entities_manager.update_entity_location(projectile,
                                                    (
                                                        projectile.pos[0] + int(
                                                            PROJECTILE_SPEED * projectile.direction[0]),
                                                        projectile.pos[1] + int(
                                                            PROJECTILE_SPEED * projectile.direction[1])),
                                                    EntityType.PROJECTILE)
    for projectile in to_remove:
        entities_manager.remove_entity(projectile)
        logging.info(f"[update] removed projectile {projectile.uuid}")


def update_mobs(entities_manager: EntityManager):
    """Update mobs position. In addition, attack if mob is locked on target"""
    with entities_manager.mob_lock:
        for mob in entities_manager.mobs.values():
            mob.update_direction(entities_manager)
            colliding = entities_manager.get_collidables_with(mob.pos, mob.uuid, kind=EntityType.MOB)

            for kind, identifier in colliding:
                if kind == EntityType.PROJECTILE:
                    continue
                mob.direction = 0., 0.  # TODO: refactor a bit into update_mob_directions

            if mob.on_player:
                mob.item.on_click(mob, entities_manager)
                # attack(entities_manager, mob, mob.weapon)
            entities_manager.update_entity_location(mob, (mob.pos[0] + int(mob.direction[0] * MOB_SPEED),
                                                          mob.pos[1] + int(mob.direction[1] * MOB_SPEED)),
                                                    EntityType.MOB)


def server_entities_handler(entities_manager):
    """Starts the schedular and update entities functions"""
    s = sched.scheduler(time.time, time.sleep)
    s.enter(FRAME_TIME, 1, server_controlled_entities_update, (entities_manager, s,))
    s.run()

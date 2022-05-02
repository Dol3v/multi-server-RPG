import logging
import sched
import time

from backend.backend_consts import FRAME_TIME
from backend.logic.entity_logic import EntityManager


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
    with entities_manager.projectile_lock:
        to_remove = filter(lambda p: not p.advance_per_tick(entities_manager), entities_manager.projectiles.values())
        for projectile in to_remove:
            entities_manager.remove_entity(projectile)
            logging.info(f"[update] removed projectile {projectile.uuid}")


def update_mobs(entities_manager: EntityManager):
    """Update mobs position. In addition, attack if mob is locked on target"""
    with entities_manager.mob_lock:
        to_remove = filter(lambda m: not m.advance_per_tick(entities_manager), entities_manager.mobs.values())
        for mob in to_remove:
            entities_manager.remove_entity(mob)
            logging.info(f"[update] killed mob {mob.uuid}")


def server_entities_handler(entities_manager):
    """Starts the schedular and update entities functions"""
    s = sched.scheduler(time.time, time.sleep)
    s.enter(FRAME_TIME, 1, server_controlled_entities_update, (entities_manager, s,))
    s.run()

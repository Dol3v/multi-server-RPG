# multi-server-RPG
Advance multi server system, with RPG client
## Packet structure
Client update message
```
[pos(x, y), new_chat_msg, dir_bit, attacked, attack_dir, equipped_id]
```
Server update message
```
[tools, last_valid_pos, HP, entities in range]
entity
[enitity_id, pos, dir]
```

# Potential hacks
- spawn player on another entity near a wall, the player will jump out of the wall.


# multi-server-RPG
Advance multi server system, with RPG client
## Packet structure
Client update message
```
[pos(x, y), new_chat_msg, dir_bit, attacked, attack_dir, slot_index]
```
Server update message
```
[tools, new_chat_msg, last_valid_pos, HP, entities in range]
entity
[enitity_type, pos, dir_vector]
```
Data base structure
```
creds
chat
user_info (uuid, pos, direction, last_seqn, health, slot, tools (JSON))

```
redirect message
```
[go_to_addr]
```



# Potential hacks
- spawn player on another entity near a wall, the player will jump out of the wall.


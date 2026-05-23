# phbot-plugins

Personal collection of [phBot](https://www.elitepvpers.com/forum/sro-pserver-bots/) plugins for Silkroad Online.

## Plugins

| Plugin | Description |
| --- | --- |
| [`xControl.py`](./xControl.py) | Control a party of bots using in-game chat. A designated leader types commands and every bot running this plugin reacts (start/stop, teleport, follow, equip, party chat, packet injection, and more). |
| [`xMagicPop.py`](./xMagicPop.py) | Loop Magic Pop spins across your inventory. Auto-detects Magic Pop items, picks Flag/Devil/Angel × M/F, supports burst mode (delay = 0) or timed delay, cycle limit, and a live status panel. |

---

## xMagicPop

Magic Pop spinner. Sends Magic Pop "play" packets (`C->S 0x7118`) for every Magic Pop item in your inventory, in a loop.

### Install

1. Copy `xMagicPop.py` into your phBot `Plugins/` folder.
2. Restart phBot (or use **Reload Plugins**).
3. Open the **xMagicPop** tab.

### Usage

1. **Magic Pop Type** — pick the booth you're at: `Flag Male / Flag Female / Devil Male / Devil Female / Angel Male / Angel Female`.
2. **Delay (sec)** — `0` means **burst mode** (~15 sends per event tick, as fast as the script engine). Set a positive number for a steady one-per-interval send.
3. **Stop after cycles** — `0` = forever, otherwise stops after N full passes over your inventory.
4. **Only play on Magic Pop items** — when checked (default), the loop skips empty slots and any non-Magic-Pop items. Matches inventory items whose `servername` contains `MAGIC_POP`.
5. Click **Refresh Inventory** if you just grabbed/dropped items, then **START**. The right-hand list shows every slot in the Magic Pop range; rows marked `[POP]` are the ones that will be played.

### Buttons

| Button | Action |
| --- | --- |
| `START` | Start the loop (auto-refreshes inventory first). |
| `STOP` | Stop the loop. |
| `SEND ONE` | Send a single packet for the current slot. |
| `RESET` | Zero attempts / cycles / current slot. |
| `Refresh Inventory` | Re-read inventory and rebuild the slot list. |

### Packet format

```
opcode  : 0x7118
payload : F5 05 00 00  <type:1>  00 00 00  <slot:1>  00
```

`<type>` is `01/04/05/06/07/08` (Flag M/F, Devil M/F, Angel M/F). `<slot>` is the inventory slot byte.

---

## xControl

Originally written by **JellyBitz**, extended with extra commands and a redesigned in-plugin UI.

### Install

1. Copy `xControl.py` into your phBot `Plugins/` folder.
2. Restart phBot (or use **Reload Plugins**).
3. Open the **xControl** tab in phBot and add party-leader names to the **Party Leaders** list on the right.
4. Any chat message from a configured leader (or from a Discord webhook, chat type 100) will be parsed as a command.

### How it works

- Commands are **UPPERCASE** keywords sent via in-game chat by a leader.
- Each bot running the plugin parses incoming chat from its **Party Leaders** list and reacts.
- Arguments use spaces; some commands accept comma separation as well.
- The plugin also exposes a few script commands (`chat`, `pinvite`, `wait_party`, `use_scroll`, `leaveparty`) for `.txt` walk scripts.

### Syntax convention

```
COMMAND  #required  #optional?
```

`#name` means a required argument, `#name?` means optional.

---

## Command reference

### Bot / session

| Command | Description | Example |
| --- | --- | --- |
| `START` | Start the bot | `START` |
| `STOP` | Stop the bot | `STOP` |
| `DC` | Disconnect from game | `DC` |
| `PROFILE #Name?` | Load profile (default: `Default`) | `PROFILE PvP` |
| `GETOUT` | Leave the party | `GETOUT` |

### Trace / follow

| Command | Description | Example |
| --- | --- | --- |
| `TRACE #Player?` | Trace leader or specified player | `TRACE Vette` |
| `NOTRACE` | Stop trace | `NOTRACE` |
| `FOLLOW #Player? #Distance?` | Follow a party player (no attack). `FOLLOW` follows sender at distance 10; `FOLLOW 0` is exact trace. | `FOLLOW Vette 5` |
| `NOFOLLOW` | Stop following | `NOFOLLOW` |

### Movement / teleport

| Command | Description | Example |
| --- | --- | --- |
| `MOVEON #Radius?` | Random movement (default radius 10) | `MOVEON 20` |
| `RETURN` | Use Return Scroll (or resurrect if dead) | `RETURN` |
| `RECALL #Town` | Set recall on city portal | `RECALL Constantinople` |
| `TP #Destination #Source?` | Teleport. Source auto-detected from nearby NPCs if omitted. | `TP Hotan` or `TP Hotan, Jangan` |
| `REVERSE #Type #Name?` | Reverse return. Types: `return` / `death` / `player` / `zone`. | `REVERSE player Vette` |
| `R #Player` | Shortcut for `REVERSE player #Player` | `R Vette` |
| `GETPOS` | Whisper current position back to leader | `GETPOS` |

### Training area

| Command | Description | Example |
| --- | --- | --- |
| `SETPOS #X? #Y? #Region? #Z?` | Set training position (current if no args) | `SETPOS 6537 1234` |
| `SETRADIUS #Radius?` | Set training radius (resets to 35 if no arg) | `SETRADIUS 50` |
| `SETSCRIPT #Path?` | Change training script path (clear if no arg) | `SETSCRIPT C:\scripts\hotan.txt` |
| `SETAREA #Name` | Change training area by config name | `SETAREA Hotan East` |

### Combat / emotes

| Command | Description | Example |
| --- | --- | --- |
| `ZERK` | Use Berserker mode | `ZERK` |
| `SIT` | Sit / stand up (toggle) | `SIT` |
| `JUMP` | Knockback emote | `JUMP` |
| `CAPE #Color?` | PVP cape. Colors: `off / red / gray / blue / white / yellow` (default `yellow`). | `CAPE red` |

### Pets / mounts

| Command | Description | Example |
| --- | --- | --- |
| `MOUNT #PetType?` | Mount horse (default). Pet types: `horse / transport / attack / fellow`. | `MOUNT transport` |
| `DISMOUNT #PetType?` | Dismount horse (default) or pet | `DISMOUNT attack` |
| `TERMINATE` | Unsummon transport pets (horse + caravan/trade); keeps grab/attack pets. | `TERMINATE` |

### Items

| Command | Description | Example |
| --- | --- | --- |
| `EQUIP #ItemName` | Equip item (partial name OK). Aliases: `TRADER / HUNTER / THIEF / JOB`. | `EQUIP Steel Sword` |
| `UNEQUIP #ItemName` | Unequip item (partial name OK). Same aliases. | `UNEQUIP HUNTER` |
| `USE #ItemName` | Use item from inventory (partial name) | `USE HP Potion` |

### Chat / packets

| Command | Description | Example |
| --- | --- | --- |
| `CHAT #Type #Message` | Send a chat message. Simple types: `all / party / guild / union / global / stall`. With target: `private #Name #Msg` / `note #Name #Msg`. | `CHAT party Ready!` |
| `INJECT #Opcode #Encrypted? #Data?` | Inject a raw packet. Opcode in hex; `Encrypted` is `true`/`false` (default `false`); data is space-separated hex bytes (omit for empty payload). | `INJECT 0x70A7 false 01` |

---

## Script commands

`xControl` also exposes commands for phBot walk-script files (`.txt`):

- `chat,<type>,<message>` — e.g. `chat,party,START`, `chat,all,GETOUT`
- `chat,private,<name>,<message>` — e.g. `chat,private,Vette,hi there`
- `pinvite,<Name1>[,<Name2>,...]` — find nearby players by name and invite to party (creates one if none).
- `wait_party,<Count>[,<TimeoutMs>]` — block the script until the party has at least `Count` members, or until timeout (default 60s).
- `use_scroll,<keyword>` — use the first item whose name contains `<keyword>` (case-insensitive). Searches main inventory and the grab-pet inventory (pulls into main first if found there).
- `leaveparty` — leaves the current party.

---

## Credits

- Original plugin: [JellyBitz](https://github.com/JellyBitz/phBot-xPlugins)
- Extensions & UI redesign: [Vette1123](https://github.com/Vette1123)

## License

MIT

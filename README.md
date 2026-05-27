# phbot-plugins

Personal collection of [phBot](https://www.elitepvpers.com/forum/sro-pserver-bots/) plugins for Silkroad Online by **Gado** ([Vette1123](https://github.com/Vette1123)).

## Plugins

| Plugin | Description |
| --- | --- |
| [`xControl.py`](./xControl.py) | Control a party of bots via in-game chat. A designated leader types commands and every bot running this plugin reacts (start/stop, teleport, follow, equip, sort inventory, party chat, packet injection, and more). |
| [`xCaravan.py`](./xCaravan.py) | Auto-Caravan / job route runner with full UI dashboard. Watches box count, equips/unequips the job suit, casts the Caravan Bugle, walks a Thief / Hunter / Trader route, settles trading, terminates transport, and either returns home or reverse-recalls to the start point. Includes live stats panel (runs, goods/h, stones/arena/gold per hour, ETA to next run), trader trade-lockdown safety, training-area gate, and chat-command control via `xControl`. Per-character config. |
| [`xAutoConfig.py`](./xAutoConfig.py) | Per-character profile/config switcher. Auto-loads the right phBot config, training script, and DB3 sidecar files when a character logs in, so multi-account setups boot into the correct profile without manual swaps. |
| [`xMagicPop.py`](./xMagicPop.py) | Magic Pop spinner. Loops Magic Pop "play" packets across every Magic Pop item in your inventory (Flag / Devil's Spirit S / Angel's Spirit S, M/F), with burst or timed delay and a live status panel. |
| [`xShining.py`](./xShining.py) | iSRO fully-automatic lightstone crafting. Finds Blue/Black Stone anywhere in inventory and loops the recipe packet until depleted, with configurable speed and a broken-stones counter. |
| [`xPacketTool.py`](./xPacketTool.py) | Packet inspector / injector. Send raw client or server packets, with a filter list to log only the opcodes you care about. |
| [`xNotify.py`](./xNotify.py) | Push live status alerts to **Telegram** and/or **Discord** — death, bot stopped, attacked, out of HP/MP potions, PMs, global/notice chat, unique sightings, and xCaravan trade start/settle. Per-event toggles, throttling, and a shared config read by every bot process. Each alert is labelled `[game • character]` so you know which bot fired it. |

---

## xControl

Originally written by **JellyBitz**, extended with extra commands and a redesigned in-plugin UI.

### Install

1. Copy `xControl.py` into your phBot `Plugins/` folder.
2. Restart phBot (or use **Reload Plugins**).
3. Open the **xControl** tab and add party-leader names to the **Party Leaders** list on the right.
4. Any chat message from a configured leader (or from a Discord webhook, chat type 100) is parsed as a command.

### How it works

- Commands are **UPPERCASE** keywords sent via in-game chat by a leader.
- Each bot running the plugin parses incoming chat from its **Party Leaders** list and reacts.
- Arguments use spaces; some commands accept comma separation as well.
- The plugin also exposes script commands (`chat`, `pinvite`, `wait_party`, `use_scroll`, `leaveparty`) for `.txt` walk scripts.

### Syntax convention

```
COMMAND  #required  #optional?
```

`#name` means a required argument, `#name?` means optional.

### Command reference

#### Bot / session

| Command | Description | Example |
| --- | --- | --- |
| `START` | Start the bot | `START` |
| `STOP` | Stop the bot | `STOP` |
| `DC` | Disconnect from game | `DC` |
| `PROFILE #Name?` | Load profile (default: `Default`) | `PROFILE PvP` |
| `GETOUT` | Leave the party | `GETOUT` |

#### Trace / follow

| Command | Description | Example |
| --- | --- | --- |
| `TRACE #Player?` | Trace leader or specified player | `TRACE Vette` |
| `NOTRACE` | Stop trace | `NOTRACE` |
| `FOLLOW #Player? #Distance?` | Follow a party player (no attack). `FOLLOW` follows sender at distance 10; `FOLLOW 0` is exact trace. Sender's own bot ignores the command so the master never chases himself. | `FOLLOW Vette 5` |
| `NOFOLLOW` | Stop following | `NOFOLLOW` |

#### Movement / teleport

| Command | Description | Example |
| --- | --- | --- |
| `MOVEON #Radius?` | Random movement (default radius 10) | `MOVEON 20` |
| `RETURN` | Use Return Scroll (or resurrect if dead) | `RETURN` |
| `RECALL #Town` | Set recall on city portal | `RECALL Constantinople` |
| `TP #Destination #Source?` | Teleport. Source auto-detected from nearby NPCs if omitted. | `TP Hotan` or `TP Hotan, Jangan` |
| `REVERSE #Type #Name?` | Reverse return. Types: `return` / `death` / `player` / `zone`. | `REVERSE player Vette` |
| `R #Player` | Shortcut for `REVERSE player #Player` | `R Vette` |
| `GETPOS` | Whisper current position back to leader | `GETPOS` |

#### Training area

| Command | Description | Example |
| --- | --- | --- |
| `SETPOS #X? #Y? #Region? #Z?` | Set training position (current if no args) | `SETPOS 6537 1234` |
| `SETRADIUS #Radius?` | Set training radius (resets to 35 if no arg) | `SETRADIUS 50` |
| `SETSCRIPT #Path?` | Change training script path (clear if no arg) | `SETSCRIPT C:\scripts\hotan.txt` |
| `SETAREA #Name` | Change training area by config name | `SETAREA Hotan East` |

#### Combat / emotes

| Command | Description | Example |
| --- | --- | --- |
| `ZERK` | Use Berserker mode | `ZERK` |
| `SIT` | Sit / stand up (toggle) | `SIT` |
| `JUMP` | Knockback emote | `JUMP` |
| `CAPE #Color?` | PVP cape. Colors: `off / red / gray / blue / white / yellow` (default `yellow`). | `CAPE red` |

#### Pets / mounts

| Command | Description | Example |
| --- | --- | --- |
| `MOUNT #PetType?` | Mount horse (default). Pet types: `horse / transport / attack / fellow`. | `MOUNT transport` |
| `DISMOUNT #PetType?` | Dismount horse (default) or pet | `DISMOUNT attack` |
| `TERMINATE` | Unsummon transport pets (horse + caravan/trade); keeps grab/attack pets. | `TERMINATE` |

#### Items

| Command | Description | Example |
| --- | --- | --- |
| `EQUIP #ItemName` | Equip item (partial name OK). Aliases: `TRADER / HUNTER / THIEF / JOB`. | `EQUIP Steel Sword` |
| `UNEQUIP #ItemName` | Unequip item (partial name OK). Same aliases. | `UNEQUIP HUNTER` |
| `USE #ItemName` | Use item from inventory (partial name) | `USE HP Potion` |
| `SORT` | Sort inventory (calls phBot's `sort_inventory()`) | `SORT` |

#### Plugins

| Command | Description | Example |
| --- | --- | --- |
| `CARAVAN ON/OFF` | Enable / disable the xCaravan plugin | `CARAVAN ON` |
| `CARAVAN STATUS` | Log xCaravan state, pouch count, armed flag, scan ETA | `CARAVAN STATUS` |
| `CARAVAN SCAN` | Force xCaravan to rescan inventory now | `CARAVAN SCAN` |
| `CARAVAN GO` | Force xCaravan to start a route immediately (if armed) | `CARAVAN GO` |

#### Chat / packets

| Command | Description | Example |
| --- | --- | --- |
| `CHAT #Type #Message` | Send chat. Simple types: `all / party / guild / union / global / stall`. With target: `private #Name #Msg` / `note #Name #Msg`. | `CHAT party Ready!` |
| `INJECT #Opcode #Encrypted? #Data?` | Inject a raw packet. Opcode in hex; `Encrypted` is `true`/`false` (default `false`); data is space-separated hex bytes (omit for empty payload). | `INJECT 0x70A7 false 01` |

### Script commands

`xControl` also exposes commands for phBot walk-script files (`.txt`):

- `chat,<type>,<message>` — e.g. `chat,party,START`, `chat,all,GETOUT`
- `chat,private,<name>,<message>` — e.g. `chat,private,Vette,hi there`
- `pinvite,<Name1>[,<Name2>,...]` — find nearby players by name and invite to party (creates one if none).
- `wait_party,<Count>[,<TimeoutMs>]` — block the script until the party has at least `Count` members, or until timeout (default 60s).
- `use_scroll,<keyword>` — use the first item whose name contains `<keyword>` (case-insensitive). Searches main inventory and the grab-pet inventory (pulls into main first if found there).
- `leaveparty` — leaves the current party.

---

## xCaravan

Auto-Caravan controller with a live stats dashboard. Watches your pouch count, equips the job suit, casts **Job - Caravan Bugle**, runs an embedded **Thief**, **Hunter**, or **Trader** route script (Jangan → Donwhang via ferry; the Hunter variant does a short Jangan loop, the Trader variant auto-target-trades via direct packet injection at the start/settle NPCs), settles target trading, terminates the transport, and either uses a return scroll or reverse-recalls to the start point. Config and stats are persisted per character.

### Install

1. Copy `xCaravan.py` into your phBot `Plugins/` folder.
2. Restart phBot or **Reload Plugins**.
3. Open the **xCaravan** tab.

### Key features

- **Live stats dashboard** — runs completed, goods/h, stones/h, arena coins/h, gold/h (all rates derived from completed-run deltas, not extrapolated samples), avg & best run time, ETA to next pouch-full, session uptime, and a `↻ Reset Counters` button.
- **Trader trade-lockdown** — once the trader role starts injecting target-trade packets, the plugin freezes all other actions (no teleports, no NPCs, no stop/start, no reverse) until the settle packet completes. Hard timeout 90s. Keeps the script running through `terminate,transport` → `use,returnscroll` naturally.
- **Armed gate** — plugin only auto-acts while the character is at the configured training area, so it stays passive when you're idling in town.
- **Bot-running gate** — auto-trigger only fires while phBot is actually botting (`get_status()` non-empty). If the bot is stopped, the plugin sits in `idle · bot not running` and waits — start the bot from phBot's main UI (or via `xControl`'s `START` chat command) and the next scan tick picks up the route. Manual buttons (`🚀 START`, `📜 Run script`, `CARAVAN GO`) are not gated.
- **Robust scanning** — scans continue across all non-route states (not just `idle`), with empty-inventory backoff and edge-detected immediate rescans.
- **xControl chat integration** — `CARAVAN ON/OFF/STATUS/SCAN/GO` from a party leader (authorized via xControl's leader list).
- **Sort inventory before reverse** — calls phBot's `sort_inventory()` to compact items before the recall.

### UI fields

| Field | Default | Meaning |
| --- | --- | --- |
| **🟢 ENABLE PLUGIN** | off | Master switch for the automation loop. |
| **🤖 Start bot after** | on | After the route finishes (and the suit is unequipped, if enabled), start the bot. |
| **🧺 Unequip after** | on | Unequip the job suit at the end of the route. Turn off to stay in suit. |
| **🌀 Reverse to recall after** | off | After the route completes, reverse-recall to the route's start point instead of a plain return scroll. |
| **🎭 Role** | Thief | Which embedded route to run: `⚔ Thief` / `🏹 Hunter` / `💰 Trader`. The Trader route auto-target-trades via packet injection and force-stops at the destination. |
| **📦 Goods item** | `Trader Sack Lv 4` | Substring match for the goods item to count (aliases include `special box`, `specialty goods`, `magic silverbag`). |
| **Run at** | `1` | Run the route once pouch count reaches this value. |
| **Scan (ms)** | `30000` | Inventory scan interval while idle. |
| **🚚 Job suit** | `Trader` | Substring used to find your job suit. |
| **Min boxes** | `20` | Minimum pouch count required to attempt the final Jangan run after teleports. |
| **Route TPs** | `3` | Final teleport hops allowed at end of route. |
| **Action (ms)** | `3500` | Generic per-action delay (equip/unequip waits, etc.). |

### Buttons

| Button | Action |
| --- | --- |
| `💾 Save` | Persist current GUI values to `Plugins/Config/xCaravan_<character>.json`. |
| `🔎 Scan` | Force an inventory read; updates **Pouch** / **Suit** / **Status** rows. |
| `🚀 START` | Manually start the route. |
| `🛑 STOP` | Cancel the current state and stop the script. |
| `📜 Run script` | Skip the wait and execute the route script immediately. |
| `🌀 Reverse now` | Trigger a reverse-recall back to the route start point on demand. |
| `↻ Reset` | Reset stats counters (runs, deltas, baselines, fill duration). |

### Stats panel

Two-row dashboard below the status block:

```
📊 Goods/h  ⏱ Next  🏁 Runs  ⌛ Avg  ⭐ Best
💎 Stones (n/h)  🪙 Arena (n/h)  💰 Gold (+n/h)  ⏲ Up   ↻ Reset
```

- Per-hour rates show `--` until the first run completes, then settle to actual session rates.
- **⏱ Next** uses the *measured* fill duration from the first complete fill cycle, not an extrapolation.
- **💰 Gold** display uses compact suffixes (`12.3k`, `1.2M`).

### Chat commands (via xControl)

If `xControl` is installed and the sender is in the leader list:

| Command | Action |
| --- | --- |
| `CARAVAN ON` | Enable the plugin and persist config |
| `CARAVAN OFF` | Disable the plugin |
| `CARAVAN STATUS` | Log state / pouch count / armed / scan ETA / lockdown |
| `CARAVAN SCAN` | Force an inventory rescan |
| `CARAVAN GO` | Force a route to start now (if armed and not already in route) |

### Flow

```
idle → (pouch ≥ Run-at) → equip suit → cast Caravan Bugle
     → walk route → settletargettrading → terminate transport
     → sort_inventory → use returnscroll / reverse_return
     → unequip suit → (optionally) start bot → idle
```

---

## xMagicPop

Magic Pop spinner. Sends Magic Pop "play" packets (`C->S 0x7118`) for every Magic Pop item in your inventory, in a loop.

### Install

1. Copy `xMagicPop.py` into your phBot `Plugins/` folder.
2. Restart phBot (or use **Reload Plugins**).
3. Open the **xMagicPop** tab.

### Usage

1. **Magic Pop Type** — pick the booth you're at: `Flag (M) / Flag (F) / Devil's Spirit S grade (M) / Devil's Spirit S grade (F) / Angel's Spirit S grade (M) / Angel's Spirit S grade (F)`.
2. **Delay (sec)** — `0` means **burst mode** (~15 sends per event tick, as fast as the script engine). Set a positive number for a steady one-per-interval send.
3. **Stop after cycles** — `0` = forever, otherwise stops after N full passes over your inventory.
4. **Only play on Magic Pop items** — when checked (default), the loop skips empty slots and any non-Magic-Pop items. Matches items whose `servername` contains `MAGIC_POP`.
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

## xShining

iSRO fully-automatic lightstone crafting. Scans inventory for any Blue Stone + Black Stone pair (anywhere in your bags, not a fixed slot), and loops the `MK_RC_TRADE_MATERIAL_LIGHTSTONE` recipe packet (`C->S 0x7538`) until one of the stones runs out. Counts broken stones from server response `0xB538`.

### Install

1. Copy `xShining.py` into your phBot `Plugins/` folder.
2. Restart phBot or **Reload Plugins**.
3. Open the **xShining** tab.

### Usage

1. Place at least one stack each of **Blue Stone** and **Black Stone** anywhere in your inventory.
2. Set **Speed (ms)** — minimum `100`, default `250`. Lower is faster.
3. Click **Start Crafting**. The status label shows `Running...` / `Searching for stones...` / `Waiting for inventory...` as it progresses, and **Broken Stones** ticks up on each server confirmation.
4. The loop auto-stops after `Stones depleted` (10 misses) or `Inventory unreadable` (30 retries).

### Buttons

| Button | Action |
| --- | --- |
| `Start Crafting` | Begin the craft loop (spawns a background thread). |
| `Stop` | Stop the loop. |

---

## xNotify

Push live status alerts from your bot(s) to **Telegram** and/or **Discord**. Built for
multi-account setups: every bot process reads the same shared config and every message is
prefixed with `[game • character]`, so one channel shows you exactly which bot did what.

### Install

1. Copy `xNotify.py` into your phBot `Plugins/` folder.
2. Restart phBot (or use **Reload Plugins**).
3. Open the **xNotify** tab, fill in your Telegram and/or Discord fields (below), tick the
   events you want, click **Save**, then **Send Test**.

You only need to fill in the channel(s) you want — leave the other blank to disable it.
Configure once: all your bots share the same `xNotify.json` next to the plugin.

### Events

| Alert | Trigger |
| --- | --- |
| ⚠️ Death | your character's HP hits 0 |
| 🛑 Bot stop | botting/training stops |
| ⚔️ Attacked | another player attacks you *(packet parser — see notes)* |
| 🩸 HP pots out | HP (or Vigor) potions reach 0 in inventory |
| 🔵 MP pots out | MP (or Vigor) potions reach 0 in inventory |
| ✉️ PM | someone whispers you (sent immediately, no throttle) |
| 📢 Global | global chat message |
| 📜 Notice | server notice |
| 👑 Unique | a global/notice whose text matches a unique keyword |
| 📦 Trade start | xCaravan begins a trade run |
| ✅ Trade settle | xCaravan completes/settles the target trade |

Noisy events (everything except PM) share a configurable **cooldown** so you don't get
spammed. Death, bot-stop, and pots-out are edge-triggered (fire once on the transition).

### Getting your Telegram fields

**Bot token**

1. In Telegram, message [@BotFather](https://t.me/BotFather) → send `/newbot`.
2. Pick a name and a username ending in `bot`.
3. BotFather replies with a token like `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. That's your **token**.

**Chat id** (for a channel)

1. Add your bot to the channel as an **Administrator** with **Post Messages** enabled
   (Channel → Manage → Administrators → Add Admin → your bot).
2. Post any message in the channel.
3. Open in a browser (replace `<TOKEN>`): `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find `"chat":{"id":-1001234567890, ... "type":"channel"}` — that `id` (the full `-100…`
   number) is your **chat id**.

> Tip: forwarding a channel message to [@userinfobot](https://t.me/userinfobot) also shows
> the id, but if it gives `-1234567890` you must use the Bot-API form: drop the leading `-`
> and prepend `-100`, e.g. `1234567890` → `-1001234567890`.

For a private chat (not a channel), just message your bot first, then read the same
`getUpdates` URL and use the positive `chat.id`.

### Getting your Discord webhook

1. In Discord: **Server Settings → Integrations → Webhooks → New Webhook** (or a channel's
   **Edit Channel → Integrations → Webhooks**).
2. Pick the target channel, click **Copy Webhook URL**.
3. Paste it into the **Discord webhook** field. (xNotify sends a normal `User-Agent`, so
   Cloudflare won't block it.)

### Config file (`xNotify.json`)

Saved next to the plugin and shared by every bot process. Fields: `telegram_token`,
`telegram_chat_id`, `discord_webhook`, `cooldown_sec`, per-event `events` toggles, and
`unique_keywords`. **Add your server's unique monster names** (or its announcement wording)
to `unique_keywords` so 👑 Unique fires for your server, e.g.:

```json
"unique_keywords": ["unique", "Tiger Girl", "Uruchi", "Isyutaru", "Lord Yarkan"]
```

### For other plugins

Any plugin can emit an alert through xNotify:

```python
try:
    import xNotify
    xNotify.notify('trade_start', 'Trade run started')   # force=True to skip throttle
except Exception:
    pass
```

### Notes / verify on your server

- **Out-of-potions** detects recovery items by phBot item type ids (`tid1=3, tid2=1`,
  `tid3` 1=HP / 2=MP / 3=Vigor), with a name fallback (`"…Potion"` / `"Vigor"`). Confirm by
  letting a stack run dry once.
- **Attacked** ships with a placeholder opcode (`0xB070`); finish it by capturing a real
  player attack with `xPacketTool` to confirm the opcode and source/target offsets.
- **Game name** uses `get_character_data()`'s server/region field, falling back to the
  loaded profile filename (e.g. `vSRO`).

---

## Credits

- All plugins maintained by **Gado** — [github.com/Vette1123](https://github.com/Vette1123)
- `xControl`, `xAutoConfig`, and `xPacketTool` originally by [JellyBitz](https://github.com/JellyBitz/phBot-xPlugins); extended, rewritten, and maintained here by Gado.
- `xCaravan`, `xMagicPop`, `xShining`, `xNotify` written by Gado.

## License

MIT

from phBot import *
from threading import Timer
import phBotChat
import QtBind
import struct
import random
import json
import os
import sqlite3
import time

pName = 'xControl'
pVersion = '1.9.1'
pUrl = 'https://raw.githubusercontent.com/JellyBitz/phBot-xPlugins/master/xControl.py'

# ______________________________ Initializing ______________________________ #

# Globals
inGame = None
followActivated = False
followPlayer = ''
followDistance = 0

# Graphic user interface
gui = QtBind.init(__name__,pName)
QtBind.createLabel(gui,'Control your party using in-game chat. Leader writes commands and your character will follow it.',11,11)

QtBind.createLabel(gui,'Syntax:  COMMAND  #required  #optional?   —   scroll the list below for all commands',11,30)

# Leaders panel (top-right) — compact, labelled
QtBind.createLabel(gui,'── Party Leaders ──',525,11)
tbxLeaders = QtBind.createLineEdit(gui,"",525,30,110,20)
lstLeaders = QtBind.createList(gui,525,53,110,242)
btnAddLeader = QtBind.createButton(gui,'btnAddLeader_clicked',"    Add   ",635,29)
btnRemLeader = QtBind.createButton(gui,'btnRemLeader_clicked',"     Remove     ",635,52)

# Scrollable command reference — single tall list, fills most of the panel.
QtBind.createLabel(gui,'  ── Command Reference ──',11,48)
lstCommands = QtBind.createList(gui,11,65,500,230)

_commandHelp = [
	'━━━━━━  BOT / SESSION  ━━━━━━',
	'  START                       ► Start the bot',
	'      ex › START',
	'  STOP                        ► Stop the bot',
	'      ex › STOP',
	'  DC                          ► Disconnect from game',
	'      ex › DC',
	'  PROFILE  #Name?             ► Load profile (default: Default)',
	'      ex › PROFILE PvP',
	'      ex › PROFILE              (loads "Default")',
	'  GETOUT                      ► Leave the party',
	'      ex › GETOUT',
	'',
	'━━━━━━  TRACE / FOLLOW  ━━━━━━',
	'  TRACE  #Player?             ► Trace leader or specified player',
	'      ex › TRACE                (traces the command sender)',
	'      ex › TRACE Vette',
	'  NOTRACE                     ► Stop trace',
	'      ex › NOTRACE',
	'  FOLLOW  #Player? #Distance? ► Follow party player (no attack)',
	'      ex › FOLLOW               (follow sender at distance 10)',
	'      ex › FOLLOW 0             (exact trace sender, distance 0)',
	'      ex › FOLLOW Vette 5',
	'  NOFOLLOW                    ► Stop following',
	'      ex › NOFOLLOW',
	'',
	'━━━━━━  MOVEMENT / TELEPORT  ━━━━━━',
	'  MOVEON  #Radius?            ► Random movement (default radius 10)',
	'      ex › MOVEON               (uses default radius)',
	'      ex › MOVEON 20',
	'  RETURN                      ► Use Return Scroll (or resurrect if dead)',
	'      ex › RETURN',
	'  RECALL  #Town               ► Set recall on city portal',
	'      ex › RECALL Constantinople',
	'      ex › RECALL Jangan',
	'  TP  #Destination #Source?   ► Teleport to destination',
	'      • Source auto-detected from nearby NPCs if omitted',
	'      ex › TP Hotan             (omit source → scan nearby NPCs)',
	'      ex › TP Constantinople    (auto-find Constantinople teleporter)',
	'      ex › TP Hotan, Jangan     (explicit: from Jangan to Hotan)',
	'      ex › TP Hotan Jangan      (space separator also works)',
	'  REVERSE  #Type #Name?       ► Reverse return',
	'      • types: return / death / player / zone',
	'      ex › REVERSE return',
	'      ex › REVERSE death',
	'      ex › REVERSE player Vette',
	'      ex › REVERSE zone Jangan',
	'  R  #Player                  ► Shortcut for REVERSE player #Player',
	'      ex › R Vette',
	'  GETPOS                      ► Print current position (whispered back)',
	'      ex › GETPOS',
	'',
	'━━━━━━  TRAINING AREA  ━━━━━━',
	'  SETPOS  #X? #Y? #Region? #Z? ► Set training position',
	'      ex › SETPOS               (uses your current position)',
	'      ex › SETPOS 6537 1234',
	'      ex › SETPOS 6537 1234 25000 50',
	'  SETRADIUS  #Radius?         ► Set training radius (default 35)',
	'      ex › SETRADIUS            (resets to 35)',
	'      ex › SETRADIUS 50',
	'  SETSCRIPT  #Path?           ► Change training script path',
	'      ex › SETSCRIPT            (clears the script)',
	'      ex › SETSCRIPT C:\\scripts\\hotan.txt',
	'  SETAREA  #Name              ► Change training area by config name',
	'      ex › SETAREA Hotan East',
	'',
	'━━━━━━  COMBAT / EMOTES  ━━━━━━',
	'  ZERK                        ► Use Berserker mode',
	'      ex › ZERK',
	'  SIT                         ► Sit / stand up (toggle)',
	'      ex › SIT',
	'  JUMP                        ► Knockback emote',
	'      ex › JUMP',
	'  CAPE  #Color?               ► Use PVP Cape',
	'      • off / red / gray / blue / white / yellow  (default: yellow)',
	'      ex › CAPE                 (uses yellow)',
	'      ex › CAPE red',
	'      ex › CAPE off',
	'',
	'━━━━━━  PETS / MOUNTS  ━━━━━━',
	'  MOUNT  #PetType?            ► Mount horse (default) or pet by type',
	'      • types: horse / transport / attack / fellow',
	'      ex › MOUNT                (omit → mounts horse)',
	'      ex › MOUNT horse',
	'      ex › MOUNT transport      (trade/job caravan)',
	'      ex › MOUNT attack         (attack pet)',
	'      ex › MOUNT fellow         (fellow pet)',
	'  DISMOUNT  #PetType?         ► Dismount horse (default) or pet',
	'      ex › DISMOUNT             (omit → dismounts horse)',
	'      ex › DISMOUNT horse',
	'      ex › DISMOUNT transport',
	'      ex › DISMOUNT attack',
	'  TERMINATE                   ► Unsummon transport pets (horse +',
	'                                caravan/trade); keeps grab/attack pets',
	'      ex › TERMINATE            (after mounting a trade caravan)',
	'      ex › TERMINATE            (also kills your horse summon)',
	'',
	'━━━━━━  ITEMS  ━━━━━━',
	'  EQUIP  #ItemName            ► Equip item (partial name OK)',
	'      • aliases: TRADER / HUNTER / THIEF / JOB',
	'      • partial name searches both display name & servername',
	'      ex › EQUIP Steel Sword    (partial — first match equipped)',
	'      ex › EQUIP TRADER         (equip trader job suit)',
	'      ex › EQUIP HUNTER         (equip hunter job suit)',
	'      ex › EQUIP THIEF          (equip thief job suit)',
	'      ex › EQUIP JOB            (equip any job suit found)',
	'  UNEQUIP  #ItemName          ► Unequip item (partial name OK)',
	'      • aliases: TRADER / HUNTER / THIEF / JOB',
	'      ex › UNEQUIP Helmet',
	'      ex › UNEQUIP TRADER',
	'      ex › UNEQUIP HUNTER',
	'      ex › UNEQUIP THIEF',
	'      ex › UNEQUIP JOB          (unequip any equipped job suit)',
	'  USE  #ItemName              ► Use item from inventory',
	'      • partial name; uses first matching item',
	'      ex › USE HP Potion',
	'      ex › USE Return Scroll',
	'      ex › USE Universal Pill',
	'  SORT                        ► Sort inventory (compact items)',
	'      ex › SORT',
	'',
	'━━━━━━  CHAT / PACKETS  ━━━━━━',
	'  CHAT  #Type #Message        ► Send a chat message',
	'      • simple types:  all / party / guild / union / global / stall',
	'      • with target:   private #Name #Msg    /    note #Name #Msg',
	'      ex › CHAT all Hello world',
	'      ex › CHAT party Ready!',
	'      ex › CHAT guild Stocking up at house',
	'      ex › CHAT union United team!',
	'      ex › CHAT global LFG Hotan',
	'      ex › CHAT stall SoX gear cheap',
	'      ex › CHAT private Vette hi there',
	'      ex › CHAT note Vette see you tomorrow',
	'  INJECT  #Opcode #Encrypted? #Data?  ► Inject raw packet',
	'      • Opcode in hex (0x….). Encrypted flag = true/false (default false)',
	'      • Data is space-separated hex bytes (omit for empty payload)',
	'      ex › INJECT 0x704F false 04        (SIT/stand)',
	'      ex › INJECT 0x7516 false 01        (red PVP cape)',
	'      ex › INJECT 0x70A7 false 01        (toggle Berserker)',
	'      ex › INJECT 0x3091 false 0c        (jump emote)',
	'      ex › INJECT 0x7061                 (leave party — no data)',
	'',
	'━━━━━━  PLUGINS  ━━━━━━',
	'  CARAVAN ON/OFF/STATUS/SCAN/GO  ► Control xCaravan (auto-caravan) plugin',
	'      ex › CARAVAN ON',
	'      ex › CARAVAN GO',
]
for _line in _commandHelp:
	QtBind.append(gui,lstCommands,_line)

# ______________________________ Methods ______________________________ #

# Return xControl folder path
def getPath():
	return get_config_dir()+pName+"\\"

# Return character configs path (JSON)
def getConfig():
	return getPath()+inGame['server'] + "_" + inGame['name'] + ".json"

# Check if character is ingame
def isJoined():
	global inGame
	inGame = get_character_data()
	if not (inGame and "name" in inGame and inGame["name"]):
		inGame = None
	return inGame

# Load default configs
def loadDefaultConfig():
	# Clear data
	QtBind.clear(gui,lstLeaders)

# Loads all config previously saved
def loadConfigs():
	loadDefaultConfig()
	if isJoined():
		# Check config exists to load
		if os.path.exists(getConfig()):
			data = {}
			with open(getConfig(),"r") as f:
				data = json.load(f)
			if "Leaders" in data:
				for nickname in data["Leaders"]:
					QtBind.append(gui,lstLeaders,nickname)

# Add leader to the list
def btnAddLeader_clicked():
	if inGame:
		player = QtBind.text(gui,tbxLeaders)
		# Player nickname it's not empty
		if player and not lstLeaders_exist(player):
			# Init dictionary
			data = {}
			# Load config if exist
			if os.path.exists(getConfig()):
				with open(getConfig(), 'r') as f:
					data = json.load(f)
			# Add new leader
			if not "Leaders" in data:
				data['Leaders'] = []
			data['Leaders'].append(player)
			# Replace configs
			with open(getConfig(),"w") as f:
				f.write(json.dumps(data, indent=4, sort_keys=True))
			QtBind.append(gui,lstLeaders,player)
			QtBind.setText(gui, tbxLeaders,"")
			log('Plugin: Leader added ['+player+']')

# Remove leader selected from list
def btnRemLeader_clicked():
	if inGame:
		selectedItem = QtBind.text(gui,lstLeaders)
		if selectedItem:
			if os.path.exists(getConfig()):
				data = {"Leaders":[]}
				with open(getConfig(), 'r') as f:
					data = json.load(f)
				try:
					# remove leader nickname from file if exists
					data["Leaders"].remove(selectedItem)
					with open(getConfig(),"w") as f:
						f.write(json.dumps(data, indent=4, sort_keys=True))
				except:
					pass # just ignore file if doesn't exist
			QtBind.remove(gui,lstLeaders,selectedItem)
			log('Plugin: Leader removed ['+selectedItem+']')

# Return True if nickname exist at the leader list
def lstLeaders_exist(nickname):
	nickname = nickname.lower()
	players = QtBind.getItems(gui,lstLeaders)
	for i in range(len(players)):
		if players[i].lower() == nickname:
			return True
	return False

# Inject teleport packet, using the source and destination name
def inject_teleport(source,destination):
	t = get_teleport_data(source, destination)
	if t:
		npcs = get_npcs()
		for key, npc in npcs.items():
			if npc['name'] == source or npc['servername'] == source:
				log("Plugin: Selecting teleporter ["+source+"]")
				# Teleport found, select it
				inject_joymax(0x7045, struct.pack('<I', key), False)
				# Start a timer to teleport in 2.0 seconds
				Timer(2.0, inject_joymax, (0x705A,struct.pack('<IBI', key, 2, t[1]),False)).start()
				Timer(2.0, log, ("Plugin: Teleporting to ["+destination+"]")).start()
				return
		log('Plugin: NPC not found. Wrong NPC name or servername')
	else:
		log('Plugin: Teleport data not found. Wrong teleport name or servername')

# Send message, Ex. "All Hello World!" or "private JellyBitz Hi!"
def handleChatCommand(msg):
	# Try to split message
	args = msg.split(' ',1)
	# Check if the format is correct and is not empty
	if len(args) != 2 or not args[0] or not args[1]:
		return
	# Split correctly the message
	t = args[0].lower()
	if t == 'private' or t == 'note':
		# then check message is not empty
		argsExtra = args[1].split(' ',1)
		if len(argsExtra) != 2 or not argsExtra[0] or not argsExtra[1]:
			return
		args.pop(1)
		args += argsExtra
	# Check message type
	sent = False
	if t == "all":
		sent = phBotChat.All(args[1])
	elif t == "private":
		sent = phBotChat.Private(args[1],args[2])
	elif t == "party":
		sent = phBotChat.Party(args[1])
	elif t == "guild":
		sent = phBotChat.Guild(args[1])
	elif t == "union":
		sent = phBotChat.Union(args[1])
	elif t == "note":
		sent = phBotChat.Note(args[1],args[2])
	elif t == "stall":
		sent = phBotChat.Stall(args[1])
	elif t == "global":
		sent = phBotChat.Global(args[1])
	if sent:
		log('Plugin: Message "'+t+'" sent successfully!')

# Move to a random position from the actual position using a maximum radius
def randomMovement(radiusMax=10):
	# Generating a random new point
	pX = random.uniform(-radiusMax,radiusMax)
	pY = random.uniform(-radiusMax,radiusMax)
	# Mixing with the actual position
	p = get_position()
	pX = pX + p["x"]
	pY = pY + p["y"]
	# Moving to new position
	move_to(pX,pY,p["z"])
	log("Plugin: Random movement to (X:%.1f,Y:%.1f)"%(pX,pY))

# Follow a player using distance. Return success
def start_follow(player,distance):
	# Don't follow self (master sending FOLLOW would otherwise target himself)
	me = get_character_data()
	if me and player and me.get('name','').lower() == player.lower():
		return False
	if party_player(player):
		global followActivated,followPlayer,followDistance
		followPlayer = player
		followDistance = distance
		followActivated = True
		return True
	return False

# Return True if the player is in the party
def party_player(player):
	players = get_party()
	if players:
		for p in players:
			if players[p]['name'] == player:
				return True
	return False

# Return point [X,Y] if player is in the party and near, otherwise return None
def near_party_player(player):
	players = get_party()
	if players:
		for p in players:
			if players[p]['name'] == player and players[p]['player_id'] > 0:
				return players[p]
	return None

# Calc the distance from point A to B
def GetDistance(ax,ay,bx,by):
	return ((bx-ax)**2 + (by-ay)**2)**0.5

# Stop follow player
def stop_follow():
	global followActivated,followPlayer,followDistance
	result = followActivated
	# stop
	followActivated = False
	followPlayer = ""
	followDistance = 0
	return result

# Try to summon a vehicle
def MountHorse():
	# search item with similar name or exact server name
	item = GetItemByExpression(lambda n,s: s.startswith('ITEM_COS_C_'),13)
	if item:
		UseItem(item)
		return True
	log('Plugin: Horse not found at your inventory')
	return False

# Try to mount pet by type, return success
def MountPet(petType):
	# just in case
	if petType == 'pick':
		return False
	elif petType == 'horse':
		return MountHorse()
	# get all summoned pets
	pets = get_pets()
	if pets:
		for uid,pet in pets.items():
			if pet['type'] == petType:
				p = b'\x01' # mount flag
				p += struct.pack('I',uid)
				inject_joymax(0x70CB,p, False)
				return True
	return False

# Try to dismount pet by type, return success
def DismountPet(petType):
	petType = petType.lower()
	# just in case
	if petType == 'pick':
		return False
	# get all summoned pets
	pets = get_pets()
	if pets:
		for uid,pet in pets.items():
			if pet['type'] == petType:
				p = b'\x00'
				p += struct.pack('I',uid)
				inject_joymax(0x70CB,p, False)
				return True
	return False

# Terminate ridden transports (mounts, trade caravans, new job-system caravans, etc).
# Whitelist: never touches grab ('pick') or attack pets ('attack','fellow').
_KEEP_PET_TYPES = ('pick','attack','fellow')
def _TerminatePetByType(petType):
	# Re-fetch pets fresh so we use the current uid (it can change after dismount)
	pets = get_pets()
	if not pets:
		return
	for uid,pet in pets.items():
		if pet['type'] == petType:
			# CLIENT_PET_TERMINATE: uint32 pet UID
			inject_joymax(0x7116,struct.pack('I',uid),False)
			return
def TerminatePet():
	pets = get_pets()
	count = 0
	if pets:
		for uid,pet in pets.items():
			if pet['type'] in _KEEP_PET_TYPES:
				continue
			# Dismount first if currently mounted on it
			p = b'\x00'
			p += struct.pack('I',uid)
			inject_joymax(0x70CB,p,False)
			# Defer the terminate so the dismount packet round-trips first
			# (sleeping here would block the chat callback thread)
			Timer(0.6, _TerminatePetByType, (pet['type'],)).start()
			count += 1
	return count

# Gets the NPC unique ID if the specified name is found near
def GetNPCUniqueID(name):
	NPCs = get_npcs()
	if NPCs:
		name = name.lower()
		for UniqueID, NPC in NPCs.items():
			NPCName = NPC['name'].lower()
			if name == NPCName:
				return UniqueID
	return 0

# Search an item by name or servername through lambda expression and return his information
def GetItemByExpression(_lambda,start=0,end=0):
	inventory = get_inventory()
	items = inventory['items']
	if end == 0:
		end = inventory['size']
	# check items between intervals
	for slot, item in enumerate(items):
		if start <= slot and slot <= end:
			if item:
				# Search by lambda
				if _lambda(item['name'],item['servername']):
					# Save slot location
					item['slot'] = slot
					return item
	return None

# Finds an empty slot, returns -1 if inventory is full
def GetEmptySlot():
	items = get_inventory()['items']
	# check the first empty
	for slot, item in enumerate(items):
		if slot >= 13:
			if not item:
				return slot
	return -1

# Injects item movement on inventory
def Inject_InventoryMovement(movementType,slotInitial,slotFinal,logItemName,quantity=0):
	p = struct.pack('<B',movementType)
	p += struct.pack('<B',slotInitial)
	p += struct.pack('<B',slotFinal)
	p += struct.pack('<H',quantity)
	log('Plugin: Moving item "'+logItemName+'"...')
	# CLIENT_INVENTORY_ITEM_MOVEMENT
	inject_joymax(0x7034,p,False)

# Try to equip item
def EquipItem(item):
	itemData = get_item(item['model'])
	# Check equipables only
	if itemData['tid1'] != 1:
		log('Plugin: '+item['name']+' cannot be equiped!')
		return
	# Check equipable type
	t = itemData['tid2']
	# garment, protector, armor, robe, light, heavy
	if t == 1 or t == 2 or t == 3 or t == 9 or t == 10 or t == 11:
		t = itemData['tid3']
		# head
		if t == 1:
			Inject_InventoryMovement(0,item['slot'],0,item['name'])
		# shoulders
		elif t == 2:
			Inject_InventoryMovement(0,item['slot'],2,item['name'])
		# chest
		elif t == 3:
			Inject_InventoryMovement(0,item['slot'],1,item['name'])
		# pants
		elif t == 4:
			Inject_InventoryMovement(0,item['slot'],4,item['name'])
		# gloves
		elif t == 5:
			Inject_InventoryMovement(0,item['slot'],3,item['name'])
		# boots
		elif t == 6:
			Inject_InventoryMovement(0,item['slot'],5,item['name'])
	# shields
	elif t == 4:
		Inject_InventoryMovement(0,item['slot'],7,item['name'])
	# accesories ch/eu
	elif t == 5 or t == 12:
		t = itemData['tid3']
		# earring
		if t == 1:
			Inject_InventoryMovement(0,item['slot'],9,item['name'])
		# necklace
		elif t == 2:
			Inject_InventoryMovement(0,item['slot'],10,item['name'])
		# ring
		elif t == 3:
			# Check if second ring slot is empty
			if not GetItemByExpression(lambda s,n: True,11):
				Inject_InventoryMovement(0,item['slot'],12,item['name'])
			else:
				Inject_InventoryMovement(0,item['slot'],11,item['name'])
	# weapon ch/eu
	elif t == 6:
		Inject_InventoryMovement(0,item['slot'],6,item['name'])
	# job
	elif t == 7:
		Inject_InventoryMovement(0,item['slot'],8,item['name'])
	# avatar
	elif t == 13:
		t = itemData['tid3']
		# hat
		if t == 1:
			Inject_InventoryMovement(36,item['slot'],0,item['name'])
		# dress
		elif t == 2:
			Inject_InventoryMovement(36,item['slot'],1,item['name'])
		# accesory
		elif t == 3:
			Inject_InventoryMovement(36,item['slot'],2,item['name'])
		# flag
		elif t == 4:
			Inject_InventoryMovement(36,item['slot'],3,item['name'])
	# devil spirit
	elif t == 14:
		Inject_InventoryMovement(36,item['slot'],4,item['name'])

# Try to unequip item
def UnequipItem(item):
	# find an empty slot
	slot = GetEmptySlot()
	if slot != -1:
		Inject_InventoryMovement(0,item['slot'],slot,item['name'])

# Try to use the item specified
def UseItem(item):
	# Create packet and inject it
	p = struct.pack('<B',item['slot'])
	loc = get_locale()

	tid = GetTIDFromItem(item['model'])
	if loc == 22: # vsro
		p += struct.pack('<H',tid)
	else:
		p += struct.pack('<I',tid)

	log('Plugin: Using item "'+item['name']+'"...')
	# CLIENT_INVENTORY_ITEM_USE
	inject_joymax(0x704C,p,True)

# Get Type ID from item
def GetTIDFromItem(itemId):
	conn = GetDatabaseConnection()
	c = conn.cursor()
	c.execute('SELECT cash_item, tid1, tid2, tid3 FROM items WHERE id=?',(itemId,))
	result = c.fetchone()
	# calculate TID
	result = result[0] + (3 * 4) + (result[1] * 32) + (result[2] * 128) + (result[3] * 2048)
	conn.close()
	return result

# Create a connection to database
def GetDatabaseConnection():
	bot_path = os.getcwd()
	# Load the server info
	data = {}
	locale = get_locale()
	# vSRO
	if locale == 22:
		with open(bot_path+"/vSRO.json","r") as f:
			data = json.load(f)
		# Match data with the current server name
		server = character_data['server']
		for k in data:
			servers = data[k]['servers']
			# Check if servers is in list
			if server in servers:
				# Scan data folder
				for path in os.scandir(bot_path+"/Data"):
					# Check databases only
					if path.is_file() and path.name.endswith(".db3"):
						# Connect to check if the data matches
						conn = sqlite3.connect(bot_path+"/Data/"+path.name)
						c = conn.cursor()
						c.execute('SELECT * FROM data WHERE k="path" AND v=?',(data[k]['path'],))
						if c.fetchone():
							# match found
							return conn
						else:
							conn.close()
	# iSRO
	elif locale == 18:
		return sqlite3.connect(bot_path+"/Data/iSRO.db3")
	# TrSRO
	elif locale == 56:
		return sqlite3.connect(bot_path+"/Data/TRSRO.db3")
	return None

# ______________________________ Events ______________________________ #

# Called when the bot successfully connects to the game server
def connected():
	global inGame
	inGame = None

# Called when the character enters the game world
def joined_game():
	loadConfigs()

# Track messages this bot sent via the script `chat` command, so we don't act on our own echoes
_selfSentChat = []

# All chat messages received are sent to this function
def handle_chat(t,player,msg):
	# Remove guild name from union chat messages
	if t == 11:
		msg = msg.split(': ',1)[1]
	# Track our own outgoing chat so we don't double-process, but let the leader
	# execute every command on himself. FOLLOW 0 self-target is blocked inside
	# start_follow, not here.
	key = (t, msg)
	if key in _selfSentChat:
		_selfSentChat.remove(key)
	# Check player at leader list or a Discord message
	if player and lstLeaders_exist(player) or t == 100:
		# Parsing message command
		if msg == "START":
			start_bot()
			log("Plugin: Bot started")
		elif msg == "STOP":
			stop_bot()
			log("Plugin: Bot stopped")
		elif msg.startswith("TRACE"):
			# deletes empty spaces on right
			msg = msg.rstrip()
			if msg == "TRACE":
				if start_trace(player):
					log("Plugin: Starting trace to ["+player+"]")
			else:
				msg = msg[5:].split()[0]
				if start_trace(msg):
					log("Plugin: Starting trace to ["+msg+"]")
		elif msg == "NOTRACE":
			stop_trace()
			log("Plugin: Trace stopped")
		elif msg.startswith("SETPOS"):
			# deletes empty spaces on right
			msg = msg.rstrip()
			if msg == "SETPOS":
				p = get_position()
				set_training_position(p['region'], p['x'], p['y'],p['z'])
				log("Plugin: Training area set to current position (X:%.1f,Y:%.1f)"%(p['x'],p['y']))
			else:
				try:
					# check arguments
					p = msg[6:].split()
					x = float(p[0])
					y = float(p[1])
					# auto calculated if is not specified
					region = int(p[2]) if len(p) >= 3 else 0
					z = float(p[3]) if len(p) >= 4 else 0
					set_training_position(region,x,y,z)
					log("Plugin: Training area set to (X:%.1f,Y:%.1f)"%(x,y))
				except:
					log("Plugin: Wrong training area coordinates!")
		elif msg == 'GETPOS':
			# Check current position
			pos = get_position()
			phBotChat.Private(player,'My position is (X:%.1f,Y:%.1f,Z:%1f,Region:%d)'%(pos['x'],pos['y'],pos['z'],pos['region']))
		elif msg.startswith("SETRADIUS"):
			# deletes empty spaces on right
			msg = msg.rstrip()
			if msg == "SETRADIUS":
				# set default radius
				radius = 35
				set_training_radius(radius)
				log("Plugin: Training radius reseted to "+str(radius)+" m.")
			else:
				try:
					# split and parse movement radius
					radius = int(float(msg[9:].split()[0]))
					# to absolute
					radius = (radius if radius > 0 else radius*-1)
					set_training_radius(radius)
					log("Plugin: Training radius set to "+str(radius)+" m.")
				except:
					log("Plugin: Wrong training radius value!")
		elif msg.startswith('SETSCRIPT'):
			# deletes empty spaces on right
			msg = msg.rstrip()
			if msg == 'SETSCRIPT':
				# reset script
				set_training_script('')
				log('Plugin: Training script path has been reseted')
			else:
				# change script to the path specified
				set_training_script(msg[9:])
				log('Plugin: Training script path has been changed')
		elif msg.startswith('SETAREA '):
			# deletes empty spaces on right
			msg = msg[8:]
			if msg:
				# try to change to specified area name
				if set_training_area(msg):
					log('Plugin: Training area has been changed to ['+msg+']')
				else:
					log('Plugin: Training area ['+msg+'] not found in the list')
		elif msg == "SIT":
			log("Plugin: Sit/Stand")
			inject_joymax(0x704F,b'\x04',False)
		elif msg == "JUMP":
			# Just a funny emote lol
			log("Plugin: Jumping!")
			inject_joymax(0x3091,b'\x0c',False)
		elif msg.startswith("CAPE"):
			# deletes empty spaces on right
			msg = msg.rstrip()
			if msg == "CAPE":
				log("Plugin: Using PVP Cape by default (Yellow)")
				inject_joymax(0x7516,b'\x05',False)
			else:
				# get cape type normalized
				cape = msg[4:].split()[0].lower()
				if cape == "off":
					log("Plugin: Removing PVP Cape")
					inject_joymax(0x7516,b'\x00',False)
				elif cape == "red":
					log("Plugin: Using PVP Cape (Red)")
					inject_joymax(0x7516,b'\x01',False)
				elif cape == "gray":
					log("Plugin: Using PVP Cape (Gray)")
					inject_joymax(0x7516,b'\x02',False)
				elif cape == "blue":
					log("Plugin: Using PVP Cape (Blue)")
					inject_joymax(0x7516,b'\x03',False)
				elif cape == "white":
					log("Plugin: Using PVP Cape (White)")
					inject_joymax(0x7516,b'\x04',False)
				elif cape == "yellow":
					log("Plugin: Using PVP Cape (Yellow)")
					inject_joymax(0x7516,b'\x05',False)
				else:
					log("Plugin: Wrong PVP Cape color!")
		elif msg == "ZERK":
			log("Plugin: Using Berserker mode")
			inject_joymax(0x70A7,b'\x01',False)
		elif msg == "RETURN":
			# Quickly check if is dead
			character = get_character_data()
			if character['hp'] == 0:
				# RIP
				log('Plugin: Resurrecting at town...')
				inject_joymax(0x3053,b'\x01',False)
			else:
				log('Plugin: Trying to use return scroll...')
				# Avoid high CPU usage with too many chars at the same time
				Timer(random.uniform(0.5,2),use_return_scroll).start()
		elif msg.startswith("TP"):
			# deletes command header and whatever used as separator
			msg = msg[3:]
			if not msg:
				return
			# select split char
			split = ',' if ',' in msg else ' '
			# extract arguments
			args = [a.strip() for a in msg.split(split) if a.strip()]
			if len(args) >= 2:
				# Explicit form: TP <source> <destination>
				inject_teleport(args[0],args[1])
			elif len(args) == 1:
				# Auto form: TP <destination> — scan nearby NPCs for one that offers this destination
				destination = args[0]
				npcs = get_npcs()
				found = False
				if npcs:
					for key,npc in npcs.items():
						source = npc['name']
						if get_teleport_data(source,destination):
							inject_teleport(source,destination)
							found = True
							break
						# also try servername in case map uses it
						source = npc['servername']
						if source and get_teleport_data(source,destination):
							inject_teleport(source,destination)
							found = True
							break
				if not found:
					log('Plugin: No nearby teleporter offers ['+destination+']')
		elif msg.startswith("INJECT "):
			msgPacket = msg[7:].split()
			msgPacketLen = len(msgPacket)
			if msgPacketLen == 0:
				log("Plugin: Incorrect structure to inject packet")
				return
			# Check packet structure
			opcode = int(msgPacket[0],16)
			data = bytearray()
			encrypted = False
			dataIndex = 1
			if msgPacketLen >= 2:
				enc = msgPacket[1].lower()
				if enc == 'true' or enc == 'false':
					encrypted = enc == "true"
					dataIndex +=1
			# Create packet data and inject it
			for i in range(dataIndex, msgPacketLen):
				data.append(int(msgPacket[i],16))
			inject_joymax(opcode,data,encrypted)
			# Log the info
			log("Plugin: Injecting packet...\nOpcode: 0x"+'{:02X}'.format(opcode)+" - Encrypted: "+("Yes" if encrypted else "No")+"\nData: "+(' '.join('{:02X}'.format(int(msgPacket[x],16)) for x in range(dataIndex, msgPacketLen)) if len(data) else 'None'))
		elif msg.startswith("CHAT "):
			handleChatCommand(msg[5:])
		elif msg.startswith("MOVEON"):
			if msg == "MOVEON":
				randomMovement()
			else:
				try:
					# split and parse movement radius
					radius = int(float(msg[6:].split()[0]))
					# to positive
					radius = (radius if radius > 0 else radius*-1)
					randomMovement(radius)
				except:
					log("Plugin: Movement maximum radius incorrect")
		elif msg.startswith("FOLLOW"):
			# default values
			charName = player
			distance = 10
			if msg != "FOLLOW":
				# Check params
				msg = msg[6:].split()
				try:
					# If first arg is numeric, treat it as distance and follow the sender
					if len(msg) >= 1:
						try:
							distance = float(msg[0])
							# charName stays as the sender (player)
						except ValueError:
							charName = msg[0]
							if len(msg) >= 2:
								distance = float(msg[1])
				except:
					log("Plugin: Follow distance incorrect")
					return
			# Start following
			if start_follow(charName,distance):
				log("Plugin: Starting to follow to ["+charName+"] using ["+str(distance)+"] as distance")					
		elif msg == "NOFOLLOW":
			if stop_follow():
				log("Plugin: Following stopped")
		elif msg.startswith("PROFILE"):
			if msg == "PROFILE":
				if set_profile('Default'):
					log("Plugin: Setting Default profile")
			else:
				msg = msg[7:]
				if set_profile(msg):
					log("Plugin: Setting "+msg+" profile")
		elif msg == "DC":
			log("Plugin: Disconnecting...")
			disconnect()
		elif msg.startswith("MOUNT"):
			# default value
			pet = "horse"
			if msg != "MOUNT":
				msg = msg[5:].split()
				if msg:
					pet = msg[0]
			# Try mount pet
			if MountPet(pet):
				log("Plugin: Mounting pet ["+pet+"]")
		elif msg.startswith("DISMOUNT"):
			# default value
			pet = "horse"
			if msg != "DISMOUNT":
				msg = msg[8:].split()
				if msg:
					pet = msg[0]
			# Try dismount pet
			if DismountPet(pet):
				log("Plugin: Dismounting pet ["+pet+"]")
		elif msg.startswith("TERMINATE"):
			# Terminates transport horse and trade pet (caravan) — grab/attack pets are left alone
			n = TerminatePet()
			if n:
				log("Plugin: Terminated "+str(n)+" transport(s)")
			else:
				log("Plugin: No transport pets to terminate")
		elif msg == "SORT":
			try:
				ok = sort_inventory()
				log("Plugin: Sorting inventory -> " + str(ok))
			except Exception as ex:
				log("Plugin: sort_inventory() failed: " + str(ex))
		elif msg == "GETOUT":
			# Check if has party
			if get_party():
				# Left it
				log("Plugin: Leaving the party..")
				inject_joymax(0x7061,b'',False)
		elif msg.startswith("RECALL "):
			msg = msg[7:]
			if msg:
				npcUID = GetNPCUniqueID(msg)
				if npcUID > 0:
					log("Plugin: Designating recall to \""+msg.title()+"\"...")
					inject_joymax(0x7059, struct.pack('I',npcUID), False)
		elif msg.startswith("EQUIP "):
			msg = msg[6:].strip().lower()
			if msg:
				# Job keyword aliases -> match against servername
				jobAliases = {
					'trader':'TRADER','trade':'TRADER',
					'hunter':'HUNTER',
					'thief':'THIEF',
					'job':'_JOB_',
				}
				if msg in jobAliases:
					key = jobAliases[msg]
					item = GetItemByExpression(lambda n,s: key in s.upper(),13)
				else:
					# Case-insensitive partial name / exact servername match
					item = GetItemByExpression(lambda n,s: msg in n.lower() or msg == s.lower(),13)
				if item:
					EquipItem(item)
				else:
					log('Plugin: EQUIP — no matching item in inventory for "'+msg+'"')
		elif msg.startswith("UNEQUIP "):
			msg = msg[8:].strip().lower()
			if msg:
				jobAliases = {
					'trader':'TRADER','trade':'TRADER',
					'hunter':'HUNTER',
					'thief':'THIEF',
					'job':'_JOB_',
				}
				if msg in jobAliases:
					key = jobAliases[msg]
					item = GetItemByExpression(lambda n,s: key in s.upper(),0,12)
				else:
					item = GetItemByExpression(lambda n,s: msg in n.lower() or msg == s.lower(),0,12)
				if item:
					UnequipItem(item)
				else:
					log('Plugin: UNEQUIP — no matching equipped item for "'+msg+'"')
		elif msg.startswith("R "):
			# Shortcut: "R <player>" -> reverse to player
			name = msg[2:].strip()
			if name and reverse_return(2,name):
				log('Plugin: Using reverse to player "'+name+'" location')
		elif msg.startswith("REVERSE "):
			# remove command
			msg = msg[8:]
			if msg:
				# check params
				msg = msg.split(' ',1)
				# param type
				if msg[0] == 'return':
					# try to use it
					if reverse_return(0,''):
						log('Plugin: Using reverse to the last return scroll location')
				elif msg[0] == 'death':
					# try to use it
					if reverse_return(1,''):
						log('Plugin: Using reverse to the last death location')
				elif msg[0] == 'player':
					# Check existing name
					if len(msg) >= 2:
						# try to use it
						if reverse_return(2,msg[1]):
							log('Plugin: Using reverse to player "'+msg[1]+'" location')
				elif msg[0] == 'zone':
					# Check existing zone
					if len(msg) >= 2:
						# try to use it
						if reverse_return(3,msg[1]):
							log('Plugin: Using reverse to zone "'+msg[1]+'" location')
		elif msg.startswith("USE "):
			# remove command
			msg = msg[4:]
			if msg:
				# search item with similar name or exact server name
				item = GetItemByExpression(lambda n,s: msg in n or msg == s,13)
				if item:
					UseItem(item)

# Called every 500ms
def event_loop():
	if inGame and followActivated:
		me = get_character_data()
		if me and me.get('name','').lower() == (followPlayer or '').lower():
			stop_follow()
			return
		player = near_party_player(followPlayer)
		# check if is near
		if not player:
			return
		# check distance to the player
		if followDistance > 0:
			p = get_position()
			playerDistance = round(GetDistance(p['x'],p['y'],player['x'],player['y']),2)
			# check if has to move
			if followDistance < playerDistance:
				# generate vector unit
				x_unit = (player['x'] - p['x']) / playerDistance
				y_unit = (player['y'] - p['y']) / playerDistance
				# distance to move
				movementDistance = playerDistance-followDistance
				log("Following "+followPlayer+"...")
				move_to(movementDistance * x_unit + p['x'],movementDistance * y_unit + p['y'],0)
		else:
			# Avoid negative numbers
			log("Following "+followPlayer+"...")
			move_to(player['x'],player['y'],0)

# ______________________________ Script Commands ______________________________ #

# Walk script command: chat,<type>,<message>
#                      chat,private,<name>,<message>
# Examples:
#   chat,party,START
#   chat,all,GETOUT
#   chat,private,JellyBitz,hi there
def chat(arguments):
	# phBot passes the command name as arguments[0], so skip it
	args = [a for a in arguments if a.strip().lower() != 'chat'] if arguments and arguments[0].strip().lower() == 'chat' else list(arguments)
	if not args or len(args) < 2:
		log('Plugin: chat script command usage: chat,<type>,<message>')
		return 0
	t = args[0].strip().lower()
	# Map type -> phBot chat type id used in handle_chat (so we can suppress the echo)
	# 1=All 2=Private 3=Guild 4=Party 5=Global 6=Note 7=Stall 11=Union
	typeIdMap = {'all':1,'private':2,'guild':3,'party':4,'global':5,'note':6,'stall':7,'union':11}
	try:
		body = ','.join(args[1:]).strip()
		if t == 'all':
			_selfSentChat.append((typeIdMap['all'], body))
			phBotChat.All(body)
		elif t == 'party':
			_selfSentChat.append((typeIdMap['party'], body))
			phBotChat.Party(body)
		elif t == 'guild':
			_selfSentChat.append((typeIdMap['guild'], body))
			phBotChat.Guild(body)
		elif t == 'union':
			_selfSentChat.append((typeIdMap['union'], body))
			phBotChat.Union(body)
		elif t == 'stall':
			_selfSentChat.append((typeIdMap['stall'], body))
			phBotChat.Stall(body)
		elif t == 'global':
			_selfSentChat.append((typeIdMap['global'], body))
			phBotChat.Global(body)
		elif t == 'private' or t == 'note':
			if len(args) < 3:
				log('Plugin: chat script command usage: chat,'+t+',<name>,<message>')
				return 0
			name = args[1].strip()
			msg = ','.join(args[2:]).strip()
			if t == 'private':
				phBotChat.Private(name, msg)
			else:
				phBotChat.Note(name, msg)
		else:
			log('Plugin: chat script command — unknown type: '+t)
	except Exception as e:
		log('Plugin: chat script command error: '+str(e))
	return 0

# Script command: pinvite,Name1[,Name2,...]
# Find each named player nearby and send a party invite (or create-party with them)
def pinvite(arguments):
	args = [a for a in arguments if a.strip().lower() != 'pinvite'] if arguments and arguments[0].strip().lower() == 'pinvite' else list(arguments)
	if not args:
		log('Plugin: pinvite usage: pinvite,Name1[,Name2,...]')
		return 0
	try:
		players = get_players() or {}
		nameToUid = {}
		for uid, p in players.items():
			if p and 'name' in p and p['name']:
				nameToUid[p['name'].lower()] = uid
		inParty = bool(get_party())
		for name in args:
			n = name.strip()
			if not n:
				continue
			uid = nameToUid.get(n.lower())
			if not uid:
				log('Plugin: pinvite — player not nearby: '+n)
				continue
			if inParty:
				# CLIENT_PARTY_INVITE
				inject_joymax(0x7062, struct.pack('<I', uid), False)
				log('Plugin: Party invite sent to '+n)
			else:
				# CLIENT_PARTY_CREATE: PartySetting(uint32) + targetUID(uint32). 0x57 = exp+item share, free invite
				setting = 0x57
				inject_joymax(0x7060, struct.pack('<II', setting, uid), False)
				log('Plugin: Party create+invite sent to '+n)
				inParty = True
			time.sleep(0.5)
	except Exception as e:
		log('Plugin: pinvite error: '+str(e))
	return 0

# Script command: wait_party,Count[,TimeoutMs]
# Blocks the script until the party has at least Count members, or timeout (default 60s)
def wait_party(arguments):
	args = [a for a in arguments if a.strip().lower() != 'wait_party'] if arguments and arguments[0].strip().lower() == 'wait_party' else list(arguments)
	if not args:
		log('Plugin: wait_party usage: wait_party,Count[,TimeoutMs]')
		return 0
	try:
		count = int(args[0].strip())
		timeoutMs = int(args[1].strip()) if len(args) >= 2 else 60000
		start = time.time()
		while (time.time() - start) * 1000 < timeoutMs:
			p = get_party() or {}
			if len(p) >= count:
				log('Plugin: wait_party — party has '+str(len(p))+' members, proceeding')
				return 0
			time.sleep(0.5)
		log('Plugin: wait_party — timed out waiting for '+str(count)+' members (have '+str(len(get_party() or {}))+')')
	except Exception as e:
		log('Plugin: wait_party error: '+str(e))
	return 0

# Script command: use_scroll,<keyword>
# Find an item whose name contains <keyword> (case-insensitive) and use it.
# Searches main inventory first; if not found, scans grab-pet inventory and transfers it to main inv first.
# Example: use_scroll,Random Awaken
def use_scroll(arguments):
	args = [a for a in arguments if a.strip().lower() != 'use_scroll'] if arguments and arguments[0].strip().lower() == 'use_scroll' else list(arguments)
	if not args:
		log('Plugin: use_scroll usage: use_scroll,<keyword>')
		return 0
	try:
		keyword = ','.join(args).strip().lower()
		def _useFromItem(item):
			# Build CLIENT_INVENTORY_ITEM_USE packet using get_item() (no DB needed)
			itemData = get_item(item['model']) or {}
			cash = itemData.get('cash_item',0) or 0
			tid1 = itemData.get('tid1',0) or 0
			tid2 = itemData.get('tid2',0) or 0
			tid3 = itemData.get('tid3',0) or 0
			tid = cash + 12 + (tid1*32) + (tid2*128) + (tid3*2048)
			p = struct.pack('<B', item['slot'])
			if get_locale() == 22:
				p += struct.pack('<H', tid)
			else:
				p += struct.pack('<I', tid)
			log('Plugin: Using item "'+item.get('name','?')+'"')
			inject_joymax(0x704C, p, True)
		# 1) Look in main inventory
		item = GetItemByExpression(lambda n,s: keyword in (n or '').lower() or keyword in (s or '').lower(),13)
		if item:
			_useFromItem(item)
			return 0
		# 2) Look in grab-pet inventory
		try:
			pets = get_pets() or {}
		except Exception:
			pets = {}
		moved = False
		for uid, pet in pets.items():
			petInv = None
			try:
				petInv = get_pet_inventory(uid)
			except Exception:
				petInv = None
			if not petInv:
				continue
			items = petInv.get('items') if isinstance(petInv, dict) else None
			if not items:
				continue
			for slot, pItem in enumerate(items):
				if not pItem:
					continue
				name = (pItem.get('name') or '').lower()
				sname = (pItem.get('servername') or '').lower()
				if keyword in name or keyword in sname:
					# Inject pet->inventory movement. Movement type 26 = grab pet -> player inv.
					targetSlot = GetEmptySlot()
					if targetSlot == -1:
						log('Plugin: use_scroll — main inventory full, cannot pull from pet')
						return 0
					p = struct.pack('<B', 26)
					p += struct.pack('<I', uid)
					p += struct.pack('<B', slot)
					p += struct.pack('<B', targetSlot)
					p += struct.pack('<H', pItem.get('quantity',1) or 1)
					log('Plugin: use_scroll — pulling "'+pItem.get('name','?')+'" from grab pet')
					inject_joymax(0x7034, p, False)
					moved = True
					break
			if moved:
				break
		if moved:
			# Give server a moment to acknowledge, then look again in main inv and use it
			time.sleep(1.0)
			item = GetItemByExpression(lambda n,s: keyword in (n or '').lower() or keyword in (s or '').lower(),13)
			if item:
				_useFromItem(item)
			else:
				log('Plugin: use_scroll — item moved but not visible in main inventory yet')
			return 0
		log('Plugin: use_scroll — no item matching "'+keyword+'" in inventory or grab pet')
	except Exception as e:
		log('Plugin: use_scroll error: '+str(e))
	return 0

# Walk script command: leaveparty
# Makes the bot leave its current party (same packet as the GETOUT chat command)
def leaveparty(arguments):
	try:
		if get_party():
			inject_joymax(0x7061, b'', False)
			log('Plugin: Leaving the party (script command)')
		else:
			log('Plugin: leaveparty — not in a party')
	except Exception as e:
		log('Plugin: leaveparty error: '+str(e))
	return 0

# Plugin loaded
log("Plugin: "+pName+" v"+pVersion+" successfully loaded")

if os.path.exists(getPath()):
	# Adding RELOAD plugin support
	loadConfigs()
else:
	# Creating configs folder
	os.makedirs(getPath())
	log('Plugin: '+pName+' folder has been created')

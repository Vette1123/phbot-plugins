# -*- coding: utf-8 -*-
from phBot import *
import QtBind
import time
import threading

pName = 'xShadow'
pVersion = '2.5.1_LOG_CLEAN'
pUrl = 'https://github.com/'

gui = QtBind.init(__name__, pName)

cycle_active = False
cycle_thread = None
last_teleport_time = 0

DELAY_PACKET = 0.15
DELAY_STEP = 1.50
SUMMON_DELAY = 1.00

def logp(msg):
	log('[%s] %s' % (pName, msg))


def should_stop_now():
	try:
		return not cycle_active
	except:
		return True


def sleep_with_stop_check(seconds, step=0.10):
	try:
		end_time = time.time() + float(seconds)
		while time.time() < end_time:
			if should_stop_now():
				return False
			time.sleep(step)
		return True
	except:
		return False


def inject_one(name, opcode, hex_data=''):
	# Silent packet injection: user log shows actions only, not packet hex.
	try:
		data = bytearray.fromhex(hex_data) if hex_data else b''
		inject_joymax(opcode, data, False)
		return True
	except Exception as e:
		logp('%s failed: %s' % (name, str(e)))
		return False

def inject_sequence(name, packets, delay=DELAY_PACKET):
	for opcode, hex_data in packets:
		if not cycle_active:
			return False
		inject_one(name, opcode, hex_data)
		time.sleep(delay)
	return True

def safe_start_bot():
	try:
		start_bot()
		logp('Bot started.')
		return True
	except Exception as e:
		logp('Start bot failed: %s' % str(e))
		return False

def safe_stop_bot():
	try:
		stop_bot()
		logp('Bot stopped.')
		return True
	except Exception as e:
		logp('Stop bot failed: %s' % str(e))
		return False

def isCheckedSafe(cb):
	try:
		return QtBind.isChecked(gui, cb)
	except:
		try:
			return QtBind.isChecked(cb)
		except:
			try:
				return QtBind.getChecked(gui, cb)
			except:
				return False

def get_int_text(tb, default_value):
	try:
		return int(QtBind.text(gui, tb).strip())
	except:
		return default_value


# ================= Party chat command =================

def send_party_chat(message):
	try:
		# phBot API chat type 2 = Party chat in most plugin builds
		phBotChat(2, message)
		logp('Party chat sent: ' + message)
		return True
	except Exception as e:
		logp('phBotChat party failed: %s' % str(e))

	try:
		# Fallback through chat packet if phBotChat is not available.
		# 0x7025 chat packet:
		# 02 = party, len + ascii message
		msg = str(message)
		data = bytearray()
		data.append(0x02)
		data += len(msg).to_bytes(2, 'little')
		data += msg.encode('ascii', errors='ignore')
		inject_joymax(0x7025, data, False)
		logp('Party chat packet sent: ' + message)
		return True
	except Exception as e:
		logp('Party chat packet failed: %s' % str(e))
		return False

# ================= Dungeon actions =================

def can_enter_dungeon_now():
	# Hard gate: no Start Dungeon inject unless self is in party and self is party master.
	count = get_party_count_safe()
	master_ok = is_self_party_master()

	if count < 2:
		logp('Enter blocked: must be in party 2/8 or more. Current: %d/8.' % count)
		try:
			QtBind.setText(gui, lblStatus, 'Status: enter blocked - party %d/8' % count)
		except:
			pass
		return False

	if not master_ok:
		logp('Enter blocked: current account is not confirmed party master.')
		try:
			QtBind.setText(gui, lblStatus, 'Status: enter blocked - not party master')
		except:
			pass
		return False

	logp('Enter allowed: party %d/8 and you are the master.' % count)
	return True


def action_start_dungeon():
	if not can_enter_dungeon_now():
		return False
	logp('Entering dungeon...')
	return inject_sequence('Start Dungeon', [
		(0x705A, '78 08 00 00 02 55 01 00 00'),
		(0x3080, '01 01')
	])

def action_begin_dungeon():
	logp('Starting dungeon...')
	return inject_sequence('Begin Dungeon', [
		(0x7045, '31 8F 30 00'),
		(0x766A, '01'),
		(0x704B, '31 8F 30 00')
	])

def action_summon_unique_once(index, total=5):
	logp('Summoning Shadow Unique %d/%d' % (index, total))
	return inject_sequence('Summon Unique %d' % index, [
		(0x7045, '2D 01 00 00'),
		(0x766A, '02 9E A5 00 00'),
		(0x704B, '2D 01 00 00')
	])

def action_getout_chat():
	# Removed by request.
	logp('getout command removed. Nothing sent.')

def action_exit_dungeon():
	logp('Exiting dungeon...')
	ok = inject_one('Exit Dungeon', 0x766A, '03')
	if ok:
		logp('Dungeon exit done.')
	return ok

storage_queue = []
_inventory_names_cache = []


def _get_inventory_items_dict():
	# Same working method used in Garnet Evolution System:
	# items = get_inventory()['items']
	# for slot, item in enumerate(items)
	result = {}

	try:
		items = get_inventory()['items']
		for slot, item in enumerate(items):
			if not item:
				continue
			# Skip equipment slots like the Garnet plugin does.
			if slot <= 13:
				continue
			result[int(slot)] = item
		return result
	except Exception as e:
		logp("Inventory read direct method failed: %s" % str(e))

	# Fallbacks only if direct method failed.
	try:
		inv = get_inventory()
		if isinstance(inv, dict):
			items = inv.get('items', None)

			if isinstance(items, dict):
				for slot, item in items.items():
					if item and int(slot) > 13:
						result[int(slot)] = item
				return result

			if isinstance(items, list):
				for slot, item in enumerate(items):
					if item and slot > 13:
						result[int(slot)] = item
				return result
	except Exception as e:
		logp("Inventory fallback failed: %s" % str(e))

	return result


def _item_name(item):
	try:
		if not isinstance(item, dict):
			return ''

		for key in ['name', 'servername', 'server_name', 'item_name', 'itemName', 'display_name', 'displayName']:
			value = item.get(key, None)
			if value:
				return str(value).strip()

		for key in ['item', 'data', 'info']:
			value = item.get(key, None)
			if isinstance(value, dict):
				n = _item_name(value)
				if n:
					return n
	except:
		pass
	return ''


def _item_match_queue(item):
	try:
		name = _item_name(item).lower()
		for q in storage_queue:
			qn = str(q or '').strip().lower()
			if qn and qn in name:
				return True
	except:
		pass
	return False


def _find_inventory_slots_for_queue():
	items = _get_inventory_items_dict()
	slots = []
	try:
		for slot, item in items.items():
			if isinstance(item, dict) and _item_match_queue(item):
				slots.append((int(slot), _item_name(item)))
	except Exception as e:
		logp('Inventory queue scan error: %s' % str(e))
	return sorted(slots, key=lambda x: x[0])


def _refresh_inventory_names_cache():
	global _inventory_names_cache
	names = []
	seen = {}
	items = _get_inventory_items_dict()
	try:
		for slot, item in sorted(items.items(), key=lambda x: int(x[0])):
			name = _item_name(item)
			if not name:
				continue

			key = name.strip().lower()
			if not key:
				continue

			if key not in seen:
				seen[key] = {'name': name.strip(), 'count': 0}
			seen[key]['count'] += 1

		# Show every repeated item name once only.
		for key in sorted(seen.keys()):
			entry = seen[key]
			if entry['count'] > 1:
				names.append('%s  x%d' % (entry['name'], entry['count']))
			else:
				names.append(entry['name'])

	except Exception as e:
		logp('Refresh inventory list failed: %s' % str(e))

	_inventory_names_cache = names
	return names


def _parse_name_from_inventory_list_text(text):
	s = str(text or '').strip()
	if '|' in s:
		s = s.split('|', 1)[1].strip()

	# Remove visible count suffix from combo display.
	# Example: "Magic POP Card  x5" -> "Magic POP Card"
	try:
		import re
		s = re.sub(r'\s+x\d+\s*$', '', s).strip()
	except:
		pass

	# Remove visible plus suffix only from combo display.
	# Example: "Tiger Spear +15" -> "Tiger Spear"
	try:
		import re
		s = re.sub(r'\s\+\d+\s*$', '', s).strip()
	except:
		pass

	return s


def action_store_inventory_slot(slot, item_name=''):
	if should_stop_now():
		logp('Storage Queue stopped by Stop Cycle before item transfer.')
		return 'stopped'

	try:
		data = bytearray()
		data.append(0x02)
		data.append(int(slot) & 0xFF)
		data.append(0x85)
		data += bytes.fromhex('1F050000')
		inject_joymax(0x7034, data, False)
		return True
	except Exception as e:
		msg = str(e)
		if 'full' in msg.lower() or 'space' in msg.lower():
			logp('Storage appears to be full. Closing storage and continuing.')
			return 'full'
		logp('Store queued item failed [%s]: %s' % (str(item_name), msg))
		return False



def get_queue_inventory_counts():
	counts = {}
	for slot, name in _find_inventory_slots_for_queue():
		key = str(name or '').strip()
		if key:
			counts[key] = counts.get(key, 0) + 1
	return counts


def action_store_all_queue_items_from_inventory(max_rounds=60):
	if should_stop_now():
		logp('Storage Queue stopped by Stop Cycle.')
		return False

	if not storage_queue:
		logp('Storage Queue is empty. Skipping storage and continuing to party check.')
		return True

	moved_counts = {}

	for round_no in range(1, max_rounds + 1):
		if should_stop_now():
			logp('Storage Queue stopped by Stop Cycle.')
			return False

		matches = _find_inventory_slots_for_queue()
		if not matches:
			if moved_counts:
				for item_name in sorted(moved_counts.keys()):
					logp('Storing item [%s], count [%d].' % (item_name, moved_counts[item_name]))
			else:
				logp('No queued items found in inventory. Skipping storage and continuing to party check.')
			return True

		slot, name = matches[0]

		if should_stop_now():
			logp('Storage Queue stopped by Stop Cycle before storing next item.')
			return False

		result = action_store_inventory_slot(slot, name)

		if result == 'stopped':
			return False

		if result == 'full':
			logp('Storage is full. Finished storage stage and continuing to party check.')
			return True

		if result is False:
			return False

		moved_counts[name] = moved_counts.get(name, 0) + 1

		if not sleep_with_stop_check(0.75):
			logp('Storage Queue stopped by Stop Cycle during storage delay.')
			return False

	logp('Storage stopped by safety limit max_rounds=%d. Continuing to party check.' % max_rounds)
	return True



def action_open_storage():
	# Open Storage sequence recorded from sniffer.
	try:
		logp('Opening storage...')
		inject_one('Open Storage 1', 0x7045, '1F 05 00 00')
		time.sleep(0.50)
		inject_one('Open Storage 2', 0x703C, '1F 05 00 00 00')
		time.sleep(0.50)
		inject_one('Open Storage 3', 0x7046, '1F 05 00 00 03')
		time.sleep(0.50)
		logp('Storage opened.')
		return True
	except Exception as e:
		logp('Open Storage error: %s' % str(e))
		return False


def action_close_storage():
	# Close Storage packet recorded from sniffer.
	try:
		return inject_one('Close Storage', 0x704B, '1F 05 00 00')
	except Exception as e:
		logp('Close Storage error: %s' % str(e))
		return False


def action_storage_magic_pop_first(require_cycle=False):
	# Inventory Storage Queue ONLY.
	# Stop Cycle must stop this stage immediately.
	# If storage is full, close storage and continue to party check.
	try:
		if require_cycle and should_stop_now():
			logp('Storage Stage skipped because cycle is stopped.')
			return False

		if not is_storage_stage_enabled():
			logp('Storage stage disabled. Skipping storage and continuing to party check.')
			QtBind.setText(gui, lblStatus, 'Status: storage disabled')
			return True

		logp('Checking storage queue items.')
		QtBind.setText(gui, lblStatus, 'Status: storage queue')

		if require_cycle and should_stop_now():
			logp('Storage Queue cancelled before open.')
			return False

		if not storage_queue:
			logp('Storage Queue is empty. Skipping storage and continuing to party check.')
			QtBind.setText(gui, lblStatus, 'Status: queue empty')
			return True

		if require_cycle and should_stop_now():
			logp('Storage Queue cancelled before opening storage.')
			return False

		logp('Opening storage.')
		if not action_open_storage():
			return False

		if not sleep_with_stop_check(1.00):
			logp('Storage Queue stopped by Stop Cycle after opening storage.')
			try:
				action_close_storage()
			except:
				pass
			return False

		ok = action_store_all_queue_items_from_inventory()

		# Always close storage after this stage, even if full or stopped.
		try:
			action_close_storage()
		except:
			pass

		if not ok:
			logp('Storage Queue stopped or failed.')
			QtBind.setText(gui, lblStatus, 'Status: queue stopped')
			return False

		logp('Finished. Now checking party members.')
		QtBind.setText(gui, lblStatus, 'Status: queue stored')
		return True

	except Exception as e:
		logp('Storage Queue error: %s' % str(e))
		try:
			action_close_storage()
		except:
			pass
		try:
			QtBind.setText(gui, lblStatus, 'Status: queue error')
		except:
			pass
		return False



# ================= Unique detection =================

def is_unique_monster(monster):
	try:
		name = str(monster.get('name', '') or monster.get('servername', '') or '').lower()
	except:
		name = ''

	try:
		mtype = monster.get('type', None)
	except:
		mtype = None

	try:
		rarity = monster.get('rarity', None)
	except:
		rarity = None

	if mtype in [3, 4, 5] or rarity in [3, 4, 5]:
		return True

	keywords = ['unique', 'legend', 'legendary', 'boss', 'shadow', 'titan', 'demon', 'lord']
	for k in keywords:
		if k in name:
			return True

	return False

def count_nearby_uniques():
	try:
		monsters = get_monsters()
	except Exception as e:
		logp('get_monsters failed: %s' % str(e))
		return 0

	count = 0
	try:
		for uid, mob in monsters.items():
			if is_unique_monster(mob):
				count += 1
	except:
		try:
			for mob in monsters:
				if is_unique_monster(mob):
					count += 1
		except:
			count = 0
	return count

def wait_until_no_uniques(timeout_no_unique):
	no_unique_since = None
	last_logged_count = None

	while cycle_active:
		count = count_nearby_uniques()

		if last_logged_count is None:
			last_logged_count = count
		elif count < last_logged_count:
			logp('Shadow Unique remaining count: %d' % count)
			last_logged_count = count
		elif count > last_logged_count:
			last_logged_count = count

		if count > 0:
			no_unique_since = None
		else:
			if no_unique_since is None:
				no_unique_since = time.time()
				logp('No Shadow Uniques left. Waiting %d seconds before stopping bot and exiting.' % timeout_no_unique)

			elapsed = int(time.time() - no_unique_since)
			QtBind.setText(gui, lblStatus, 'Status: waiting before stop %d/%d sec' % (elapsed, timeout_no_unique))

			if elapsed >= timeout_no_unique:
				logp('Wait finished. Stopping bot before exit.')
				safe_stop_bot()
				return True

		if not sleep_with_stop_check(2):
			return False

	return False



# ================= Party invite =================

def get_player_uid_by_name(player_name):
	target = str(player_name or '').strip().lower()
	if not target:
		return None

	try:
		players = get_players()
	except Exception as e:
		logp('get_players failed: %s' % str(e))
		return None

	try:
		for uid, player in players.items():
			try:
				name = str(player.get('name', '') or '').strip().lower()
				servername = str(player.get('servername', '') or '').strip().lower()
			except:
				name = ''
				servername = ''

			if name == target or servername == target:
				return uid
	except:
		try:
			for player in players:
				try:
					name = str(player.get('name', '') or '').strip().lower()
					servername = str(player.get('servername', '') or '').strip().lower()
					uid = player.get('uid', None) or player.get('unique_id', None) or player.get('id', None)
				except:
					name = ''
					servername = ''
					uid = None

				if uid is not None and (name == target or servername == target):
					return uid
		except:
			pass

	return None

def invite_player_by_name(player_name):
	player_name = str(player_name or '').strip()
	if not player_name:
		logp('Invite failed: empty player name.')
		return False

	uid = get_player_uid_by_name(player_name)
	if uid is None:
		logp('Invite failed: player [%s] not found nearby.' % player_name)
		return False

	try:
		data = struct.pack('<IB', int(uid), 0x07)
		inject_joymax(0x7060, data, False)
		logp('Party invite sent to [%s] UID[%s] -> 0x7060 | %s' % (player_name, uid, ' '.join(['%02X' % b for b in bytearray(data)])))
		return True
	except Exception as e:
		logp('Invite failed for [%s]: %s' % (player_name, str(e)))
		return False


def is_player_in_party(player_name):
	target = str(player_name or '').strip().lower()
	if not target:
		return False

	try:
		party = get_party()
	except Exception as e:
		logp('get_party failed: %s' % str(e))
		return False

	try:
		for key, member in party.items():
			name = str(member.get('name', '') or member.get('player_name', '') or '').strip().lower()
			if name == target:
				return True
	except:
		try:
			for member in party:
				name = str(member.get('name', '') or member.get('player_name', '') or '').strip().lower()
				if name == target:
					return True
		except:
			pass

	return False

def invite_until_in_party(player_name, max_seconds=60, interval=3):
	start_time = time.time()
	player_name = str(player_name or '').strip()

	if not player_name:
		logp('Invite loop stopped: empty player name.')
		return False

	logp('Invite loop started for [%s].' % player_name)

	while cycle_active or invite_active:
		if is_player_in_party(player_name):
			logp('[%s] is already in party. Invite loop stopped.' % player_name)
			return True

		if time.time() - start_time > max_seconds:
			logp('Invite loop timeout for [%s].' % player_name)
			return False

		invite_player_by_name(player_name)

		for i in range(interval):
			if not (cycle_active or invite_active):
				logp('Invite loop manually stopped.')
				return False
			time.sleep(1)

	return False

def start_invite_loop(max_seconds=60):
	logp('Invite removed by request.')
	return False

def stop_invite_loop():
	return



# ================= Party start condition =================

def get_self_name():
	try:
		data = get_character_data()
		name = data.get('name', '')
		if name:
			return str(name)
	except:
		pass
	return ''


def normalize_name(name):
	return str(name or '').strip().lower()


def get_party_members_list():
	try:
		party = get_party()
	except Exception as e:
		logp('get_party failed: %s' % str(e))
		return []

	members = []

	try:
		for key, member in party.items():
			if isinstance(member, dict):
				member_copy = dict(member)
				member_copy['_uid'] = key
				members.append(member_copy)
	except:
		try:
			for member in party:
				if isinstance(member, dict):
					members.append(member)
		except:
			pass

	return members


def get_party_count_safe():
	members = get_party_members_list()
	return len(members)


def member_name(member):
	try:
		return str(member.get('name', '') or member.get('player_name', '') or member.get('charname', '') or '').strip()
	except:
		return ''


def has_master_flag(member):
	# Different phBot builds may expose leader/master using different keys.
	master_keys = [
		'is_master', 'isMaster', 'master', 'Master',
		'is_leader', 'isLeader', 'leader', 'Leader',
		'is_party_master', 'party_master', 'partyMaster',
		'is_pt_master', 'pt_master'
	]

	for k in master_keys:
		try:
			if k in member:
				v = member.get(k)
				if v is True:
					return True
				if isinstance(v, int) and v == 1:
					return True
				if isinstance(v, str) and v.strip().lower() in ['1', 'true', 'yes', 'master', 'leader']:
					return True
		except:
			pass

	return False


def is_self_party_master():
	self_name = normalize_name(get_self_name())
	if not self_name:
		logp('Cannot read current character name.')
		return False

	members = get_party_members_list()
	if len(members) == 0:
		logp('Party data empty. Not ready.')
		return False

	found_self = False
	leader_fields_found = False

	for m in members:
		n = normalize_name(member_name(m))

		# If any member has a master/leader flag, we can use strict detection.
		for key in ['is_master','isMaster','master','Master','is_leader','isLeader','leader','Leader','is_party_master','party_master','partyMaster','is_pt_master','pt_master']:
			try:
				if key in m:
					leader_fields_found = True
			except:
				pass

		if n == self_name:
			found_self = True
			if has_master_flag(m):
				return True

	if leader_fields_found:
		logp('Current char [%s] is in party but is not detected as party master.' % get_self_name())
		return False

	if found_self:
		logp('Party master flag not exposed by phBot. Cannot confirm self is party master. Enter blocked.')
		return False

	logp('Current char [%s] not found in party list. Enter blocked.' % get_self_name())
	return False


def wait_until_party_ready_before_start():
	min_count = 2
	logp('Checking party: you must be master and party must be 2/8 or more.')

	while cycle_active:
		count = get_party_count_safe()
		master_ok = is_self_party_master()

		if master_ok and count >= min_count:
			QtBind.setText(gui, lblStatus, 'Status: party ready %d/8 - self master' % count)
			logp('Party ready: %d/8 and you are the master.' % count)
			return True

		if not master_ok:
			QtBind.setText(gui, lblStatus, 'Status: waiting self master, party %d/8' % count)
		else:
			QtBind.setText(gui, lblStatus, 'Status: waiting party 2/8, now %d/8' % count)

		time.sleep(2)

	return False


# ================= Cycle worker =================

def cycle_worker():
	global cycle_active

	loop_no = 0
	while cycle_active:
		loop_no += 1
		QtBind.setText(gui, lblStatus, 'Status: cycle %d starting' % loop_no)
		logp('Plugin started. Cycle %d' % loop_no)
		logp('Storage stage will run before party check.')

		summon_count = get_int_text(tbSummonCount, 5)
		no_unique_timeout = get_int_text(tbNoUniqueTimeout, 20)
		restart_delay = get_int_text(tbRestartDelay, 5)

		if summon_count <= 0:
			summon_count = 5

		if no_unique_timeout <= 0:
			no_unique_timeout = 20

		if should_stop_now():
			logp('Cycle stopped before storage stage.')
			return

		if not action_storage_magic_pop_first(True):
			logp('Storage stage failed or cycle stopped.')
			break

		logp('Now checking party members...')
		if not wait_until_party_ready_before_start():
			break

		logp('Party ready and you are the master.')
		if not action_start_dungeon():
			break

		if not cycle_active:
			break

		after_enter_delay = get_int_text(tbAfterEnterDelay, 2) if 'tbAfterEnterDelay' in globals() else 2
		QtBind.setText(gui, lblStatus, 'Status: entered, waiting %d sec before begin' % after_enter_delay)

		for x in range(after_enter_delay):
			if not cycle_active:
				break
			time.sleep(1)

		if not cycle_active:
			break

		if not action_begin_dungeon():
			break

		if not cycle_active:
			break

		time.sleep(DELAY_STEP)
		logp('Starting bot after Begin...')
		safe_start_bot()

		logp('Summoning Shadow Unique...')
		for i in range(1, summon_count + 1):
			if not cycle_active:
				break
			action_summon_unique_once(i, summon_count)
			if i < summon_count:
				time.sleep(SUMMON_DELAY)

		if not cycle_active:
			break

		logp('%d Shadow Uniques summoned. Monitoring started...' % summon_count)
		time.sleep(DELAY_STEP)
		wait_until_no_uniques(no_unique_timeout)

		if not cycle_active:
			break

		time.sleep(0.50)
		action_exit_dungeon()

		auto_restart = isCheckedSafe(cbAutoRestart)

		if not auto_restart:
			logp('Cycle finished. Auto Restart is disabled.')
			QtBind.setText(gui, lblStatus, 'Status: finished - restart off')
			break

		logp('Starting again...')
		QtBind.setText(gui, lblStatus, 'Status: restarting')

		for x in range(restart_delay):
			if not cycle_active:
				break
			time.sleep(1)

	cycle_active = False
	QtBind.setText(gui, lblStatus, 'Status: stopped')



def handle_joymax(opcode, data):
	global last_teleport_time
	# These opcodes commonly appear after successful teleport/loading/region refresh.
	# We use them as confirmation that Start Dungeon succeeded before Begin Dungeon.
	try:
		if opcode in [0x34B6, 0x37AA, 0x3708, 0x3790, 0x377A, 0x3780, 0x37F2, 0x750E]:
			last_teleport_time = time.time()
	except:
		pass
	return True


def wait_for_teleport_success(timeout=20):
	global last_teleport_time
	start_wait = time.time()
	last_teleport_time = 0

	logp('Waiting for dungeon entry success, timeout %s sec...' % timeout)
	QtBind.setText(gui, lblStatus, 'Status: waiting dungeon entry')

	while cycle_active:
		if last_teleport_time > start_wait:
			logp('Dungeon entry detected.')
			QtBind.setText(gui, lblStatus, 'Status: dungeon entry detected')
			return True

		if time.time() - start_wait >= timeout:
			logp('Dungeon entry wait timeout.')
			QtBind.setText(gui, lblStatus, 'Status: entry timeout')
			return False

		time.sleep(0.5)

	return False


# ================= Storage Queue UI =================

QUEUE_CONFIG_FILE = get_config_dir() + pName + '_storage_queue.json'


def is_storage_stage_enabled():
	try:
		return QtBind.isChecked(gui, cbEnableStorageStage)
	except:
		return True


def save_storage_queue():
	try:
		import json
		data = {
			'storage_enabled': is_storage_stage_enabled(),
			'queue': storage_queue
		}
		with open(QUEUE_CONFIG_FILE, 'w') as f:
			f.write(json.dumps(data, indent=2))
		logp('Storage settings saved. Enabled=%s Queue=%s' % (str(is_storage_stage_enabled()), ', '.join(storage_queue)))
	except Exception as e:
		logp('Storage Queue save failed: %s' % str(e))


def load_storage_queue():
	global storage_queue
	try:
		import json
		with open(QUEUE_CONFIG_FILE, 'r') as f:
			data = json.loads(f.read())

		if isinstance(data, list):
			storage_queue = [str(x).strip() for x in data if str(x).strip()]
			try:
				QtBind.setChecked(gui, cbEnableStorageStage, True)
			except:
				pass
		elif isinstance(data, dict):
			storage_queue = [str(x).strip() for x in data.get('queue', []) if str(x).strip()]
			try:
				QtBind.setChecked(gui, cbEnableStorageStage, bool(data.get('storage_enabled', True)))
			except:
				pass
	except:
		storage_queue = []


def cb_enable_storage_stage_changed(checked):
	save_storage_queue()
	if checked:
		logp('Storage Stage enabled.')
	else:
		logp('Storage Stage disabled.')


def refresh_queue_list_ui():
	try:
		QtBind.clear(gui, lstStorageQueue)
		for name in storage_queue:
			QtBind.append(gui, lstStorageQueue, name)
		try:
			QtBind.setIndex(gui, lstStorageQueue, 0)
		except:
			pass
	except Exception as e:
		logp('Refresh queue UI failed: %s' % str(e))


def refresh_inventory_list_ui():
	try:
		names = _refresh_inventory_names_cache()
		QtBind.clear(gui, lstInventoryItems)
		for name in names:
			QtBind.append(gui, lstInventoryItems, name)
		try:
			QtBind.setIndex(gui, lstInventoryItems, 0)
		except:
			pass
		logp('Inventory list refreshed. Items: %d' % len(names))
		if len(names) == 0:
			logp('Inventory list is empty. Try opening inventory in game or teleport once, then Refresh again.')
	except Exception as e:
		logp('Refresh inventory UI failed: %s' % str(e))


def btn_refresh_inventory():
	refresh_inventory_list_ui()


def _get_selected_inventory_combo_text():
	try:
		idx = int(QtBind.currentIndex(gui, lstInventoryItems))
		if idx >= 0 and idx < len(_inventory_names_cache):
			return _inventory_names_cache[idx]
	except:
		pass
	try:
		return QtBind.text(gui, lstInventoryItems)
	except:
		return ''


def _get_selected_queue_combo_text():
	try:
		idx = int(QtBind.currentIndex(gui, lstStorageQueue))
		if idx >= 0 and idx < len(storage_queue):
			return storage_queue[idx]
	except:
		pass
	try:
		return QtBind.text(gui, lstStorageQueue)
	except:
		return ''


def btn_add_item_to_queue():
	selected = _get_selected_inventory_combo_text()
	name = _parse_name_from_inventory_list_text(selected)
	if not name:
		logp('Add Item failed: select an inventory item first.')
		return
	if name not in storage_queue:
		storage_queue.append(name)
	refresh_queue_list_ui()
	save_storage_queue()
	logp('Added to Storage Queue: ' + name)


def btn_remove_item_from_queue():
	name = str(_get_selected_queue_combo_text() or '').strip()
	if not name:
		logp('Remove Item failed: select queue item first.')
		return
	try:
		storage_queue.remove(name)
	except:
		pass
	refresh_queue_list_ui()
	save_storage_queue()
	logp('Removed from Storage Queue: ' + name)


def btn_clear_queue():
	global storage_queue
	storage_queue = []
	refresh_queue_list_ui()
	save_storage_queue()
	logp('Storage Queue cleared.')


# ================= Buttons =================

def btn_start_cycle():
	global cycle_active, cycle_thread
	if cycle_active:
		logp('Cycle already running.')
		return

	cycle_active = True
	cycle_thread = threading.Thread(target=cycle_worker)
	cycle_thread.daemon = True
	cycle_thread.start()
	QtBind.setText(gui, lblStatus, 'Status: running')
	logp('Cycle started.')

def btn_stop_cycle():
	global cycle_active
	cycle_active = False
	try:
		QtBind.setText(gui, lblStatus, 'Status: stopping')
	except:
		pass
	logp('Stop Cycle pressed. Stopping all active processes now.')



def btn_start_dungeon_manual():
	action_start_dungeon()

def btn_begin_manual():
	action_begin_dungeon()

def btn_summon_manual():
	action_summon_unique_once(1)

def btn_getout_manual():
	logp('getout removed by request.')

def btn_exit_manual():
	action_exit_dungeon()

def btn_storage_first_manual():
	try:
		action_storage_magic_pop_first(False)
	except Exception as e:
		logp('Manual Store Queue error: %s' % str(e))



def cb_auto_restart_changed(checked):
	logp('Auto Restart '+('enabled' if checked else 'disabled'))


	logp('Invite removed by request.')

def cb_auto_invite_changed(checked):
	logp('Auto Invite removed by request.')


# ================= GUI =================

QtBind.createLabel(gui, 'Shadow test Cycle', 20, 5)

QtBind.createButton(gui, 'btn_start_cycle', 'START CYCLE', 20, 32)
QtBind.createButton(gui, 'btn_stop_cycle', 'STOP CYCLE', 140, 32)

QtBind.createLabel(gui, 'Summon Count', 20, 70)
tbSummonCount = QtBind.createLineEdit(gui, '5', 120, 67, 45, 20)

QtBind.createLabel(gui, 'No Unique Timeout', 190, 70)
tbNoUniqueTimeout = QtBind.createLineEdit(gui, '20', 315, 67, 45, 20)

cbAutoRestart = QtBind.createCheckBox(gui, 'cb_auto_restart_changed', 'Auto Restart', 385, 67)
QtBind.setChecked(gui, cbAutoRestart, True)

QtBind.createLabel(gui, 'Restart Delay', 385, 95)
tbRestartDelay = QtBind.createLineEdit(gui, '5', 485, 92, 45, 20)

QtBind.createLabel(gui, 'After Enter Delay', 385, 120)
tbAfterEnterDelay = QtBind.createLineEdit(gui, '2', 500, 117, 45, 20)

lblStatus = QtBind.createLabel(gui, 'Status: stopped', 20, 105)
cbEnableStorageStage = QtBind.createCheckBox(gui, 'cb_enable_storage_stage_changed', 'Enable Storage Stage', 20, 128)
QtBind.setChecked(gui, cbEnableStorageStage, True)

QtBind.createLabel(gui, 'Inventory Items', 20, 155)
lstInventoryItems = QtBind.createCombobox(gui, 120, 152, 300, 22)
QtBind.createButton(gui, 'btn_refresh_inventory', 'Refresh', 430, 150)
QtBind.createButton(gui, 'btn_add_item_to_queue', 'Add', 505, 150)

QtBind.createLabel(gui, 'Storage Queue', 20, 185)
lstStorageQueue = QtBind.createCombobox(gui, 120, 182, 300, 22)
QtBind.createButton(gui, 'btn_remove_item_from_queue', 'Remove', 430, 180)
QtBind.createButton(gui, 'btn_clear_queue', 'Clear', 505, 180)



QtBind.createLabel(gui, 'Manual buttons:', 20, 220)

QtBind.createButton(gui, 'btn_start_dungeon_manual', 'Start Dungeon', 20, 245)
QtBind.createButton(gui, 'btn_begin_manual', 'Begin', 120, 245)
QtBind.createButton(gui, 'btn_summon_manual', 'Summon Once', 220, 245)
QtBind.createButton(gui, 'btn_exit_manual', 'Exit', 320, 245)
QtBind.createButton(gui, 'btn_storage_first_manual', 'Store Queue', 420, 245)


def auto_refresh_inventory_on_load():
	try:
		refresh_inventory_list_ui()
		logp('Inventory refreshed on plugin load.')
	except Exception as e:
		logp('Inventory refresh on load failed: %s' % str(e))


load_storage_queue()
refresh_queue_list_ui()
logp('Loaded v%s' % pVersion)
auto_refresh_inventory_on_load()

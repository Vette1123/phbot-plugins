from phBot import *
from threading import Timer
import QtBind
import shutil
import time
import os
import re
import webbrowser

GITHUB_URL = 'https://github.com/Vette1123'

def btn_github_clicked():
    try:
        webbrowser.open(GITHUB_URL)
    except Exception:
        pass

pName = 'xAutoConfig'
pVersion = '2.0.0'
pAuthor = 'JellyBitz, Vette1123 (Gado)'
pUrl = 'https://raw.githubusercontent.com/Vette1123/phbot-plugins/main/xAutoConfig.py'
# GitHub: https://github.com/Vette1123

# ______________________________ Constants ______________________________ #

DATABASE_LOADING_TIME = 90.0
DB3_SIDECARS = ('-shm', '-wal')

# ______________________________ Helpers ______________________________ #

def getConfigFilename():
	data = get_character_data()
	return data['server'] + "_" + data['name']

def FindFiles(pattern, dir=''):
	return [x for x in os.listdir(dir) if re.search(pattern, x)]

def ReplaceFile(newPath, oldPath, message):
	shutil.copyfile(newPath, oldPath)
	log(message)

def _config_dir():
	d = get_config_dir()
	if not d.endswith(os.sep) and not d.endswith('/'):
		d += os.sep
	return d

def list_characters():
	"""Return sorted list of '{server}_{name}' identifiers found in Config dir."""
	d = _config_dir()
	try:
		entries = os.listdir(d)
	except Exception:
		return []
	chars = set()
	for f in entries:
		# main char config: exactly one dot, ends with .json, contains underscore
		if not f.lower().endswith('.json'):
			continue
		base = f[:-5]
		if '.' in base:
			continue
		if base.lower().startswith('default'):
			continue
		if '_' not in base:
			continue
		chars.add(base)
	return sorted(chars, key=str.lower)

def list_extra_json(char_id):
	"""Return list of extra .json filenames for a character (e.g. uniques, named profiles)."""
	d = _config_dir()
	prefix = char_id + '.'
	try:
		entries = os.listdir(d)
	except Exception:
		return []
	extras = []
	for f in entries:
		if not f.lower().endswith('.json'):
			continue
		if f == char_id + '.json':
			continue
		if f.startswith(prefix):
			extras.append(f)
	return sorted(extras, key=str.lower)

# ______________________________ UI ______________________________ #

gui = QtBind.init(__name__, pName)

# ---------- Header ----------
QtBind.createLabel(gui, 'xAutoConfig  -  Copy Settings Between Characters', 12, 8)
QtBind.createLabel(gui, 'Clone .json settings and/or .db3 item filter from one character to another.', 12, 26)

# ---------- LEFT column: source / destination ----------
QtBind.createLabel(gui, 'Source:', 12, 58)
cmbSource = QtBind.createCombobox(gui, 90, 55, 230, 22)

QtBind.createLabel(gui, 'Destination:', 12, 88)
cmbDest = QtBind.createCombobox(gui, 90, 85, 230, 22)

QtBind.createLabel(gui, 'or new name:', 12, 118)
txtNewDest = QtBind.createLineEdit(gui, '', 90, 115, 230, 22)

btnSwap    = QtBind.createButton(gui, 'btnSwap_clicked',    '  Swap  <->  ',  12, 148)
btnRefresh = QtBind.createButton(gui, 'btnRefresh_clicked', '   Refresh   ', 170, 148)

# ---------- RIGHT column: what to copy + action ----------
QtBind.createLabel(gui, 'What to copy:', 360, 58)

cbJson  = QtBind.createCheckBox(gui, 'noop', 'Main settings  (.json)',                              360, 80)
cbDb3   = QtBind.createCheckBox(gui, 'noop', 'Item filter database  (.db3)',                        360, 100)
cbExtra = QtBind.createCheckBox(gui, 'noop', 'Extra .json profiles  (uniques, named filters, ...)', 360, 120)

QtBind.setChecked(gui, cbJson, True)
QtBind.setChecked(gui, cbDb3, True)
QtBind.setChecked(gui, cbExtra, False)

btnCopy = QtBind.createButton(gui, 'btnCopy_clicked', '     Copy Settings   -->     ', 360, 148)

# ---------- Footer: status + hint ----------
lblStatus = QtBind.createLabel(gui, 'Status:  ready.' + (' ' * 80), 12, 188)
lblHint   = QtBind.createLabel(gui, 'Tip: leave "new name" empty to use the dropdown.  Example new name:  MyNewAlt   or   Astyra_MyNewAlt', 12, 210)
QtBind.createButton(gui, 'btn_github_clicked', '  GitHub: Vette1123 (Gado)  ', 12, 235)

# ______________________________ UI logic ______________________________ #

def noop():
	pass

def _set_status(msg):
	QtBind.setText(gui, lblStatus, 'Status:  ' + msg + (' ' * 4))

def _combo_set_index(combo, idx):
	"""QtBind exposes the 'set current index' call under different names across phBot
	builds. Try the known variants and silently no-op if none exist."""
	for fn_name in ('setIndex', 'setCurrentIndex', 'setSelectedIndex', 'select', 'setCurrent'):
		fn = getattr(QtBind, fn_name, None)
		if callable(fn):
			try:
				fn(gui, combo, idx)
				return
			except Exception:
				continue

def _populate_combos(preserve=True):
	prev_src = QtBind.text(gui, cmbSource) if preserve else ''
	prev_dst = QtBind.text(gui, cmbDest) if preserve else ''
	QtBind.clear(gui, cmbSource)
	QtBind.clear(gui, cmbDest)
	chars = list_characters()
	for c in chars:
		QtBind.append(gui, cmbSource, c)
		QtBind.append(gui, cmbDest, c)
	# restore prior selections when possible
	def _restore(combo, value, fallback_index):
		if value and value in chars:
			_combo_set_index(combo, chars.index(value))
		elif chars:
			_combo_set_index(combo, min(fallback_index, len(chars) - 1))
	_restore(cmbSource, prev_src, 0)
	_restore(cmbDest,   prev_dst, 1 if len(chars) > 1 else 0)
	return chars

def btnRefresh_clicked():
	chars = _populate_combos(preserve=True)
	if chars:
		_set_status('found ' + str(len(chars)) + ' character(s).')
	else:
		_set_status('no character configs found in Config folder.')

def btnSwap_clicked():
	a = QtBind.text(gui, cmbSource)
	b = QtBind.text(gui, cmbDest)
	chars = list_characters()
	if a in chars:
		_combo_set_index(cmbDest, chars.index(a))
	if b in chars:
		_combo_set_index(cmbSource, chars.index(b))
	_set_status('swapped source and destination.')

def _safe_copy(src_path, dst_path):
	shutil.copyfile(src_path, dst_path)

def _remove_if_exists(path):
	try:
		if os.path.exists(path):
			os.remove(path)
	except Exception as ex:
		log('Plugin: could not remove ' + path + ' - ' + str(ex))

def _resolve_destination(src):
	"""Returns destination char-id. Prefers the 'new name' field; falls back to the combo.
	A bare name (no underscore) is auto-prefixed with the source's server."""
	new_name = QtBind.text(gui, txtNewDest).strip()
	if new_name:
		# strip any path-unsafe chars
		new_name = re.sub(r'[\\/:*?"<>|]+', '', new_name).strip()
		if not new_name:
			return ''
		if '_' not in new_name and '_' in src:
			server = src.split('_', 1)[0]
			return server + '_' + new_name
		return new_name
	return QtBind.text(gui, cmbDest).strip()

def btnCopy_clicked():
	src = QtBind.text(gui, cmbSource).strip()
	dst = _resolve_destination(src)
	d = _config_dir()

	if not src:
		_set_status('pick a source character.')
		return
	if not dst:
		_set_status('pick a destination or type a new name.')
		return
	if src == dst:
		_set_status('source and destination are the same.')
		return

	do_json  = QtBind.isChecked(gui, cbJson)
	do_db3   = QtBind.isChecked(gui, cbDb3)
	do_extra = QtBind.isChecked(gui, cbExtra)

	if not (do_json or do_db3 or do_extra):
		_set_status('select at least one file type to copy.')
		return

	copied = 0
	errors = 0

	# Main .json
	if do_json:
		s = d + src + '.json'
		t = d + dst + '.json'
		if os.path.exists(s):
			try:
				_safe_copy(s, t)
				log('Plugin: copied ' + src + '.json  ->  ' + dst + '.json')
				copied += 1
			except Exception as ex:
				log('Plugin: failed copying main .json - ' + str(ex))
				errors += 1
		else:
			log('Plugin: source main .json missing: ' + s)
			errors += 1

	# .db3 (+ clear sidecars on destination to avoid sqlite WAL mismatch)
	if do_db3:
		s = d + src + '.db3'
		t = d + dst + '.db3'
		if os.path.exists(s):
			try:
				for suf in DB3_SIDECARS:
					_remove_if_exists(t + suf)
				_safe_copy(s, t)
				log('Plugin: copied ' + src + '.db3  ->  ' + dst + '.db3')
				copied += 1
			except Exception as ex:
				log('Plugin: failed copying .db3 - ' + str(ex))
				errors += 1
		else:
			log('Plugin: source .db3 missing: ' + s)
			errors += 1

	# Extra .json profiles
	if do_extra:
		extras = list_extra_json(src)
		if not extras:
			log('Plugin: no extra .json profiles found for ' + src)
		for fname in extras:
			suffix = fname[len(src):]  # e.g. ".uniques.json"
			t = d + dst + suffix
			try:
				_safe_copy(d + fname, t)
				log('Plugin: copied ' + fname + '  ->  ' + dst + suffix)
				copied += 1
			except Exception as ex:
				log('Plugin: failed copying ' + fname + ' - ' + str(ex))
				errors += 1

	if errors == 0:
		_set_status('done. ' + str(copied) + ' file(s) copied  ' + src + '  ->  ' + dst + '.')
	else:
		_set_status('done with ' + str(errors) + ' error(s). ' + str(copied) + ' copied. see log.')

	# clear new-name field and refresh dropdowns so newly created char shows up
	QtBind.setText(gui, txtNewDest, '')
	_populate_combos(preserve=True)

# Initial population
_populate_combos(preserve=False)

# ______________________________ Events ______________________________ #

def joined_game():
	configDir = get_config_dir()
	configFilename = getConfigFilename()

	if not os.path.exists(configDir + configFilename + ".json"):
		defaultConfigs = FindFiles(r'[Dd]efault\.json|[Dd]efault\.[\s\S]*\.json', configDir)
		for cfg in defaultConfigs:
			ReplaceFile(configDir + cfg, configDir + configFilename + cfg[7:], 'Plugin: "' + str(cfg) + '" loaded')

	defaultFilter = FindFiles(r'[Dd]efault\.db3', configDir)
	if not defaultFilter:
		_populate_combos(preserve=True)
		return
	defaultFilter = configDir + defaultFilter[0]
	configFilter = configDir + configFilename + ".db3"

	if os.path.exists(configFilter):
		lastModification = time.time() - os.path.getmtime(configFilter)
		if lastModification <= 2:
			log("Plugin: Filter created few seconds ago! Default filter will be loaded in " + str(DATABASE_LOADING_TIME) + " seconds...")
			Timer(DATABASE_LOADING_TIME, ReplaceFile, [defaultFilter, configFilter, "Plugin: Default filter loaded"]).start()
	else:
		log("Plugin: Filter not found. Default filter will be loaded in " + str(DATABASE_LOADING_TIME) + " seconds...")
		Timer(DATABASE_LOADING_TIME, ReplaceFile, [defaultFilter, configFilter, "Plugin: Default filter loaded"]).start()

	# refresh combos so the just-created config shows up
	_populate_combos(preserve=True)

log('Plugin: ' + pName + ' v' + pVersion + ' successfully loaded')

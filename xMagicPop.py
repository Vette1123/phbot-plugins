# -*- coding: utf-8 -*-
from phBot import *
import QtBind
import time
import webbrowser

GITHUB_URL = 'https://github.com/Vette1123'

def btn_github_clicked():
    try:
        webbrowser.open(GITHUB_URL)
    except Exception:
        pass

pName = 'xMagicPop'
pVersion = '2.0.0'
pAuthor = 'Vette1123 (Gado)'
pUrl = 'https://raw.githubusercontent.com/Vette1123/phbot-plugins/main/xMagicPop.py'
# GitHub: https://github.com/Vette1123

# ============================================================
# Magic Pop loop (C->S 0x7118)
# Payload: F5 05 00 00  <type:1> 00 00 00  <slot:1> 00
# ============================================================
OPCODE = 0x7118
ENCRYPTED = False

TYPES = [
    ("Flag (M)",                  0x01),
    ("Flag (F)",                  0x04),
    ("Devil's Spirit S grade (M)", 0x05),
    ("Devil's Spirit S grade (F)", 0x06),
    ("Angel's Spirit S grade (M)", 0x07),
    ("Angel's Spirit S grade (F)", 0x08),
]

# Inventory slot bytes to spin on (slots 0x0D - 0x69, full magic pop range).
SLOTS = [
    0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
    0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24,
    0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30,
    0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C,
    0x3D, 0x3E, 0x3F, 0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48,
    0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x51, 0x52, 0x53, 0x54,
    0x55, 0x56, 0x57, 0x58, 0x59, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61,
    0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0xCB,
]

# ============================================================
# Runtime state
# ============================================================
running = False
slot_index = 0
attempts = 0
cycles = 0
last_send_time = 0.0
last_packet_text = '-'
start_time = 0.0
inventory_cache = {}  # slot_byte -> item name

# ============================================================
# GUI
# ============================================================
gui = QtBind.init(__name__, pName)

# Long placeholder so QLabel sizes wide enough for later updates (Qt labels
# don't auto-resize after setText, so short initial text would clip long values).
_PAD = ' ' * 80

# =====================================================================
# LEFT COLUMN: Settings + Controls + Status     (x = 12 .. 380)
# RIGHT COLUMN: Inventory list                  (x = 395 .. 715)
# =====================================================================

# --- LEFT: Settings ---
QtBind.createLabel(gui, '--- Settings ---', 12, 8)

QtBind.createLabel(gui, 'Magic Pop Type:', 12, 32)
combo_type = QtBind.createCombobox(gui, 130, 29, 230, 22)
for name, _ in TYPES:
    QtBind.append(gui, combo_type, name)
try:
    QtBind.setIndex(gui, combo_type, 0)
except Exception:
    pass

QtBind.createLabel(gui, 'Delay (sec):', 12, 60)
txt_delay = QtBind.createLineEdit(gui, '0', 130, 57, 70, 22)

QtBind.createLabel(gui, 'Stop after cycles:', 12, 88)
txt_max_cycles = QtBind.createLineEdit(gui, '0', 130, 85, 70, 22)
QtBind.createLabel(gui, '(0 = forever)', 210, 88)

cbx_magic_only = QtBind.createCheckBox(gui, 'cbx_magic_only_clicked',
                                       'Only play on Magic Pop items', 12, 114)
QtBind.setChecked(gui, cbx_magic_only, True)
magic_only = True

# --- LEFT: Controls ---
QtBind.createLabel(gui, '--- Controls ---', 12, 146)
QtBind.createButton(gui, 'btn_start',       '  START  ',  12, 168)
QtBind.createButton(gui, 'btn_stop',        '  STOP   ',  92, 168)
QtBind.createButton(gui, 'btn_send_once',   ' SEND ONE ', 172, 168)
QtBind.createButton(gui, 'btn_reset',       '  RESET  ', 268, 168)
QtBind.createButton(gui, 'btn_refresh_inv', '  Refresh Inventory  ', 12, 200)

# --- LEFT: Status (vertical stack) ---
QtBind.createLabel(gui, '--- Status ---', 12, 238)

_y = 262
QtBind.createLabel(gui, 'State:',        12, _y)
lbl_status   = QtBind.createLabel(gui, 'Idle' + _PAD,        110, _y)

_y += 24
QtBind.createLabel(gui, 'Current slot:', 12, _y)
lbl_slot     = QtBind.createLabel(gui, '-' + _PAD,           110, _y)

_y += 24
QtBind.createLabel(gui, 'Last sent:',    12, _y)
lbl_last     = QtBind.createLabel(gui, '-' + _PAD,           110, _y)

_y += 24
QtBind.createLabel(gui, 'Progress:',     12, _y)
lbl_progress = QtBind.createLabel(gui, 'Attempts 0  |  Cycles 0  |  Elapsed 0s' + _PAD, 110, _y)

_y += 32
QtBind.createButton(gui, 'btn_github_clicked', ' (Gado) GitHub ', 12, _y)

# --- RIGHT: Inventory ---
QtBind.createLabel(gui, '--- Inventory (Magic Pop slot range) ---', 395, 8)
lst_inv = QtBind.createList(gui, 395, 32, 320, 360)


# ============================================================
# Helpers
# ============================================================
def logx(msg):
    try:
        log('[%s] %s' % (pName, str(msg)))
    except Exception:
        pass


def set_label(label, text):
    try:
        QtBind.setText(gui, label, str(text))
    except Exception:
        pass


def get_selected_type():
    try:
        idx = QtBind.currentIndex(gui, combo_type)
        if idx is None or idx < 0 or idx >= len(TYPES):
            return TYPES[0]
        return TYPES[idx]
    except Exception:
        return TYPES[0]


def get_delay_seconds():
    try:
        s = QtBind.text(gui, txt_delay).strip()
        v = float(s) if s else 0.0
        return max(0.0, v)
    except Exception:
        return 0.0


def get_max_cycles():
    try:
        s = QtBind.text(gui, txt_max_cycles).strip()
        v = int(s) if s else 0
        return max(0, v)
    except Exception:
        return 0


def cbx_magic_only_clicked(checked):
    global magic_only
    magic_only = checked


BURST_PER_TICK = 15  # max sends per event_loop call when delay <= 0


def is_magic_pop_item(item):
    if not item:
        return False
    sn = (item.get('servername') or '').upper()
    nm = (item.get('name') or '').lower()
    return 'MAGIC_POP' in sn or 'MAGICPOP' in sn or 'magic pop' in nm


def payload_hex(data):
    try:
        return ' '.join('%02X' % b for b in bytearray(data))
    except Exception:
        return str(data)


def make_payload(type_byte, slot_byte):
    return bytearray([0xF5, 0x05, 0x00, 0x00,
                      type_byte, 0x00, 0x00, 0x00,
                      slot_byte, 0x00])


def _friendly_item_name(item):
    """Return a clean display name, avoiding raw codes like ITEM_ETC_..."""
    name = item.get('name')
    if name and not name.startswith('ITEM_') and not name.startswith('MAGICOPTION_'):
        return name
    sn = item.get('servername', '')
    if sn:
        # ITEM_ETC_E101216_MAGIC_POP_NORMAL -> "Magic Pop Normal"
        s = sn
        for prefix in ('ITEM_ETC_', 'ITEM_'):
            if s.startswith(prefix):
                s = s[len(prefix):]
                break
        # drop leading code like E101216_
        parts = s.split('_')
        if parts and len(parts[0]) > 2 and parts[0][0].isalpha() and parts[0][1:].isdigit():
            parts = parts[1:]
        return ' '.join(w.capitalize() for w in parts) if parts else (name or sn)
    return name or '?'


def refresh_inventory():
    """Read inventory -> per-slot {pretty, magic} dicts."""
    global inventory_cache
    inventory_cache = {}
    try:
        inv = get_inventory()
        items = inv.get('items', []) if inv else []
        for slot, item in enumerate(items):
            if item:
                pretty = _friendly_item_name(item)
                qty = item.get('quantity', 1)
                disp = '%s  x%d' % (pretty, qty) if qty > 1 else pretty
                inventory_cache[slot] = {'pretty': disp, 'magic': is_magic_pop_item(item)}
    except Exception as e:
        logx('refresh_inventory error: %s' % e)

    QtBind.clear(gui, lst_inv)
    filled = 0
    magic = 0
    for sb in SLOTS:
        info = inventory_cache.get(sb)
        if info:
            marker = '[POP]' if info['magic'] else '     '
            line = '%s Slot %3d   %s' % (marker, sb, info['pretty'])
            filled += 1
            if info['magic']:
                magic += 1
        else:
            line = '      Slot %3d   --' % sb
        QtBind.append(gui, lst_inv, line)
    logx('Inventory refresh: %d filled / %d Magic Pop / %d total slots'
         % (filled, magic, len(SLOTS)))


def slot_is_playable(sb):
    info = inventory_cache.get(sb)
    if not info:
        return False
    if magic_only and not info['magic']:
        return False
    return True


def slot_display(sb):
    info = inventory_cache.get(sb)
    return info['pretty'] if info else '(empty)'


def current_slot_byte():
    if not SLOTS:
        return None
    return SLOTS[slot_index % len(SLOTS)]


def advance_slot():
    """Move forward to next playable slot. Returns True if found; increments cycle on wrap."""
    global slot_index, cycles
    n = len(SLOTS)
    if n == 0:
        return False
    for _ in range(n):
        slot_index = (slot_index + 1) % n
        if slot_index == 0:
            cycles += 1
            logx('Cycle complete #%d' % cycles)
        if slot_is_playable(SLOTS[slot_index]):
            return True
    return False


def find_first_usable_slot():
    global slot_index
    n = len(SLOTS)
    if n == 0:
        return False
    for i in range(n):
        if slot_is_playable(SLOTS[i]):
            slot_index = i
            return True
    return False


def update_status_panel():
    set_label(lbl_status, 'Running' if running else 'Idle')
    sb = current_slot_byte()
    if sb is None:
        set_label(lbl_slot, '-')
    else:
        set_label(lbl_slot, 'Slot %d  (%d / %d)   %s'
                  % (sb, (slot_index % len(SLOTS)) + 1, len(SLOTS), slot_display(sb)))
    set_label(lbl_last, last_packet_text)
    elapsed = int(time.time() - start_time) if start_time > 0 else 0
    set_label(lbl_progress,
              'Attempts %d   |   Cycles %d   |   Elapsed %ds'
              % (attempts, cycles, elapsed))


def send_current_slot(quiet=False):
    global attempts, last_send_time, last_packet_text
    sb = current_slot_byte()
    if sb is None:
        set_label(lbl_status, 'No slots')
        return False

    type_name, type_byte = get_selected_type()
    data = make_payload(type_byte, sb)
    try:
        inject_joymax(OPCODE, data, ENCRYPTED)
    except Exception as e:
        set_label(lbl_status, 'Error')
        logx('inject error: %s' % e)
        return False

    attempts += 1
    last_send_time = time.time()
    last_packet_text = '%s  -  Slot %d  -  %s' % (type_name, sb, slot_display(sb))
    if not quiet:
        logx('SENT %s' % last_packet_text)
    return True


# ============================================================
# Buttons
# ============================================================
def btn_start():
    global running, attempts, cycles, last_send_time, start_time
    if running:
        return
    refresh_inventory()
    if not find_first_usable_slot():
        set_label(lbl_status, 'No usable slot')
        logx('Start aborted: no playable slot (magic_only=%s)' % magic_only)
        return
    running = True
    attempts = 0
    cycles = 0
    last_send_time = 0.0
    start_time = time.time()
    t = get_selected_type()
    logx('Started | Type=%s | Delay=%.2fs | MaxCycles=%d | Slots=%d | MagicOnly=%s'
         % (t[0], get_delay_seconds(), get_max_cycles(), len(SLOTS), magic_only))
    # send first, then loop in event_loop
    send_current_slot()
    update_status_panel()


def btn_stop():
    global running
    if not running:
        return
    running = False
    set_label(lbl_status, 'Stopped')
    logx('Stopped after %d attempts, %d cycles' % (attempts, cycles))


def btn_send_once():
    refresh_inventory()
    send_current_slot()
    update_status_panel()


def btn_reset():
    global slot_index, attempts, cycles, last_send_time, last_packet_text, start_time
    slot_index = 0
    attempts = 0
    cycles = 0
    last_send_time = 0.0
    last_packet_text = '-'
    start_time = 0.0
    set_label(lbl_status, 'Idle')
    update_status_panel()
    logx('Reset')


def btn_refresh_inv():
    refresh_inventory()
    update_status_panel()
    logx('Inventory refreshed (%d items in range)' % len(inventory_cache))


# ============================================================
# phBot events
# ============================================================
def event_loop():
    global running
    try:
        if not running:
            return True
        max_c = get_max_cycles()
        delay = get_delay_seconds()

        if delay <= 0:
            # BURST: blast through up to BURST_PER_TICK sends in one tick
            sent = 0
            while sent < BURST_PER_TICK:
                if max_c > 0 and cycles >= max_c:
                    running = False
                    set_label(lbl_status, 'Done (%d cycles)' % cycles)
                    logx('Reached cycle limit %d - stopping' % max_c)
                    return True
                if not advance_slot():
                    running = False
                    set_label(lbl_status, 'No playable slots left')
                    logx('No playable slots - stopping')
                    return True
                send_current_slot(quiet=True)
                sent += 1
        else:
            if max_c > 0 and cycles >= max_c:
                running = False
                set_label(lbl_status, 'Done (%d cycles)' % cycles)
                return True
            if time.time() - last_send_time >= delay:
                if not advance_slot():
                    running = False
                    set_label(lbl_status, 'No playable slots left')
                    return True
                send_current_slot()

        update_status_panel()
    except Exception as e:
        logx('event_loop error: %s' % e)
    return True


def joined_game():
    refresh_inventory()
    update_status_panel()
    return True


def disconnected():
    global running
    running = False
    set_label(lbl_status, 'Disconnected')
    logx('Disconnected - stopped')
    return True


# Boot
try:
    refresh_inventory()
except Exception:
    pass
update_status_panel()
logx('Loaded v%s' % pVersion)

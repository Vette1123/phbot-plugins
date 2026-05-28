# -*- coding: utf-8 -*-
from phBot import *
import QtBind
import ctypes
from ctypes import wintypes
import json
import os
import time
import webbrowser

pName = 'xSpeedSpear'
pVersion = '3.1.0'
pAuthor = 'Vette1123 (Gado)'
pUrl = ''

GITHUB_URL = 'https://github.com/Vette1123'
GITHUB_BTN_STYLE = (
    'QPushButton{background:#ffd54a;color:#222;font-weight:bold;'
    'border:1px solid #8b6b00;border-radius:6px;padding:2px 10px;}'
    'QPushButton:hover{background:#ffe27a;}'
)

def btn_github_clicked(*_):
    try:
        webbrowser.open(GITHUB_URL)
    except Exception:
        pass

def _try_style_github(btn):
    for fn_name in ('setStyleSheet', 'setStylesheet', 'setStyle'):
        fn = getattr(QtBind, fn_name, None)
        if callable(fn):
            try:
                fn(gui, btn, GITHUB_BTN_STYLE)
                return
            except Exception:
                pass

# ============================================================
# Speed-bug helper. Sends quickbar keystrokes to the Silkroad
# client window. Hardcoded to your spear setup:
#   speed = F2 page, slot 1
#   imbue = F2 page, slot 2
# Override via xSpeedSpear.json if needed.
# ============================================================

CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xSpeedSpear.json')

DEFAULT_CONFIG = {
    'enabled': True,
    'speed_cooldown_ms': 1000,
    'imbue_cooldown_ms': 20000,
    'page_key':   'F2',   # quickbar page where speed + imbue live
    'speed_slot': '1',    # slot number on that page for speed
    'imbue_slot': '2',    # slot number on that page for imbue
    'window_match': '',          # blank = auto from character name
    'window_class': 'SRClient',
    'background_focus': True,    # focus-borrow when game is in background
}
cfg = json.loads(json.dumps(DEFAULT_CONFIG))

def load_config():
    global cfg
    try:
        if os.path.exists(CFG_PATH):
            with open(CFG_PATH, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            merged = json.loads(json.dumps(DEFAULT_CONFIG))
            for k, v in loaded.items():
                merged[k] = v
            cfg = merged
    except Exception as e:
        log('[xSpeedSpear] load_config: %s' % e)

def save_config():
    try:
        with open(CFG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        log('[xSpeedSpear] save_config: %s' % e)

load_config()

# ============================================================
# Win32 helpers
# ============================================================
user32 = ctypes.windll.user32
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype  = wintypes.BOOL
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype  = ctypes.c_int
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype  = ctypes.c_int
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype  = wintypes.BOOL
user32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]
user32.MapVirtualKeyW.restype  = ctypes.c_uint

WM_KEYDOWN = 0x0100
WM_KEYUP   = 0x0101

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype  = wintypes.BOOL

EnumChildProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumChildWindows.argtypes = [wintypes.HWND, EnumChildProc, wintypes.LPARAM]
user32.EnumChildWindows.restype  = wintypes.BOOL

def _window_title(hwnd):
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, buf, 512)
    return buf.value

def _window_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value

def _resolve_match():
    m = (cfg.get('window_match') or '').strip()
    if m:
        return m
    try:
        ch = get_character_data() or {}
        return (ch.get('name') or '').strip()
    except Exception:
        return ''

def find_game_window():
    match = _resolve_match().lower()
    want_class = (cfg.get('window_class') or '').strip().lower()
    found = [None]
    def cb(hwnd, _lp):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _window_title(hwnd)
        cls = _window_class(hwnd)
        if match and match in title.lower():
            found[0] = hwnd
            return False
        if not match and want_class and cls.lower() == want_class:
            found[0] = hwnd
            return False
        return True
    user32.EnumWindows(EnumWindowsProc(cb), 0)
    return found[0]

_VK_NAMED = {
    'SPACE': 0x20, 'TAB': 0x09, 'ENTER': 0x0D,
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73,
    'F5': 0x74, 'F6': 0x75, 'F7': 0x76, 'F8': 0x77,
}

def parse_vk(s):
    if not s: return None
    s = s.strip().upper()
    if s in _VK_NAMED: return _VK_NAMED[s]
    if s.startswith('F') and s[1:].isdigit():
        n = int(s[1:])
        if 1 <= n <= 24: return 0x6F + n
    if len(s) == 1 and (s.isdigit() or ('A' <= s <= 'Z')):
        return ord(s)
    return None

def _lp(vk, key_up):
    scan = user32.MapVirtualKeyW(vk, 0) & 0xFF
    lp = 1
    lp |= (scan & 0xFF) << 16
    if key_up:
        lp |= (1 << 30); lp |= (1 << 31)
    return lp

_child_cache = {}

def _input_targets(hwnd):
    now = time.time()
    cached = _child_cache.get(hwnd)
    if cached and now - cached[0] < 30.0:
        return cached[1]
    kids = []
    def cb(h, _lp):
        kids.append(h); return True
    user32.EnumChildWindows(hwnd, EnumChildProc(cb), 0)
    targets = [hwnd] + kids
    _child_cache[hwnd] = (now, targets)
    return targets

# --- keybd_event path (works only when game window has foreground focus) ---
user32.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_uint, ctypes.c_void_p]
user32.keybd_event.restype  = None
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype  = wintypes.BOOL
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype  = wintypes.HWND
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.AttachThreadInput.restype  = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype  = wintypes.DWORD
kernel32 = ctypes.windll.kernel32
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_SCANCODE    = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

def _send_via_keybd(vk):
    scan = user32.MapVirtualKeyW(vk, 0) & 0xFF
    user32.keybd_event(vk, scan, 0, 0)
    user32.keybd_event(vk, scan, KEYEVENTF_KEYUP, 0)

def _post_key_to(hwnd, vk):
    """PostMessage to top-level + every child. Works when window is
    foreground; sometimes works in background depending on the game."""
    for h in _input_targets(hwnd):
        try:
            user32.PostMessageW(h, WM_KEYDOWN, vk, _lp(vk, False))
            user32.PostMessageW(h, WM_KEYUP,   vk, _lp(vk, True))
        except Exception:
            pass

def _post_key(hwnd, vk):
    """Always post to the game window hierarchy (silent, background-safe).
    Additionally, if the game already has foreground focus, also send a
    real keybd_event keystroke — that's what DirectInput games actually
    listen to. We never steal focus."""
    _post_key_to(hwnd, vk)
    try:
        if user32.GetForegroundWindow() == hwnd:
            _send_via_keybd(vk)
    except Exception:
        pass

def cast_slot(hwnd, slot_key):
    """Switch to the configured quickbar page, then press the slot key."""
    if not hwnd: return False
    page_vk = parse_vk(cfg.get('page_key', 'F2'))
    slot_vk = parse_vk(slot_key)
    if not page_vk or not slot_vk: return False
    try:
        _post_key(hwnd, page_vk)   # ensure F2 page is active
        _post_key(hwnd, slot_vk)   # press slot digit
        return True
    except Exception as e:
        log('[xSpeedSpear] cast_slot failed: %s' % e)
        return False

# ============================================================
# Runtime state
# ============================================================
last_speed_at = 0.0
last_imbue_at = 0.0
stats = {'speeds': 0, 'imbues': 0}
_last_tick_at = 0.0
_last_debug_at = 0.0
_cached_hwnd = None
_cached_hwnd_at = 0.0
_last_saved_snapshot = None

def _hwnd():
    global _cached_hwnd, _cached_hwnd_at
    now = time.time()
    if _cached_hwnd and (now - _cached_hwnd_at) < 5.0:
        return _cached_hwnd
    _cached_hwnd = find_game_window()
    _cached_hwnd_at = now
    return _cached_hwnd

def _in_game():
    try:    return bool(get_character_data())
    except: return False

def _can_speed(now): return (now - last_speed_at) * 1000.0 >= cfg.get('speed_cooldown_ms', 1000)
def _can_imbue(now): return (now - last_imbue_at) * 1000.0 >= cfg.get('imbue_cooldown_ms', 20000)

def _autosave_if_changed():
    """Snapshot the UI into cfg and save to JSON if anything changed."""
    global _last_saved_snapshot
    try:
        _pull_ui_into_cfg()
    except Exception:
        return
    snap = json.dumps(cfg, sort_keys=True)
    if snap != _last_saved_snapshot:
        _last_saved_snapshot = snap
        save_config()

def event_loop():
    global last_speed_at, last_imbue_at, _last_tick_at, _last_debug_at
    now = time.time()
    if now - _last_tick_at < 0.1:
        return True
    _last_tick_at = now
    _autosave_if_changed()
    if not cfg.get('enabled') or not _in_game():
        return True
    hwnd = _hwnd()
    if not hwnd:
        if now - _last_debug_at > 10.0:
            _last_debug_at = now
            log('[xSpeedSpear] tick — window not found (match=%r)' % _resolve_match())
        return True
    if _can_speed(now) and cast_slot(hwnd, cfg.get('speed_slot', '1')):
        last_speed_at = now
        stats['speeds'] += 1
    if _can_imbue(now) and cast_slot(hwnd, cfg.get('imbue_slot', '2')):
        last_imbue_at = now
        stats['imbues'] += 1
    _refresh_status()
    return True

# ============================================================
# GUI — minimal
# ============================================================
gui = QtBind.init(__name__, pName)
_PAD = ' ' * 80

QtBind.createLabel(gui, 'Speed-bug helper. Defaults: speed = F2/slot 1,  imbue = F2/slot 2.', 12, 8)
QtBind.createLabel(gui, 'Make sure those skillbar slots are bound in the game client.', 12, 26)

cb_enabled = QtBind.createCheckBox(gui, 'cb_enabled_clicked', 'Active', 12, 52)
if cfg.get('enabled'):
    QtBind.setChecked(gui, cb_enabled, True)

QtBind.createLabel(gui, 'Speed cd (ms):', 12, 84)
tb_speedcd = QtBind.createLineEdit(gui, str(cfg['speed_cooldown_ms']), 110, 82, 60, 22)
QtBind.createLabel(gui, 'Imbue cd (ms):', 190, 84)
tb_imbuecd = QtBind.createLineEdit(gui, str(cfg['imbue_cooldown_ms']), 290, 82, 65, 22)

QtBind.createLabel(gui, 'Page (F1..F4):', 12, 116)
tb_page = QtBind.createLineEdit(gui, str(cfg.get('page_key', 'F2')), 110, 114, 50, 22)
QtBind.createLabel(gui, 'Speed slot:', 190, 116)
tb_speed_slot = QtBind.createLineEdit(gui, str(cfg.get('speed_slot', '1')), 265, 114, 40, 22)
QtBind.createLabel(gui, 'Imbue slot:', 330, 116)
tb_imbue_slot = QtBind.createLineEdit(gui, str(cfg.get('imbue_slot', '2')), 405, 114, 40, 22)
QtBind.createLabel(gui, '(slots: 1..9 or 0 for the 10th)', 460, 116)

btn_save     = QtBind.createButton(gui, 'btn_save_clicked',     '      Save      ',  12, 150)
btn_test_spd = QtBind.createButton(gui, 'btn_test_spd_clicked', '   Test SPEED   ', 120, 150)
btn_test_imb = QtBind.createButton(gui, 'btn_test_imb_clicked', '   Test IMBUE   ', 240, 150)
btn_findwin  = QtBind.createButton(gui, 'btn_findwin_clicked',  '   Find window   ',360, 150)
btn_github   = QtBind.createButton(gui, 'btn_github_clicked',   '  ⭐  Gado  ⭐  ',   490, 150)
_try_style_github(btn_github)

lbl_state = QtBind.createLabel(gui, '-' + _PAD, 12, 186)
lbl_hwnd  = QtBind.createLabel(gui, 'window: -' + _PAD, 12, 206)

def _pull_ui_into_cfg():
    cfg['enabled'] = bool(QtBind.isChecked(gui, cb_enabled))
    try: cfg['speed_cooldown_ms'] = int(QtBind.text(gui, tb_speedcd))
    except: pass
    try: cfg['imbue_cooldown_ms'] = int(QtBind.text(gui, tb_imbuecd))
    except: pass
    try:
        v = QtBind.text(gui, tb_page).strip().upper()
        if v in ('F1','F2','F3','F4'):
            cfg['page_key'] = v
    except: pass
    try:
        v = QtBind.text(gui, tb_speed_slot).strip()
        if v in ('0','1','2','3','4','5','6','7','8','9'):
            cfg['speed_slot'] = v
    except: pass
    try:
        v = QtBind.text(gui, tb_imbue_slot).strip()
        if v in ('0','1','2','3','4','5','6','7','8','9'):
            cfg['imbue_slot'] = v
    except: pass

def cb_enabled_clicked(*_):
    cfg['enabled'] = bool(QtBind.isChecked(gui, cb_enabled))
    _refresh_status()

def btn_save_clicked(*_):
    _pull_ui_into_cfg()
    save_config()
    log('[xSpeedSpear] saved — page=%s speed_slot=%s imbue_slot=%s' % (
        cfg['page_key'], cfg['speed_slot'], cfg['imbue_slot']))

def btn_test_spd_clicked(*_):
    _pull_ui_into_cfg()
    hwnd = _hwnd()
    ok = cast_slot(hwnd, cfg.get('speed_slot', '1'))
    log('[xSpeedSpear] TEST speed — hwnd=%s page=%s slot=%s ok=%s' % (
        hwnd, cfg['page_key'], cfg['speed_slot'], ok))

def btn_test_imb_clicked(*_):
    _pull_ui_into_cfg()
    hwnd = _hwnd()
    ok = cast_slot(hwnd, cfg.get('imbue_slot', '2'))
    log('[xSpeedSpear] TEST imbue — hwnd=%s page=%s slot=%s ok=%s' % (
        hwnd, cfg['page_key'], cfg['imbue_slot'], ok))

def btn_findwin_clicked(*_):
    global _cached_hwnd, _cached_hwnd_at
    _cached_hwnd = None; _cached_hwnd_at = 0
    hwnd = _hwnd()
    if hwnd:
        log('[xSpeedSpear] window found — hwnd=%s title=%r class=%r' % (hwnd, _window_title(hwnd), _window_class(hwnd)))
    else:
        log('[xSpeedSpear] window NOT found  (match=%r class=%r)' % (_resolve_match(), cfg.get('window_class')))
    _refresh_status()

def _refresh_status():
    try:
        hwnd = _hwnd()
        if cfg.get('enabled') and _in_game():
            state = 'Active'
        elif cfg.get('enabled'):
            state = 'Active (waiting for character)'
        else:
            state = 'Disabled'
        QtBind.setText(gui, lbl_state,
            '%s   speeds:%d  imbues:%d' % (state, stats['speeds'], stats['imbues']))
        if hwnd:
            QtBind.setText(gui, lbl_hwnd, 'window: hwnd=%s title=%r' % (hwnd, _window_title(hwnd)))
        else:
            QtBind.setText(gui, lbl_hwnd, 'window: NOT FOUND — click Find window')
    except Exception:
        pass

# Baseline snapshot so we don't write the JSON on the very first tick.
try:
    _pull_ui_into_cfg()
    _last_saved_snapshot = json.dumps(cfg, sort_keys=True)
except Exception:
    pass

_refresh_status()

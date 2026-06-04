# -*- coding: utf-8 -*-
from phBot import *
import QtBind
import os
import time
import json
import struct
import webbrowser
from threading import Timer

pName = "xJupiter"
pVersion = "4.5"
pAuthor = 'Vette1123 (Gado)'
pUrl = 'https://raw.githubusercontent.com/Vette1123/phbot-plugins/main/xJupiter.py'
GITHUB_URL = 'https://github.com/Vette1123'
gui = QtBind.init(__name__, pName)

# ========================= Hidden packets ========================= #
def b(hexstr):
    hexstr = (hexstr or "").replace(" ", "")
    return bytes.fromhex(hexstr) if hexstr else b""

PACKET_DELAY_DEFAULT = 3.0
ENTRY_WAIT_DEFAULT = 2.0
NO_UNIQUE_WAIT_DEFAULT = 2.0
CLEAR_WAIT_DEFAULT = 10.0
AFTER_KILL_WAIT_DEFAULT = 15.0
EXIT_WAIT_DEFAULT = 5.0
BACK_MAX_SECONDS = 90.0  # maximum movement time for reversed back script, not after-kill wait
ARRIVAL_TOLERANCE = 3.0
BACK_MIN_CHECK_SECONDS = 3.0
SPAWN_SUPPRESS_SECONDS = 600.0  # prevents re-queueing a target just finished/killed

ROOM_PACKETS = {
    "The Earth": {
        "entry": [(0x7045, b("12 04 00 00")), (0x705A, b("12 04 00 00 02 89 01 00 00"))],
        "exit":  [(0x7045, b("3A 01 00 00")), (0x705A, b("3A 01 00 00 02 B2 01 00 00"))],
    },
    "Yuno": {
        "entry": [(0x7045, b("12 04 00 00")), (0x705A, b("12 04 00 00 02 8A 01 00 00"))],
        "exit":  [(0x7045, b("3B 01 00 00")), (0x705A, b("3B 01 00 00 02 B2 01 00 00"))],
    },
    "Jupiter": {
        "entry": [(0x7045, b("12 04 00 00")), (0x705A, b("12 04 00 00 02 8B 01 00 00"))],
        "exit":  [(0x7045, b("3C 01 00 00")), (0x705A, b("3C 01 00 00 02 B2 01 00 00"))],
    },
    "Zealots": {
        "entry": [(0x7045, b("12 04 00 00")), (0x705A, b("12 04 00 00 02 8C 01 00 00"))],
        "exit":  [(0x7045, b("4E 00 00 00")), (0x705A, b("4E 00 00 00 02 D1 00 00 00"))],
    },
}

# ========================= Walk scripts ========================= #
TARGETS = [
    {
        "name": "The Earth",
        "room": "The Earth",
        "aliases": ["the earth"],
        "walk": [
            "walk,-32749,-20832,101,-134",
            "walk,-32749,-20830,112,-134",
        ],
    },
    {
        "name": "Yuno",
        "room": "Yuno",
        "aliases": ["yuno"],
        "walk": [
            "walk,-32748,-20640,101,-134",
            "walk,-32748,-20639,116,-134",
        ],
    },
    {
        "name": "Jupiter",
        "room": "Jupiter",
        "aliases": ["jupiter"],
        "walk": [
            "walk,-32747,-20447,115,-134",
            "walk,-32747,-20448,101,-134",
        ],
    },
    {
        "name": "Baal",
        "room": "Zealots",
        "aliases": ["baal"],
        # Custom exit route for Baal.
        # This route is used before the Zealots exit teleport.
        "back_walk": [
            "walk,-32746,-20184,101,1",
            "walk,-32746,-20201,88,1",
            "walk,-32746,-20193,94,1",
        ],
        "exit_packets": [(0x7045, b("48 00 00 00")), (0x705A, b("48 00 00 00 02 D1 00 00 00"))],
        "walk": [
            "walk,-32746,-20203,85,1",
            "walk,-32746,-20336,10,1",
            "walk,-32746,-20319,19,1",
            "walk,-32746,-20302,28,1",
            "walk,-32746,-20284,39,1",
            "walk,-32746,-20268,48,1",
            "walk,-32746,-20253,56,1",
            "walk,-32746,-20240,64,1",
            "walk,-32746,-20227,71,1",
            "walk,-32746,-20212,80,1",
        ],
    },
    {
        "name": "Zieliaxe",
        "room": "Zealots",
        "aliases": ["zieliaxe", "zielkiaxe"],
        # Custom exit route and teleport packet for Zieliaxe only.
        # This is used instead of reversing the entry route.
        "back_walk": [
            "walk,-32746,-20349,-194,1",
            "walk,-32746,-20351,-177,1",
            "walk,-32746,-20350,-183,1",
            "walk,-32746,-20350,-189,1",
        ],
        "exit_packets": [(0x7045, b("4F 00 00 00")), (0x705A, b("4F 00 00 00 02 D1 00 00 00"))],
        "walk": [
            "walk,-32746,-20351,-169,1",
            "walk,-32746,-20352,-11,1",
            "walk,-32746,-20352,-35,1",
            "walk,-32746,-20352,-52,1",
            "walk,-32746,-20352,-69,1",
            "walk,-32746,-20352,-84,1",
            "walk,-32746,-20351,-100,1",
            "walk,-32746,-20351,-116,1",
            "walk,-32746,-20352,-129,1",
            "walk,-32746,-20352,-143,1",
            "walk,-32746,-20352,-155,1",
        ],
    },
    {
        "name": "Babilion",
        "room": "Zealots",
        "aliases": ["babilion", "babilon", "babylon"],
        # Custom exit route and teleport packet for Babilion.
        # This is used instead of reversing the entry route.
        "back_walk": [
            "walk,-32746,-20523,91,1",
            "walk,-32746,-20502,82,1",
            "walk,-32746,-20512,86,1",
        ],
        "exit_packets": [(0x7045, b("50 00 00 00")), (0x705A, b("50 00 00 00 02 D1 00 00 00"))],
        "walk": [
            "walk,-32746,-20500,85,1",
            "walk,-32746,-20364,7,1",
            "walk,-32746,-20384,19,1",
            "walk,-32746,-20402,29,1",
            "walk,-32746,-20419,39,1",
            "walk,-32746,-20437,49,1",
            "walk,-32746,-20453,58,1",
            "walk,-32746,-20470,68,1",
            "walk,-32746,-20485,76,1",
        ],
    },
]

# ========================= UI ========================= #
# Two-column layout that uses the full plugin width (matches xMagicPop):
#   LEFT  (x ~10..360) : controls, settings, target table
#   RIGHT (x ~420..710): live status panel
# QtBind labels size to their INITIAL text and do not grow on setText, so every
# label that updates at runtime is padded with trailing spaces to reserve room
# for its longest future value (otherwise the queue list, character name, kill
# timers, etc. clip). Vertical footprint stays under ~300px so nothing is cut
# off at the panel's bottom edge.

# Heading / accent colors used across the panel.
COL_HEAD = (170, 190, 255)   # section headers
COL_GOLD = (255, 215, 0)
COL_CYAN = (120, 200, 255)
COL_GREEN = (150, 220, 150)
COL_AMBER = (255, 200, 120)


def _mklabel(text, x, y, pad=0, color=None):
    if pad is True:
        pad = 30
    lbl = QtBind.createLabel(gui, text + (" " * pad if pad else ""), x, y)
    if color:
        try:
            QtBind.setColor(gui, lbl, *color)
        except:
            pass
    return lbl


def _style(widget, css):
    # setStyleSheet is optional in some QtBind builds; fail silently if absent.
    for fn_name in ("setStyleSheet", "setStylesheet", "setStyle"):
        fn = getattr(QtBind, fn_name, None)
        if callable(fn):
            try:
                fn(gui, widget, css)
                return True
            except Exception:
                pass
    return False


def _btn_css(bg, bg_hover, fg="#ffffff"):
    return ("QPushButton{background:%s;color:%s;font-weight:bold;"
            "border:1px solid #00000055;border-radius:6px;padding:3px 10px;}"
            "QPushButton:hover{background:%s;}"
            "QPushButton:pressed{background:%s;}" % (bg, fg, bg_hover, bg))


_CSS_AMBER = _btn_css("#e0a82e", "#f2bd47", "#222222")
_CSS_GREEN = _btn_css("#2e9e57", "#38b866")
_CSS_RED = _btn_css("#c0392b", "#d8493a")
_CSS_SLATE = _btn_css("#3a4a5a", "#4a5d70")
_CSS_BLUE = _btn_css("#2f6fb0", "#3a83ce")
_CSS_GOLD = _btn_css("#ffd54a", "#ffe27a", "#222222")

# --- Header ---
lbl_title = _mklabel("<b>⚔️ xJupiter ⚔️</b>", 320, 6, color=COL_GOLD)
btn_github = QtBind.createButton(gui, "btn_github_clicked", "  ⭐  (Gado) GitHub  ⭐  ", 530, 2)
_style(btn_github, _CSS_GOLD)
lbl_power = _mklabel("<b>🔴 OFF</b> | 👁️ Monitor: Active", 10, 30, pad=20, color=(255, 80, 80))
lbl_account = _mklabel("<b>👤 Loading...</b>", 300, 30, pad=24, color=(80, 180, 255))

# --- Controls (left) ---
cbx_enabled = QtBind.createCheckBox(gui, "cbx_enabled_clicked", "🟢 Enable", 10, 54)
btn_standby = QtBind.createButton(gui, "btn_standby_clicked", "🟡 Standby", 120, 52)
btn_search = QtBind.createButton(gui, "btn_search_clicked", "🔍 Search", 225, 52)
btn_stop = QtBind.createButton(gui, "btn_stop_clicked", "⛔ Stop", 320, 52)
_style(btn_standby, _CSS_AMBER)
_style(btn_search, _CSS_GREEN)
_style(btn_stop, _CSS_RED)

btn_update = QtBind.createButton(gui, "btn_update_clicked", "🔄 Update", 10, 80)
btn_save = QtBind.createButton(gui, "btn_save_clicked", "💾 Save", 110, 80)
btn_load = QtBind.createButton(gui, "btn_load_clicked", "📂 Load", 195, 80)
for _b in (btn_update, btn_save, btn_load):
    _style(_b, _CSS_SLATE)

# Auto-use scrolls is a toggle (a control), so it lives with the other controls;
# its "Used" counter lives with the stats on the right.
cbx_autoscroll = QtBind.createCheckBox(gui, "cbx_autoscroll_clicked", "📜 Auto-use scrolls", 280, 82)
QtBind.setChecked(gui, cbx_autoscroll, True)

# --- Settings row (left) ---
QtBind.createLabel(gui, "⚔️ Range:", 10, 108)
tbx_attack_range = QtBind.createLineEdit(gui, "45", 78, 106, 42, 20)
QtBind.createLabel(gui, "⏳ Kill:", 135, 108)
tbx_after_kill_wait = QtBind.createLineEdit(gui, "15", 185, 106, 42, 20)
QtBind.createLabel(gui, "🕒 No-unq:", 240, 108)
tbx_no_unique_wait = QtBind.createLineEdit(gui, "2", 330, 106, 42, 20)

# --- Section headers ---
_mklabel("<b>🎯 Unique</b>", 10, 134, color=COL_HEAD)
_mklabel("<b>☠️</b>", 152, 134, color=COL_HEAD)
_mklabel("<b>⏱️ Dead</b>", 195, 134, color=COL_HEAD)
_mklabel("<b>🚀</b>", 290, 134, color=COL_HEAD)
_mklabel("<b>📊 Status</b>", 420, 134, color=COL_HEAD)

# --- Target table (left) ---
target_widgets = {}
y = 156
for i, t in enumerate(TARGETS):
    cb = QtBind.createCheckBox(gui, "target_checkbox_clicked", "✅ " + t["name"], 10, y)
    QtBind.setChecked(gui, cb, True)
    kill = _mklabel("<b>0</b>", 152, y + 2, pad=4, color=COL_GOLD)
    last = _mklabel("--", 195, y + 2, pad=12)
    go = QtBind.createButton(gui, "go_%d_clicked" % i, "➡️ Go", 290, y - 2)
    _style(go, _CSS_BLUE)
    target_widgets[t["name"]] = {"cb": cb, "kill": kill, "last": last, "go": go}
    y += 22

# --- Status panel (right): all live stats grouped together ---
lbl_status = _mklabel("📌 Stopped", 420, 156, pad=30)
lbl_active = _mklabel("🎯 None", 420, 174, pad=30, color=COL_GREEN)
lbl_mode = _mklabel("⚙️ None", 420, 192, pad=30)
lbl_total = _mklabel("☠️ Kills: 0", 420, 210, pad=30, color=COL_GOLD)
lbl_runtime = _mklabel("⏱️ 00:00:00", 420, 228, pad=30, color=COL_CYAN)
lbl_queue = _mklabel("📥 Empty", 420, 246, pad=52, color=COL_AMBER)
lbl_scrolls = _mklabel("📜 Used: 0", 420, 264, pad=20, color=COL_GREEN)

# ========================= State ========================= #
PLUGIN_ENABLED = False
MODE = "stopped"  # stopped/search/standby
PENDING_STANDBY = False
ACTIVE = None
ACTIVE_SEEN = False
ACTIVE_KILL_CONFIRMED = False
ACTIVE_COUNTED = False
ACTIVE_STARTED_AT = 0
BACK_STARTED_TS = 0
QUEUE = []
SEARCH_VISITED = set()
STOP_REQUESTED = False
RUN_STARTED = 0
TIMER = None
TOKEN = 0
COUNTS = {t["name"]: 0 for t in TARGETS}
LAST_DEAD = {t["name"]: 0 for t in TARGETS}
RECENTLY_HANDLED_UNTIL = {t["name"]: 0 for t in TARGETS}
TOTAL_KILLS = 0
MONITOR_STAGE = ""
STAGE_TS = 0
SCRIPT_FINISH_WAIT = 0
BACK_ROUTE_LINES = []
BACK_ROUTE_INDEX = 0
BACK_STEP_TS = 0
BACK_STEP_TIMEOUT = 12.0

# ========================= Helpers ========================= #
def _log(msg):
    log("[%s] %s" % (pName, msg))

def _now():
    return time.time()

def _safe_float(text, default):
    try:
        return float(str(text).strip())
    except:
        return float(default)

def _attack_range():
    return max(5.0, _safe_float(QtBind.text(gui, tbx_attack_range), 45.0))

def _after_kill_wait():
    return max(0.0, _safe_float(QtBind.text(gui, tbx_after_kill_wait), AFTER_KILL_WAIT_DEFAULT))

def _no_unique_wait():
    return max(0.0, _safe_float(QtBind.text(gui, tbx_no_unique_wait), NO_UNIQUE_WAIT_DEFAULT))

def _active_targets():
    out = []
    for t in TARGETS:
        try:
            if QtBind.isChecked(gui, target_widgets[t["name"]]["cb"]):
                out.append(t["name"])
        except:
            pass
    return out

def _is_recently_handled(name):
    try:
        return _now() < float(RECENTLY_HANDLED_UNTIL.get(name, 0) or 0)
    except:
        return False

def _suppress_spawn(name, seconds=SPAWN_SUPPRESS_SECONDS):
    try:
        RECENTLY_HANDLED_UNTIL[name] = _now() + float(seconds)
    except:
        pass

def _target_by_name(name):
    n = (name or "").strip().lower()
    for t in TARGETS:
        names = [t["name"].lower()] + [a.lower() for a in t.get("aliases", [])]
        if n in names:
            return t
    return None

def _match_unique_name(mob_name):
    m = (mob_name or "").strip().lower()
    if not m:
        return None
    for t in TARGETS:
        if t["name"] not in _active_targets():
            continue
        names = [t["name"].lower()] + [a.lower() for a in t.get("aliases", [])]
        for a in names:
            if a and a in m:
                return t
    return None

def _target_last_point(t):
    line = t["walk"][-1]
    # walk,region,x,y,z or walk,region,x,y? phBot logs show x,y only but script has 4 nums after walk.
    parts = line.split(",")
    try:
        return float(parts[2]), float(parts[3])
    except:
        return None, None

def _distance_to_last(t):
    try:
        tx, ty = _target_last_point(t)
        if tx is None:
            return 999999.0
        pos = get_position() or {}
        x = float(pos.get("x", 0.0) or 0.0)
        y = float(pos.get("y", 0.0) or 0.0)
        return ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
    except:
        return 999999.0

def _target_first_point(t):
    try:
        parts = (t["walk"][0] or "").split(",")
        return float(parts[2]), float(parts[3])
    except:
        return None, None

def _distance_to_first(t):
    try:
        tx, ty = _target_first_point(t)
        if tx is None:
            return 999999.0
        pos = get_position() or {}
        x = float(pos.get("x", 0.0) or 0.0)
        y = float(pos.get("y", 0.0) or 0.0)
        return ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
    except:
        return 999999.0


def _target_exit_point(t):
    try:
        route = t.get("back_walk") or list(reversed(t.get("walk", [])))
        if not route:
            return _target_first_point(t)
        parts = (route[-1] or "").split(",")
        return float(parts[2]), float(parts[3])
    except:
        return _target_first_point(t)


def _distance_to_exit_point(t):
    try:
        tx, ty = _target_exit_point(t)
        if tx is None:
            return 999999.0
        pos = get_position() or {}
        x = float(pos.get("x", 0.0) or 0.0)
        y = float(pos.get("y", 0.0) or 0.0)
        return ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
    except:
        return 999999.0


def _walk_xy(line):
    try:
        parts = (line or "").split(",")
        # phBot format used here: walk,region,x,y,z
        return float(parts[2]), float(parts[3])
    except:
        return None, None

def _distance_to_xy(tx, ty):
    try:
        if tx is None or ty is None:
            return 999999.0
        pos = get_position() or {}
        x = float(pos.get("x", 0.0) or 0.0)
        y = float(pos.get("y", 0.0) or 0.0)
        return ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
    except:
        return 999999.0

def _back_timeout_for(t):
    try:
        return max(20.0, min(float(BACK_MAX_SECONDS), len(t.get("back_walk") or t.get("walk", [])) * 5.0))
    except:
        return 30.0


def _write_script(name, lines):
    base = os.path.join(get_config_dir(), "xJupiter")
    try:
        os.makedirs(base, exist_ok=True)
    except:
        pass
    path = os.path.join(base, name + ".txt")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path

def _make_attack_script(t):
    lines = list(t["walk"])
    lines.append("AttackArea,%d" % int(_attack_range()))
    return _write_script("attack_%s" % t["name"].replace(" ", "_"), lines)

def _make_back_script(t):
    # Default back route is the exact entry walk script reversed.
    # Some targets can define a custom back_walk route.
    # No AttackArea, no waits, no custom commands.
    lines = list(t.get("back_walk") or list(reversed(t.get("walk", []))))
    return _write_script("back_%s" % t["name"].replace(" ", "_"), lines)


def _make_back_step_script(t, line, idx):
    # Kept only for compatibility; normal back route uses _make_back_script once.
    return _write_script("back_%s_step_%02d" % (t["name"].replace(" ", "_"), int(idx)), [line])

def _inject_packet(opcode, data):
    try:
        inject_joymax(opcode, data, False)
        return True
    except Exception as e:
        _log("Packet failed.")
        return False

def _run_packets(packet_list):
    delay = PACKET_DELAY_DEFAULT
    def run_one(idx):
        if STOP_REQUESTED:
            return
        if idx >= len(packet_list):
            return
        op, data = packet_list[idx]
        _inject_packet(op, data)
        if idx + 1 < len(packet_list):
            Timer(delay, lambda: run_one(idx+1)).start()
    run_one(0)

def _set_status(s):
    try: QtBind.setText(gui, lbl_status, "📌 " + s)
    except: pass

def _set_active_label(s):
    try: QtBind.setText(gui, lbl_active, "🎯 " + (s or "None"))
    except: pass

def _set_mode_label():
    try: QtBind.setText(gui, lbl_mode, "⚙️ " + MODE.capitalize())
    except: pass

def _fmt_elapsed(ts):
    if not ts:
        return "--"
    sec = int(_now() - ts)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h:
        return "%02d:%02d:%02d" % (h, m, s)
    return "%02d:%02d" % (m, s)

def _character_name():
    try:
        cd = get_character_data() or {}
        return cd.get("name") or "Unknown"
    except:
        return "Unknown"

def _set_power_label():
    try:
        if PLUGIN_ENABLED:
            QtBind.setText(gui, lbl_power, "<b>🟢 ON</b> | 👁️ Monitor: Active")
            try:
                QtBind.setColor(gui, lbl_power, 80, 220, 80)
            except:
                pass
        else:
            QtBind.setText(gui, lbl_power, "<b>🔴 OFF</b> | 👁️ Monitor: Active")
            try:
                QtBind.setColor(gui, lbl_power, 255, 80, 80)
            except:
                pass
        QtBind.setText(gui, lbl_account, "<b>👤 %s</b>" % _character_name())
    except:
        pass

def _refresh_ui():
    try:
        _set_power_label()
        try:
            QtBind.setText(gui, lbl_queue, "📥 " + (", ".join(QUEUE) if QUEUE else "Empty"))
        except:
            pass
        QtBind.setText(gui, lbl_total, "☠️ Kills: %d" % TOTAL_KILLS)
        if RUN_STARTED:
            QtBind.setText(gui, lbl_runtime, "⏱️ " + _fmt_elapsed(RUN_STARTED))
        else:
            QtBind.setText(gui, lbl_runtime, "⏱️ 00:00:00")
        for t in TARGETS:
            nm = t["name"]
            QtBind.setText(gui, target_widgets[nm]["kill"], "<b>%d</b>" % int(COUNTS.get(nm, 0)))
            QtBind.setText(gui, target_widgets[nm]["last"], _fmt_elapsed(LAST_DEAD.get(nm, 0)))
    except:
        pass

def _has_unique_near(t):
    try:
        monsters = get_monsters() or {}
        for _, m in monsters.items():
            nm = (m.get("name") or "").strip()
            mt = _match_unique_name(nm)
            if mt and mt["name"] == t["name"]:
                return True
        return False
    except:
        return False

def _read_hp_percent(t):
    # Best effort only. Some phBot builds do not expose HP fields in get_monsters().
    try:
        monsters = get_monsters() or {}
        for _, m in monsters.items():
            mt = _match_unique_name(m.get("name", ""))
            if not mt or mt["name"] != t["name"]:
                continue
            for k in ("hp_percent", "hpPercent", "hp_percentage", "hp"):
                if k in m:
                    try:
                        val = float(m.get(k))
                        if val <= 1.0:
                            val *= 100.0
                        if 0 <= val <= 100:
                            return val
                    except:
                        pass
            cur_keys = ("current_hp", "cur_hp", "hp_current")
            max_keys = ("max_hp", "hp_max")
            cur = None; mx = None
            for k in cur_keys:
                if k in m:
                    cur = float(m.get(k)); break
            for k in max_keys:
                if k in m:
                    mx = float(m.get(k)); break
            if cur is not None and mx and mx > 0:
                return max(0.0, min(100.0, cur * 100.0 / mx))
    except:
        pass
    return None

def _queue_add(name, front=False, force=False):
    if name not in _active_targets():
        return False
    if name == ACTIVE:
        return False
    # In Search Mode, do not return to a target already handled in the same search run.
    if (not force) and MODE == "search" and name in SEARCH_VISITED:
        return False
    if (not force) and _is_recently_handled(name):
        return False
    if name in QUEUE:
        return False
    if front:
        QUEUE.insert(0, name)
    else:
        QUEUE.append(name)
    return True

def _next_from_queue():
    while QUEUE:
        n = QUEUE.pop(0)
        if n not in _active_targets():
            continue
        if MODE == "search" and n in SEARCH_VISITED:
            continue
        if _is_recently_handled(n):
            continue
        return n
    return None

# ========================= Auto-use scrolls ========================= #
# Item model IDs to auto-consume so they don't fill the inventory page.
# Random Wheel Scroll (44194) + all Honor Scroll tiers (44001-44004).
AUTO_USE_ITEM_IDS = {44194, 44001, 44002, 44003, 44004}
# Use-action descriptor captured from the client (0x704C). Shared by these scrolls
# because it is derived from the item category (tid1/tid2/tid3), not the unique id.
SCROLL_USE_TAIL = b("31 0C 0D 01")
SCROLL_USE_MIN_INTERVAL = 1.5  # seconds between scroll uses, avoids spamming the server
LAST_SCROLL_USE_TS = 0
SCROLLS_USED = 0

# --- Pet pull ---
# Grab/pick pets auto-loot these scrolls into their own bag (get_pets()[uid]["items"]).
# We move a matching scroll out to the player inventory so the inventory scan can use it.
SCROLL_PET_DRYRUN = False    # True = log only, do not inject; False = perform the move
SCROLL_PET_VERBOSE = False   # True = log pet-bag detection (debugging only); keep off in normal use
LAST_SCROLL_DIAG_TS = 0
SCROLL_DIAG_INTERVAL = 8.0   # seconds between pet-bag diagnostic lines when verbose
# Safety against an ineffective move packet: if scrolls never actually leave the pet,
# pause the pull for a cooldown instead of spamming. The counter resets on each
# successful use (so a working move runs forever) and the cooldown self-heals.
PET_MOVE_ATTEMPTS = 0
PET_MOVE_LIMIT = 5
PET_PULL_COOLDOWN_UNTIL = 0
PET_PULL_COOLDOWN_SECS = 60.0

def _set_scrolls_label():
    try:
        QtBind.setText(gui, lbl_scrolls, "📜 Used: %d" % SCROLLS_USED)
    except:
        pass

def _is_hunting():
    # "Hunting" = plugin enabled and a cycle is running (search/standby) or a target is active.
    return bool(PLUGIN_ENABLED) and (not STOP_REQUESTED) and (MODE != "stopped" or ACTIVE)

def _matches_auto_scroll(item):
    try:
        if int(item.get("model", 0)) in AUTO_USE_ITEM_IDS:
            return True
    except:
        pass
    # Name fallback in case the model field is unavailable.
    nm = (item.get("name") or "").lower()
    return ("honor scroll" in nm) or ("random wheel scroll" in nm)

def _first_empty_inv_slot():
    # First free player-inventory slot (>=13, equipment slots 0-12 are skipped).
    # Returns -1 if the inventory is full.
    try:
        inv = get_inventory() or {}
        items = inv.get("items") or []
    except:
        return -1
    for slot, item in enumerate(items):
        if slot < 13:
            continue
        if not item:
            return slot
    return -1

def _pull_scroll_from_pet():
    # Grab/pick pets auto-loot these scrolls into their own bag. On this build
    # get_pet_inventory() does not exist, but each get_pets() entry already carries its
    # bag under an "items" key (list index == pet slot). Move one matching scroll out to
    # the player inventory so the next tick's inventory scan consumes it.
    global LAST_SCROLL_DIAG_TS, PET_MOVE_ATTEMPTS, PET_PULL_COOLDOWN_UNTIL
    if _now() < PET_PULL_COOLDOWN_UNTIL:
        return False
    diag = SCROLL_PET_VERBOSE and (_now() - LAST_SCROLL_DIAG_TS) >= SCROLL_DIAG_INTERVAL

    pets_fn = globals().get("get_pets")
    if not callable(pets_fn):
        return False
    try:
        pets = pets_fn() or {}
    except Exception as e:
        if diag:
            LAST_SCROLL_DIAG_TS = _now()
            _log("PetDiag: get_pets() raised: %s" % e)
        return False
    if diag:
        LAST_SCROLL_DIAG_TS = _now()

    for uid, pet in (pets.items() if isinstance(pets, dict) else []):
        if not isinstance(pet, dict):
            continue
        items = pet.get("items")
        ptype = pet.get("type")
        if not items:
            continue
        scroll_slots = [s for s, it in enumerate(items) if it and _matches_auto_scroll(it)]
        if diag:
            _log("PetDiag: pet %s type=%s items=%d scrolls_at=%s" % (uid, ptype, len(items), scroll_slots))
        if not scroll_slots:
            continue
        slot = scroll_slots[0]
        item = items[slot]
        target = _first_empty_inv_slot()
        if target < 0:
            _log("Auto-scroll: inventory full, cannot pull scroll from pet.")
            return False
        if SCROLL_PET_DRYRUN:
            if diag:
                _log("PetDiag: WOULD move %r pet(type=%s uid=%s) slot %d -> inv-slot %d (qty %s) [dry-run]"
                     % (item.get("name", "?"), ptype, uid, slot, target, item.get("quantity", 1)))
            return False
        # Safety: a wrong/ineffective packet leaves the scroll in the pet, so we'd be
        # called again next tick. Cap the attempts and pause; a successful inventory use
        # resets the counter, so a working move keeps running.
        if PET_MOVE_ATTEMPTS >= PET_MOVE_LIMIT:
            PET_PULL_COOLDOWN_UNTIL = _now() + PET_PULL_COOLDOWN_SECS
            PET_MOVE_ATTEMPTS = 0
            _log("Auto-scroll: pet moves not taking effect — pausing pet pull for %ds."
                 % int(PET_PULL_COOLDOWN_SECS))
            return False
        try:
            data = (struct.pack("<B", 26) + struct.pack("<I", int(uid))
                    + struct.pack("<B", slot) + struct.pack("<B", target)
                    + struct.pack("<H", int(item.get("quantity", 1) or 1)))
            inject_joymax(0x7034, data, False)
            PET_MOVE_ATTEMPTS += 1
            _log("Auto-scroll: pulled %s from pet (slot %d -> %d)."
                 % (item.get("name", "?"), slot, target))
            return True
        except:
            _log("Auto-scroll: pet move inject failed at slot %d." % slot)
            return False
    return False

def _auto_use_scrolls():
    global LAST_SCROLL_USE_TS, SCROLLS_USED, PET_MOVE_ATTEMPTS
    if (_now() - LAST_SCROLL_USE_TS) < SCROLL_USE_MIN_INTERVAL:
        return
    try:
        inv = get_inventory() or {}
        items = inv.get("items") or []
    except:
        return
    for slot, item in enumerate(items):
        if not item or slot < 13:  # skip empty + equipment slots (0-12)
            continue
        if not _matches_auto_scroll(item):
            continue
        try:
            data = struct.pack("<B", slot) + SCROLL_USE_TAIL
            inject_joymax(0x704C, data, True)
            LAST_SCROLL_USE_TS = _now()
            SCROLLS_USED += 1
            PET_MOVE_ATTEMPTS = 0  # a scroll reached the inventory and was used -> move works
            _set_scrolls_label()
            _log("Auto-used scroll: %s (slot %d). Total: %d." % (item.get("name", "?"), slot, SCROLLS_USED))
        except:
            _log("Scroll use failed at slot %d." % slot)
        return  # one per tick; the next tick handles any remaining
    # Nothing usable in the player inventory — pull one out of the grab pet so the
    # next tick finds it in the inventory and uses it. Throttle the pull on the same
    # interval to avoid spamming move packets.
    if _pull_scroll_from_pet():
        LAST_SCROLL_USE_TS = _now()

# ========================= Core flow ========================= #
def _go_target(name, manual=False):
    global ACTIVE, ACTIVE_SEEN, ACTIVE_KILL_CONFIRMED, ACTIVE_COUNTED, ACTIVE_STARTED_AT
    global MONITOR_STAGE, STAGE_TS, SCRIPT_FINISH_WAIT
    if ACTIVE:
        added = _queue_add(name, front=manual, force=manual)
        if added:
            _log("Added to queue: %s" % name)
        return
    t = _target_by_name(name)
    if not t:
        return
    ACTIVE = t["name"]
    ACTIVE_SEEN = False
    ACTIVE_KILL_CONFIRMED = False
    ACTIVE_COUNTED = False
    ACTIVE_STARTED_AT = _now()
    MONITOR_STAGE = "entering"
    STAGE_TS = _now()
    SCRIPT_FINISH_WAIT = 0
    _set_active_label(ACTIVE)
    _set_status("Entering")
    _log("Entering %s." % ACTIVE)
    _run_packets(ROOM_PACKETS[t["room"]]["entry"])
    Timer(PACKET_DELAY_DEFAULT + ENTRY_WAIT_DEFAULT, lambda: _start_attack_script(t["name"])).start()

def _start_attack_script(name):
    global MONITOR_STAGE, STAGE_TS, SCRIPT_FINISH_WAIT
    if STOP_REQUESTED or ACTIVE != name:
        return
    t = _target_by_name(name)
    if not t:
        return
    try:
        stop_bot()
    except:
        pass
    path = _make_attack_script(t)
    try:
        set_training_script(path)
        start_bot()
    except Exception as e:
        _log("Failed to start attack script: %s" % name)
        return
    MONITOR_STAGE = "walking_to_attack"
    STAGE_TS = _now()
    SCRIPT_FINISH_WAIT = max(20, len(t["walk"]) * 4)
    _set_status("Moving")
    _log("Moving to attack area: %s." % name)

def _begin_unique_check(t):
    global MONITOR_STAGE, STAGE_TS, ACTIVE_SEEN
    if _has_unique_near(t):
        ACTIVE_SEEN = True
        hp = _read_hp_percent(t)
        if hp is None:
            _log("Start attack: %s." % t["name"])
        else:
            _log("Start attack: %s. HP %.0f%%." % (t["name"], hp))
        _set_status("Attacking")
        MONITOR_STAGE = "attacking"
        STAGE_TS = _now()
    else:
        _log("Unique not found: %s. Waiting %.0f seconds." % (t["name"], _no_unique_wait()))
        MONITOR_STAGE = "no_unique_wait"
        STAGE_TS = _now()

def _start_back(name):
    global MONITOR_STAGE, STAGE_TS, BACK_STARTED_TS
    global BACK_ROUTE_LINES, BACK_ROUTE_INDEX, BACK_STEP_TS
    t = _target_by_name(name)
    if not t:
        _finish_target(name)
        return
    try:
        stop_bot()
    except:
        pass

    # Run the full reversed walk script once.
    # Do not stop/start between points. Do not add AttackArea or SetTrainingArea.
    BACK_ROUTE_LINES = list(t.get("back_walk") or list(reversed(t.get("walk", []))))
    BACK_ROUTE_INDEX = 0
    BACK_STARTED_TS = _now()
    MONITOR_STAGE = "backing"
    STAGE_TS = _now()
    _set_status("Returning")
    _log("Returning to exit point: %s." % name)
    path = _make_back_script(t)
    try:
        set_training_script(path)
        start_bot()
    except Exception:
        _log("Failed to start return script: %s" % name)
        _exit_target(name)

def _start_back_step(t):
    global BACK_ROUTE_INDEX, BACK_STEP_TS, MONITOR_STAGE, STAGE_TS
    if STOP_REQUESTED or not ACTIVE:
        return
    if BACK_ROUTE_INDEX >= len(BACK_ROUTE_LINES):
        _log("Exit point reached: %s." % ACTIVE)
        _exit_target(ACTIVE)
        return
    line = BACK_ROUTE_LINES[BACK_ROUTE_INDEX]
    try:
        stop_bot()
    except:
        pass
    path = _make_back_step_script(t, line, BACK_ROUTE_INDEX)
    try:
        set_training_script(path)
        start_bot()
    except:
        pass
    BACK_STEP_TS = _now()
    STAGE_TS = _now()
    MONITOR_STAGE = "backing_step"

def _advance_back_step(t):
    global BACK_ROUTE_INDEX
    BACK_ROUTE_INDEX += 1
    _start_back_step(t)

def _exit_target(name):
    global MONITOR_STAGE, STAGE_TS
    t = _target_by_name(name)
    if not t:
        return
    try:
        stop_bot()
    except:
        pass
    MONITOR_STAGE = "exiting"
    STAGE_TS = _now()
    _set_status("Exiting")
    _log("Exiting %s." % name)
    _run_packets(t.get("exit_packets") or ROOM_PACKETS[t["room"]]["exit"])
    Timer(EXIT_WAIT_DEFAULT + PACKET_DELAY_DEFAULT, lambda: _finish_target(name)).start()

def _finish_target(name):
    global ACTIVE, MONITOR_STAGE, STAGE_TS, PENDING_STANDBY, MODE
    if MODE == "search":
        SEARCH_VISITED.add(name)
    _suppress_spawn(name)
    try:
        while name in QUEUE:
            QUEUE.remove(name)
    except:
        pass
    if ACTIVE == name:
        ACTIVE = None
    MONITOR_STAGE = ""
    STAGE_TS = _now()
    _set_active_label("None")
    if PENDING_STANDBY:
        MODE = "standby"
        PENDING_STANDBY = False
        _log("Standby mode active after current target.")
    _set_mode_label()
    if MODE == "search":
        nxt = _next_from_queue()
        if not nxt:
            for n in _active_targets():
                if n != name and n not in SEARCH_VISITED and not _is_recently_handled(n):
                    nxt = n
                    break
        if nxt:
            Timer(0.5, lambda: _go_target(nxt)).start()
        else:
            _set_status("Waiting")
            _log("Waiting at standby point.")
    elif MODE == "standby":
        nxt = _next_from_queue()
        if nxt:
            Timer(0.5, lambda: _go_target(nxt)).start()
        else:
            _set_status("Waiting")
            _log("Waiting at standby point.")
    else:
        _set_status("Stopped")

def _count_kill(name):
    global TOTAL_KILLS, ACTIVE_COUNTED, ACTIVE_KILL_CONFIRMED
    if not name:
        return
    # Count only once per active hunt.
    if ACTIVE == name and ACTIVE_COUNTED:
        return
    COUNTS[name] = COUNTS.get(name, 0) + 1
    TOTAL_KILLS += 1
    if ACTIVE == name:
        ACTIVE_COUNTED = True
        ACTIVE_KILL_CONFIRMED = True
    _log("Kill counted: %s." % name)
    _refresh_ui()

def _mark_dead(name, confirmed=False):
    LAST_DEAD[name] = _now()
    if confirmed:
        _count_kill(name)
    _refresh_ui()

def _timer_tick(token):
    global TIMER, MONITOR_STAGE, STAGE_TS
    if token != TOKEN:
        return
    try:
        _refresh_ui()
        # Auto-use scrolls only while hunting, and only if the toggle is on.
        if _is_hunting():
            try:
                if QtBind.isChecked(gui, cbx_autoscroll):
                    _auto_use_scrolls()
            except:
                pass
        if ACTIVE:
            t = _target_by_name(ACTIVE)
            if t:
                if MONITOR_STAGE == "walking_to_attack":
                    # Only check after reaching last script point, not after first steps.
                    if _distance_to_last(t) <= ARRIVAL_TOLERANCE:
                        _log("Attack point reached: %s." % ACTIVE)
                        _begin_unique_check(t)
                    elif (_now() - STAGE_TS) > SCRIPT_FINISH_WAIT:
                        # Safety only: if phBot did not reach exactly, check once late.
                        _begin_unique_check(t)
                elif MONITOR_STAGE == "no_unique_wait":
                    if (_now() - STAGE_TS) >= _no_unique_wait():
                        if _has_unique_near(t):
                            _begin_unique_check(t)
                        else:
                            _log("Unique not found: %s. Going back." % ACTIVE)
                            _start_back(ACTIVE)
                elif MONITOR_STAGE == "attacking":
                    if not _has_unique_near(t):
                        LAST_DEAD[ACTIVE] = _now()
                        _suppress_spawn(ACTIVE)
                        try:
                            while ACTIVE in QUEUE:
                                QUEUE.remove(ACTIVE)
                        except:
                            pass
                        # If this hunt reached attack stage and the unique disappeared, count it for this character.
                        # Server kill-credit text is still accepted by handle_event when available.
                        if ACTIVE_SEEN:
                            _count_kill(ACTIVE)
                        _log("Target finished: %s. Waiting %.0f seconds before returning." % (ACTIVE, _after_kill_wait()))
                        Timer(_after_kill_wait(), lambda n=ACTIVE: _start_back(n)).start()
                        MONITOR_STAGE = "after_kill_wait"
                        STAGE_TS = _now()
                elif MONITOR_STAGE == "backing":
                    # Back script is full reversed entry route.
                    # Exit only after reaching the final back-route point.
                    if (_now() - STAGE_TS) >= BACK_MIN_CHECK_SECONDS and _distance_to_exit_point(t) <= ARRIVAL_TOLERANCE:
                        _log("Exit point reached: %s." % ACTIVE)
                        _exit_target(ACTIVE)
                    elif (_now() - STAGE_TS) >= _back_timeout_for(t):
                        _log("Return timeout: %s. Exiting now." % ACTIVE)
                        _exit_target(ACTIVE)
        elif MODE == "standby":
            nxt = _next_from_queue()
            if nxt:
                _go_target(nxt)
    except Exception as e:
        _log("Loop error.")
    finally:
        TIMER = Timer(1.0, lambda: _timer_tick(token))
        TIMER.start()

def _start_timer():
    global TOKEN, TIMER
    TOKEN += 1
    try:
        if TIMER:
            TIMER.cancel()
    except:
        pass
    TIMER = Timer(1.0, lambda: _timer_tick(TOKEN))
    TIMER.start()

def _stop_timer():
    global TOKEN, TIMER
    TOKEN += 1
    try:
        if TIMER:
            TIMER.cancel()
    except:
        pass
    TIMER = None

# ========================= Buttons ========================= #
def btn_github_clicked():
    try:
        webbrowser.open(GITHUB_URL)
    except Exception:
        pass

def cbx_enabled_clicked(checked):
    global PLUGIN_ENABLED
    PLUGIN_ENABLED = bool(checked)
    _start_timer()  # UI/death monitor must keep running even when OFF.
    _set_power_label()
    if checked:
        _set_status("Ready")
        _log("Plugin enabled. Death monitor is active.")
    else:
        btn_stop_clicked()
        _set_status("Stopped - Monitor Active")
        _log("Plugin disabled. Death monitor is still active.")

def btn_standby_clicked():
    global MODE, PENDING_STANDBY, RUN_STARTED, STOP_REQUESTED
    STOP_REQUESTED = False
    if not RUN_STARTED:
        RUN_STARTED = _now()
    if ACTIVE:
        PENDING_STANDBY = True
        _log("Standby mode queued. Current target will finish first.")
        return
    MODE = "standby"
    _set_mode_label()
    _set_status("Waiting")
    _start_timer()
    _log("Standby mode started. Waiting at standby point.")

def btn_search_clicked():
    global MODE, RUN_STARTED, STOP_REQUESTED
    STOP_REQUESTED = False
    SEARCH_VISITED.clear()
    if ACTIVE:
        _log("Search ignored. Current target is active.")
        return
    if not RUN_STARTED:
        RUN_STARTED = _now()
    MODE = "search"
    _set_mode_label()
    _start_timer()
    _log("Search mode started.")
    active = _active_targets()
    QUEUE[:] = []
    for n in active:
        QUEUE.append(n)
    nxt = _next_from_queue()
    if nxt:
        _go_target(nxt)
    else:
        _set_status("Waiting")

def btn_stop_clicked():
    global MODE, ACTIVE, QUEUE, STOP_REQUESTED, MONITOR_STAGE, PENDING_STANDBY
    STOP_REQUESTED = True
    MODE = "stopped"
    PENDING_STANDBY = False
    QUEUE[:] = []
    SEARCH_VISITED.clear()
    ACTIVE = None
    MONITOR_STAGE = ""
    try:
        stop_bot()
    except:
        pass
    _set_mode_label()
    _set_active_label("None")
    _set_status("Stopped")
    _log("Cycle stopped.")

def btn_update_clicked():
    _set_mode_label()
    _refresh_ui()
    _log("Settings updated.")

def _go_clicked(idx):
    global RUN_STARTED, STOP_REQUESTED
    STOP_REQUESTED = False
    if not RUN_STARTED:
        RUN_STARTED = _now()
    name = TARGETS[idx]["name"]
    if name not in _active_targets():
        try:
            QtBind.setChecked(gui, target_widgets[name]["cb"], True)
        except:
            pass
    if ACTIVE:
        _queue_add(name, front=True, force=True)
        _log("Go queued: %s." % name)
    else:
        _log("Go: %s." % name)
        _go_target(name, manual=True)

def go_0_clicked(): _go_clicked(0)
def go_1_clicked(): _go_clicked(1)
def go_2_clicked(): _go_clicked(2)
def go_3_clicked(): _go_clicked(3)
def go_4_clicked(): _go_clicked(4)
def go_5_clicked(): _go_clicked(5)

def target_checkbox_clicked(checked):
    return

def cbx_autoscroll_clicked(checked):
    _log("Auto-use scrolls %s." % ("enabled" if checked else "disabled"))

# ========================= Save / Load ========================= #
def _cfg_path():
    cd = get_character_data() or {}
    server = cd.get("server", "server")
    char = cd.get("name", "char")
    base = os.path.join(get_config_dir(), "xJupiter")
    try: os.makedirs(base, exist_ok=True)
    except: pass
    return os.path.join(base, "%s_%s_v3.json" % (server, char))

def btn_save_clicked():
    try:
        data = {
            "attack_range": QtBind.text(gui, tbx_attack_range),
            "after_kill_wait": QtBind.text(gui, tbx_after_kill_wait),
            "no_unique_wait": QtBind.text(gui, tbx_no_unique_wait),
            "enabled": {t["name"]: bool(QtBind.isChecked(gui, target_widgets[t["name"]]["cb"])) for t in TARGETS},
        }
        with open(_cfg_path(), "w") as f:
            json.dump(data, f, indent=2)
        _log("Settings saved.")
    except Exception as e:
        _log("Save failed.")

def btn_load_clicked():
    try:
        path = _cfg_path()
        if not os.path.exists(path):
            return
        with open(path, "r") as f:
            data = json.load(f) or {}
        QtBind.setText(gui, tbx_attack_range, str(data.get("attack_range", "45")))
        QtBind.setText(gui, tbx_after_kill_wait, str(data.get("after_kill_wait", "15")))
        QtBind.setText(gui, tbx_no_unique_wait, str(data.get("no_unique_wait", "2")))
        en = data.get("enabled", {})
        for t in TARGETS:
            if t["name"] in en:
                QtBind.setChecked(gui, target_widgets[t["name"]]["cb"], bool(en[t["name"]]))
        _log("Settings loaded.")
    except Exception as e:
        _log("Load failed.")

# ========================= Spawn / Death reader ========================= #
UNIQUE_OBJ_CACHE = {}

def handle_joymax(opcode, data):
    try:
        if opcode != 0x300C or not data or len(data) < 6:
            return True
        event_type = data[0]
        import struct
        obj_id = struct.unpack_from("<I", data, 2)[0]
        name = ""
        mob = None
        try:
            mob = get_monster(obj_id)
        except:
            mob = None
        if mob:
            name = (mob.get("name") or "").strip()
        if event_type == 5 and name:
            UNIQUE_OBJ_CACHE[obj_id] = name
        if not name:
            name = UNIQUE_OBJ_CACHE.get(obj_id, "")
        t = _match_unique_name(name)
        if not t:
            return True
        if event_type == 5:
            if MODE == "search" and t["name"] in SEARCH_VISITED:
                return True
            if _is_recently_handled(t["name"]):
                return True
            added = _queue_add(t["name"])
            if added:
                _log("Unique spawned: %s. Added to queue." % t["name"])
            if MODE == "standby" and not ACTIVE and added:
                _go_target(t["name"])
        elif event_type == 6:
            LAST_DEAD[t["name"]] = _now()
            _suppress_spawn(t["name"])
            _log("Death detected: %s. Last dead timer updated." % t["name"])
            try:
                while t["name"] in QUEUE:
                    QUEUE.remove(t["name"])
            except:
                pass
            # Death packet updates Last dead and suppress only.
            # Kill counters are updated when kill credit text is seen or when the active attack target disappears.
            if obj_id in UNIQUE_OBJ_CACHE:
                UNIQUE_OBJ_CACHE.pop(obj_id, None)
    except Exception as e:
        _log("Spawn reader error.")
    return True

# Best effort kill confirmation from event text, if your phBot build sends it here.
def handle_event(t, data):
    try:
        txt = str(data or "")
        me = (get_character_data() or {}).get("name", "")
        low = txt.lower()
        if me and me.lower() in low:
            for tg in TARGETS:
                if tg["name"].lower() in low or any(a.lower() in low for a in tg.get("aliases", [])):
                    _mark_dead(tg["name"], confirmed=True)
                    break
    except:
        pass

# ========================= Lifecycle ========================= #
def plugin_load():
    _set_status("Loaded - Monitor Active")
    _set_active_label("None")
    _set_mode_label()
    _set_power_label()
    _refresh_ui()
    _start_timer()
    _log("Plugin loaded. Death monitor is active even while OFF.")

def joined_game():
    _set_power_label()
    _refresh_ui()

def plugin_unload():
    _stop_timer()
    try:
        stop_bot()
    except:
        pass
    _log("Plugin unloaded.")

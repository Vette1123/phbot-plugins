# xNotify - Telegram + Discord status alerts for phBot
# Sends labeled alerts (death, bot stopped, attacked, caravan trade start/settle)
# to Telegram and/or Discord. Other plugins emit via:  import xNotify; xNotify.notify(type, text)
from phBot import *
import QtBind
import os
import json
import time
import queue
import threading
import urllib.request
import urllib.parse
import urllib.error
import webbrowser

pName = 'xNotify'
pVersion = '1.1.1'
pAuthor = 'Vette1123 (Gado)'
pUrl = 'https://raw.githubusercontent.com/Vette1123/phbot-plugins/main/xNotify.py'

GITHUB_URL = 'https://github.com/Vette1123'
GITHUB_BTN_STYLE = (
    'QPushButton{background:#ffd54a;color:#222;font-weight:bold;'
    'border:1px solid #8b6b00;border-radius:6px;padding:2px 10px;}'
    'QPushButton:hover{background:#ffe27a;}'
)


def _mask_secret(s):
    """Masked display form of a secret: bullets + last 4 chars (empty stays empty).
    phBot's QtBind has no password echo mode, so we mask the displayed text instead."""
    s = s or ''
    if not s:
        return ''
    if len(s) <= 4:
        return '•' * len(s)
    return '•' * (len(s) - 4) + s[-4:]


def _resolve_secret(field_text, stored):
    """If the field still shows the mask of the stored value, it's unchanged -> keep
    stored. Otherwise the user typed/pasted a new value -> use it."""
    field_text = (field_text or '').strip()
    if field_text == _mask_secret(stored):
        return stored
    return field_text


def btn_github_clicked():
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

# ______________________________ Config ______________________________ #

_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'xNotify.json')
_cfg_lock = threading.Lock()

DEFAULT_CONFIG = {
    'telegram_token': '',
    'telegram_chat_id': '',
    'discord_webhook': '',
    'cooldown_sec': 60,
    'events': {
        'death': True,
        'bot_stopped': True,
        'attacked': True,
        'trade_start': True,
        'trade_settle': True,
        'hp_pots_out': True,
        'mp_pots_out': True,
        'pm': True,
        'global': True,
        'notice': True,
        'unique': True,
    },
    # Extra substrings (lowercase) that mark a global/notice as a unique sighting.
    # Server-specific; add your server's unique names here.
    'unique_keywords': ['unique'],
}

# Order + labels for the GUI checkboxes
EVENT_LABELS = [
    ('death', '⚠️ Death'),
    ('bot_stopped', '🛑 Bot stop'),
    ('attacked', '⚔️ Attacked'),
    ('trade_start', '📦 Trade start'),
    ('trade_settle', '✅ Trade settle'),
    ('hp_pots_out', '🩸 HP pots out'),
    ('mp_pots_out', '🔵 MP pots out'),
    ('pm', '✉️ PM'),
    ('global', '📢 Global'),
    ('notice', '📜 Notice'),
    ('unique', '👑 Unique'),
]


def load_config():
    try:
        with open(_CFG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {}
    cfg = dict(DEFAULT_CONFIG)
    cfg.update({k: v for k, v in data.items() if k != 'events'})
    cfg['events'] = dict(DEFAULT_CONFIG['events'])
    cfg['events'].update(data.get('events', {}) or {})
    return cfg


def save_config(cfg):
    with _cfg_lock:
        with open(_CFG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)


config = load_config()


def _safe_log(msg):
    try:
        log('[xNotify] ' + str(msg))
    except Exception:
        pass


# ______________________________ Channels ______________________________ #

def _http_post(url, data_bytes, headers):
    # Cloudflare (Discord) blocks the default urllib User-Agent with 403/1010.
    headers = dict(headers)
    headers.setdefault('User-Agent', 'xNotify/%s (+phBot plugin)' % pVersion)
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return getattr(resp, 'status', 200)
    except urllib.error.HTTPError as e:
        # Surface the API's reason (Telegram/Discord put it in the response body).
        try:
            detail = e.read().decode('utf-8', 'replace')
        except Exception:
            detail = ''
        raise Exception('HTTP %s: %s' % (e.code, detail[:300]))


def send_telegram(token, chat_id, text):
    if not token or not chat_id:
        return False
    url = 'https://api.telegram.org/bot%s/sendMessage' % token
    body = urllib.parse.urlencode({'chat_id': chat_id, 'text': text}).encode('utf-8')
    _http_post(url, body, {'Content-Type': 'application/x-www-form-urlencoded'})
    return True


def send_discord(webhook, text):
    if not webhook:
        return False
    body = json.dumps({'content': text}).encode('utf-8')
    _http_post(webhook, body, {'Content-Type': 'application/json'})
    return True


# ______________________________ Sender thread ______________________________ #

_send_q = queue.Queue()


def _send_one(label, fn):
    """Run one channel send with up to 3 retries; log per-channel result. Independent
    of the other channel so a bad Telegram config never blocks Discord."""
    for attempt in range(3):
        try:
            if fn() is False:
                return  # channel not configured -> silently skip
            return
        except Exception as e:
            _safe_log('%s send failed (try %d): %s' % (label, attempt + 1, e))
            if attempt < 2:
                time.sleep(2 * (attempt + 1))


def _worker():
    while True:
        text = _send_q.get()
        try:
            cfg = config
            _send_one('telegram', lambda: send_telegram(
                cfg.get('telegram_token', ''), cfg.get('telegram_chat_id', ''), text))
            _send_one('discord', lambda: send_discord(
                cfg.get('discord_webhook', ''), text))
        finally:
            _send_q.task_done()


_worker_thread = threading.Thread(target=_worker, name='xNotify-sender', daemon=True)
_worker_thread.start()


def _enqueue(text):
    _send_q.put(text)


# ______________________________ notify() ______________________________ #

_last_sent = {}
_throttle_lock = threading.Lock()

EMOJI = {
    'death': '⚠️',
    'bot_stopped': '🛑',
    'attacked': '⚔️',
    'trade_start': '📦',
    'trade_settle': '✅',
    'hp_pots_out': '🩸',
    'mp_pots_out': '🔵',
    'pm': '✉️',
    'global': '📢',
    'notice': '📜',
    'unique': '👑',
}


def _profile_game_name():
    # Fallback game name from the loaded profile (e.g. vSRO.json) next to phBot.exe.
    # CONFIRM live (verification): prefer get_character_data() server/region field.
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for fn in os.listdir(base):
            if fn.lower().endswith('.json'):
                return os.path.splitext(fn)[0]
    except Exception:
        pass
    return None


def _identity():
    try:
        ch = get_character_data() or {}
    except Exception:
        ch = {}
    name = ch.get('name') or '??'
    game = ch.get('server') or ch.get('region') or _profile_game_name() or '??'
    return game, name


def _format(event_type, text):
    game, name = _identity()
    return '%s [%s • %s] %s' % (EMOJI.get(event_type, 'ℹ️'), game, name, text)


def _throttled(event_type):
    cd = config.get('cooldown_sec', 60)
    now = time.monotonic()
    with _throttle_lock:
        last = _last_sent.get(event_type, 0)
        if now - last < cd:
            return True
        _last_sent[event_type] = now
        return False


def notify(event_type, text, force=False):
    """Public API. Other plugins: import xNotify; xNotify.notify('trade_start', '...')
    force=True bypasses the per-event cooldown (used for PMs)."""
    if not config.get('events', {}).get(event_type, False):
        return
    if not force and _throttled(event_type):
        return
    _enqueue(_format(event_type, text))


# ______________________________ Event detectors ______________________________ #

_prev_hp = None
_prev_botting = None
ATTACK_OPCODE = 0xB070  # CONFIRM live: skill/attack action opcode


def _is_botting():
    # CONFIRM live: correct field/function for botting-running state.
    try:
        ch = get_character_data() or {}
    except Exception:
        return None
    for key in ('botting', 'training', 'bot'):
        if key in ch:
            return bool(ch[key])
    return None


def _my_object_id():
    try:
        ch = get_character_data() or {}
    except Exception:
        return None
    return ch.get('uid') or ch.get('object_id') or ch.get('jid')


_prev_hp_pots = None
_prev_mp_pots = None
_last_pot_check = 0
POT_CHECK_INTERVAL = 5.0  # seconds between inventory scans (keep event_loop cheap)


def _potion_counts():
    """Return (hp_qty, mp_qty) of recovery potions in inventory; (None, None) if
    inventory is unavailable. Vigor potions (tid3==3) count toward both."""
    try:
        inv = get_inventory()
    except Exception:
        return None, None
    items = (inv or {}).get('items') or []
    if not items:
        return None, None
    hp = mp = 0
    for it in items:
        if not it:
            continue
        qty = it.get('quantity') or it.get('amount') or 0
        is_hp = is_mp = False
        d = None
        try:
            d = get_item(it.get('model'))
        except Exception:
            d = None
        # CONFIRM live: tid1=3/tid2=1 recovery, tid3 1=HP 2=MP 3=Vigor.
        if d and d.get('tid1') == 3 and d.get('tid2') == 1:
            t3 = d.get('tid3')
            if t3 == 1:
                is_hp = True
            elif t3 == 2:
                is_mp = True
            elif t3 == 3:
                is_hp = is_mp = True
        else:
            name = (it.get('name') or it.get('servername') or '').lower()
            if 'vigor' in name:
                is_hp = is_mp = True
            elif 'potion' in name or 'recovery' in name:
                if 'hp' in name:
                    is_hp = True
                if 'mp' in name:
                    is_mp = True
        if is_hp:
            hp += qty
        if is_mp:
            mp += qty
    return hp, mp


def _check_potions():
    global _prev_hp_pots, _prev_mp_pots, _last_pot_check
    now = time.monotonic()
    if now - _last_pot_check < POT_CHECK_INTERVAL:
        return
    _last_pot_check = now
    hp, mp = _potion_counts()
    if hp is not None:
        if _prev_hp_pots is not None and _prev_hp_pots > 0 and hp == 0:
            notify('hp_pots_out', 'Out of HP potions')
        _prev_hp_pots = hp
    if mp is not None:
        if _prev_mp_pots is not None and _prev_mp_pots > 0 and mp == 0:
            notify('mp_pots_out', 'Out of MP potions')
        _prev_mp_pots = mp


def event_loop():
    global _prev_hp, _prev_botting
    try:
        ch = get_character_data() or {}
    except Exception:
        return
    hp = ch.get('hp')
    if hp is not None:
        if _prev_hp is not None and _prev_hp > 0 and hp == 0:
            notify('death', 'Died')
        _prev_hp = hp
    b = _is_botting()
    if b is not None:
        if _prev_botting is True and b is False:
            notify('bot_stopped', 'Bot stopped')
        _prev_botting = b
    _check_potions()


def handle_joymax(opcode, data):
    if opcode != ATTACK_OPCODE:
        return
    # CONFIRM live: parse source/target object ids from `data`. When target ==
    # _my_object_id() and source resolves to a player, fire:
    #   notify('attacked', 'Attacked by ' + attacker_name)
    return


def _is_unique_text(msg):
    low = (msg or '').lower()
    for kw in config.get('unique_keywords', []) or []:
        if kw and kw.lower() in low:
            return True
    return False


def handle_chat(t, player, msg):
    # 2 = PM, 6 = Global, 7 = Notice
    if t == 2:
        notify('pm', 'PM from %s: %s' % (player or '?', msg), force=True)
    elif t in (6, 7):
        if _is_unique_text(msg):
            notify('unique', msg)
            return
        if t == 6:
            notify('global', '%s: %s' % (player or '?', msg))
        else:
            notify('notice', msg)


# ______________________________ GUI ______________________________ #

gui = QtBind.init(__name__, pName)
QtBind.createLabel(gui, 'xNotify — Telegram + Discord alerts', 6, 8)

QtBind.createLabel(gui, 'Telegram token:', 6, 36)
txtToken = QtBind.createLineEdit(gui, _mask_secret(config['telegram_token']), 120, 32, 200, 20)
QtBind.createLabel(gui, 'Telegram chat id:', 6, 62)
txtChat = QtBind.createLineEdit(gui, _mask_secret(config['telegram_chat_id']), 120, 58, 200, 20)
QtBind.createLabel(gui, 'Discord webhook:', 6, 88)
txtHook = QtBind.createLineEdit(gui, _mask_secret(config['discord_webhook']), 120, 84, 200, 20)
QtBind.createLabel(gui, 'Cooldown (s):', 6, 114)
txtCd = QtBind.createLineEdit(gui, str(config['cooldown_sec']), 120, 110, 60, 20)

QtBind.createLabel(gui, 'Events:', 6, 140)
_event_checks = {}
_COLS = 4
_COL_W = 110
_ROW_H = 24
_X0 = 60
_Y0 = 138
for _i, (_key, _lbl) in enumerate(EVENT_LABELS):
    _x = _X0 + (_i % _COLS) * _COL_W
    _y = _Y0 + (_i // _COLS) * _ROW_H
    chk = QtBind.createCheckBox(gui, '', _lbl, _x, _y)
    QtBind.setChecked(gui, chk, bool(config['events'].get(_key, True)))
    _event_checks[_key] = chk

_rows = (len(EVENT_LABELS) + _COLS - 1) // _COLS
_btn_y = _Y0 + _rows * _ROW_H + 6
btnSave = QtBind.createButton(gui, 'btnSave_clicked', '  Save  ', 6, _btn_y)
btnTest = QtBind.createButton(gui, 'btnTest_clicked', '  Send Test  ', 80, _btn_y)
# Labels auto-size to their initial text, so pad with trailing spaces to reserve
# width for longer status messages set later (matches xCaravan's _STAT_PAD idiom).
_STATUS_PAD = ' ' * 48


def _set_status(msg):
    QtBind.setText(gui, lblStatus, ('Status: ' + msg + _STATUS_PAD))


lblStatus = QtBind.createLabel(gui, 'Status: idle' + _STATUS_PAD, 6, _btn_y + 28)
btnGithub = QtBind.createButton(gui, 'btn_github_clicked', '  ⭐  (Gado) GitHub  ⭐  ', 6, _btn_y + 50)
_try_style_github(btnGithub)


def btnSave_clicked():
    config['telegram_token'] = _resolve_secret(QtBind.text(gui, txtToken), config['telegram_token'])
    config['telegram_chat_id'] = _resolve_secret(QtBind.text(gui, txtChat), config['telegram_chat_id'])
    config['discord_webhook'] = _resolve_secret(QtBind.text(gui, txtHook), config['discord_webhook'])
    try:
        config['cooldown_sec'] = int(QtBind.text(gui, txtCd))
    except Exception:
        pass
    for _key, chk in _event_checks.items():
        config['events'][_key] = bool(QtBind.isChecked(gui, chk))
    save_config(config)
    # Re-mask the fields so the plaintext secrets aren't left on screen.
    QtBind.setText(gui, txtToken, _mask_secret(config['telegram_token']))
    QtBind.setText(gui, txtChat, _mask_secret(config['telegram_chat_id']))
    QtBind.setText(gui, txtHook, _mask_secret(config['discord_webhook']))
    _safe_log('config saved')
    _set_status('saved')


def btnTest_clicked():
    _enqueue(_format('death', 'xNotify test message'))
    _set_status('test queued')


_safe_log('xNotify %s loaded' % pVersion)

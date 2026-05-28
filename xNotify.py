# xNotify - Telegram + Discord status alerts for phBot
# Sends labeled alerts (death, bot stopped, attacked, caravan trade start/settle,
# uniques, drops, level ups, chats, notices...) to Telegram and/or Discord as
# rich cards. Other plugins emit via:  import xNotify; xNotify.notify(type, text)
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
import hashlib

pName = 'xNotify'
pVersion = '1.4.1'
pAuthor = 'Vette1123 (Gado)'
pUrl = 'https://raw.githubusercontent.com/Vette1123/phbot-plugins/main/xNotify.py'

GITHUB_URL = 'https://github.com/Vette1123'
GITHUB_BTN_STYLE = (
    'QPushButton{background:#ffd54a;color:#222;font-weight:bold;'
    'border:1px solid #8b6b00;border-radius:6px;padding:2px 10px;}'
    'QPushButton:hover{background:#ffe27a;}'
)


def _mask_secret(s):
    s = s or ''
    if not s:
        return ''
    if len(s) <= 4:
        return '•' * len(s)
    return '•' * (len(s) - 4) + s[-4:]


def _resolve_secret(field_text, stored):
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
    'rich_cards': True,
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
        'level_up': True,
        'rare_drop': True,
        'guild_chat': False,
        'party_chat': False,
        'union_chat': False,
        'academy_chat': False,
        'all_chat': False,
        'stall_chat': False,
    },
    # name substrings (lowercase) flagging a global/notice as a unique sighting
    'unique_keywords': ['unique', 'legend', 'legendary', 'boss', 'titan', 'demon lord'],
    # mob 'rarity' codes treated as uniques. In phBot/SRO, 3=Giant, 4=Champion-party,
    # 5=Elite, 6=Unique. Only 6 is a real Unique — the others are common field spawns
    # and were the source of false-positive "unique" alerts.
    'unique_types': [6],
    # Known SRO unique monster names (lowercase substrings). These spawn without the
    # word "unique" in their name, so we match them explicitly.
    'unique_names': [
        'tiger girl', 'uruchi', 'isyutaru', 'lord yarkan', 'cerberus',
        'captain ivy', 'medusa', 'roc', 'demon shaitan', 'selket',
        'anubis', 'isis', 'seth', 'neith', 'horus', 'apis',
        'kidemonas', 'kerveros', 'ymir', 'hekaton', 'olympos',
        'beelzebub', 'lucifer', 'belial', 'baal',
    ],
    # Substrings that mark an item as "rare" enough to alert on (lowercase)
    'rare_drop_keywords': ['sun ', 'moon ', 'star ', 'seal of', 'devil', 'd13', 'd14', 'd15', 'd16'],
}

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
    ('level_up', '⬆️ Level up'),
    ('rare_drop', '💎 Rare drop'),
    ('party_chat', '🎉 Party'),
    ('guild_chat', '🛡️ Guild'),
    ('union_chat', '🤝 Union'),
    ('academy_chat', '🎓 Academy'),
    ('all_chat', '🗣️ All'),
    ('stall_chat', '🏪 Stall'),
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


# ______________________________ Cross-process dedup ______________________________ #

SHARED_EVENTS = {'global', 'notice', 'unique', 'all_chat'}
SHARED_WINDOW = {'global': 30.0, 'notice': 30.0, 'unique': 120.0, 'all_chat': 15.0}
_DEDUP_DIR = os.path.join(os.path.dirname(_CFG_PATH), 'xNotify_dedup')
_last_dedup_cleanup = 0.0


def _dedup_cleanup(now):
    global _last_dedup_cleanup
    if now - _last_dedup_cleanup < 300:
        return
    _last_dedup_cleanup = now
    try:
        for fn in os.listdir(_DEDUP_DIR):
            p = os.path.join(_DEDUP_DIR, fn)
            try:
                if now - os.stat(p).st_mtime > 3600:
                    os.remove(p)
            except Exception:
                pass
    except Exception:
        pass


def _claim_shared(key, window):
    try:
        os.makedirs(_DEDUP_DIR, exist_ok=True)
    except Exception:
        return True
    now = time.time()
    _dedup_cleanup(now)
    h = hashlib.md5(key.encode('utf-8', 'replace')).hexdigest()
    path = os.path.join(_DEDUP_DIR, h)
    try:
        if now - os.stat(path).st_mtime < window:
            return False
    except FileNotFoundError:
        pass
    except Exception:
        return True
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return True
    except FileExistsError:
        try:
            if now - os.stat(path).st_mtime >= window:
                os.utime(path, None)
                return True
        except Exception:
            pass
        return False
    except Exception:
        return True


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
        try:
            detail = e.read().decode('utf-8', 'replace')
        except Exception:
            detail = ''
        raise Exception('HTTP %s: %s' % (e.code, detail[:300]))


def send_telegram_text(token, chat_id, text, html=False):
    if not token or not chat_id:
        return False
    url = 'https://api.telegram.org/bot%s/sendMessage' % token
    params = {'chat_id': chat_id, 'text': text, 'disable_web_page_preview': 'true'}
    if html:
        params['parse_mode'] = 'HTML'
    body = urllib.parse.urlencode(params).encode('utf-8')
    _http_post(url, body, {'Content-Type': 'application/x-www-form-urlencoded'})
    return True


def send_discord_text(webhook, text):
    if not webhook:
        return False
    body = json.dumps({'content': text}).encode('utf-8')
    _http_post(webhook, body, {'Content-Type': 'application/json'})
    return True


def send_discord_embed(webhook, embed):
    if not webhook:
        return False
    body = json.dumps({'embeds': [embed]}).encode('utf-8')
    _http_post(webhook, body, {'Content-Type': 'application/json'})
    return True


# ______________________________ Sender thread ______________________________ #

_send_q = queue.Queue()


def _send_one(label, fn):
    for attempt in range(3):
        try:
            if fn() is False:
                return
            return
        except Exception as e:
            _safe_log('%s send failed (try %d): %s' % (label, attempt + 1, e))
            if attempt < 2:
                time.sleep(2 * (attempt + 1))


def _worker():
    while True:
        payload = _send_q.get()
        try:
            cfg = config
            tg_text, tg_html, dc_text, dc_embed = _render(payload)
            _send_one('telegram', lambda: send_telegram_text(
                cfg.get('telegram_token', ''), cfg.get('telegram_chat_id', ''),
                tg_text, html=tg_html))
            if dc_embed is not None:
                _send_one('discord', lambda: send_discord_embed(
                    cfg.get('discord_webhook', ''), dc_embed))
            else:
                _send_one('discord', lambda: send_discord_text(
                    cfg.get('discord_webhook', ''), dc_text))
        finally:
            _send_q.task_done()


_worker_thread = threading.Thread(target=_worker, name='xNotify-sender', daemon=True)
_worker_thread.start()


# ______________________________ Rich rendering ______________________________ #

EMOJI = {
    'death': '⚠️', 'bot_stopped': '🛑', 'attacked': '⚔️',
    'trade_start': '📦', 'trade_settle': '✅',
    'hp_pots_out': '🩸', 'mp_pots_out': '🔵',
    'pm': '✉️', 'global': '📢', 'notice': '📜', 'unique': '👑',
    'level_up': '⬆️', 'rare_drop': '💎',
    'party_chat': '🎉', 'guild_chat': '🛡️', 'union_chat': '🤝',
    'academy_chat': '🎓', 'all_chat': '🗣️', 'stall_chat': '🏪',
}

# Discord embed colours (decimal RGB)
COLOURS = {
    'death': 0xE74C3C, 'bot_stopped': 0x95A5A6, 'attacked': 0xE67E22,
    'trade_start': 0x3498DB, 'trade_settle': 0x2ECC71,
    'hp_pots_out': 0xC0392B, 'mp_pots_out': 0x2980B9,
    'pm': 0x9B59B6, 'global': 0xF1C40F, 'notice': 0xECEC4F,
    'unique': 0xFFD700, 'level_up': 0x1ABC9C, 'rare_drop': 0x00CED1,
    'party_chat': 0xE91E63, 'guild_chat': 0x7B68EE, 'union_chat': 0x4682B4,
    'academy_chat': 0x9370DB, 'all_chat': 0xBDC3C7, 'stall_chat': 0xCD853F,
}

TITLES = {
    'death': 'Character died',
    'bot_stopped': 'Bot stopped',
    'attacked': 'Attacked by player',
    'trade_start': 'Trade route started',
    'trade_settle': 'Trade settled',
    'hp_pots_out': 'Out of HP potions',
    'mp_pots_out': 'Out of MP potions',
    'pm': 'Private message',
    'global': 'Global chat',
    'notice': 'Server notice',
    'unique': 'Unique spawned',
    'level_up': 'Level up',
    'rare_drop': 'Rare item dropped',
    'party_chat': 'Party chat',
    'guild_chat': 'Guild chat',
    'union_chat': 'Union chat',
    'academy_chat': 'Academy chat',
    'all_chat': 'All chat',
    'stall_chat': 'Stall chat',
}


def _profile_game_name():
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
    return game, name, ch


def _position_str(ch):
    try:
        pos = get_position() or {}
    except Exception:
        pos = {}
    x = pos.get('x') or ch.get('x')
    y = pos.get('y') or ch.get('y')
    region = pos.get('region') or ch.get('region_id')
    if x is None or y is None:
        return None
    try:
        if region is not None:
            return '%d, %d (r%s)' % (int(x), int(y), region)
        return '%d, %d' % (int(x), int(y))
    except Exception:
        return str(x) + ', ' + str(y)


def _hp_str(ch):
    hp = ch.get('hp'); mp = ch.get('mp')
    hp_max = ch.get('max_hp') or ch.get('hp_max')
    mp_max = ch.get('max_mp') or ch.get('mp_max')
    parts = []
    if hp is not None:
        parts.append('HP %s%s' % (hp, ('/' + str(hp_max)) if hp_max else ''))
    if mp is not None:
        parts.append('MP %s%s' % (mp, ('/' + str(mp_max)) if mp_max else ''))
    return ' · '.join(parts) if parts else None


def _build_fields(event_type, ch, extras):
    """Returns list of (name, value, inline) for embed fields."""
    fields = []
    game, name, _ = _identity()
    if event_type not in SHARED_EVENTS:
        fields.append(('Character', '%s' % name, True))
    fields.append(('Server', game, True))
    lvl = ch.get('level')
    if lvl is not None:
        fields.append(('Level', str(lvl), True))
    hp = _hp_str(ch)
    if hp:
        fields.append(('Vitals', hp, True))
    pos = _position_str(ch)
    if pos:
        fields.append(('Position', pos, True))
    if extras:
        for k, v in extras:
            if v not in (None, ''):
                fields.append((k, str(v), True))
    return fields


def _render(payload):
    """Build channel-specific payloads.
    payload = {type, text, extras (list of (k,v)), force}
    Returns (telegram_text, telegram_is_html, discord_text, discord_embed_or_None)
    """
    event_type = payload['type']
    text = payload.get('text') or ''
    extras = payload.get('extras') or []
    rich = config.get('rich_cards', True)

    try:
        ch = get_character_data() or {}
    except Exception:
        ch = {}
    game, name, _ = _identity()
    emoji = EMOJI.get(event_type, 'ℹ️')
    title = TITLES.get(event_type, event_type.replace('_', ' ').title())

    # Plain fallback (used if rich_cards is off)
    if event_type in SHARED_EVENTS:
        plain = '%s [%s] %s' % (emoji, game, text)
    else:
        plain = '%s [%s • %s] %s' % (emoji, game, name, text)

    if not rich:
        return plain, False, plain, None

    fields = _build_fields(event_type, ch, extras)

    # Telegram HTML card
    def esc(s):
        return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

    lines = ['<b>%s %s</b>' % (emoji, esc(title))]
    if text:
        lines.append(esc(text))
    if fields:
        lines.append('')
        for k, v, _ in fields:
            lines.append('<b>%s:</b> <code>%s</code>' % (esc(k), esc(v)))
    tg_html = '\n'.join(lines)

    # Discord embed
    embed = {
        'title': '%s %s' % (emoji, title),
        'description': text[:2000] if text else None,
        'color': COLOURS.get(event_type, 0x607D8B),
        'fields': [{'name': k, 'value': str(v)[:1024], 'inline': inline}
                   for (k, v, inline) in fields],
        'footer': {'text': 'xNotify v%s' % pVersion},
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime()),
    }
    # Strip None description (Discord rejects nulls in some validators)
    if embed['description'] is None:
        embed.pop('description', None)

    return tg_html, True, plain, embed


# ______________________________ notify() ______________________________ #

_last_sent = {}
_throttle_lock = threading.Lock()


def _throttled(event_type):
    cd = config.get('cooldown_sec', 60)
    now = time.monotonic()
    with _throttle_lock:
        last = _last_sent.get(event_type, 0)
        if now - last < cd:
            return True
        _last_sent[event_type] = now
        return False


def notify(event_type, text, force=False, extras=None):
    """Public API. Other plugins: import xNotify; xNotify.notify('trade_start', '...')
    force=True bypasses the per-event cooldown (used for PMs / uniques).
    extras: optional list of (label, value) tuples added to the card."""
    if not config.get('events', {}).get(event_type, False):
        return
    if event_type in SHARED_EVENTS:
        key = event_type + '|' + (text or '')
        if not _claim_shared(key, SHARED_WINDOW.get(event_type, 30.0)):
            return
    elif not force and _throttled(event_type):
        return
    _send_q.put({'type': event_type, 'text': text or '', 'extras': extras or []})


# ______________________________ Event detectors ______________________________ #

_prev_hp = None
_prev_botting = None
_prev_level = None
ATTACK_OPCODE = 0xB070


def _is_botting():
    try:
        ch = get_character_data() or {}
    except Exception:
        return None
    for key in ('botting', 'training', 'bot'):
        if key in ch:
            return bool(ch[key])
    return None


_prev_hp_pots = None
_prev_mp_pots = None
_last_pot_check = 0
POT_CHECK_INTERVAL = 5.0


def _potion_counts():
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
            notify('hp_pots_out', 'Out of HP potions', extras=[('Before', _prev_hp_pots)])
        _prev_hp_pots = hp
    if mp is not None:
        if _prev_mp_pots is not None and _prev_mp_pots > 0 and mp == 0:
            notify('mp_pots_out', 'Out of MP potions', extras=[('Before', _prev_mp_pots)])
        _prev_mp_pots = mp


_seen_uniques = set()


def _is_unique_mob(mob):
    """Detect a real Unique. phBot mob 'rarity' codes: 0=general, 1=champion,
    3=giant, 4=party-champion, 5=elite, 6=unique. Only 6 is a true Unique —
    matching 3/4/5 falsely flagged every champion/giant that spawned near the
    character. We require either rarity==6 OR an explicit name match."""
    if not mob:
        return False
    unique_types = set(config.get('unique_types') or [6])
    r = mob.get('rarity')
    if r in unique_types:
        return True
    name = str(mob.get('name') or mob.get('servername') or '').lower()
    if not name:
        return False
    for kw in config.get('unique_keywords') or []:
        if kw and kw.lower() in name:
            return True
    for nm in config.get('unique_names') or []:
        if nm and nm.lower() in name:
            return True
    return False


def _check_uniques():
    """Alert on every unique monster in view, once per spawn. Re-spawns (new
    entity key) re-alert."""
    global _seen_uniques
    try:
        mons = get_monsters() or {}
    except Exception:
        return
    present = set()
    try:
        iterator = mons.items()
    except Exception:
        iterator = ((i, m) for i, m in enumerate(mons or []))
    for key, mob in iterator:
        if not _is_unique_mob(mob):
            continue
        present.add(key)
        if key not in _seen_uniques:
            mname = mob.get('name') or mob.get('servername') or '?'
            extras = [
                ('Mob', mname),
                ('HP', mob.get('hp')),
                ('Type', mob.get('type')),
                ('Rarity', mob.get('rarity')),
            ]
            try:
                pos = get_position() or {}
                if 'x' in mob and 'y' in mob and pos:
                    dx = float(mob['x']) - float(pos.get('x', 0))
                    dy = float(mob['y']) - float(pos.get('y', 0))
                    extras.append(('Distance', '%dm' % int((dx * dx + dy * dy) ** 0.5)))
            except Exception:
                pass
            notify('unique', 'Unique spawned: ' + mname, force=True, extras=extras)
    _seen_uniques = present


_seen_drops = set()
_last_drop_check = 0
DROP_CHECK_INTERVAL = 3.0


def _is_rare_drop(item_name):
    name = (item_name or '').lower()
    for kw in config.get('rare_drop_keywords') or []:
        if kw and kw.lower() in name:
            return True
    return False


def _check_drops():
    global _seen_drops, _last_drop_check
    now = time.monotonic()
    if now - _last_drop_check < DROP_CHECK_INTERVAL:
        return
    _last_drop_check = now
    try:
        drops = get_drops() or {}
    except Exception:
        return
    present = set()
    try:
        iterator = drops.items()
    except Exception:
        iterator = ((i, d) for i, d in enumerate(drops or []))
    for key, drop in iterator:
        if not drop:
            continue
        present.add(key)
        if key in _seen_drops:
            continue
        nm = drop.get('name') or ''
        if _is_rare_drop(nm):
            notify('rare_drop', 'Dropped: ' + nm, extras=[
                ('Item', nm),
                ('Owner', drop.get('owner') or '—'),
            ])
    _seen_drops = present


def event_loop():
    global _prev_hp, _prev_botting, _prev_level
    try:
        ch = get_character_data() or {}
    except Exception:
        return
    hp = ch.get('hp')
    if hp is not None:
        if _prev_hp is not None and _prev_hp > 0 and hp == 0:
            notify('death', 'Character died', extras=[('Last HP', _prev_hp)])
        _prev_hp = hp
    lvl = ch.get('level')
    if lvl is not None:
        if _prev_level is not None and lvl > _prev_level:
            notify('level_up', 'Reached level %s' % lvl,
                   extras=[('Previous', _prev_level), ('New', lvl)])
        _prev_level = lvl
    b = _is_botting()
    if b is not None:
        if _prev_botting is True and b is False:
            notify('bot_stopped', 'Bot stopped')
        _prev_botting = b
    _check_potions()
    _check_uniques()
    _check_drops()


def handle_joymax(opcode, data):
    if opcode != ATTACK_OPCODE:
        return
    return


def _is_unique_text(msg):
    low = (msg or '').lower()
    for kw in config.get('unique_keywords', []) or []:
        if kw and kw.lower() in low:
            return True
    return False


# Map known SRO chat type codes to xNotify event keys.
# 1=All, 2=PM, 3=Party, 4=Guild, 5=Global, 6=Notice (server-dependent on 5/6),
# 7=Stall, 9=Union, 11=Academy. Many servers swap 5/6 — treat both as "broad".
CHAT_TYPE_MAP = {
    1: ('all_chat', False),
    2: ('pm', True),       # force=True bypasses cooldown for PMs
    3: ('party_chat', False),
    4: ('guild_chat', False),
    5: ('global', False),
    6: ('global', False),
    7: ('stall_chat', False),
    9: ('union_chat', False),
    11: ('academy_chat', False),
}


def handle_chat(t, player, msg):
    # Server notices/system messages typically arrive as t==7 on some servers and
    # t==6 on others. We treat any "broad" chat (5/6) as global, surface a unique
    # alert if it contains a known keyword, and route the rest by type.
    text = msg or ''
    if t in (5, 6) and _is_unique_text(text):
        notify('unique', text, extras=[('Source', 'chat')])
        return

    mapping = CHAT_TYPE_MAP.get(t)
    if mapping is None:
        # Unknown chat type — surface as a notice so nothing is silently dropped.
        notify('notice', '[type %s] %s' % (t, text),
               extras=[('From', player or '—'), ('Chat type', t)])
        return

    event_key, force = mapping
    sender = player or '—'
    if event_key == 'pm':
        notify('pm', text, force=force, extras=[('From', sender)])
    else:
        notify(event_key, text, force=force, extras=[('From', sender)])


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

chkRich = QtBind.createCheckBox(gui, '', 'Rich card layout (Discord embed / Telegram HTML)', 200, 112)
QtBind.setChecked(gui, chkRich, bool(config.get('rich_cards', True)))

QtBind.createLabel(gui, 'Events:', 6, 140)
_event_checks = {}
_COLS = 4
_COL_W = 130
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
btnTestUnique = QtBind.createButton(gui, 'btnTestUnique_clicked', '  Test Unique  ', 180, _btn_y)
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
    config['rich_cards'] = bool(QtBind.isChecked(gui, chkRich))
    for _key, chk in _event_checks.items():
        config['events'][_key] = bool(QtBind.isChecked(gui, chk))
    save_config(config)
    QtBind.setText(gui, txtToken, _mask_secret(config['telegram_token']))
    QtBind.setText(gui, txtChat, _mask_secret(config['telegram_chat_id']))
    QtBind.setText(gui, txtHook, _mask_secret(config['discord_webhook']))
    _safe_log('config saved')
    _set_status('saved')


def btnTest_clicked():
    _send_q.put({'type': 'death', 'text': 'xNotify test message',
                 'extras': [('Note', 'Manual test from GUI')]})
    _set_status('test queued')


def btnTestUnique_clicked():
    _send_q.put({'type': 'unique', 'text': 'Unique spawned: Tiger Girl (test)',
                 'extras': [('Mob', 'Tiger Girl'), ('HP', '120000'),
                            ('Type', 1), ('Rarity', 6), ('Distance', '37m')]})
    _set_status('unique test queued')


_safe_log('xNotify %s loaded' % pVersion)

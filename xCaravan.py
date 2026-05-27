from phBot import *
import QtBind
import json
import os
import struct
import time
import webbrowser

GITHUB_URL = 'https://github.com/Vette1123'
GITHUB_BTN_STYLE = (
    'QPushButton{background:#ffd54a;color:#222;font-weight:bold;'
    'border:1px solid #8b6b00;border-radius:6px;padding:2px 10px;}'
    'QPushButton:hover{background:#ffe27a;}'
)

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

pName = 'xCaravan'
pVersion = '1.0.0'
pAuthor = 'Vette1123 (Gado)'
pUrl = 'https://raw.githubusercontent.com/Vette1123/phbot-plugins/main/xCaravan.py'
# GitHub: https://github.com/Vette1123

DEFAULT_BOX_NAME = 'Trader Sack Lv 4'
BOX_NAME_ALIASES = {
    'trader sack lv 4': ('special box', 'specialty goods', 'magic silverbag', 'trade trader 04'),
    'special box': ('specialty goods',),
    'magic silverbag': ('trade trader 04',)
}

gui = QtBind.init(__name__, pName)

_PAD = ' ' * 160

QtBind.createLabel(gui, '🚛  xCaravan  —  Auto Caravan  ' + ('═' * 80), 12, 8)

chkEnabled = QtBind.createCheckBox(gui, 'cbx_enabled_clicked', '🟢  ENABLE  PLUGIN  🟢', 12, 30)
chkStartBotAfter = QtBind.createCheckBox(gui, 'cbx_start_bot_after_clicked', '🤖 Start bot after', 200, 30)
chkUnequipAfter = QtBind.createCheckBox(gui, 'cbx_unequip_after_clicked', '🧺 Unequip after', 345, 30)
chkReverseAfter = QtBind.createCheckBox(gui, 'cbx_reverse_after_clicked', '🌀 Reverse to recall after', 480, 30)

QtBind.createLabel(gui, '🎭 Role:', 12, 56)
chkRouteThief = QtBind.createCheckBox(gui, 'cbx_route_thief_clicked', '⚔ Thief', 65, 54)
chkRouteHunter = QtBind.createCheckBox(gui, 'cbx_route_hunter_clicked', '🏹 Hunter', 135, 54)
chkRouteTrader = QtBind.createCheckBox(gui, 'cbx_route_trader_clicked', '💰 Trader', 220, 54)

QtBind.createLabel(gui, '📦 Goods item', 12, 80)
txtBoxName = QtBind.createLineEdit(gui, DEFAULT_BOX_NAME, 95, 78, 150, 20)
QtBind.createLabel(gui, 'Run at', 255, 80)
txtBoxLimit = QtBind.createLineEdit(gui, '1', 300, 78, 40, 20)
QtBind.createLabel(gui, 'Scan (ms)', 350, 80)
txtScanMs = QtBind.createLineEdit(gui, '30000', 410, 78, 60, 20)

QtBind.createLabel(gui, '🚚 Job suit', 12, 104)
txtSuitFilter = QtBind.createLineEdit(gui, 'Trader', 95, 102, 150, 20)
QtBind.createLabel(gui, 'Min boxes', 255, 104)
txtFinalBoxMin = QtBind.createLineEdit(gui, '20', 325, 102, 40, 20)
QtBind.createLabel(gui, 'Route TPs', 375, 104)
txtFinalTeleports = QtBind.createLineEdit(gui, '3', 440, 102, 35, 20)
QtBind.createLabel(gui, 'Action (ms)', 485, 104)
txtActionMs = QtBind.createLineEdit(gui, '3500', 550, 102, 55, 20)

QtBind.createButton(gui, 'btn_save_clicked', '💾  Save', 12, 130)
QtBind.createButton(gui, 'btn_scan_clicked', '🔎  Scan', 95, 130)
QtBind.createButton(gui, 'btn_start_clicked', '🚀  START', 180, 130)
QtBind.createButton(gui, 'btn_stop_clicked', '🛑  STOP', 275, 130)
QtBind.createButton(gui, 'btn_run_route_clicked', '📜  Run script', 360, 130)
QtBind.createButton(gui, 'btn_reverse_now_clicked', '🌀  Reverse now', 470, 130)

QtBind.createLabel(gui, '━━ Status ' + ('━' * 110), 12, 162)
lblBox = QtBind.createLabel(gui, '📦 Box: not read' + _PAD, 12, 184)
lblSuit = QtBind.createLabel(gui, '👕 Suit: not read' + _PAD, 12, 210)
lblStatus = QtBind.createLabel(gui, '⏺ Status: loading…' + _PAD, 12, 236)

_STAT_PAD = ' ' * 40
lblStatGoodsPerHour = QtBind.createLabel(gui, '📊 Goods/h: 0' + _STAT_PAD, 12, 262)
lblStatNextTrade = QtBind.createLabel(gui, '⏱ Next: --:--' + _STAT_PAD, 165, 262)
lblStatRuns = QtBind.createLabel(gui, '🏁 Runs: 0' + _STAT_PAD, 320, 262)
lblStatAvgRun = QtBind.createLabel(gui, '⌛ Avg: 0m' + _STAT_PAD, 420, 262)
lblStatBestRun = QtBind.createLabel(gui, '⭐ Best: --' + _STAT_PAD, 520, 262)

lblStatStones = QtBind.createLabel(gui, '💎 Stones: 0' + _STAT_PAD, 12, 284)
lblStatArena = QtBind.createLabel(gui, '🪙 Arena: 0' + _STAT_PAD, 165, 284)
lblStatGold = QtBind.createLabel(gui, '💰 Gold: 0' + _STAT_PAD, 320, 284)
lblStatUptime = QtBind.createLabel(gui, '⏲ Up: 0m' + _STAT_PAD, 520, 284)
QtBind.createButton(gui, 'btn_reset_stats_clicked', '↻ Reset', 595, 282)
btnGithub = QtBind.createButton(gui, 'btn_github_clicked', ' 🟡 Gado 🟡 ', 605, 130)
_try_style_github(btnGithub)

ROUTE_SCRIPT = '''walk,6430,1099,-32
walk,6428,1113,0
walk,6419,1134,-6
walk,6405,1134,-6
walk,6383,1133,-6
walk,6365,1134,-6
walk,6333,1134,-5
walk,6317,1134,-6
walk,6301,1134,-6
walk,6292,1132,-2
walk,6290,1126,0
walk,6289,1113,2
walk,6289,1100,8
walk,6287,1092,0
cast,Job - Caravan Bugle
begintargettrading
walk,6259,1093,0
walk,6233,1090,0
walk,6221,1091,0
walk,6219,1105,8
walk,6220,1124,0
walk,6189,1133,-3
walk,6161,1134,1
walk,6131,1133,-4
walk,6101,1122,13
walk,6062,1105,28
walk,6033,1089,56
walk,5998,1074,77
walk,5952,1064,81
walk,5913,1066,104
walk,5864,1068,96
walk,5824,1065,160
walk,5788,1059,214
walk,5748,1057,287
walk,5707,1054,355
walk,5673,1054,418
walk,5628,1059,520
walk,5589,1058,573
walk,5549,1045,636
walk,5519,1024,686
walk,5483,996,687
walk,5439,986,684
walk,5393,976,671
walk,5345,969,667
walk,5311,957,684
walk,5277,935,690
walk,5244,906,689
walk,5211,873,710
walk,5172,833,717
walk,5146,792,756
walk,5131,750,781
walk,5115,710,745
walk,5089,678,764
walk,5078,650,754
walk,5066,624,680
walk,5030,590,563
walk,4988,563,570
walk,4951,538,599
walk,4915,518,632
walk,4866,487,725
walk,4823,471,813
walk,4773,477,853
walk,4722,493,864
walk,4689,498,859
walk,4661,503,835
walk,4611,512,743
walk,4571,521,681
walk,4534,538,630
walk,4506,563,609
walk,4481,592,572
walk,4480,615,578
walk,4489,643,607
walk,4506,691,482
walk,4521,736,361
walk,4517,780,271
walk,4505,816,169
walk,4485,856,77
walk,4467,890,51
walk,4456,914,49
walk,4451,922,48
wait,2000
teleport,Ferry Ticket Seller Chau,Ferry Ticket Seller Hageuk
wait,2000
walk,4110,1259,42
walk,4098,1288,63
walk,4077,1326,70
walk,4056,1356,73
walk,4035,1381,54
walk,4007,1395,32
walk,3971,1390,-3
walk,3936,1378,-11
walk,3882,1353,-23
walk,3850,1338,-6
walk,3808,1318,-10
walk,3771,1303,-10
walk,3731,1285,-3
walk,3690,1272,0
walk,3645,1262,0
walk,3604,1259,0
walk,3556,1248,1
walk,3528,1216,4
walk,3499,1182,8
walk,3467,1148,17
walk,3441,1122,19
walk,3406,1089,6
walk,3370,1064,3
walk,3333,1049,1
walk,3303,1071,0
walk,3280,1102,0
walk,3267,1139,0
walk,3245,1169,0
walk,3210,1186,0
walk,3164,1198,0
walk,3116,1206,0
walk,3079,1212,0
walk,3032,1222,1
walk,2986,1227,-11
walk,2934,1224,-13
walk,2897,1224,8
walk,2867,1234,26
walk,2816,1251,21
walk,2779,1261,-21
walk,2735,1266,25
walk,2680,1260,2
walk,2630,1223,5
walk,2610,1187,58
walk,2587,1138,57
walk,2564,1093,-53
walk,2543,1034,-229
walk,2521,988,-282
walk,2508,956,-304
walk,2496,922,-307
walk,2476,879,-296
walk,2461,838,-259
walk,2444,797,-213
walk,2428,766,-199
walk,2406,726,-197
walk,2381,688,-224
walk,2345,644,-215
walk,2296,609,-152
walk,2246,584,-134
walk,2196,570,-72
walk,2143,557,-29
walk,2104,546,-21
walk,2066,536,-37
walk,2025,530,-49
walk,1971,526,-86
walk,1928,511,-83
walk,1907,474,-55
walk,1882,427,-48
walk,1864,379,-35
walk,1850,331,-25
walk,1849,285,-11
walk,1854,232,0
walk,1857,189,15
walk,1853,146,17
walk,1841,110,26
walk,1824,73,64
walk,1802,34,84
walk,1768,-10,69
walk,1743,-63,10
walk,1729,-112,7
walk,1699,-158,9
walk,1673,-197,-19
walk,1651,-233,-42
walk,1611,-264,-56
walk,1584,-285,-56
walk,1573,-294,-57
walk,1566,-295,-28
wait,2000
teleport,Boat Ticket Seller Asa,Boat Ticket Seller Asimo
wait,2000
walk,1070,-302,-34
walk,1028,-300,-76
walk,997,-294,-111
walk,964,-289,-127
walk,930,-277,-129
walk,889,-261,-108
walk,857,-242,-95
walk,825,-223,-72
walk,789,-207,-93
walk,754,-191,-83
walk,711,-177,-79
walk,677,-172,-41
walk,633,-176,-23
walk,600,-188,11
walk,557,-203,-8
walk,520,-207,18
walk,500,-209,57
walk,459,-213,-3
walk,418,-233,12
walk,382,-253,101
walk,362,-266,157
walk,323,-294,115
walk,305,-299,167
walk,265,-321,73
walk,230,-319,71
walk,194,-317,47
walk,158,-305,39
walk,123,-283,3
walk,114,-270,3
walk,113,-244,10
walk,114,-214,10
walk,113,-185,10
walk,112,-155,12
walk,104,-131,10
walk,97,-117,22
walk,93,-99,84
walk,92,-89,99
settletargettrading
terminate,transport
use,returnscroll
'''

HUNTER_ROUTE_SCRIPT = '''walk,6446,1069,-32
walk,6451,1048,-32
walk,6445,1018,-32
walk,6440,990,1
walk,6444,978,0
walk,6467,982,0
walk,6480,995,0
walk,6490,1016,0
cast,Job - Caravan Bugle
begintargettrading
walk,6477,995,0
walk,6448,974,0
walk,6436,969,0
walk,6434,962,0
walk,6434,932,0
walk,6433,905,-9
walk,6403,882,-4
walk,6374,863,-14
walk,6342,863,-10
walk,6322,838,-22
walk,6299,806,-38
walk,6275,791,-14
walk,6227,771,-5
walk,6196,752,16
walk,6149,725,39
walk,6108,709,70
walk,6074,699,140
walk,6031,692,160
walk,5987,691,172
walk,5945,689,161
walk,5901,687,154
walk,5854,687,158
walk,5817,687,167
walk,5792,686,167
walk,5774,686,208
walk,5738,686,170
walk,5709,683,204
walk,5685,683,253
walk,5652,676,309
walk,5630,666,410
walk,5602,655,504
walk,5565,636,593
walk,5530,617,684
walk,5505,603,747
walk,5470,582,805
walk,5448,567,858
walk,5428,557,892
walk,5406,548,923
walk,5379,547,955
walk,5358,544,977
walk,5327,540,969
walk,5301,536,945
walk,5266,538,866
walk,5224,552,813
walk,5192,562,776
walk,5159,572,746
walk,5121,582,707
walk,5085,589,662
walk,5046,577,599
walk,5011,559,574
walk,4964,537,591
walk,4932,520,624
walk,4895,498,669
walk,4856,485,752
walk,4826,476,815
walk,4785,479,849
walk,4762,493,865
walk,4728,499,867
walk,4695,501,862
walk,4665,499,836
walk,4634,503,769
walk,4594,511,715
walk,4558,518,665
walk,4529,540,626
walk,4501,562,599
walk,4480,597,573
walk,4471,624,575
walk,4480,642,606
walk,4498,669,553
walk,4514,699,463
walk,4527,734,360
walk,4523,759,329
walk,4513,792,239
walk,4489,840,105
walk,4472,876,58
walk,4459,904,49
walk,4453,919,48
wait,2000
teleport,Ferry Ticket Seller Chau,Ferry Ticket Seller Hageuk
wait,2000
walk,4130,1237,40
walk,4124,1266,44
walk,4108,1297,57
walk,4079,1333,70
walk,4059,1358,71
walk,4035,1384,51
walk,4023,1406,40
walk,4008,1426,30
walk,3994,1434,8
walk,3982,1414,0
walk,3975,1397,0
walk,3939,1380,-12
walk,3903,1366,-26
walk,3873,1349,-13
walk,3842,1333,-14
walk,3811,1320,-13
walk,3786,1310,-6
walk,3760,1297,-9
walk,3732,1279,-4
walk,3707,1271,-8
walk,3673,1264,0
walk,3641,1261,0
walk,3607,1263,0
walk,3592,1265,0
walk,3567,1259,0
walk,3545,1231,2
walk,3521,1205,4
walk,3498,1179,8
walk,3477,1158,16
walk,3450,1130,19
walk,3419,1098,12
walk,3394,1075,4
walk,3373,1058,3
walk,3349,1045,2
walk,3325,1045,0
walk,3302,1056,0
walk,3289,1068,0
walk,3276,1114,0
walk,3270,1146,0
walk,3263,1164,0
walk,3251,1173,0
walk,3211,1187,0
walk,3172,1198,0
walk,3137,1205,0
walk,3103,1208,0
walk,3068,1214,0
walk,3030,1228,-7
walk,2996,1232,-19
walk,2971,1227,-20
walk,2938,1229,-9
walk,2897,1246,6
walk,2881,1253,20
walk,2851,1266,-39
walk,2825,1276,-37
walk,2797,1284,-26
walk,2771,1294,-1
walk,2752,1293,39
walk,2725,1287,17
walk,2687,1269,2
walk,2666,1256,2
walk,2638,1237,2
walk,2614,1206,41
walk,2600,1187,69
walk,2586,1160,76
walk,2572,1129,37
walk,2554,1088,-85
walk,2533,1033,-243
walk,2521,995,-282
walk,2514,974,-288
walk,2500,937,-309
walk,2489,909,-304
walk,2471,871,-288
walk,2462,844,-262
walk,2452,817,-235
walk,2441,791,-208
walk,2430,764,-200
walk,2415,736,-197
walk,2397,703,-216
walk,2377,675,-224
walk,2352,645,-217
walk,2335,631,-190
walk,2304,613,-157
walk,2279,599,-142
walk,2249,585,-137
walk,2218,575,-110
walk,2195,569,-71
walk,2163,563,-50
walk,2140,557,-28
walk,2115,549,-22
walk,2085,540,-32
walk,2057,530,-54
walk,2034,527,-51
walk,2004,529,-59
walk,1975,530,-84
walk,1943,524,-94
walk,1921,507,-79
walk,1907,485,-58
walk,1888,451,-52
walk,1872,422,-46
walk,1858,395,-38
walk,1845,369,-37
walk,1840,337,-34
walk,1842,298,-20
walk,1849,262,2
walk,1855,228,2
walk,1858,188,15
walk,1858,160,17
walk,1855,131,17
walk,1843,102,31
walk,1827,74,63
walk,1812,50,78
walk,1793,30,84
walk,1774,12,82
walk,1756,-2,62
walk,1734,-5,53
walk,1699,0,28
walk,1675,2,22
walk,1651,4,-13
walk,1626,-5,-17
walk,1599,-12,-23
walk,1586,-16,-20
walk,1582,-17,-20
wait,2000
teleport,Boat Ticket Seller Salmai,Boat Ticket Seller Rahan
wait,2000
walk,1025,-38,-21
walk,997,-21,-18
walk,969,-4,-20
walk,945,10,-31
walk,915,12,-27
walk,888,13,-27
walk,850,16,-30
walk,820,19,-26
walk,781,31,-22
walk,748,49,-16
walk,718,67,-2
walk,694,82,13
walk,666,91,17
walk,641,92,23
walk,611,81,20
walk,586,69,14
walk,555,59,4
walk,515,50,1
walk,491,48,5
walk,450,48,2
walk,429,47,11
walk,397,48,11
walk,364,48,11
walk,374,48,11
walk,347,48,11
walk,317,48,13
walk,294,48,11
walk,272,47,78
walk,251,48,164
walk,242,48,224
walk,223,47,243
walk,197,47,243
walk,178,46,243
walk,168,45,243
walk,164,42,243
walk,159,35,243
walk,158,19,243
walk,151,8,243
walk,147,2,243
settletargettrading
terminate,transport
use,returnscroll
'''

TRADER_ROUTE_SCRIPT = HUNTER_ROUTE_SCRIPT \
    .replace('begintargettrading', 'wait,8000') \
    .replace('settletargettrading', 'wait,5000')

TRADER_START_X = 6488
TRADER_START_Y = 1014
TRADER_START_RADIUS = 35
TRADER_SETTLE_X = 147
TRADER_SETTLE_Y = 4
TRADER_SETTLE_RADIUS = 15

TRADER_PACKET_DELAY_AFTER_READY = 400
TRADER_PACKET_DELAY_BETWEEN = 600
TRADER_PACKET_DELAY_CLOSE = 400
TRADER_PACKET_SETTLE_HOLD_MS = 2000
TRADER_PACKET_COOLDOWN_MS = 30000

TRADER_PACKET_START_TALK = (0x7045, 'D3 01 00 00')
TRADER_PACKET_START_BEGIN = (0x7533, '07 D3 01 00 00')
TRADER_PACKET_SETTLE_TALK = (0x7045, '06 06 00 00')
TRADER_PACKET_SETTLE_CONFIRM = (0x7533, '08 06 06 00 00')
TRADER_PACKET_SETTLE_CLOSE = (0x704B, '06 06 00 00')

DEFAULT_CONFIG = {
    'enabled': False,
    'start_bot_after': True,
    'unequip_after': True,
    'reverse_after': False,
    'route_mode': 'Thief',
    'verbose_logs': False,
    'box_name': DEFAULT_BOX_NAME,
    'box_limit': 1,
    'scan_ms': 5000,
    'suit_filter': 'Trader',
    'final_box_min': 20,
    'final_teleports': 3,
    'equip_wait_ms': 20000,
    'unequip_wait_ms': 20000,
    'action_ms': 3500
}

config = dict(DEFAULT_CONFIG)

state = 'idle'
last_scan_at = 0
action_at = 0
route_teleports = 0
last_box_count = 0
route_start_wait_ms = 3500
loaded_char_name = ''
last_town_guard_at = 0

trader_pkt_start_stage = 0
trader_pkt_settle_stage = 0
trader_pkt_stage_at = 0
trader_pkt_settle_arrived_at = 0
trader_pkt_start_done_visit = False
trader_pkt_settle_done_visit = False
trader_pkt_last_start_at = 0
trader_pkt_last_settle_at = 0

reverse_pending = False
reverse_last_pos = None
reverse_stationary_since = 0
reverse_started_at = 0
reverse_last_stop_at = 0

REVERSE_MIN_RUN_MS = 30000
REVERSE_STATIONARY_MS = 6000
REVERSE_POS_TOLERANCE = 2.0
REVERSE_HARD_TIMEOUT_MS = 30 * 60 * 1000
REVERSE_POST_TELEPORT_WAIT_MS = 2500
REVERSE_TELEPORT_TIMEOUT_MS = 30000
REVERSE_STOP_SCRIPT_INTERVAL_MS = 500

RETURN_RETRY_MS = 20000
RETURN_MAX_ATTEMPTS = 4

return_attempts = 0
return_last_try_at = 0

trade_lockdown_until = 0
last_bot_status = -1
bot_ever_seen_running = False
empty_inventory_scans = 0
_training_area_warned = False

stats_started_at = 0
stats_runs = 0
stats_run_durations_ms = []
stats_current_run_started_at = 0
stats_baseline_gold = None
stats_baseline_stones = None
stats_baseline_arena = None
stats_last_ui_update = 0
stats_fill_samples = []
stats_last_seen_count = -1
stats_last_empty_at = 0
stats_known_fill_ms = 0
stats_total_boxes_returned = 0
STONE_FILTERS = ('magic stone', 'astral stone', 'stone of', 'devil stone', 'lucky stone', 'tablet')
ARENA_FILTERS = ('arena coin', 'arena point')

ROUTE_ACTIVE_STATES = {
    'starting_route', 'route_running', 'returning_to_town',
    'awaiting_reverse_teleport', 'town_returned', 'route_returned', 'finishing',
    'reverse_completed', 'awaiting_sort_settle'
}

REVERSE_SORT_SETTLE_MS = 15000

TRADER_LOCKDOWN_MS = 90000


def _trade_locked(now):
    return now < trade_lockdown_until


def _at_training_area():
    global _training_area_warned
    fn = globals().get('get_training_area')
    area = None
    if callable(fn):
        try:
            area = fn()
        except Exception:
            area = None
    if area:
        try:
            pos = get_position()
        except Exception:
            pos = None
        if not pos:
            return False
        try:
            px = float(pos.get('x', 0))
            py = float(pos.get('y', 0))
        except Exception:
            return False
        try:
            if isinstance(area, dict):
                ax = float(area.get('x', area.get('center_x', 0)))
                ay = float(area.get('y', area.get('center_y', 0)))
                ar = float(area.get('radius', area.get('r', 35)))
            else:
                ax = float(area[0]); ay = float(area[1]); ar = float(area[2])
        except Exception:
            return False
        dx = px - ax
        dy = py - ay
        return (dx * dx + dy * dy) <= (ar * ar)
    if not _training_area_warned:
        _training_area_warned = True
        _log('get_training_area unavailable; falling back to bot-status only.', True)
    return True


def _armed(now):
    return True


_bot_status_api_warned = False
_bot_status_probed = False


def _bot_is_running():
    # Only auto-trigger the caravan when the user is actively botting.
    # phBot exposes get_status() (undocumented). One-shot log of the raw return
    # value the first time we call it, so we can confirm the truthiness mapping.
    global _bot_status_api_warned, _bot_status_probed, bot_ever_seen_running
    fn = globals().get('get_status')
    if not callable(fn):
        if not _bot_status_api_warned:
            _bot_status_api_warned = True
            log('[%s] get_status() not available; auto-trigger gate disabled.' % pName)
        bot_ever_seen_running = True
        return True
    try:
        value = fn()
        running = bool(value)
        if not _bot_status_probed:
            _bot_status_probed = True
            label = str(value).strip() if value else 'idle'
            log('[%s] Bot status detected: %s (%s)' % (pName, label, 'running' if running else 'not running'))
        if running:
            bot_ever_seen_running = True
        return running
    except Exception as ex:
        if not _bot_status_api_warned:
            _bot_status_api_warned = True
            log('[%s] get_status() raised %s; treating bot as running.' % (pName, ex))
        bot_ever_seen_running = True
        return True


def _now():
    return int(time.time() * 1000)


def _normalize(value):
    text = str(value or '').lower()
    for char in '._-[]()':
        text = text.replace(char, ' ')
    return ' '.join(text.split())


STATUS_GLYPHS = (
    ('lockdown', '🔒'),
    ('trade', '💱'),
    ('paused', '⏸'),
    ('disabled', '⚪'),
    ('stopped', '⛔'),
    ('idle', '⏺'),
    ('monitoring', '🟢'),
    ('scan', '🔎'),
    ('route', '🚚'),
    ('return', '↩'),
    ('reverse', '↺'),
    ('finish', '🏁'),
    ('wait', '⏳'),
    ('start', '▶'),
    ('error', '⚠'),
)


def _status_glyph(message):
    m = str(message).lower()
    for key, glyph in STATUS_GLYPHS:
        if key in m:
            return glyph
    return '•'


def _set_status(message):
    glyph = _status_glyph(message)
    QtBind.setText(gui, lblStatus, '%s Status: %s%s' % (glyph, str(message), _PAD))


def _set_suit(text):
    t = str(text)
    low = t.lower()
    if 'worn' in low or 'equipping' in low:
        glyph = '👕'
    elif 'not found' in low or 'no empty' in low or 'not worn' in low:
        glyph = '⚪'
    elif 'unequipping' in low:
        glyph = '↩'
    else:
        glyph = '·'
    QtBind.setText(gui, lblSuit, '%s %s%s' % (glyph, t, _PAD))


_log_file_warned = False
_log_file_truncated = set()
_phbot_log = log  # capture the original phBot log before we shadow it


def _log_path():
    # Per-character log so each account has its own clean trace. Falls back
    # to a shared file before character data is available (e.g. very early
    # at module load, before joined_game fires).
    try:
        base = get_config_dir()
    except Exception:
        base = os.path.dirname(os.path.abspath(__file__))
    char = _character_name() if 'loaded_char_name' in globals() else 'default'
    if not char or char == 'default':
        return os.path.join(base, '%s.log' % pName)
    return os.path.join(base, '%s_%s.log' % (pName, char))


def _log_to_file(message):
    global _log_file_warned
    try:
        path = _log_path()
        stamp = time.strftime('%Y-%m-%d %H:%M:%S')
        line = '[%s] %s\n' % (stamp, message)
        mode = 'a' if path in _log_file_truncated else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(line)
        _log_file_truncated.add(path)
    except Exception as ex:
        if not _log_file_warned:
            _log_file_warned = True
            try:
                _phbot_log('[%s] Dedicated log write failed: %s' % (pName, ex))
            except Exception:
                pass


def log(message):
    # Shadow phBot's log so every line emitted by xCaravan is captured in
    # the dedicated xCaravan.log alongside phBot's main log. Other plugins
    # are unaffected — this rebinding lives only in this module's namespace.
    try:
        _log_to_file(str(message))
    except Exception:
        pass
    try:
        _phbot_log(message)
    except Exception:
        pass


def _log(message, force=False):
    if force or config.get('verbose_logs', False):
        log('[%s] %s' % (pName, message))
    else:
        _log_to_file('[%s] %s' % (pName, message))


def _error(message):
    log('[%s] %s' % (pName, message))


def _snapshot_inventory():
    # get_inventory() returns an empty/None dict during transient states (right
    # after login, between teleports, while phBot is asleep due to a full pouch).
    # xShining hit the same issue and falls back to get_inventory_data() — match
    # that pattern so the caravan trigger doesn't silently observe 0 boxes when
    # the pouch is actually full.
    inv = None
    try:
        inv = get_inventory()
    except Exception:
        inv = None
    if not inv or not inv.get('items'):
        fn = globals().get('get_inventory_data')
        if callable(fn):
            try:
                fallback = fn()
                if fallback and fallback.get('items'):
                    inv = fallback
            except Exception:
                pass
    return inv or {}


def _count_items_matching(filters, inv=None):
    if inv is None:
        inv = _snapshot_inventory()
    items = inv.get('items') or []
    total = 0
    for item in items:
        if not item:
            continue
        name = _normalize(item.get('name') or item.get('servername') or '')
        if any(f in name for f in filters):
            total += int(item.get('quantity', 1) or 1)
    return total


def _current_gold(inv=None):
    if inv is None:
        inv = _snapshot_inventory()
    try:
        return int(inv.get('gold', 0) or 0)
    except Exception:
        return 0


def _stats_init_baseline():
    global stats_baseline_gold, stats_baseline_stones, stats_baseline_arena
    if stats_baseline_gold is None:
        stats_baseline_gold = _current_gold()
    if stats_baseline_stones is None:
        stats_baseline_stones = _count_items_matching(STONE_FILTERS)
    if stats_baseline_arena is None:
        stats_baseline_arena = _count_items_matching(ARENA_FILTERS)


def _stats_record_run_complete():
    global stats_runs, stats_current_run_started_at, stats_total_boxes_returned, stats_last_empty_at
    if stats_current_run_started_at <= 0:
        return
    dur = _now() - stats_current_run_started_at
    if dur > 0:
        stats_run_durations_ms.append(dur)
        if len(stats_run_durations_ms) > 50:
            del stats_run_durations_ms[:-50]
    stats_runs += 1
    stats_total_boxes_returned += last_box_count if last_box_count > 0 else config.get('box_limit', 1)
    stats_current_run_started_at = 0
    stats_last_empty_at = _now()


def _format_hms(ms):
    if ms <= 0:
        return '0m'
    s = ms // 1000
    h = s // 3600
    m = (s % 3600) // 60
    if h > 0:
        return '%dh%02dm' % (h, m)
    return '%dm' % m


def _format_countdown(ms):
    if ms <= 0:
        return 'now'
    s = ms // 1000
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return '%d:%02d:%02d' % (h, m, sec)
    return '%02d:%02d' % (m, sec)


def _stats_sample_fill(now, count):
    global stats_last_seen_count, stats_known_fill_ms, stats_last_empty_at
    if state in ROUTE_ACTIVE_STATES:
        stats_last_seen_count = -1
        return
    limit = config.get('box_limit', 1)
    if stats_last_seen_count >= 0 and count < stats_last_seen_count:
        stats_last_empty_at = now
    if stats_last_seen_count >= 0 and stats_last_seen_count < limit and count >= limit:
        if stats_last_empty_at > 0:
            stats_known_fill_ms = now - stats_last_empty_at
    stats_last_seen_count = count


def _compact_num(n):
    n = int(n)
    if n < 1000:
        return str(n)
    if n < 1000000:
        return '%.1fk' % (n / 1000.0)
    if n < 1000000000:
        return '%.1fM' % (n / 1000000.0)
    return '%.1fB' % (n / 1000000000.0)


def _stats_update_ui(now):
    global stats_last_ui_update
    if now - stats_last_ui_update < 1000:
        return
    stats_last_ui_update = now

    uptime_ms = now - stats_started_at if stats_started_at else 0
    hours = uptime_ms / 3600000.0 if uptime_ms > 0 else 0
    has_data = stats_runs >= 1

    inv = _snapshot_inventory()
    stones_now = _count_items_matching(STONE_FILTERS, inv)
    arena_now = _count_items_matching(ARENA_FILTERS, inv)
    gold_now = _current_gold(inv)

    if has_data and hours > 0.0167:
        goods_per_hour = int(stats_total_boxes_returned / hours)
        stones_h = int(max(0, stones_now - (stats_baseline_stones or 0)) / hours)
        arena_h = int(max(0, arena_now - (stats_baseline_arena or 0)) / hours)
        gold_h = int(max(0, gold_now - (stats_baseline_gold or 0)) / hours)
    else:
        goods_per_hour = stones_h = arena_h = gold_h = -1

    if state in ROUTE_ACTIVE_STATES:
        next_trade = 'in route'
    elif not config.get('enabled', False):
        next_trade = 'off'
    elif _trade_locked(now) and config.get('route_mode') == 'Trader':
        next_trade = 'locked'
    elif stats_known_fill_ms <= 0:
        next_trade = 'after 1st run'
    elif stats_last_empty_at <= 0:
        next_trade = 'pouch full'
    else:
        remaining = stats_known_fill_ms - (now - stats_last_empty_at)
        next_trade = _format_countdown(remaining) if remaining > 0 else 'pouch full'

    avg_ms = sum(stats_run_durations_ms) // len(stats_run_durations_ms) if stats_run_durations_ms else 0
    best_ms = min(stats_run_durations_ms) if stats_run_durations_ms else 0

    stones_total = max(0, stones_now - (stats_baseline_stones or 0))
    arena_total = max(0, arena_now - (stats_baseline_arena or 0))
    gold_total = max(0, gold_now - (stats_baseline_gold or 0))

    rate_tag = lambda v: ('--' if v < 0 else str(v))
    rate_tag_g = lambda v: ('--' if v < 0 else _compact_num(v))

    QtBind.setText(gui, lblStatGoodsPerHour, '📊 Goods/h: %s%s' % (rate_tag(goods_per_hour), _STAT_PAD))
    QtBind.setText(gui, lblStatNextTrade, '⏱ Next: %s%s' % (next_trade, _STAT_PAD))
    QtBind.setText(gui, lblStatRuns, '🏁 Runs: %d%s' % (stats_runs, _STAT_PAD))
    QtBind.setText(gui, lblStatAvgRun, '⌛ Avg: %s%s' % (_format_hms(avg_ms), _STAT_PAD))
    QtBind.setText(gui, lblStatBestRun, '⭐ Best: %s%s' % (_format_hms(best_ms) if best_ms else '--', _STAT_PAD))
    QtBind.setText(gui, lblStatStones, '💎 Stones: %d (%s/h)%s' % (stones_total, rate_tag(stones_h), _STAT_PAD))
    QtBind.setText(gui, lblStatArena, '🪙 Arena: %d (%s/h)%s' % (arena_total, rate_tag(arena_h), _STAT_PAD))
    QtBind.setText(gui, lblStatGold, '💰 Gold: %s (%s/h)%s' % (_compact_num(gold_total), rate_tag_g(gold_h), _STAT_PAD))
    QtBind.setText(gui, lblStatUptime, '⏲ Up: %s%s' % (_format_hms(uptime_ms), _STAT_PAD))


def btn_reset_stats_clicked():
    global stats_started_at, stats_runs, stats_baseline_gold
    global stats_baseline_stones, stats_baseline_arena, stats_current_run_started_at
    global stats_total_boxes_returned, stats_known_fill_ms, stats_last_empty_at, stats_last_seen_count
    stats_started_at = _now()
    stats_runs = 0
    del stats_run_durations_ms[:]
    stats_baseline_gold = _current_gold()
    stats_baseline_stones = _count_items_matching(STONE_FILTERS)
    stats_baseline_arena = _count_items_matching(ARENA_FILTERS)
    stats_current_run_started_at = 0
    stats_total_boxes_returned = 0
    stats_known_fill_ms = 0
    stats_last_empty_at = _now()
    stats_last_seen_count = -1
    _stats_update_ui(_now())
    log('[%s] Stats reset.' % pName)


def _sort_inventory():
    try:
        ok = sort_inventory()
        log('[%s] sort_inventory() -> %s' % (pName, ok))
        return bool(ok)
    except Exception as ex:
        log('[%s] sort_inventory() failed: %s' % (pName, ex))
        return False


def _safe_int(value, default_value, minimum_value):
    try:
        return max(minimum_value, int(str(value).strip()))
    except Exception:
        return default_value


def _config_path():
    try:
        char = get_character_data()
        char_name = char.get('name', 'default') if char else 'default'
    except Exception:
        char_name = 'default'
    return os.path.join(get_config_dir(), '%s_%s.json' % (pName, char_name))


def _character_name():
    try:
        char = get_character_data()
        return char.get('name', 'default') if char else 'default'
    except Exception:
        return 'default'


def _read_gui():
    config['enabled'] = QtBind.isChecked(gui, chkEnabled)
    config['start_bot_after'] = QtBind.isChecked(gui, chkStartBotAfter)
    config['unequip_after'] = QtBind.isChecked(gui, chkUnequipAfter)
    config['reverse_after'] = QtBind.isChecked(gui, chkReverseAfter)
    if QtBind.isChecked(gui, chkRouteTrader):
        config['route_mode'] = 'Trader'
    elif QtBind.isChecked(gui, chkRouteHunter):
        config['route_mode'] = 'Hunter'
    else:
        config['route_mode'] = 'Thief'
    config['box_name'] = QtBind.text(gui, txtBoxName).strip() or DEFAULT_BOX_NAME
    config['box_limit'] = _safe_int(QtBind.text(gui, txtBoxLimit), 1, 1)
    config['scan_ms'] = _safe_int(QtBind.text(gui, txtScanMs), 30000, 1000)
    config['suit_filter'] = QtBind.text(gui, txtSuitFilter).strip() or 'Trader'
    config['final_box_min'] = _safe_int(QtBind.text(gui, txtFinalBoxMin), 20, 1)
    config['final_teleports'] = _safe_int(QtBind.text(gui, txtFinalTeleports), 3, 1)
    config['action_ms'] = _safe_int(QtBind.text(gui, txtActionMs), 3500, 500)


def _write_gui():
    QtBind.setChecked(gui, chkEnabled, bool(config.get('enabled', False)))
    QtBind.setChecked(gui, chkStartBotAfter, bool(config.get('start_bot_after', True)))
    QtBind.setChecked(gui, chkUnequipAfter, bool(config.get('unequip_after', True)))
    QtBind.setChecked(gui, chkReverseAfter, bool(config.get('reverse_after', False)))
    mode = config.get('route_mode', 'Thief')
    QtBind.setChecked(gui, chkRouteThief, mode == 'Thief')
    QtBind.setChecked(gui, chkRouteHunter, mode == 'Hunter')
    QtBind.setChecked(gui, chkRouteTrader, mode == 'Trader')
    QtBind.setText(gui, txtBoxName, str(config.get('box_name', DEFAULT_BOX_NAME)))
    QtBind.setText(gui, txtBoxLimit, str(config.get('box_limit', 1)))
    QtBind.setText(gui, txtScanMs, str(config.get('scan_ms', 30000)))
    QtBind.setText(gui, txtSuitFilter, str(config.get('suit_filter', 'Trader')))
    QtBind.setText(gui, txtFinalBoxMin, str(config.get('final_box_min', 20)))
    QtBind.setText(gui, txtFinalTeleports, str(config.get('final_teleports', 3)))
    QtBind.setText(gui, txtActionMs, str(config.get('action_ms', 3500)))


def _load_config():
    global config
    global loaded_char_name

    config.clear()
    config.update(DEFAULT_CONFIG)
    loaded_char_name = _character_name()
    path = _config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                config.update(json.load(f))
        except Exception as ex:
            _error('Could not read config: %s' % ex)
    if _normalize(config.get('box_name')) == 'special box':
        config['box_name'] = DEFAULT_BOX_NAME
    if config.get('scan_ms') in (15000, 30000, 60000):
        config['scan_ms'] = 5000
    if config.get('final_box_min') == 50:
        config['final_box_min'] = 20
    _write_gui()
    _set_status('monitoring' if config.get('enabled', False) else 'disabled')


def _save_config():
    _read_gui()
    try:
        with open(_config_path(), 'w') as f:
            f.write(json.dumps(config, indent=4, sort_keys=True))
        _log('Config saved.', True)
    except Exception as ex:
        _error('Could not save config: %s' % ex)


def _item_quantity(item):
    if not isinstance(item, dict):
        return 1
    for key in ('quantity', 'qty', 'count', 'stack'):
        try:
            if key in item:
                return int(item.get(key) or 0)
        except Exception:
            pass
    return 1


def _item_text(item):
    parts = [item.get('name', ''), item.get('servername', '')]
    try:
        item_data = get_item(item.get('model'))
        if item_data:
            parts.append(item_data.get('name', ''))
            parts.append(item_data.get('servername', ''))
    except Exception:
        pass
    return _normalize(' '.join([str(part or '') for part in parts]))


def _container_items(container):
    if not container:
        return []
    if isinstance(container, dict):
        if 'items' in container:
            return container.get('items') or []
        for key in ('job_pouch', 'job_inventory', 'pouch', 'goods', 'slots'):
            if key in container:
                value = container.get(key)
                if isinstance(value, dict) and 'items' in value:
                    return value.get('items') or []
                if isinstance(value, list):
                    return value
    if isinstance(container, list):
        return container
    return []


def _box_count(debug=False):
    box_filter = _normalize(config.get('box_name', DEFAULT_BOX_NAME))
    box_filters = [box_filter]
    for alias in BOX_NAME_ALIASES.get(box_filter, ()):
        normalized_alias = _normalize(alias)
        if normalized_alias and normalized_alias not in box_filters:
            box_filters.append(normalized_alias)
    total = 0
    sources = []
    probe_report = []  # diagnostic: what each API returned this call

    for func_name in ('get_job_pouch', 'get_job_pouch_data', 'get_job_inventory', 'get_job_data'):
        func = globals().get(func_name)
        if not func:
            if debug:
                probe_report.append('%s=missing' % func_name)
            continue
        try:
            raw = func()
            items = _container_items(raw)
            if debug:
                probe_report.append('%s=%d items' % (func_name, len(items)))
            if items:
                sources.append((func_name, items))
        except Exception as ex:
            if debug:
                probe_report.append('%s=err:%s' % (func_name, ex))

    # Query BOTH inventory APIs and keep whichever has more matching boxes —
    # get_inventory() can return a stale snapshot while phBot is auto-paused
    # on a full pouch, so it may report fewer sacks than get_inventory_data().
    # Previously this loop broke on the first non-empty source and missed the
    # truer count.
    inv_candidates = []
    # Scan grab-pet inventories too — for AFK botting, mob-drop trader sacks
    # accumulate in the grab pet, not the character inventory. phBot's pet
    # inventory shows the same "121/120" counter the user sees in-game.
    pets_fn = globals().get('get_pets')
    pet_inv_fn = globals().get('get_pet_inventory')
    if callable(pets_fn) and callable(pet_inv_fn):
        try:
            pets = pets_fn() or {}
        except Exception:
            pets = {}
        for uid, pet in (pets.items() if isinstance(pets, dict) else []):
            try:
                pet_inv = pet_inv_fn(uid)
            except Exception:
                pet_inv = None
            items = _container_items(pet_inv) if pet_inv else []
            if debug:
                pet_label = 'pet#%s' % uid
                if isinstance(pet, dict):
                    pet_label = pet.get('name') or pet.get('type') or pet_label
                probe_report.append('pet_inv(%s)=%d items' % (pet_label, len(items)))
            if items:
                sources.append(('get_pet_inventory(%s)' % uid, items))

    for func_name in ('get_inventory', 'get_inventory_data'):
        func = globals().get(func_name)
        if not func:
            if debug:
                probe_report.append('%s=missing' % func_name)
            continue
        try:
            raw = func()
            items = _container_items(raw)
            if debug:
                gold = raw.get('gold') if isinstance(raw, dict) else None
                probe_report.append('%s=%d items%s' % (
                    func_name, len(items),
                    (' gold=%s' % gold) if gold is not None else ''
                ))
            if items:
                inv_candidates.append((func_name, items))
        except Exception as ex:
            if debug:
                probe_report.append('%s=err:%s' % (func_name, ex))

    best_inv = None
    best_inv_count = -1
    for func_name, items in inv_candidates:
        c = 0
        for it in items:
            if not it:
                continue
            if any(cand in _item_text(it) for cand in box_filters):
                c += _item_quantity(it)
        if c > best_inv_count:
            best_inv_count = c
            best_inv = (func_name, items)
    if best_inv is not None:
        sources.append(best_inv)

    names = []
    seen_names = []
    for source_name, items in sources:
        for item in items:
            if not item:
                continue
            item_text = _item_text(item)
            if debug and item_text:
                seen_names.append('%s:%s' % (source_name, item_text))
            if any(candidate in item_text for candidate in box_filters):
                qty = _item_quantity(item)
                total += qty
                names.append('%s:%s' % (source_name, qty))

    if debug and total == 0 and seen_names:
        # Only complain when inventory was actually read but the box wasn't
        # there — a genuinely empty read means phBot hasn't loaded the
        # inventory yet (common right after login), which is noise, not a bug.
        log('[%s] Box not found. Filter: %s | APIs: %s | Items seen: %s' % (
            pName,
            ', '.join(box_filters),
            ', '.join(probe_report) if probe_report else 'none probed',
            ' | '.join(seen_names[:12])
        ))

    if debug:
        jp_filled, jp_capacity, jp_goods, jp_goods_cap, _ = _job_pouch_state()
        log('[%s] Scan: %d goods in %d/%d stacks (cap %d).' % (
            pName, jp_goods, jp_filled, jp_capacity, jp_goods_cap))

    limit = config.get('box_limit', 1)
    pet_used, pet_total, pet_empty = _grab_pet_fullness()
    pet_label = ('  ·  🐴 %d/%d' % (pet_used, pet_total)) if pet_total > 0 else ''
    jp_filled, jp_capacity, jp_goods, jp_goods_cap, _jp_smax = _job_pouch_state()
    jp_full = (jp_goods_cap > 0 and jp_goods >= jp_goods_cap)
    pet_full_ui = (pet_total > 0 and pet_empty == 0)
    glyph = '🟢' if (jp_full or pet_full_ui) else ('🟡' if (jp_goods > 0) else '⚪')
    if jp_goods_cap > 0:
        pouch_text = '🎒 %d/%d (%d/%d stacks)' % (jp_goods, jp_goods_cap, jp_filled, jp_capacity)
    else:
        pouch_text = '🎒 pouch unavailable'
    QtBind.setText(gui, lblBox, '%s %s%s%s' % (
        glyph,
        pouch_text,
        pet_label,
        _PAD,
    ))
    _stats_sample_fill(_now(), total)
    return total


def _inventory_items():
    inv = _snapshot_inventory()
    if inv and 'items' in inv:
        return inv['items']
    return []


def _empty_slot():
    items = _inventory_items()
    for slot, item in enumerate(items):
        if slot >= 13 and not item:
            return slot
    return -1


def _empty_regular_slot_count():
    # Counts empty slots in the regular inventory area (slot 13 and above).
    # When this is 0 the inventory is physically full, regardless of whether
    # the name filter caught every item — that's the real "pouch full" signal.
    items = _inventory_items()
    if not items:
        return -1
    empty = 0
    for slot, item in enumerate(items):
        if slot >= 13 and not item:
            empty += 1
    return empty


_pouch_high_water = {'filled': 0, 'goods': 0, 'capacity': 0, 'goods_cap': 0}


_SPECIALTY_STACK_MAX = 5  # specialty goods stack at 5 per slot (server-fixed)


def _job_pouch_state():
    # Reads the in-game job pouch and returns
    # (filled_stacks, capacity, goods_count, goods_cap, stack_max).
    fn = globals().get('get_job_pouch')
    if not callable(fn):
        return (-1, -1, -1, -1, -1)
    try:
        jp = fn()
    except Exception:
        return (-1, -1, -1, -1, -1)
    if not isinstance(jp, dict):
        return (-1, -1, -1, -1, -1)

    capacity = jp.get('size')
    capacity = int(capacity) if isinstance(capacity, (int, float)) else -1
    items = jp.get('items') or []

    filled = 0
    goods = 0
    for it in items:
        if not it:
            continue
        qty = _item_quantity(it)
        if qty <= 0:
            continue
        filled += 1
        goods += qty

    if capacity <= 0:
        capacity = len(items) if items else -1

    stack_max = _SPECIALTY_STACK_MAX
    goods_cap = capacity * stack_max if capacity > 0 else -1
    return (filled, capacity, goods, goods_cap, stack_max)


def _pouch_reset_after_trade():
    _pouch_high_water['filled'] = 0
    _pouch_high_water['goods'] = 0


def handle_joymax(opcode, data):
    # Real-time pouch refresh. Any packet related to specialty goods /
    # inventory updates invalidates our cached high-water-mark check and pokes
    # the event loop to re-read on the next tick. We don't try to identify
    # specific opcodes — every Joymax frame is cheap to handle and pouches
    # rarely change outside of looting, so re-reading is safe.
    # Poke phBot to refresh its pouch cache. The actual UI redraw happens in
    # event_loop on the main thread (Qt isn't safe to touch from this thread).
    try:
        fn = globals().get('get_job_pouch')
        if callable(fn):
            jp = fn()
            if isinstance(jp, dict):
                items = jp.get('items') or []
                goods = 0
                for it in items:
                    if isinstance(it, dict):
                        goods += _item_quantity(it)
                hw = _pouch_high_water
                if goods > hw['goods']:
                    hw['goods'] = goods
    except BaseException:
        pass
    return True


def _grab_pet_fullness():
    # Returns (used, total, empty) across all grab-pet inventories. While AFK
    # botting, mob drops accumulate in the grab pet, and when it fills phBot
    # stops looting — this is the "121/120" pouch counter visible in-game.
    pets_fn = globals().get('get_pets')
    pet_inv_fn = globals().get('get_pet_inventory')
    if not (callable(pets_fn) and callable(pet_inv_fn)):
        return (-1, -1, -1)
    try:
        pets = pets_fn() or {}
    except Exception:
        return (-1, -1, -1)
    used = 0
    total = 0
    for uid in (pets.keys() if isinstance(pets, dict) else []):
        try:
            inv = pet_inv_fn(uid)
        except Exception:
            inv = None
        if not isinstance(inv, dict):
            continue
        items = inv.get('items') or []
        for it in items:
            total += 1
            if it:
                used += 1
    if total <= 0:
        return (-1, -1, -1)
    return (used, total, total - used)


def _job_slot_item():
    items = _inventory_items()
    if len(items) > 8:
        return items[8]
    return None


def _is_near_jangan():
    try:
        pos = get_position()
    except Exception:
        return False
    if not pos:
        return False
    try:
        x = float(pos.get('x', 0))
        y = float(pos.get('y', 0))
    except Exception:
        return False
    return 6200 <= x <= 6600 and 900 <= y <= 1250


def _find_suit_slot():
    suit_filter = _normalize(config.get('suit_filter', 'Trader'))
    items = _inventory_items()
    for slot, item in enumerate(items):
        if slot < 13 or not item:
            continue
        if suit_filter and suit_filter not in _item_text(item):
            continue
        try:
            item_data = get_item(item.get('model'))
            if item_data and item_data.get('tid2') != 7:
                continue
        except Exception:
            pass
        return slot, item
    return -1, None


def _move_item(source_slot, target_slot, name):
    packet = struct.pack('<BBBH', 0, int(source_slot), int(target_slot), 0)
    inject_joymax(0x7034, packet, False)
    _log('Item moved: %s slot %s -> %s' % (name, source_slot, target_slot), True)


def _equip_suit():
    current = _job_slot_item()
    if current:
        _set_suit('Suit: already worn (%s)' % current.get('name', 'slot 8'))
        return 'already'

    slot, item = _find_suit_slot()
    if slot < 0 or not item:
        _set_suit('Suit: not found')
        _log('Job suit not found. Filter: %s' % config.get('suit_filter', 'Trader'), True)
        return False

    _move_item(slot, 8, item.get('name', 'job suit'))
    _set_suit('Suit: equipping (%s)' % item.get('name', 'job suit'))
    return 'equipped'


def _unequip_suit():
    item = _job_slot_item()
    if not item:
        _set_suit('Suit: not worn')
        return True

    slot = _empty_slot()
    if slot < 0:
        _log('No empty inventory slot to unequip suit.', True)
        _set_suit('Suit: no empty slot')
        return False

    _move_item(8, slot, item.get('name', 'job suit'))
    _set_suit('Suit: unequipping')
    return True


def _stop_all():
    try:
        stop_bot()
    except Exception:
        pass
    try:
        stop_trade()
    except Exception:
        pass
    try:
        stop_script()
    except Exception:
        pass


def _set_state(new_state):
    global state, action_at
    state = new_state
    action_at = _now()
    _set_status(new_state)


def _route_script():
    mode = config.get('route_mode', 'Thief')
    if mode == 'Hunter':
        script = HUNTER_ROUTE_SCRIPT.strip()
        if not script:
            _error('Hunter script is not loaded yet.')
            _set_status('no hunter script')
            return ''
        script = script + '\n'
    elif mode == 'Trader':
        script = TRADER_ROUTE_SCRIPT.strip()
        if not script:
            _error('Trader script is not loaded yet.')
            _set_status('no trader script')
            return ''
        script = script + '\n'
    else:
        script = ROUTE_SCRIPT
    if config.get('reverse_after', False):
        script = script.replace('use,returnscroll\n', '').replace('use,returnscroll', '')
    return script


def _fallback_return_to_training():
    _log('Falling back to normal return scroll so bot can resume training.', True)
    try:
        start_script('use,returnscroll\n')
        return True
    except Exception as ex:
        _log('Fallback start_script failed: %s' % ex, True)
    try:
        use_return_scroll()
        return True
    except Exception as ex:
        _log('Fallback use_return_scroll failed: %s' % ex, True)
    try:
        start_bot()
        _log('Last-resort fallback: starting bot in place so attacking can engage.', True)
    except Exception as ex:
        _log('Last-resort start_bot failed: %s' % ex, True)
    return False


def _fire_reverse_return():
    global reverse_pending, reverse_last_stop_at
    reverse_pending = False
    reverse_last_stop_at = 0
    # Stop the caravan script and any trading before teleporting — otherwise the
    # leftover script keeps issuing walk commands and fights start_bot at the recall point.
    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_trade()
    except Exception:
        pass
    _sort_inventory()
    _log('Inventory sorted: holding %d ms before reverse return.' % REVERSE_SORT_SETTLE_MS, True)
    _set_state('awaiting_sort_settle')
    return True


def _execute_reverse_return():
    try:
        ok = reverse_return(0, '')
    except Exception as ex:
        _log('Reverse return scroll failed: %s' % ex, True)
        ok = False
    if ok:
        _log('Reverse return scroll used: waiting for teleport to land.', True)
        _set_state('awaiting_reverse_teleport')
        return True
    _log('Reverse return scroll could not be used; falling back.', True)
    _fallback_return_to_training()
    _set_state('reverse_completed')
    return False


def _reverse_return_tick(now):
    global reverse_last_pos, reverse_stationary_since
    if now - reverse_started_at < REVERSE_MIN_RUN_MS:
        return
    if now - reverse_started_at >= REVERSE_HARD_TIMEOUT_MS:
        _log('Reverse return hard timeout reached; firing fallback now.', True)
        _fire_reverse_return()
        return
    # Wait until terminate,transport has actually killed the vehicle —
    # firing reverse mid-settle conflicts with the script and start_bot
    # would later attack the still-alive transport.
    if _trader_transport_ready():
        reverse_last_pos = None
        reverse_stationary_since = now
        _set_status('waiting for transport to be terminated')
        return
    try:
        pos = get_position()
    except Exception:
        return
    if not pos:
        return
    try:
        x = float(pos.get('x', 0))
        y = float(pos.get('y', 0))
    except Exception:
        return
    if reverse_last_pos is None:
        reverse_last_pos = (x, y)
        reverse_stationary_since = now
        return
    lx, ly = reverse_last_pos
    if abs(x - lx) > REVERSE_POS_TOLERANCE or abs(y - ly) > REVERSE_POS_TOLERANCE:
        reverse_last_pos = (x, y)
        reverse_stationary_since = now
        return
    if now - reverse_stationary_since >= REVERSE_STATIONARY_MS:
        _fire_reverse_return()


def _do_return_scroll():
    global return_last_try_at, return_attempts
    return_last_try_at = _now()
    return_attempts += 1
    ok = False
    try:
        start_script('use,returnscroll\n')
        ok = True
    except Exception as ex:
        _log('Return script failed: %s' % ex, True)
    if not ok:
        try:
            use_return_scroll()
            ok = True
        except Exception as ex:
            _log('Return scroll API failed: %s' % ex, True)
    _log('Return scroll attempt %d/%d issued.' % (return_attempts, RETURN_MAX_ATTEMPTS), True)
    return ok


def _trigger_return_for_route():
    global last_box_count, return_attempts, return_last_try_at
    global stats_current_run_started_at
    _read_gui()
    _stop_all()
    last_box_count = _box_count()
    _log('Limit reached: %d. Returning to town.' % last_box_count, True)
    _set_state('returning_to_town')
    return_attempts = 0
    return_last_try_at = 0
    stats_current_run_started_at = _now()
    _stats_init_baseline()
    _do_return_scroll()


def _start_route():
    global route_teleports
    global route_start_wait_ms
    _read_gui()
    route_teleports = 0
    _trader_packet_reset()
    equip_result = _equip_suit()
    if not equip_result:
        _set_state('idle')
        return
    _stop_all()
    route_start_wait_ms = config.get('equip_wait_ms', 20000) if equip_result == 'equipped' else config.get('action_ms', 3500)
    _set_state('starting_route')
    if equip_result == 'equipped':
        _log('Job suit just equipped. Waiting 20 seconds before script starts.', True)


def _trader_inject(opcode, hex_data, label):
    try:
        inject_joymax(opcode, bytearray.fromhex(hex_data), False)
        _log('Trader packet sent: %s' % label, True)
    except Exception as ex:
        _error('Trader packet failed (%s): %s' % (label, ex))


def _trader_near(target_x, target_y, radius):
    try:
        pos = get_position()
    except Exception:
        return False
    if not pos:
        return False
    try:
        x = float(pos.get('x', 0))
        y = float(pos.get('y', 0))
    except Exception:
        return False
    dx = x - target_x
    dy = y - target_y
    return (dx * dx + dy * dy) <= (radius * radius)


def _trader_transport_ready():
    try:
        pets = get_pets()
    except Exception:
        return False
    if not pets:
        return False
    keywords = ('transport', 'caravan', 'trade', 'camel', 'horse', 'bull', 'ox', 'yak',
                'behemoth', 'lizard', 'elephant', 'job')
    excludes = ('fellow', 'grab', 'pick')
    for uid, pet in pets.items():
        try:
            blob = ' '.join(str(pet.get(k, '')) for k in ('type', 'name', 'model', 'servername')).lower()
        except Exception:
            continue
        if any(x in blob for x in excludes):
            continue
        if any(k in blob for k in keywords):
            return True
    return False


def _trader_packet_reset():
    global trader_pkt_start_stage, trader_pkt_settle_stage
    global trader_pkt_stage_at, trader_pkt_settle_arrived_at
    global trader_pkt_start_done_visit, trader_pkt_settle_done_visit
    global trader_pkt_last_start_at, trader_pkt_last_settle_at
    trader_pkt_start_stage = 0
    trader_pkt_settle_stage = 0
    trader_pkt_stage_at = 0
    trader_pkt_settle_arrived_at = 0
    trader_pkt_start_done_visit = False
    trader_pkt_settle_done_visit = False
    trader_pkt_last_start_at = 0
    trader_pkt_last_settle_at = 0


def _trader_packet_tick(now):
    global trader_pkt_start_stage, trader_pkt_settle_stage
    global trader_pkt_stage_at, trader_pkt_settle_arrived_at
    global trader_pkt_start_done_visit, trader_pkt_settle_done_visit
    global trader_pkt_last_start_at, trader_pkt_last_settle_at
    global trade_lockdown_until

    if config.get('route_mode', 'Thief') != 'Trader':
        return
    if state != 'route_running':
        return

    near_start = _trader_near(TRADER_START_X, TRADER_START_Y, TRADER_START_RADIUS)
    near_settle = _trader_near(TRADER_SETTLE_X, TRADER_SETTLE_Y, TRADER_SETTLE_RADIUS)

    if not near_start:
        trader_pkt_start_done_visit = False
    if not near_settle:
        trader_pkt_settle_done_visit = False
        trader_pkt_settle_arrived_at = 0

    if (near_start and not trader_pkt_start_done_visit
            and now - trader_pkt_last_start_at > TRADER_PACKET_COOLDOWN_MS
            and trader_pkt_start_stage == 0):
        if not _trader_transport_ready():
            _set_status('waiting for Caravan Bugle')
        else:
            trader_pkt_start_done_visit = True
            trader_pkt_last_start_at = now
            trader_pkt_start_stage = 1
            trader_pkt_stage_at = now
            trade_lockdown_until = now + TRADER_LOCKDOWN_MS
            _log('Trader: transport summoned, talking to start NPC. Lockdown ON.', True)

    if trader_pkt_start_stage == 1 and now - trader_pkt_stage_at >= TRADER_PACKET_DELAY_AFTER_READY:
        _trader_inject(TRADER_PACKET_START_TALK[0], TRADER_PACKET_START_TALK[1], 'start talk')
        trader_pkt_start_stage = 2
        trader_pkt_stage_at = now
    elif trader_pkt_start_stage == 2 and now - trader_pkt_stage_at >= TRADER_PACKET_DELAY_BETWEEN:
        _trader_inject(TRADER_PACKET_START_BEGIN[0], TRADER_PACKET_START_BEGIN[1], 'start begin')
        trader_pkt_start_stage = 0

    if near_settle and not trader_pkt_settle_done_visit and trader_pkt_settle_stage == 0:
        if not _trader_transport_ready():
            _set_status('waiting for transport at settle')
        else:
            if trader_pkt_settle_arrived_at == 0:
                trader_pkt_settle_arrived_at = now
                _log('Trader: at settle NPC, holding before settle.', True)
            elif (now - trader_pkt_settle_arrived_at >= TRADER_PACKET_SETTLE_HOLD_MS
                  and now - trader_pkt_last_settle_at > TRADER_PACKET_COOLDOWN_MS):
                trader_pkt_settle_done_visit = True
                trader_pkt_last_settle_at = now
                trader_pkt_settle_stage = 1
                trader_pkt_stage_at = now

    if trader_pkt_settle_stage == 1 and now - trader_pkt_stage_at >= TRADER_PACKET_DELAY_AFTER_READY:
        _trader_inject(TRADER_PACKET_SETTLE_TALK[0], TRADER_PACKET_SETTLE_TALK[1], 'settle talk')
        trader_pkt_settle_stage = 2
        trader_pkt_stage_at = now
        trade_lockdown_until = now + TRADER_LOCKDOWN_MS
    elif trader_pkt_settle_stage == 2 and now - trader_pkt_stage_at >= TRADER_PACKET_DELAY_BETWEEN:
        _trader_inject(TRADER_PACKET_SETTLE_CONFIRM[0], TRADER_PACKET_SETTLE_CONFIRM[1], 'settle confirm')
        trader_pkt_settle_stage = 3
        trader_pkt_stage_at = now
        trade_lockdown_until = now + TRADER_LOCKDOWN_MS
    elif trader_pkt_settle_stage == 3 and now - trader_pkt_stage_at >= TRADER_PACKET_DELAY_CLOSE:
        _trader_inject(TRADER_PACKET_SETTLE_CLOSE[0], TRADER_PACKET_SETTLE_CLOSE[1], 'settle close')
        trader_pkt_settle_stage = 0
        trade_lockdown_until = 0
        _log('Trader: settle close fired. Lockdown OFF.', True)


def _run_route_script():
    global route_teleports, route_start_wait_ms
    global reverse_pending, reverse_last_pos, reverse_stationary_since, reverse_started_at
    route_teleports = 0
    reverse_pending = False
    reverse_last_pos = None
    reverse_stationary_since = 0
    reverse_started_at = 0
    if not _job_slot_item():
        _log('Job suit not detected before script start; re-equipping.', True)
        if _equip_suit():
            route_start_wait_ms = config.get('equip_wait_ms', 20000)
            _set_state('starting_route')
            return
        _error('Job suit could not be equipped; aborting route.')
        _set_state('idle')
        return
    try:
        script = _route_script()
        if not script:
            _set_state('idle')
            return
        start_script(script)
        _set_state('route_running')
        _log('Caravan script started.', True)
        if config.get('reverse_after', False):
            reverse_pending = True
            reverse_last_pos = None
            reverse_stationary_since = 0
            reverse_started_at = _now()
            _log('Reverse return armed: will trigger after script ends.', True)
    except Exception as ex:
        _error('Caravan script could not start: %s' % ex)
        _set_state('idle')


def _finish_route():
    _stats_record_run_complete()
    _pouch_reset_after_trade()
    count = _box_count()
    if config.get('reverse_after', False):
        # Reverse return was already issued by _fire_reverse_return after the
        # transport was killed; just resume the bot in place once teleport landed.
        _log('Reverse return: %d boxes left. Resuming bot at recall point.' % count, True)
        _resume_bot_after_reverse()
        return
    if not config.get('unequip_after', True):
        _log('Jangan check: %d boxes left. Keeping suit on (Unequip when done disabled).' % count, True)
        _finish_after_suit()
        return
    _log('Jangan check: %d boxes left. Suit will be unequipped and bot started after 20 seconds.' % count, True)
    if not _unequip_suit():
        return
    _set_state('finishing')


def _recover_if_dead_returned_to_jangan():
    # Thief/Hunter walk through Jangan legitimately and also pass back through it
    # after the return-leg ferry teleports. The recovery guard was firing on those
    # passes and aborting the route with a return scroll. Restrict to Trader only.
    if config.get('route_mode', 'Thief') != 'Trader':
        return False
    count = _box_count()
    if count >= config.get('final_box_min', 20):
        return False
    if not _job_slot_item():
        return False
    if not _is_near_jangan():
        return False

    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_trade()
    except Exception:
        pass
    _finish_route()
    return True


def _finish_after_suit():
    if config.get('start_bot_after', True):
        try:
            start_bot()
            _log('Bot started.', True)
        except Exception as ex:
            _log('Bot could not start: %s' % ex, True)
    _set_state('idle')


def _resume_bot_after_reverse():
    # Belt-and-suspenders: make sure no caravan script/trade state is left running
    # before the bot takes over at the recall point.
    try:
        stop_script()
    except Exception:
        pass
    try:
        stop_trade()
    except Exception:
        pass
    if config.get('start_bot_after', True):
        try:
            start_bot()
            _log('Bot started at recall point after reverse return.', True)
        except Exception as ex:
            _log('Bot could not start: %s' % ex, True)
    _set_state('idle')


def btn_save_clicked():
    _save_config()


def _sync_scan(debug=True):
    _read_gui()
    count = _box_count(debug)
    if _job_slot_item():
        _set_suit('Suit: worn (%s)' % _job_slot_item().get('name', 'slot 8'))
    else:
        slot, item = _find_suit_slot()
        _set_suit('Suit: slot %s %s' % (slot, item.get('name', 'found')) if item else 'Suit: not found')
    return count


def btn_scan_clicked():
    _sync_scan(True)


def btn_start_clicked():
    _read_gui()
    config['enabled'] = True
    QtBind.setChecked(gui, chkEnabled, True)
    _save_config()
    _set_status('monitoring')


def btn_stop_clicked():
    global state, action_at, route_teleports
    config['enabled'] = False
    QtBind.setChecked(gui, chkEnabled, False)
    _save_config()
    _stop_all()
    _trader_packet_reset()
    state = 'idle'
    action_at = _now()
    route_teleports = 0
    _set_status('stopped')


def btn_run_route_clicked():
    _start_route()


def btn_reverse_now_clicked():
    _log('Manual reverse: stopping bot and using reverse return scroll.', True)
    _stop_all()
    try:
        if reverse_return(0, ''):
            _log('Reverse return scroll used. Bot will resume at recall point.', True)
            try:
                start_bot()
                _log('Bot started (will engage after teleport completes).', True)
            except Exception as ex:
                _log('start_bot failed: %s' % ex, True)
            return
        _log('Reverse return scroll could not be used (no scroll or no recall point).', True)
    except Exception as ex:
        _log('Reverse return scroll failed: %s' % ex, True)


def cbx_enabled_clicked(checked=None):
    config['enabled'] = QtBind.isChecked(gui, chkEnabled)
    _save_config()


def cbx_start_bot_after_clicked(checked=None):
    config['start_bot_after'] = QtBind.isChecked(gui, chkStartBotAfter)
    _save_config()


def cbx_unequip_after_clicked(checked=None):
    config['unequip_after'] = QtBind.isChecked(gui, chkUnequipAfter)
    _save_config()


def cbx_reverse_after_clicked(checked=None):
    config['reverse_after'] = QtBind.isChecked(gui, chkReverseAfter)
    _save_config()


def _select_route_mode(mode):
    QtBind.setChecked(gui, chkRouteThief, mode == 'Thief')
    QtBind.setChecked(gui, chkRouteHunter, mode == 'Hunter')
    QtBind.setChecked(gui, chkRouteTrader, mode == 'Trader')
    config['route_mode'] = mode
    _save_config()


def cbx_route_thief_clicked(checked=None):
    if QtBind.isChecked(gui, chkRouteThief):
        _select_route_mode('Thief')
    elif not (QtBind.isChecked(gui, chkRouteHunter) or QtBind.isChecked(gui, chkRouteTrader)):
        _select_route_mode('Thief')


def cbx_route_hunter_clicked(checked=None):
    if QtBind.isChecked(gui, chkRouteHunter):
        _select_route_mode('Hunter')
    elif not (QtBind.isChecked(gui, chkRouteThief) or QtBind.isChecked(gui, chkRouteTrader)):
        _select_route_mode('Hunter')


def cbx_route_trader_clicked(checked=None):
    if QtBind.isChecked(gui, chkRouteTrader):
        _select_route_mode('Trader')
    elif not (QtBind.isChecked(gui, chkRouteThief) or QtBind.isChecked(gui, chkRouteHunter)):
        _select_route_mode('Trader')


def joined_game():
    global state
    global last_scan_at
    global route_teleports

    _load_config()
    state = 'idle'
    last_scan_at = 0
    route_teleports = 0
    if not config.get('enabled', False):
        return
    _set_status('active: %s' % loaded_char_name)
    try:
        last_scan_at = _now()
        count = _box_count(True)
        _log('Join scan: %d boxes (limit %d).' % (count, config.get('box_limit', 1)), True)
        if count >= config.get('box_limit', 1):
            _trigger_return_for_route()
    except Exception as ex:
        _log('Join scan failed: %s' % ex, True)


def disconnected():
    global state
    global last_scan_at
    global route_teleports
    global bot_ever_seen_running

    state = 'idle'
    last_scan_at = 0
    route_teleports = 0
    bot_ever_seen_running = False


def teleported():
    global route_teleports
    if _trade_locked(_now()) and config.get('route_mode') == 'Trader':
        _log('[lockdown] teleport ignored', True)
        return
    if state == 'returning_to_town':
        _set_state('town_returned')
    elif state == 'awaiting_reverse_teleport':
        _log('Reverse return teleport landed.', True)
        # phBot auto-resumes the loaded script after teleport — kill it now,
        # before it walks the character out of the recall point.
        try:
            stop_script()
        except Exception:
            pass
        try:
            stop_trade()
        except Exception:
            pass
        _set_state('reverse_completed')
    elif state == 'route_running':
        if reverse_pending:
            _log('Gate teleport during route ignored (waiting for reverse return).', True)
            return
        route_teleports += 1
        _log('Route teleport count: %d/%d' % (route_teleports, config.get('final_teleports', 3)), True)
        if route_teleports >= config.get('final_teleports', 3):
            _set_state('route_returned')


def event_loop():
    global last_scan_at
    global last_town_guard_at
    global reverse_last_stop_at
    global empty_inventory_scans
    global trade_lockdown_until
    current_char = _character_name()
    if current_char != loaded_char_name:
        gui_enabled_pre = QtBind.isChecked(gui, chkEnabled)
        _load_config()
        if QtBind.isChecked(gui, chkEnabled) != gui_enabled_pre:
            QtBind.setChecked(gui, chkEnabled, gui_enabled_pre)
            config['enabled'] = gui_enabled_pre

    _read_gui()
    now = _now()

    global stats_started_at
    if stats_started_at == 0:
        stats_started_at = now
    _stats_update_ui(now)

    if not config.get('enabled', False):
        return

    if _trade_locked(now) and config.get('route_mode') == 'Trader':
        _trader_packet_tick(now)
        last_town_guard_at = now
        _set_status('trade lockdown %ds' % max(0, (trade_lockdown_until - now) // 1000))
        return
    if trade_lockdown_until and now >= trade_lockdown_until:
        trade_lockdown_until = 0

    if state not in ROUTE_ACTIVE_STATES:
        # Cheap label refresh on every tick so the pouch counter reflects
        # looted goods in real time, not on the 30s scan cadence.
        _box_count(False)
        scan_ms = config.get('scan_ms', 30000)
        if now - last_scan_at >= scan_ms or last_scan_at == 0:
            last_scan_at = now
            count = _sync_scan(False)
            limit = config.get('box_limit', 1)
            inv_items = _inventory_items()
            if not inv_items:
                empty_inventory_scans += 1
                if empty_inventory_scans >= 2:
                    last_scan_at = now - scan_ms + 3000
            else:
                empty_inventory_scans = 0
            # Safety-net for the off-by-N stale-snapshot case: when phBot
            # auto-pauses the bot because the pouch is actually full, its
            # cached inventory can stay a few sacks short of `limit` forever
            # and the strict `count >= limit` gate never fires. If the bot
            # was running this session and is now stopped while we're close
            # to the limit, treat it as full and trigger anyway.
            # Bot-running gate removed — caused stuck pouches to never
            # trigger because the gate required either an active bot or a
            # prior "bot was seen running" flag, both of which can be False
            # right after a plugin reload or on alts where get_status()
            # reports oddly. We now trigger purely on inventory signals.
            empty_slots = _empty_regular_slot_count()
            inventory_physically_full = (empty_slots == 0 and count > 0)
            pet_used, pet_total, pet_empty = _grab_pet_fullness()
            pet_full = (pet_total > 0 and pet_empty == 0)
            jp_filled, jp_capacity, jp_goods, jp_goods_cap, _jp_smax = _job_pouch_state()
            # Strict: only fire when job-pouch goods are at the true cap
            # (e.g. 120/120). Do NOT trigger off regular inventory fill, grab
            # pet fill, or matched-box count — those are not the job pouch.
            job_pouch_full = (jp_goods_cap > 0 and jp_goods >= jp_goods_cap)
            if state == 'idle' and job_pouch_full:
                log('[%s] Job pouch full (%d/%d goods, %d/%d stacks); starting route.' % (
                    pName, jp_goods, jp_goods_cap, jp_filled, jp_capacity))
                _trigger_return_for_route()
                return
        if state == 'idle':
            remaining = scan_ms - (now - last_scan_at)
            if not _bot_is_running():
                _set_status('idle · bot not running · next scan %ds' % max(0, remaining // 1000))
            else:
                _set_status('idle · next scan %ds' % max(0, remaining // 1000))
            return

    if state == 'returning_to_town':
        if now - return_last_try_at >= RETURN_RETRY_MS:
            if return_attempts >= RETURN_MAX_ATTEMPTS:
                _log('Return scroll never teleported after %d attempts. Restarting bot in place so attacking can engage.' % return_attempts, True)
                try:
                    start_bot()
                except Exception as ex:
                    _log('Last-resort start_bot failed: %s' % ex, True)
                _set_state('idle')
            else:
                _log('Return scroll didn\'t teleport yet; retrying.', True)
                _do_return_scroll()
        return

    if state == 'route_running':
        _trader_packet_tick(now)
        if now - last_town_guard_at >= config.get('scan_ms', 30000):
            last_town_guard_at = now
            if _recover_if_dead_returned_to_jangan():
                return
        if reverse_pending:
            _reverse_return_tick(now)

    if state == 'town_returned' and now - action_at >= config.get('action_ms', 3500):
        _start_route()
        return

    if state == 'starting_route':
        wait_ms = route_start_wait_ms
        if now - action_at < wait_ms:
            _set_status('waiting after suit %d ms' % (wait_ms - (now - action_at)))
            return
        _run_route_script()
        return

    if state == 'route_returned' and now - action_at >= config.get('action_ms', 3500):
        _finish_route()
        return

    if state == 'awaiting_sort_settle':
        if now - action_at >= REVERSE_SORT_SETTLE_MS:
            _execute_reverse_return()
        else:
            _set_status('settling after sort %d ms' % (REVERSE_SORT_SETTLE_MS - (now - action_at)))
        return

    if state == 'awaiting_reverse_teleport':
        # Keep hammering stop_script while we wait for teleport — phBot can
        # auto-resume the loaded route script and walk us back out of town.
        if now - reverse_last_stop_at >= REVERSE_STOP_SCRIPT_INTERVAL_MS:
            reverse_last_stop_at = now
            try:
                stop_script()
            except Exception:
                pass
        if now - action_at >= REVERSE_TELEPORT_TIMEOUT_MS:
            _log('Reverse teleport callback timed out; resuming bot anyway.', True)
            _set_state('reverse_completed')
        else:
            _set_status('waiting for reverse teleport %d ms' % (REVERSE_TELEPORT_TIMEOUT_MS - (now - action_at)))
        return

    if state == 'reverse_completed':
        # Same belt-and-suspenders during the short post-teleport settle window.
        if now - reverse_last_stop_at >= REVERSE_STOP_SCRIPT_INTERVAL_MS:
            reverse_last_stop_at = now
            try:
                stop_script()
            except Exception:
                pass
        if now - action_at >= REVERSE_POST_TELEPORT_WAIT_MS:
            _finish_route()
        return

    if state == 'finishing':
        wait_ms = config.get('unequip_wait_ms', 20000)
        if now - action_at < wait_ms:
            _set_status('waiting for suit unequip %d ms' % (wait_ms - (now - action_at)))
            return
        _finish_after_suit()


def _xcontrol_leaders():
    try:
        char = get_character_data()
        if not char:
            return []
        server = char.get('server', '')
        name = char.get('name', '')
        path = os.path.join(get_config_dir(), 'xControl', '%s_%s.json' % (server, name))
        if not os.path.exists(path):
            return []
        with open(path, 'r') as f:
            data = json.load(f)
        return list(data.get('Leaders', []) or [])
    except Exception:
        return []


def handle_chat(t, player, msg):
    try:
        text = str(msg or '').strip()
        if not text:
            return
        upper = text.upper()
        if not upper.startswith('CARAVAN '):
            return
        leaders = _xcontrol_leaders()
        if not player or player not in leaders:
            return
        cmd = upper[len('CARAVAN '):].strip()
        if cmd == 'ON':
            config['enabled'] = True
            QtBind.setChecked(gui, chkEnabled, True)
            _save_config()
            log('[%s] Chat: enabled by %s.' % (pName, player))
        elif cmd == 'OFF':
            config['enabled'] = False
            QtBind.setChecked(gui, chkEnabled, False)
            _save_config()
            log('[%s] Chat: disabled by %s.' % (pName, player))
        elif cmd == 'STATUS':
            now = _now()
            armed = _armed(now)
            scan_ms = config.get('scan_ms', 30000)
            remaining = max(0, scan_ms - (now - last_scan_at))
            log('[%s] Status: state=%s box=%d armed=%s next_scan=%dms locked=%s' % (
                pName, state, last_box_count, armed, remaining, _trade_locked(now)))
        elif cmd == 'SCAN':
            _sync_scan(True)
            log('[%s] Chat: scan triggered by %s.' % (pName, player))
        elif cmd == 'GO':
            if _armed(_now()) and state not in ROUTE_ACTIVE_STATES:
                _trigger_return_for_route()
                log('[%s] Chat: route triggered by %s.' % (pName, player))
            else:
                log('[%s] Chat: GO ignored (armed=%s state=%s).' % (pName, _armed(_now()), state))
    except Exception as ex:
        _log('handle_chat error: %s' % ex, True)


_load_config()
_box_count()
log('[%s] v%s loaded.' % (pName, pVersion))

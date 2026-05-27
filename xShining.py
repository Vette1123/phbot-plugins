from phBot import *
import QtBind
import struct
import threading
import time
import webbrowser

GITHUB_URL = 'https://github.com/Vette1123'

def btn_github_clicked():
    try:
        webbrowser.open(GITHUB_URL)
    except Exception:
        pass

pName = 'xShining'
pVersion = '4.1.2'
pAuthor = 'Vette1123 (Gado)'
pUrl = 'https://raw.githubusercontent.com/Vette1123/phbot-plugins/main/xShining.py'
# GitHub: https://github.com/Vette1123
isRunning = False
broken_count = 0

# iSRO Constants
RECIPE_NAME = "MK_RC_TRADE_MATERIAL_LIGHTSTONE"

# Default delay (ms)
DEFAULT_DELAY_MS = 250

# Safety settings
MAX_INVENTORY_RETRY = 30
MAX_MISSING_STONE_RETRY = 10

# ______________________________ Initializing ______________________________ #

gui = QtBind.init(__name__, pName)
QtBind.createLabel(gui, 'xShining - iSRO v4.1.2 Fully Automatic Crafting', 6, 10)
QtBind.createLabel(gui, 'Finds Blue/Black Stone automatically anywhere!', 6, 30)

btnStart = QtBind.createButton(gui, 'btnStart_clicked', "    Start Crafting    ", 6, 55)
btnStop  = QtBind.createButton(gui, 'btnStop_clicked',  "    Stop    ", 145, 55)

QtBind.createLabel(gui, 'Speed (ms):', 6, 92)
txtDelay = QtBind.createLineEdit(gui, str(DEFAULT_DELAY_MS), 65, 88, 60, 20)

lblStatus = QtBind.createLabel(gui, 'Status: Waiting...', 6, 118)
lblCount  = QtBind.createLabel(gui, 'Broken Stones: 0',   6, 138)
QtBind.createButton(gui, 'btn_github_clicked', '  ★  (Gado) GitHub  ★  ', 6, 165)

# ______________________________ Helper Methods ______________________________ #

def get_delay():
    """Read ms value from GUI, fall back to default if invalid."""
    try:
        val = int(QtBind.text(gui, txtDelay))
        if val < 100:
            val = 100
        return val / 1000.0
    except:
        return DEFAULT_DELAY_MS / 1000.0

def get_inventory_items():
    try:
        inv = get_inventory()
    except:
        try:
            inv = get_inventory_data()
        except:
            return None

    if inv and 'items' in inv:
        return inv['items']

    return None

def is_blue_stone(servername):
    try:
        s = servername.upper()
        return "BLUESTONE" in s or "BLUE_STONE" in s
    except:
        return False

def is_black_stone(servername):
    try:
        s = servername.upper()
        return "BLACKSTONE" in s or "BLACK_STONE" in s
    except:
        return False

def start_worker_thread():
    try:
        threading.Thread(target=craft_loop, daemon=True).start()
    except:
        t = threading.Thread(target=craft_loop)
        t.daemon = True
        t.start()

# ______________________________ Main Process ______________________________ #

def craft_loop():
    global isRunning

    inventory_retry = 0
    missing_stone_retry = 0

    while isRunning:
        try:
            items = get_inventory_items()

            if not items:
                inventory_retry += 1
                QtBind.setText(gui, lblStatus, "Status: Waiting for inventory...")
                log("Plugin: Could not read inventory, retrying... ({}/{})".format(
                    inventory_retry, MAX_INVENTORY_RETRY
                ))

                if inventory_retry >= MAX_INVENTORY_RETRY:
                    log("Plugin: Inventory unreadable for too long, stopping.")
                    QtBind.setText(gui, lblStatus, "Error: Inventory unreadable")
                    isRunning = False
                    break

                time.sleep(0.5)
                continue

            inventory_retry = 0

            blue_slot = None
            black_slot = None

            for i in range(13, len(items)):
                item = items[i]

                if not item:
                    continue

                sname = item.get('servername', '')

                if blue_slot is None and is_blue_stone(sname):
                    blue_slot = i

                elif black_slot is None and is_black_stone(sname):
                    black_slot = i

                if blue_slot is not None and black_slot is not None:
                    break

            if blue_slot is None or black_slot is None:
                missing_stone_retry += 1
                QtBind.setText(gui, lblStatus, "Status: Searching for stones...")
                log("Plugin: Blue/Black Stone not found, retrying... ({}/{})".format(
                    missing_stone_retry, MAX_MISSING_STONE_RETRY
                ))

                if missing_stone_retry >= MAX_MISSING_STONE_RETRY:
                    log("Plugin: Blue or Black Stone depleted! Stopping.")
                    QtBind.setText(gui, lblStatus, "Done: Stones depleted")
                    isRunning = False
                    break

                time.sleep(0.5)
                continue

            missing_stone_retry = 0

            packet = bytearray()
            packet.append(0x01)
            packet.extend(struct.pack('<I', 29))
            packet.extend(struct.pack('<H', len(RECIPE_NAME)))
            packet.extend(RECIPE_NAME.encode('ascii'))
            packet.append(0x02)
            packet.append(blue_slot)
            packet.append(black_slot)
            packet.append(0x01)

            inject_joymax(0x7538, packet, False)

            QtBind.setText(gui, lblStatus, "Status: Running...")
            time.sleep(get_delay())

        except Exception as ex:
            log("Plugin Loop Error: " + str(ex))
            QtBind.setText(gui, lblStatus, "Error: retrying")
            time.sleep(1.0)

    QtBind.setText(gui, lblStatus, "Status: Stopped")

# ______________________________ Events ______________________________ #

def btnStart_clicked():
    global isRunning, broken_count

    if isRunning:
        return

    isRunning = True
    broken_count = 0

    QtBind.setText(gui, lblCount, 'Broken Stones: 0')
    QtBind.setText(gui, lblStatus, 'Status: Running...')

    log("Plugin: v{} started. Delay: {}ms".format(
        pVersion, int(get_delay() * 1000)
    ))

    start_worker_thread()

def btnStop_clicked():
    global isRunning

    isRunning = False
    QtBind.setText(gui, lblStatus, "Stopped")
    log("Plugin: Stopped. Total broken: " + str(broken_count))

def handle_joymax(opcode, data):
    global isRunning, broken_count

    if isRunning and opcode == 0xB538:
        broken_count += 1
        QtBind.setText(gui, lblCount, 'Broken Stones: ' + str(broken_count))

    return True

log('Plugin: ' + pName + ' v' + pVersion + ' loaded!')

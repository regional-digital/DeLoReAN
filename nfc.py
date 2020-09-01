from pyscan import Pyscan
from MFRC630 import MFRC630
from machine import Pin, PWM
import time
import _thread

def discovery_loop(nfc, lora_socket):
    while True:
        # Send REQA for ISO14443A card type
        atqa = nfc.mfrc630_iso14443a_WUPA_REQA(nfc.MFRC630_ISO14443_CMD_REQA)
        if (atqa != 0):
            # A card has been detected, read UID
            uid = bytearray(10)
            uid_len = nfc.mfrc630_iso14443a_select(uid)
            print("UID [%d]: %s" % (uid_len, nfc.format_block(uid, uid_len)))
            lora_socket.send(uid)
        nfc.mfrc630_cmd_reset()
        time.sleep(.5)
        nfc.mfrc630_cmd_init()

def start_thread(lora_socket):
    # Setup Pyscan
    py = Pyscan()
    # Setup NFC reader
    nfc = MFRC630(py)
    # Initialise the MFRC630 with some settings
    nfc.mfrc630_cmd_init()

    _thread.start_new_thread(discovery_loop, (nfc, lora_socket))

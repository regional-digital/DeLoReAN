from pyscan import Pyscan
from MFRC630 import MFRC630
from machine import Pin, PWM
import time
import config
import _thread

buzzer = Pin(config.BUZZER)
tim = PWM(0, frequency=300)
ch = tim.channel(2, duty_cycle=0, pin=buzzer)
jingle = [2637, 2637, 0]
def play_jingle():
    for i in jingle:
        if i == 0:
            ch.duty_cycle(0)
        else:
            tim = PWM(0, frequency=i) # change frequency for change tone
            ch.duty_cycle(0.5)
        time.sleep(0.2)

def discovery_loop(nfc, lora_socket):
    while True:
        # Send REQA for ISO14443A card type
        atqa = nfc.mfrc630_iso14443a_WUPA_REQA(nfc.MFRC630_ISO14443_CMD_REQA)
        if (atqa != 0):
            # A card has been detected, read uid and try to authenticate
            uid = bytearray(10)
            nfc.mfrc630_cmd_load_key(config.MF_AUTH_KEY_A)
            uid_len = nfc.mfrc630_iso14443a_select(uid)
            if (uid_len > 0) and (nfc.mfrc630_MF_auth(uid, nfc.MFRC630_MF_AUTH_KEY_A, 0)):
                print("UID [%d]: %s" % (uid_len, nfc.format_block(uid, uid_len)))
                lora_socket.send(uid)
                play_jingle()
                nfc.mfrc630_MF_deauth()
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

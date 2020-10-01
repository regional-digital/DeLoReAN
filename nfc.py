from pyscan import Pyscan
from MFRC630 import MFRC630
from machine import Pin, PWM
import time
import _thread

CARDkey = [ 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]

buzzer = Pin('P19')
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
            # A card has been detected, read UID
            uid = bytearray(10)
            uid_len = nfc.mfrc630_iso14443a_select(uid)
            print("UID [%d]: %s" % (uid_len, nfc.mfrc630_format_block(uid, uid_len)))
            if True:
                # Try to authenticate with CARD key
                nfc.mfrc630_cmd_load_key(CARDkey)
                for sector in range(0, 16):
                    if (nfc.mfrc630_MF_auth(uid, nfc.MFRC630_MF_AUTH_KEY_A, sector * 4)):
                        # Authentication was sucessful, read card data
                        play_jingle()
                        readbuf = bytearray(16)
                        for b in range(0, 4):
                            f_sect = sector * 4 + b
                            len = nfc.mfrc630_MF_read_block(f_sect, readbuf)
                            print("Sector %s: Block: %s: %s" % (nfc.format_block([sector], 1), nfc.format_block([b], 1), nfc.format_block(readbuf, len)))

                    else:
                        print("Authentication denied for sector %s!" % nfc.format_block([sector], 1))
                # It is necessary to call mfrc630_MF_deauth after authentication
                # Although this is also handled by the reset / init cycle
                nfc.mfrc630_MF_deauth()
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

from pyscan import Pyscan
from MFRC630 import MFRC630
from machine import Pin, PWM
import time
import config
import _thread
import struct
import json

buzzer = Pin(config.BUZZER)
tim = PWM(0, frequency=300)
ch = tim.channel(2, duty_cycle=0, pin=buzzer)
in_jingle = [2430, 2637, 0]
out_jingle = [2637, 2430, 0]
err_jingle = [500, 0]

filename = '/flash/devices.txt'

def write_file(data, filename):
    with open(filename, 'wt') as f:
        f.write(json.dumps(data))

def read_file(filename):
    with open(filename, 'r') as f:
        data = json.loads(f.read())
    return data

def add_card(uid, filename, lora_socket):
    print("add card to dict")
    device = str(uid).replace("'", "").replace("\\x", "").replace("bytearray(b", "").replace(")", "")
    print("device:", device)
    try:
        checkedin_devices_dict = read_file(filename)
    except Exception as e:
        print("error:", e)
        checkedin_devices_dict = {}
    print("checkedin_devices_dict:", checkedin_devices_dict)        
    checkedin_devices_dict[device] = time.time()
    write_file(checkedin_devices_dict, filename)
    amount = len(checkedin_devices_dict)
    print("amount:", amount)
    lora_socket.send(uid + struct.pack("!h", amount))
    print("{} checking in.".format(device))
    print("checkedin_devices_dict:", checkedin_devices_dict)    

def delete_card(uid, filename, lora_socket):
    device = str(uid).replace("'", "").replace("\\x", "").replace("bytearray(b", "").replace(")", "")
    print("delete card:", device)
    try:
        checkedin_devices_dict = read_file(filename)
    except Exception as e:
        print("error:", e)
        checkedin_devices_dict = {}
    checkedin_devices_dict.pop(device, None)
    write_file(checkedin_devices_dict, filename)
    print("{} deleted".format(device))


def checkout_card(uid, filename, lora_socket):
    device = str(uid).replace("'", "").replace("\\x", "").replace("bytearray(b", "").replace(")", "")
    print(checkout_card)
    try:
        checkedin_devices_dict = read_file(filename)
    except Exception as e:
        print("error:", e)
        checkedin_devices_dict = {}
    try:
        time_diff = time.time() - checkedin_devices_dict[device]
        amount = len(checkedin_devices_dict) - 1
        print("amount:", amount)
        lora_socket.send(uid + struct.pack("!h", amount) + struct.pack("!h", time_diff))
        print("sending:", struct.pack("!I", time_diff))
    except Exception as e:
        print(e)

    delete_card(uid, filename, lora_socket)
    print("len dict:", len(checkedin_devices_dict))
    print("{} checking out after: {} s".format(device, time_diff))


def check_for_orphaned_cards(filename):
    print("check for orphaned cards")
    
    try:
        print("loading dict")
        checkedin_devices_dict = read_file(filename)
    except Exception as e:
        print("loading dict error:", e)
        checkedin_devices_dict = {}

    for device in checkedin_devices_dict.keys():
        try:
            print("calc time_diff")
            time_diff = time.time() - checkedin_devices_dict[device]
            if time_diff > 32400:
                # delete device from dict
                print("removing", device)
                checkedin_devices_dict.pop(device, None)
                write_file(checkedin_devices_dict, filename)
                print("{} deleted".format(device))
        except Exception as e:
            print("removing device error", e)
    

def play_jingle(jingle):
    for i in jingle:
        if i == 0:
            ch.duty_cycle(0)
        else:
            tim = PWM(0, frequency=i) # change frequency for change tone
            ch.duty_cycle(0.5)
        time.sleep(0.2)

def discovery_loop(nfc, lora_socket):
    try:
        checkedin_devices_dict = read_file(filename)
        print("file loading ok.")
    except Exception as e:
        print("error:", e)
        checkedin_devices_dict = {}

    print("Start up @{} s.".format(time.time()))
    amount = len(checkedin_devices_dict)
    lora_socket.send(struct.pack("!I", time.time()) + struct.pack("!h", amount))            
    while True:
        # send a hearbeat message every hour (3600s)
        if time.time() % 3600 == 0:
            try:
                check_for_orphaned_cards(filename)
                checkedin_devices_dict = read_file(filename)
                print("file loading ok.")
                print("test:", checkedin_devices_dict)
            except Exception as e:
                print("error:", e)
                checkedin_devices_dict = {}
            print("Heartbeat @{} s.".format(time.time()))
            amount = len(checkedin_devices_dict)
            print("Heartbeat @{} s w/ amount of {}.".format(time.time(), amount))
            lora_socket.send(struct.pack("!I", time.time()) + struct.pack("!h", amount))            
            time.sleep(2)
        # Send REQA for ISO14443A card type
        atqa = nfc.mfrc630_iso14443a_WUPA_REQA(nfc.MFRC630_ISO14443_CMD_REQA)
        if (atqa != 0):
            # A card has been detected, read uid and try to authenticate
            uid = bytearray(10)
            nfc.mfrc630_cmd_load_key(config.MF_AUTH_KEY_A)
            uid_len = nfc.mfrc630_iso14443a_select(uid)
            if (uid_len > 0) and (nfc.mfrc630_MF_auth(uid, nfc.MFRC630_MF_AUTH_KEY_A, 0)):
                print("UID [%d]: %s, ts: %d s" % (uid_len, nfc.format_block(uid, uid_len), time.time()))
                device = str(uid).replace("'", "").replace("\\x", "").replace("bytearray(b", "").replace(")", "")

                try:
                    checkedin_devices_dict = read_file(filename)
                except Exception as e:
                    print("error:", e)
                    checkedin_devices_dict = {}
                
                if len(checkedin_devices_dict) > 0:
                    # in case the dict is not empty search for device
                    if device in checkedin_devices_dict.keys():
                        print("len dict:", len(checkedin_devices_dict))
                        time_diff = time.time() - checkedin_devices_dict[device]
                        if time_diff < 20:
                            print("Same card presented twice.")
                            play_jingle(err_jingle)
                        else:
                            # check out device and transmit duration
                            checkout_card(uid, filename, lora_socket)
                            play_jingle(out_jingle)
                    else:
                        # otherwise add it to the dict
                        add_card(uid, filename, lora_socket)
                        play_jingle(in_jingle)
                else:
                    # otherwise add it to the dict
                    add_card(uid, filename, lora_socket)
                    play_jingle(in_jingle)
                
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

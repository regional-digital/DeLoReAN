#!/usr/bin/env python

from network import LoRa
import pycom
import socket
import ubinascii
import struct
import time
import config

'''
    Utility function to setup the lora channels
'''
def prepare_channels(lora, channel):
    if not channel in range(0, 9):
        raise RuntimeError("ERROR: channel should be in range 0-8 for EU868")

    if channel == 0:
        import  uos
        channel = (struct.unpack('B',uos.urandom(1))[0] % 7) + 1

    upstream = (item for item in config.EU868_FREQUENCIES if item["chan"] == channel).__next__()

    # set the 3 default channels to the same frequency
    # (must be before sending the OTAA join request)
    lora.add_channel(0, frequency=int(upstream.get('fq')), dr_min=0, dr_max=5)
    lora.add_channel(1, frequency=int(upstream.get('fq')), dr_min=0, dr_max=5)
    lora.add_channel(2, frequency=int(upstream.get('fq')), dr_min=0, dr_max=5)

    for i in range(3, 16):
        lora.remove_channel(i)

'''
    Call back for handling RX packets
'''
def lora_cb(lora):
    events = lora.events()
    if events & LoRa.RX_PACKET_EVENT:
        if lora_socket is not None:
            frame, port = lora_socket.recvfrom(512)
            print(port, frame)
    if events & LoRa.TX_PACKET_EVENT:
        print("tx_time_on_air: {} ms @dr {}", lora.stats().tx_time_on_air, lora.stats().sftx)

def join_otaa():
    # Setup LoRa
    lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.EU868, device_class=LoRa.CLASS_C)
    # Prepare the 3 default channels
    prepare_channels(lora, config.LORA_CHANNEL)
    # Set the OTA authentication keys
    dev_eui = ubinascii.unhexlify(config.DEV_EUI)
    app_eui = ubinascii.unhexlify(config.APP_EUI)
    app_key = ubinascii.unhexlify(config.APP_KEY)
    # Join a network using OTAA
    lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0, dr=config.LORA_NODE_DR)

    # wait until the module has joined the network
    print('Over the air network activation ...', end='')
    while not lora.has_joined():
        pycom.rgbled(config.RGB_LORA_JOINING)
        time.sleep(1)
        print('.', end='')
        pycom.rgbled(config.RGB_OFF)
        time.sleep(1)
        print('.', end='')

    if lora.has_joined():
        pycom.rgbled(config.RGB_LORA_JOINED)
        print("... LoRa joined")

    # Create a LoRa socket
    lora_socket = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    # and make the socket non-blocking
    lora_socket.setblocking(False)

    # Set a callback for RX,TX and TX_FAILED events
    lora.callback(trigger=( LoRa.RX_PACKET_EVENT |
                            LoRa.TX_PACKET_EVENT |
                            LoRa.TX_FAILED_EVENT  ), handler=lora_cb)

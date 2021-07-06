import pycom
import machine

pycom.heartbeat(False)
checkedin_devices_dict = {}
machine.main('main.py')

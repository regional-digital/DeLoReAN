"""
Change these for your own keys (see https://www.thethingsnetwork.org)
Type has to be string
"""
DEV_EUI = '0123456789ABCDEF'
APP_EUI = '0123456789ABCDEF'
APP_KEY = '0123456789ABCDEF0123456789ABCDEF'

EU868_FREQUENCIES = [
    { "chan": 1, "fq": "868100000" },
    { "chan": 2, "fq": "868300000" },
    { "chan": 3, "fq": "868500000" },
    { "chan": 4, "fq": "867100000" },
    { "chan": 5, "fq": "867300000" },
    { "chan": 6, "fq": "867500000" },
    { "chan": 7, "fq": "867700000" },
    { "chan": 8, "fq": "867900000" },
]
LORA_CHANNEL = 0 # Set 0 to choose a random channel
LORA_NODE_DR = 4

RGB_OFF = (0x000000)
RGB_LORA_JOINING = (0x111100)
RGB_LORA_JOINED = (0x001100)

BUZZER = 'P19'

MF_AUTH_KEY_A = [ 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]

"""DeLoReAN is a LoRaWAN based NFC time recording node
   based on the Lopy4 and the Pyscan board.

   Released under the MIT License.
   Copyright (c) 2020 Stadt Bühl.
"""

import lora
import nfc


lora_socket = lora.join_otaa()
nfc.start_thread(lora_socket)

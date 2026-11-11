import queue, threading
import numpy as np
from scipy import signal
import sounddevice as sd
import adi
from common.config import SDR1_IP


# Create a device interface
sdr = adi.ad9361()
# Configure properties
sdr.rx_rf_bandwidth = 4000000
sdr.rx_lo = 2000000000
sdr.tx_lo = 2000000000
sdr.tx_cyclic_buffer = True
sdr.tx_hardwaregain = -30
sdr.gain_control_mode = "slow_attack"
# Read back properties from hardware
print(sdr.rx_hardwaregain)




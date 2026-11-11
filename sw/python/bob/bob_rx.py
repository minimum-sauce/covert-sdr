import adi
from common.config import *
import numpy as np

sdr = adi.ad9361(uri=SDR2_IP) 

sdr.rx_lo = FC
sdr.sample_rate = int(2e6)    
sdr.rx_rf_bandwidth = int(2e6)
sdr.rx_enabled_channels = [0]            
sdr.rx_buffer_size = 2**16        




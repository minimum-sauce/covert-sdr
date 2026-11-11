import adi
import numpy as np

sdr = adi.ad9361(uri="ip:192.168.2.1") 

sdr.rx_lo = int(868e6)
sdr.sample_rate = int(2e6)    
sdr.rx_rf_bandwidth = int(2e6)
sdr.rx_enabled_channels = [0]            
sdr.rx_buffer_size = 2**16         
        



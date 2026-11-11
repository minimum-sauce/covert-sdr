import numpy as np
import adi
from common.config import SDR2_IP, FC

N = 100000     # Number of samples

# Setup Willie SDR
def setup_willie():
    sdr = adi.ad9361(SDR2_IP)
    #sdr.sample_rate = int(FS) # Set the sample rate
    sdr.rx_lo = FC # Set the carrier frequency
    #sdr.rx_rf_bandwidth = int(FS) # Set the RF bandwidth
    #sdr.rx_enabled_channels = [0]  # Enable channel 1
    sdr.rx_buffer_size = N  # Set the buffer size to return one measurement per call
    sdr.gain_control_mode_chan0 = "manual" # Set gain control to manual to not miss transmissions
    sdr.rx_hardwaregain_chan0 = 40

    return sdr

# Measure the power of the received signal
def measure_power(sdr):
    samples = sdr.rx()

    return np.mean(np.abs(samples)**2)

# Calibrate the average noise power and set detection threshold
def calibrate(sdr, n=50, k=2):
    # Measure the noise power and calculate the threshold
    noise = [measure_power(sdr) for _ in range(n)]
    threshold = np.mean(noise) + k * np.std(noise)

    return threshold

# Check if a signal can be detected
def detect(sdr, threshold): return bool(measure_power(sdr) > threshold)
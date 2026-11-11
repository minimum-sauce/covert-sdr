import numpy as np
import adi
#from common.config import SDR2_IP

# SDR
ip = '192.168.2.1'
sdr = adi.ad9361(ip)

# Settings
FC = 868e6  # Carrier frequency
FS = 10e6    # Sampling frequency
N = 1000     # Number of samples

# Setup SDR
def setup_willie():
    sdr.sample_rate = int(FS) # Set the sample rate
    sdr.rx_lo = int(FC) # Set the carrier frequency
    sdr.rx_rf_bandwidth = int(FS) # Set the RF bandwidth
    sdr.rx_enabled_channels = [0]  # Enable channel 1
    sdr.rx_buffer_size = N  # Set the buffer size to return one measurement per call

    # Set gain control to manual to not miss the transmission from Alice
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_hardwaregain_chan0 = 40

def measure_power():
    samples = sdr.rx()
    return np.mean(np.abs(samples)**2)

def calibrate(sdr, n=50, k=4):
    # Measure the noise power and calculate the threshold
    noise = [measure_power(sdr) for _ in range(n)]
    threshold = np.mean(noise) + k * np.std(noise)

    return threshold

def detect(threshold):
    return bool(measure_power(sdr) > threshold)
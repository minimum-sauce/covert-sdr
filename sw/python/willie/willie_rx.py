import numpy as np
import adi
from common.config import FS, SDR2_IP, FC

N = 100000  # Default samples per power measurement

def setup_willie(sdr=None, uri=None, buffer_size=N, rx_gain=20):
    if sdr is None:
        sdr = adi.ad9361(uri=uri or f"ip:{SDR2_IP}")

    sdr.sample_rate = FS
    sdr.rx_lo = FC
    sdr.rx_rf_bandwidth = int(2e6)
    sdr.rx_enabled_channels = [0]
    sdr.rx_buffer_size = buffer_size
    sdr.rx_cyclic_buffer = False
    sdr.gain_control_mode_chan0 = "manual"
    sdr.rx_hardwaregain_chan0 = rx_gain
    return sdr


def measure_power(sdr):
    samples = np.asarray(sdr.rx(), dtype=complex)
    if samples.ndim > 1:
        samples = samples[0]
    return float(np.mean(np.abs(samples) ** 2))


def calibrate(sdr, n=50, k=4):
    noise = [measure_power(sdr) for _ in range(n)]
    return float(np.mean(noise) + k * np.std(noise))


def detect(sdr, threshold):
    return measure_power(sdr) > threshold
# alice/alice_tx.py
import numpy as np
import adi
from scipy.signal import firwin, lfilter
from common.config import CENTER_FREQUENCY, SDR1_IP

# --- local settings ---
SDR_IP  = SDR1_IP
FS      = 1_000_000      # sample rate
BW      = 200_000        # occupied bandwidth of the noise
TX_GAIN = 0            # dB, 0 is max
N       = 2**18          # buffer length

# --- complex Gaussian noise ---
noise = (np.random.randn(N) + 1j * np.random.randn(N)) / np.sqrt(2)

# --- low-pass filter to the wanted bandwidth ---
taps = firwin(257, BW / 2, fs=FS)
samples = lfilter(taps, 1.0, noise)

# --- scale for the DAC ---
samples = samples / np.max(np.abs(samples)) * 2**14 * 0.5

# --- SDR ---
sdr = adi.Pluto(uri=f"ip:{SDR_IP}")   # or adi.ad9361(...) if this fails
sdr.tx_lo = int(CENTER_FREQUENCY)
sdr.sample_rate = FS
sdr.tx_rf_bandwidth = FS
sdr.tx_hardwaregain_chan0 = TX_GAIN
sdr.tx_cyclic_buffer = True
sdr.tx(samples)

input("Transmitting, press Enter to stop")
sdr.tx_destroy_buffer()
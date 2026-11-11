import queue, threading
import numpy as np
from scipy import signal
import sounddevice as sd
import adi

# ---- Settings ----
station   = 96.6e6       # Hz, change to your station
fs        = 1_200_000    # SDR sample rate
dec1      = 5            # 1.2 MHz -> 240 kHz
dec2      = 5            # 240 kHz -> 48 kHz
audio_fs  = 48_000
buf_size  = 120_000      # multiple of dec1*dec2, ~0.1 s per read

sdr = adi.ad9361("ip:192.168.1.10")   # or adi.ad9361(...)
sdr.sample_rate = fs
sdr.rx_lo = int(station)
sdr.rx_rf_bandwidth = 200_000
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.rx_buffer_size = buf_size
sdr.rx_enabled_channels = [0]     # needed on 2-channel devices

# ---- Filters (stateful, so there are no clicks between blocks) ----
lp1 = signal.firwin(101, 100_000, fs=fs)          # channel filter
lp2 = signal.firwin(101, 15_000, fs=fs / dec1)    # audio filter
zi1 = signal.lfilter_zi(lp1, 1.0) * 0
zi2 = signal.lfilter_zi(lp2, 1.0) * 0

# De-emphasis (50 µs in Europe, 75 µs in the Americas)
tau = 50e-6
a = np.exp(-1 / (audio_fs * tau))
b_de, a_de = [1 - a], [1, -a]
zi3 = np.zeros(1)

prev = np.complex64(0)
q = queue.Queue(maxsize=20)
running = True

def sdr_worker():
    global zi1, zi2, zi3, prev
    while running:
        x = sdr.rx()

        # Channel filter + decimate
        x, zi1 = signal.lfilter(lp1, 1.0, x, zi=zi1)
        x = x[::dec1]

        # FM demod: phase difference between consecutive samples
        xx = np.concatenate(([prev], x))
        prev = x[-1]
        audio = np.angle(xx[1:] * np.conj(xx[:-1]))

        # Audio filter + decimate
        audio, zi2 = signal.lfilter(lp2, 1.0, audio, zi=zi2)
        audio = audio[::dec2]

        # De-emphasis
        audio, zi3 = signal.lfilter(b_de, a_de, audio, zi=zi3)

        audio = (audio * 0.5).astype(np.float32)   # adjust volume here
        try:
            q.put(audio, timeout=1)
        except queue.Full:
            pass

# ---- Audio sink ----
leftover = np.zeros(0, dtype=np.float32)

def audio_callback(outdata, frames, time_info, status):
    global leftover
    while len(leftover) < frames:
        try:
            leftover = np.concatenate((leftover, q.get_nowait()))
        except queue.Empty:
            break
    n = min(frames, len(leftover))
    outdata[:n, 0] = leftover[:n]
    outdata[n:, 0] = 0          # underrun -> silence
    leftover = leftover[n:]

t = threading.Thread(target=sdr_worker, daemon=True)
t.start()

with sd.OutputStream(samplerate=audio_fs, channels=1, dtype="float32",
                     callback=audio_callback, blocksize=2048):
    print(f"Playing {station/1e6:.1f} MHz. Ctrl+C to stop.")
    try:
        while True:
            sd.sleep(1000)
    except KeyboardInterrupt:
        running = False
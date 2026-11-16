import time

import adi

from alice.scenarios.send_message import MESSAGE, build_message_samples
from alice.sdr_tx import SdrTx
from alice.settings import FS, TX_GAIN
from common.config import FC, SDR1_IP
from willie.willie_rx import calibrate, measure_power, setup_willie

DURATION_S = 10.0   # total run time
MESSAGES = 3        # number of transmissions
RX_GAIN = -10


device = adi.ad9361(uri=f"ip:{SDR1_IP}")
device.loopback = 0
device.tx_enabled_channels = [0]

willie = setup_willie(sdr=device, buffer_size=1024, rx_gain=RX_GAIN)
threshold = calibrate(willie, n=100, k=4)
samples = build_message_samples()
schedule = [DURATION_S * i / (MESSAGES + 1) for i in range(1, MESSAGES + 1)]
print(f"Threshold {threshold:.2f}, sending {MESSAGE!r} {MESSAGES} times over {DURATION_S}s")

sent = 0
detections = 0
start = time.monotonic()

try:
    with SdrTx(SDR1_IP, FC, FS, TX_GAIN, sdr=device) as alice:
        while (now := time.monotonic() - start) < DURATION_S:
            if sent < MESSAGES and now >= schedule[sent]:
                alice.send(samples)
                sent += 1
                print(f"[{now:.2f}s] Alice sent {sent}/{MESSAGES}")

            power = measure_power(willie)
            if power > threshold:
                detections += 1
                print(f"[{time.monotonic() - start:.2f}s] Willie: power {power:.2f} > {threshold:.2f}")
finally:
    device.rx_destroy_buffer()

print(f"Alice sent {sent}, Willie flagged {detections} buffers")
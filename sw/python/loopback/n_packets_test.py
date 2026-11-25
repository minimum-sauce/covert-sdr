import threading
import time

import adi
import numpy as np

from alice.framing import text_to_bits
from alice.scenarios.send_message import MESSAGE, build_message_samples
from alice.sdr_tx import SdrTx
from alice.settings import TX_GAIN
from bob.sdrRx import sdrRx
from common.config import FC, FS, SDR1_IP

N_PACKETS = 50
SPACING = 1       
PRINT_EVERY = 10


def main():
    dev = adi.ad9361(uri=SDR1_IP)
    dev.tx_enabled_channels = [0]
    dev.rx_enabled_channels = [0]
    dev.loopback = 0

    packets, expected = [], []
    for i in range(N_PACKETS):
        message = f"{MESSAGE}#{i:03d}"
        packets.append(np.asarray(build_message_samples(message)))
        expected.append(np.asarray(text_to_bits(message), dtype=np.uint8).ravel())

    pkt_dur = len(packets[0]) / FS
    print(f"{N_PACKETS} packets, {pkt_dur * 1e3:.1f} ms each, spacing {SPACING:.2f} s")

    rx = sdrRx().setup()
    decodes = []                 # (monotonic time, bits)
    stop = threading.Event()
    rx_error = []

    def receive():
        try:
            while not stop.is_set():
                data = rx.listen()
                if data is not None:
                    decodes.append((time.monotonic(), np.asarray(data, dtype=np.uint8).ravel()))
        except Exception as e:
            rx_error.append(e)

    worker = threading.Thread(target=receive, daemon=True)
    worker.start()

    send_times = []
    try:
        with SdrTx(SDR1_IP, FC, FS, TX_GAIN, sdr=dev) as tx:
            for i in range(N_PACKETS):
                if rx_error:
                    raise rx_error[0]

                t0 = time.monotonic()
                send_times.append(t0)
                tx.send(packets[i], cyclic=False)

                if (i + 1) % PRINT_EVERY == 0:
                    print(f"Sent {i + 1}/{N_PACKETS}", flush=True)

                # Keep a fixed schedule so decode times map cleanly to packets
                time.sleep(max(0.0, t0 + SPACING - time.monotonic()))

            time.sleep(SPACING)  # let trailing decodes arrive
    finally:
        stop.set()
        worker.join(timeout=1)
        rx.close()

    # ---- Scoring ----
    dropped = corrupted = clean = extra = misattributed = 0
    bit_errors = compared_bits = 0
    window_ends = send_times[1:] + [float("inf")]

    for i in range(N_PACKETS):
        exp = expected[i]
        cands = [b for t, b in decodes if send_times[i] <= t < window_ends[i] and b.size == exp.size]
        if not cands:
            dropped += 1
            continue

        extra += len(cands) - 1
        errs = [int(np.count_nonzero(b != exp)) for b in cands]
        e = min(errs)
        best = cands[int(np.argmin(errs))]

        # Diagnostic: does this decode look more like a different packet?
        k = int(np.argmin([np.count_nonzero(best != x) for x in expected]))
        if k != i and np.count_nonzero(best != expected[k]) < e:
            misattributed += 1

        bit_errors += e
        compared_bits += exp.size
        if e:
            corrupted += 1
        else:
            clean += 1

    print("\n--- Results ---")
    print(f"Sent {N_PACKETS} | clean {clean} | corrupted {corrupted} | dropped {dropped}")
    print(f"PER: {(dropped) / N_PACKETS:.3f} (dropped / packets sent)")
    if compared_bits:
        print(f"BER (received packets only):     {bit_errors / compared_bits:.3f} "
              f"({bit_errors}/{compared_bits} bits)")
    else:
        print("BER: n/a (no packets received)")
    if extra:
        print(f"Note: {extra} duplicate decodes inside send windows (best one scored)")
    if misattributed:
        print(f"Warning: {misattributed} decodes look like a neighbouring packet; "
              f"raise SPACING if this is large")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped")
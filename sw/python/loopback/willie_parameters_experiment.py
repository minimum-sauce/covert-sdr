from alice.tx_chain import to_samples
from alice.framing import text_to_bits, build_packet
from willie.willie_rx import setup_willie, calibrate
from alice.sdr_tx import SdrTx
from alice.settings import TX_GAIN
from common.config import FS, SDR1_IP, FC
import adi, threading, queue, time, os, itertools
from collections import deque
import numpy as np

# ---- sweep parameters ----
TX_GAINS = [-10, -20, -30, -40, -50, -60]
MESSAGES = ["Hi", "Hello, Bob!", "Hello, Bob! This is a longer message."]
AMP_SCALES = [1.0]            # extra baseband scaling, e.g. [1.0, 0.5, 0.25]
REPEATS = 3                   # messages per parameter combination
INTERVAL = 1.5                # seconds between sends
RX_GAIN = 40
OUT_DIR = os.path.join("willie_captures", "parameter_sweep")

stop = threading.Event()
save_q = queue.Queue()
sends = queue.Queue()         # Alice -> Willie: (send_time, meta)


def power(x):
    return float(np.mean(np.abs(x) ** 2))


def alice_worker(alice, device):
    combos = itertools.product(TX_GAINS, MESSAGES, AMP_SCALES)
    for gain, msg, scale in combos:
        device.tx_hardwaregain_chan0 = gain
        time.sleep(0.5)                                   # let the gain settle
        samples = scale * np.asarray(
            to_samples(build_packet(text_to_bits(msg)), FS), dtype=complex)
        for rep in range(REPEATS):
            if stop.is_set():
                return
            meta = dict(tx_gain=gain, message=msg, amp_scale=scale,
                        repeat=rep, n_samples=len(samples))
            sends.put((time.time(), meta))
            alice.send(samples)
            print(f"Alice: gain={gain} scale={scale} len={len(msg)} rep={rep}")
            stop.wait(INTERVAL)
    stop.wait(2.0)
    stop.set()                                            # sweep finished


def willie_worker(willie, threshold, pre_buffers=2):
    ring = deque(maxlen=pre_buffers)
    pending = []
    buf = willie.rx_buffer_size
    while not stop.is_set():
        x = willie.rx()
        p = power(x)

        while not sends.empty():
            t, meta = sends.get()
            need = -(-meta["n_samples"] // buf) + 3       # ceil(n/buf) + margin
            pending.append(dict(t=t, meta=meta, bufs=list(ring), powers=[], need=need))

        for it in pending[:]:
            it["bufs"].append(x)
            it["powers"].append(p)
            if len(it["powers"]) >= it["need"]:
                m = it["meta"]
                m["max_power"] = max(it["powers"])
                m["detected"] = m["max_power"] > threshold
                save_q.put((int(it["t"] * 1000), np.concatenate(it["bufs"]), m))
                print(f"Willie: gain={m['tx_gain']} max power {m['max_power']:.1f} "
                      f"(thr {threshold:.1f}) detected={m['detected']}")
                pending.remove(it)
        ring.append(x)


def saver(threshold):
    os.makedirs(OUT_DIR, exist_ok=True)
    while True:
        item = save_q.get()
        if item is None:
            break
        ts, data, meta = item
        np.savez(os.path.join(OUT_DIR, f"sweep_{ts}.npz"),
                 samples=data, sample_rate=FS, fc=FC, rx_gain=RX_GAIN,
                 threshold=threshold, **meta)


def main():
    device = adi.ad9361(uri=f"ip:{SDR1_IP}")
    willie = setup_willie(sdr=device, rx_gain=RX_GAIN)
    threshold = calibrate(willie, n=100, k=4)             # Alice silent
    print(f"Threshold: {threshold:.2f}")

    with SdrTx(SDR1_IP, FC, FS, TX_GAIN, sdr=device) as alice:
        t_w = threading.Thread(target=willie_worker, args=(willie, threshold))
        t_a = threading.Thread(target=alice_worker, args=(alice, device))
        t_s = threading.Thread(target=saver, args=(threshold,))
        for t in (t_w, t_a, t_s):
            t.start()
        try:
            while not stop.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopping")
        finally:
            stop.set()
            t_a.join()
            t_w.join()
            save_q.put(None)      # after Willie can no longer add captures
            t_s.join()


if __name__ == "__main__":
    main()
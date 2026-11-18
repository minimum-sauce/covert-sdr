from alice.tx_chain import to_samples
from alice.framing import text_to_bits, build_packet
from numpy import rec
from willie.willie_rx import setup_willie, calibrate, measure_power
from alice.sdr_tx import SdrTx
from alice.settings import TX_GAIN
from common.config import FS, SDR1_IP, FC
import adi
import threading
import queue
import time
from collections import deque
import numpy as np
import os


stop = threading.Event()
save_q = queue.Queue()


def start_willie(device):
    willie = setup_willie(sdr=device, rx_gain=40)
    print("Calibrating Willie...")
    threshold = calibrate(willie, n=100, k=4)
    print(f"Willie calibrated, threshold: {threshold:.2f}")
    return willie, threshold


def willie_worker(willie, threshold, pre_buffers=4, post_buffers=4):
    # Worker function for handling Willie's operations
    ring = deque(maxlen=pre_buffers)
    recording, quiet, rec = False, 0, []
    while not stop.is_set():
        x = willie.rx()
        hit = measure_power(x) > threshold
        if not recording:
            ring.append(x)
            if hit:
                print("Willie: FLAG")
                recording, quiet = True, 0
                rec = list(ring)
        else:
            rec.append(x)
            quiet = 0 if hit else quiet + 1
            if quiet >= post_buffers:  # burst is over
                # in willie_worker, when saving
                print(f"Willie: saved {len(rec)} buffers")
                save_q.put((int(time.time()), np.concatenate(rec)))
                recording = False
                ring.clear()

    pass


def alice_worker(alice, samples, interval):
    # Worker function for handling Alice's operations
    while not stop.is_set():
        alice.send(samples)
        print("Alice sent a message to Bob.")
        stop.wait(interval) 


def saver(threshold):
    os.makedirs("willie_captures", exist_ok=True)
    while True:
        item = save_q.get()
        if item is None:
            break
        ts, data = item
        np.savez(f"willie_captures/detect_{ts}.npz", samples=data, sample_rate=FS, fc=FC, rx_gain=40, threshold=threshold)


def main():
    device = adi.ad9361(uri=f"ip:{SDR1_IP}")

    willie = setup_willie(sdr=device, rx_gain=40)
    threshold = calibrate(willie, n=100, k=4)   # before Alice transmits anything
    print(f"Threshold: {threshold:.2f}")

    with SdrTx(SDR1_IP, FC, FS, TX_GAIN, sdr=device) as alice:
        message = "Hello, Bob!"
        bits = text_to_bits(message)
        samples = to_samples(build_packet(bits), FS)


        threads = [
            threading.Thread(target=willie_worker, args=(willie, threshold)),
            threading.Thread(target=alice_worker, args=(alice, samples, 5.0)),
            threading.Thread(target=saver, args=(threshold,)),
        ]
        for t in threads:
            t.start()

        try:
            while True:
                time.sleep(0.5)        # main thread just waits for Ctrl+C
                
        except KeyboardInterrupt:
            print("\nStopping")
        finally:
            stop.set()
            save_q.put(None)
            for t in threads:
                t.join()


if __name__ == "__main__":
    main()

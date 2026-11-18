from willie.willie_rx import setup_willie, calibrate, detect, measure_power
from alice.sdr_tx import SdrTx
from common.config import FS, SDR1_IP, FC
import adi
import threading
import queue
import time
from collections import deque


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

    pass


def alice_workeder(alice, samples):
    # Worker function for handling Alice's operations
    alice.send(samples)
    print("Alice sent a message to Bob.")






def main():

    # Initialize the SDR device
    device = adi.ad9361(uri=f"ip:{SDR1_IP}")
    
    willie, threshold = start_willie(device)

    
    try:
        with SdrTx(SDR1_IP, FC, FS, 0, sdr=device) as alice:
            samples = alice.build_message_samples("Hello, Bob!")
            alice.send(samples)
            print("Alice sent a message to Bob.")
    except Exception as e:
        print(f"Failed to send message: {e}")



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped")
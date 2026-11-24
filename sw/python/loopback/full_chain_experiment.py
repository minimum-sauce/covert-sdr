from alice.tx_chain import to_samples
from alice.framing import text_to_bits, build_packet
from willie.willie_rx import setup_willie, calibrate
from alice.sdr_tx import SdrTx
from alice.settings import TX_GAIN
from bob.rxChain import process
from bob.helper import read_samples
from bob.sdrRx import sdrRx               # adjust to your actual module name
from common.config import FS, SDR1_IP, SDR2_IP, FC
import adi, threading, queue, time, os, itertools
from collections import deque
import numpy as np

# ---- sweep parameters ----
TX_GAINS = [-10, -20, -30, -40, -50, -60]
MESSAGES = ["Hi", "Hello, Bob!", "Hello, Bob! This is a longer message."]
AMP_SCALES = [1.0]
REPEATS = 3
INTERVAL = 1.5
BOB_RX_GAIN, WILLIE_RX_GAIN = 40, 40
OUT_DIR = os.path.join("willie_captures", "full_chain")

stop = threading.Event()
save_q = queue.Queue()
send_qs = {"bob": queue.Queue(), "willie": queue.Queue()}
results, lock = {}, threading.Lock()


def power(x):
    return float(np.mean(np.abs(x) ** 2))


def deliver(sid, who, meta, data):
    """Pair Bob's and Willie's capture of the same send, then hand over together."""
    with lock:
        r = results.setdefault(sid, {"meta": meta})
        r[who] = data
        if "bob" in r and "willie" in r:
            save_q.put((sid, results.pop(sid)))


def alice_worker(alice, device):
    sid = 0
    for gain, msg, scale in itertools.product(TX_GAINS, MESSAGES, AMP_SCALES):
        device.tx_hardwaregain_chan0 = gain
        time.sleep(0.5)
        bits = text_to_bits(msg)
        samples = scale * np.asarray(to_samples(build_packet(bits), FS), dtype=complex)
        for rep in range(REPEATS):
            if stop.is_set():
                return
            meta = dict(tx_gain=gain, message=msg, amp_scale=scale, repeat=rep,
                        n_samples=len(samples), msg_len=len(msg),
                        bits_sent=np.asarray(bits, dtype=np.uint8))
            t = time.time()
            for q in send_qs.values():
                q.put((sid, t, meta))
            alice.send(samples)
            print(f"Alice: gain={gain} len={len(msg)} rep={rep}")
            sid += 1
            stop.wait(INTERVAL)
    stop.wait(2.0)
    stop.set()


def rx_worker(who, sdr, pre_buffers=2):
    """Scheduled capture for Bob and Willie; each reads its own SDR."""
    ring = deque(maxlen=pre_buffers)
    pending = []
    buf = sdr.rx_buffer_size
    while not stop.is_set():
        x = read_samples(sdr)
        p = power(x)
        while not send_qs[who].empty():
            sid, t, meta = send_qs[who].get()
            need = -(-meta["n_samples"] // buf) + 3
            pending.append(dict(sid=sid, meta=meta, bufs=list(ring), powers=[], need=need))
        for it in pending[:]:
            it["bufs"].append(x)
            it["powers"].append(p)
            if len(it["powers"]) >= it["need"]:
                data = dict(iq=np.concatenate(it["bufs"]), max_power=max(it["powers"]))
                deliver(it["sid"], who, it["meta"], data)
                pending.remove(it)
        ring.append(x)


def bit_errors(sent, decoded):
    if decoded is None:
        return len(sent), len(sent), False             # sync failed: all bits wrong
    decoded = np.asarray(decoded, dtype=np.uint8)
    m = min(len(sent), len(decoded))
    errs = int(np.sum(sent[:m] != decoded[:m])) + (len(sent) - m)
    return errs, len(sent), True


def saver(w_threshold, bob_cfg):
    os.makedirs(OUT_DIR, exist_ok=True)
    while True:
        item = save_q.get()
        if item is None:
            break
        sid, r = item
        meta, bob, willie = r["meta"], r["bob"], r["willie"]
        try:
            decoded = process(bob_cfg, bob["iq"])      # Bob's real decoder, off the RX loops
        except Exception as e:
            print(f"Bob decode error: {e}")
            decoded = None
        errs, total, sync_ok = bit_errors(meta["bits_sent"], decoded)
        w_det = willie["max_power"] > w_threshold
        print(f"sid={sid} gain={meta['tx_gain']} len={meta['msg_len']} "
              f"BER={errs/total:.3f} sync={sync_ok} willie_detected={w_det}")
        np.savez(os.path.join(OUT_DIR, f"chain_{sid:04d}.npz"),
                 bob_samples=bob["iq"], willie_samples=willie["iq"],
                 bob_max_power=bob["max_power"], willie_max_power=willie["max_power"],
                 willie_threshold=w_threshold, willie_detected=w_det,
                 bit_errors=errs, n_bits=total, ber=errs / total, sync_ok=sync_ok,
                 bits_decoded=np.asarray(decoded if decoded is not None else [], dtype=np.uint8),
                 sample_rate=FS, fc=FC, bob_rx_gain=BOB_RX_GAIN, willie_rx_gain=WILLIE_RX_GAIN,
                 **meta)


def main():
    dev1 = adi.ad9361(uri=f"ip:{SDR1_IP}")     # Alice TX
    dev2 = adi.ad9361(uri=f"ip:{SDR2_IP}")     # Willie RX

    bob_cfg = sdrRx(uri=SDR1_IP)               # Bob RX on SDR1 (builds sps, taps, preamble)
    bob_cfg.setup()
    bob_cfg.sdr.rx_hardwaregain_chan0 = BOB_RX_GAIN
    bob = bob_cfg.sdr

    willie = setup_willie(sdr=dev2, rx_gain=WILLIE_RX_GAIN)
    threshold = calibrate(willie, n=100, k=4)  # Alice silent
    print(f"Willie threshold: {threshold:.2f}")

    with SdrTx(SDR1_IP, FC, FS, TX_GAIN, sdr=dev1) as alice:
        t_a = threading.Thread(target=alice_worker, args=(alice, dev1))
        t_b = threading.Thread(target=rx_worker, args=("bob", bob))
        t_w = threading.Thread(target=rx_worker, args=("willie", willie))
        t_s = threading.Thread(target=saver, args=(threshold, bob_cfg))
        for t in (t_b, t_w, t_a, t_s):
            t.start()
        try:
            while not stop.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopping")
        finally:
            stop.set()
            for t in (t_a, t_b, t_w):
                t.join()
            save_q.put(None)
            t_s.join()
            bob_cfg.close()


if __name__ == "__main__":
    main()
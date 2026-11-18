"""
Software loopback test for the covert-sdr DSSS link (no hardware needed).

Put this file in sw/python/ (next to alice/, bob/, common/) and run from there:

    python loopback_test.py            # SNR 0 dB, 10 trials
    python loopback_test.py -5 20      # SNR -5 dB, 20 trials

It builds the real TX samples with build_message_samples(MESSAGE), repeats them
like a cyclic TX buffer, cuts out one RX-sized window at a random start, adds
noise (and a random carrier phase), then runs the real bob.rxChain.process().
"""
import sys
import types

import numpy as np

try:
    import adi  # noqa: F401
except ImportError:                       # sdrRx imports adi at module level
    sys.modules["adi"] = types.ModuleType("adi")

from common.config import FS
from common.rrc import matched_filter
from common.dsss import find_code, despread_symbols, SPREAD_CODE
from alice.scenarios.send_message import MESSAGE, build_message_samples
from bob.sdrRx import sdrRx
from bob.rxChain import process
from bob.helper import bits_to_text


def make_window(tx, n, shift, snr_db=None, cfo_hz=0.0, phase=0.0, rng=None):
    """One simulated RX read: n samples of the repeating TX buffer."""
    rng = rng or np.random.default_rng()
    reps = n // len(tx) + 2
    x = np.tile(tx, reps)[shift:shift + n].astype(complex)

    t = np.arange(n)
    x = x * np.exp(1j * (phase + 2 * np.pi * cfo_hz * t / FS))

    if snr_db is not None:
        rms = np.sqrt(np.mean(np.abs(tx) ** 2))
        sigma = rms * 10 ** (-snr_db / 20) / np.sqrt(2)
        x = x + sigma * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    return x


def diagnose(rx, window):
    """Replicates the front of process() and prints what the chain sees."""
    filtered = matched_filter(window - np.mean(window), rx.taps)
    off, _, score = find_code(filtered, sps=rx.sps, return_info=True)
    symbols = despread_symbols(filtered[off::rx.sps])
    mag = np.abs(symbols)
    blocks = mag[: len(mag) // 8 * 8].reshape(-1, 8).mean(axis=1)
    print(f"  code score={score:.1f} offset={off} n_symbols={len(symbols)}")
    print("  mean |symbol| per block of 8 (should be flat while the frame is on air):")
    print("  ", np.round(blocks / max(blocks.max(), 1e-12), 2))


def main():
    snr_db = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    trials = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    rng = np.random.default_rng(1)

    rx = sdrRx(buffer_size=2**19)                          # no setup(): only builds taps/preamble
    tx = build_message_samples(MESSAGE)
    n = rx.buffer_size
    period = len(SPREAD_CODE) * rx.sps

    print(f"MESSAGE      : {MESSAGE!r}")
    print(f"TX samples   : {len(tx)}  = {len(tx) / period:.3f} code periods "
          f"(should be a whole number)")
    print(f"RX window    : {n} samples = {n / period:.0f} symbols")
    print(f"frame length : about {len(tx) / period:.0f} symbols incl. gaps")
    print(f"max |tx|     : {np.max(np.abs(tx)):.1f}")

    print("\n--- 1) noise-free, shift 0: diagnostics ---")
    clean = make_window(tx, n, 0, snr_db=None, phase=0.7, rng=rng)
    diagnose(rx, clean)
    out = process(rx, clean)
    print("  decoded:", None if out is None else repr(bits_to_text(out)))

    print(f"\n--- 2) {trials} trials, random start, SNR {snr_db} dB (per sample, 1 MHz band) ---")
    ok = 0
    for i in range(trials):
        shift = int(rng.integers(0, len(tx)))
        phase = float(rng.uniform(-np.pi, np.pi))
        w = make_window(tx, n, shift, snr_db=snr_db, phase=phase, rng=rng)
        out = process(rx, w)
        text = None if out is None else bits_to_text(out)
        good = text == MESSAGE
        ok += good
        print(f"  trial {i:2d} shift={shift:7d}  ->  {text!r}  {'OK' if good else 'FAIL'}")
    print(f"\n{ok}/{trials} decoded correctly")


if __name__ == "__main__":
    main()
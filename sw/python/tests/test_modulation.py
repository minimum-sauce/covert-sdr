import numpy as np
import pytest
from common.modulation import modulate, demodulate

# Check if the modulation works as intended Bit: 0 -> -1 Bit: 1 -> 1
def test_BPSK_mapping():
    symbols = modulate(np.array([1, 0, 0, 1]), "BPSK")
    assert np.array_equal(symbols, np.array([1, -1, -1, 1], dtype=complex))

# Check sent bits is recieved correclty by demodulating the symbols
def test_bpsk_roundtrip():
    rng = np.random.default_rng(0)
    bits = rng.integers(0, 2, 1000)
    symbols = modulate(bits, "BPSK")
    assert np.array_equal(demodulate(symbols, "BPSK"), bits)

# Add some noise and do the same roundtrip
def test_bpsk_survives_mild_noise():
    rng = np.random.default_rng(1)
    bits = rng.integers(0, 2, 10_000)
    noise = 0.1 * (rng.standard_normal(10_000) + 1j * rng.standard_normal(10_000))
    rx = demodulate(modulate(bits, "BPSK") + noise, "BPSK")
    assert np.mean(rx != bits) < 0.001

import numpy as np
import pytest
from alice.framing import build_packet, text_to_bits
from alice.tx_chain import to_samples
from bob.sdrRx import sdrRx            # adjust to your module path
from common.config import FS

BITS = text_to_bits("hello")

def make_rx(delay=0, snr_db=None, phase=0.0, cfo_hz=0.0, seed=0):
    tx = to_samples(build_packet(BITS), FS)
    n = np.arange(len(tx))
    rx = tx * np.exp(1j * phase) * np.exp(2j * np.pi * cfo_hz * n / FS)
    rx = np.concatenate([np.zeros(delay, complex), rx, np.zeros(3000, complex)])
    if snr_db is not None:
        rng = np.random.default_rng(seed)
        p_sig = np.mean(np.abs(tx[tx != 0]) ** 2)
        sigma = np.sqrt(p_sig / 10 ** (snr_db / 10) / 2)
        rx = rx + sigma * (rng.standard_normal(len(rx)) + 1j * rng.standard_normal(len(rx)))
    return rx

def decode(rx):
    return sdrRx()._process(rx)

def test_ideal_channel():
    assert np.array_equal(decode(make_rx()), BITS)

def test_with_delay():
    assert np.array_equal(decode(make_rx(delay=1234)), BITS)

@pytest.mark.parametrize("phase", [0.5, 1.5, 3.0, -2.0])
def test_with_constant_phase(phase):
    assert np.array_equal(decode(make_rx(phase=phase)), BITS)

def test_with_noise():
    assert np.array_equal(decode(make_rx(delay=500, snr_db=15)), BITS)

@pytest.mark.parametrize("cfo", [100, 500, 1000])
def test_with_frequency_offset(cfo):
    assert np.array_equal(decode(make_rx(delay=500, cfo_hz=cfo)), BITS)

def test_pure_noise_returns_none():
    rng = np.random.default_rng(1)
    noise = rng.standard_normal(20000) + 1j * rng.standard_normal(20000)
    assert decode(noise) is None
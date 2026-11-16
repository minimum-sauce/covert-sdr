import numpy as np
import pytest

from alice.framing import build_packet, text_to_bits
from alice.scenarios.send_message import MESSAGE, build_message_samples
from alice.tx_chain import to_samples
from common.config import FS, HEADER_BITS, PREAMBLE_LEN, SYMBOL_RATE
from common.dsp import preamble_bits
from common.modulation import modulate
from common.rrc import matched_filter
from bob.sdrRx import sdrRx
from bob.rxChain import find_preamble, process
from bob.helper import symbols_samples

BITS = text_to_bits("hello")


def make_receiver():
    receiver = sdrRx()
    receiver.init()
    return receiver


def test_message_scenario_uses_shared_packet_chain():
    assert np.array_equal(
        build_message_samples("hello"),
        to_samples(build_packet(text_to_bits("hello")), FS),
    )


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
    return process(make_receiver(), rx)

def detect(w):
    rx = make_receiver()
    filtered = matched_filter(w - np.mean(w), rx.taps)
    return rx, filtered, find_preamble(rx, filtered)


def test_preamble_detected_with_clean_peak():
    rx, filtered, start = detect(make_rx(delay=1234))
    assert start is not None
    sym = symbols_samples(rx, filtered, start, 0, PREAMBLE_LEN)
    c = abs(np.vdot(rx.preamble, sym)) / (np.linalg.norm(sym) * np.linalg.norm(rx.preamble))
    assert c > 0.95, f"symbols at detected start don't match preamble ({c:.2f})"


@pytest.mark.parametrize("extra", [1, 7, 100])
def test_start_tracks_delay_exactly(extra):
    _, _, s0 = detect(make_rx(delay=1000))
    _, _, s1 = detect(make_rx(delay=1000 + extra))
    assert s1 - s0 == extra


@pytest.mark.parametrize("gain", [1e-3, 1.0, 1e3])
def test_amplitude_invariant(gain):
    assert np.array_equal(decode(make_rx(delay=500) * gain), BITS)


def test_dc_offset_is_removed():
    rx = make_rx(delay=500)
    rx = rx + 0.3 * np.max(np.abs(rx)) * (1 + 1j)
    assert np.array_equal(decode(rx), BITS)


def test_truncated_frame_returns_none_not_exception():
    rx = make_rx(delay=500)
    partial_frame_samples = 500 + (PREAMBLE_LEN + HEADER_BITS + len(BITS) // 2) * (FS // SYMBOL_RATE)
    assert decode(rx[:partial_frame_samples]) is None

def test_silence_is_not_decoded():
    assert decode(np.zeros(2048, dtype=complex)) is None


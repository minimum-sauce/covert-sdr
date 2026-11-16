import numpy as np
import pytest

from alice.framing import build_packet, text_to_bits
from alice.scenarios.send_message import MESSAGE, build_message_samples
from alice.tx_chain import to_samples
from common.config import FS, HEADER_BITS, PREAMBLE_LEN, SYMBOL_RATE
from common.rrc import matched_filter
from bob.sdrRx import sdrRx
from bob.rx_chain import RxChain
from loopback.willie_experiment import transmission_times

BITS = text_to_bits("hello")


def test_message_scenario_uses_shared_packet_chain():
    assert np.array_equal(
        build_message_samples("hello"),
        to_samples(build_packet(text_to_bits("hello")), FS),
    )


def test_willie_experiment_schedules_transmissions_inside_window():
    assert transmission_times(10, 3) == [2.5, 5.0, 7.5]


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
    return RxChain().process(rx)

def detect(w):
    rx = RxChain()
    filtered = matched_filter(w - np.mean(w), rx.taps)
    return rx, filtered, rx.find_preamble(filtered)


def test_preamble_detected_with_clean_peak():
    rx, filtered, start = detect(make_rx(delay=1234))
    assert start is not None
    assert rx.last_metric > 0.95, f"metric only {rx.last_metric:.2f}"
    sym = rx.sample_symbols(filtered, start, 0, PREAMBLE_LEN)
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


def test_frame_in_filter_tail_is_not_decoded():
    capture = make_rx(delay=500)
    rx = RxChain()
    filtered = matched_filter(capture - np.mean(capture), rx.taps)
    start = rx.find_preamble(filtered)
    last_payload_sample = start + (PREAMBLE_LEN + HEADER_BITS + len(BITS) - 1) * rx.sps
    assert decode(capture[:last_payload_sample]) is None


class FakeSdr:
    """Mimics a cyclic TX looped back into an RX with a random start offset."""
    def __init__(self, wave, offset):
        self.wave, self.pos = wave, offset
    def rx(self):
        idx = (self.pos + np.arange(self.rx_buffer_size)) % len(self.wave)
        self.pos += self.rx_buffer_size
        return self.wave[idx]
    def rx_destroy_buffer(self):
        pass


@pytest.mark.parametrize("offset", [0, 12345, 40000])
def test_listen_with_cyclic_buffers(offset):
    wave = to_samples(build_packet(BITS), FS)
    with sdrRx(sdr=FakeSdr(wave, offset)) as rx:
        bits = rx.listen(timeout_s=3)
    assert bits is not None and np.array_equal(bits, BITS)


def test_listen_receives_repeated_cyclic_packets():
    wave = to_samples(build_packet(BITS), FS)
    with sdrRx(sdr=FakeSdr(wave, 0)) as rx:
        for _ in range(3):
            assert np.array_equal(rx.listen(timeout_s=3), BITS)
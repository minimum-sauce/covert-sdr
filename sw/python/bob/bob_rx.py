
import numpy as np
import adi

from common.config import *
from common.rrc import rrc_taps, matched_filter
from common.modulation import modulate, demodulate


def generate_preamble(length, seed):
    """Generate the same preamble as the transmitter."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, length)


def setup_bob():
    sdr = adi.ad9361(uri=SDR2_IP)

    sdr.sample_rate = FS
    sdr.rx_lo = FC
    sdr.rx_rf_bandwidth = int(1e6)
    sdr.rx_enabled_channels = [0]
    sdr.rx_buffer_size = 65536

    return sdr


def find_preamble(filtered, preamble_symbols):
    best_metric = 0
    best_start = None

    for phase in range(SPS):
        symbols = filtered[phase::SPS]

        if len(symbols) < PREAMBLE_LEN:
            continue

        correlation = np.correlate(symbols, preamble_symbols, mode="valid")
        energy = np.convolve(np.abs(symbols)**2, np.ones(PREAMBLE_LEN), mode="valid")
        metric = np.abs(correlation) / (np.sqrt(energy * PREAMBLE_LEN) + 1e-12)

        peak = np.argmax(metric)

        if metric[peak] > best_metric:
            best_metric = metric[peak]
            best_start = phase + peak * SPS

  
    if best_metric < 0.6:
        return None

    return best_start


def decode_frame(filtered, frame_start, preamble_symbols):
    preamble_indices = frame_start + np.arange(PREAMBLE_LEN) * SPS
    received_preamble = filtered[preamble_indices]

    payload_indices = frame_start + (PREAMBLE_LEN + np.arange(PAYLOAD_BITS)) * SPS
    received_payload = filtered[payload_indices]
    phase = np.angle(np.sum(received_preamble * np.conj(preamble_symbols)))
    received_payload *= np.exp(-1j * phase)

    received_bits = demodulate(received_payload, MODULATION)

    return received_bits


def bob_rx():
    preamble_bits = generate_preamble(PREAMBLE_LEN, PREAMBLE_SEED)
    preamble_symbols = modulate(preamble_bits, MODULATION)

    sdr = setup_bob()
    rx_buffer = np.array([], dtype=complex)

    while True:
        samples = np.asarray(sdr.rx(), dtype=complex)

        if samples.ndim > 1:
            samples = samples[0]

        rx_buffer = np.concatenate((rx_buffer, samples))
        filtered = matched_filter(rx_buffer - np.mean(rx_buffer), TAPS)

        frame_start = find_preamble(filtered, preamble_symbols)

        if frame_start is None:
            continue

        last_sample = (frame_start + (PREAMBLE_LEN + PAYLOAD_BITS - 1) * SPS)

        if last_sample >= len(filtered):
            continue

        # Decode frame
        received_bits = decode_frame(
            filtered,
            frame_start,
            preamble_symbols
        )

        print("Message received!")

        return received_bits



if __name__ == "__main__":

    received_bits = receive()

    print("Received bits:")
    print(received_bits)

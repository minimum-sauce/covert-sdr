import numpy as np

from common.config import PREAMBLE_LEN, HEADER_BITS, MAX_PAYLOAD_BYTES, MODULATION
from common.rrc import matched_filter
from common.modulation import demodulate
from common.dsp import bits_to_int
from bob.helper import symbols_samples

def find_preamble(rx, filtered):
    best_metric = 0 
    best_start = None

    for phase in range(rx.sps): 
        symbols = filtered[phase::rx.sps]

        if len(symbols) < PREAMBLE_LEN:
            continue

        corr = np.correlate(symbols, rx.preamble, mode="valid")
        energy = np.convolve(np.abs(symbols) ** 2, np.ones(PREAMBLE_LEN), mode="valid")
        metric = np.abs(corr) / (np.sqrt(energy * PREAMBLE_LEN) + 1e-12)
        peak = np.argmax(metric)

        if metric[peak] > best_metric:
            best_metric = metric[peak]
            best_start = phase + peak * rx.sps
        
    return best_start if best_metric >= 0.6 else None


def decode_frame(rx, filtered, start):
    header_start = start + PREAMBLE_LEN * rx.sps
    header_end = header_start + HEADER_BITS * rx.sps

    if header_end > len(filtered):
        return None

    preamble = symbols_samples(rx, filtered, start, 0, PREAMBLE_LEN)
    phase = np.angle(np.sum(preamble * np.conj(rx.preamble)))
    rotation = np.exp(-1j * phase)
    
    header = symbols_samples(rx, filtered, start, PREAMBLE_LEN, HEADER_BITS) * rotation

    header_bits = demodulate(header, MODULATION)
    payload_length_bytes = bits_to_int(header_bits)
    
    if payload_length_bytes > MAX_PAYLOAD_BYTES or payload_length_bytes == 0:
        return None
    
    payload_length_bits = 8 * payload_length_bytes
    payload_start = PREAMBLE_LEN + HEADER_BITS

    if start + (payload_start + payload_length_bits - 1) * rx.sps >= len(filtered):
        return None

    payload = symbols_samples(rx, filtered, start, payload_start, payload_length_bits) * rotation

    return demodulate(payload, MODULATION)


def process(rx, window):
    filtered = matched_filter(window - np.mean(window), rx.taps)
    start = find_preamble(rx, filtered)

    if start is None:
        return None
    
    return decode_frame(rx, filtered, start)
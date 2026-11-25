import numpy as np

from common.config import (PREAMBLE_LEN, HEADER_BITS, MAX_PAYLOAD_BYTES,
                           MODULATION, DETECT_THRESH, USE_DSSS)
from common.rrc import matched_filter
from common.modulation import demodulate
from common.dsp import bits_to_int
from bob.helper import symbols_samples
from common.dsss import despread_symbols, find_code


def find_preamble(rx, filtered, sps):
    best_metric = 0
    best_start = None

    for phase in range(sps):
        symbols = filtered[phase::sps]
        
        if len(symbols) < PREAMBLE_LEN:
            continue

        corr = np.correlate(symbols, rx.preamble, mode="valid")
        energy = np.convolve(np.abs(symbols) ** 2, np.ones(PREAMBLE_LEN), mode="valid")
        metric = np.abs(corr) / (np.sqrt(energy * PREAMBLE_LEN) + 1e-12)
        peak = np.argmax(metric)

        if metric[peak] > best_metric:
            best_metric = metric[peak]
            best_start = phase + peak * sps

    #print(f"preamble metric={best_metric:.2f}")
    return best_start if best_metric >= 0.8 else None


def decode_frame(rx, filtered, start, sps):
    header_start = start + PREAMBLE_LEN * sps
    header_end = header_start + HEADER_BITS * sps

    if header_end > len(filtered):
        return None

    preamble = symbols_samples(filtered, start, 0, PREAMBLE_LEN, sps)
    phase = np.angle(np.sum(preamble * np.conj(rx.preamble)))
    rotation = np.exp(-1j * phase)

    header = symbols_samples(filtered, start, PREAMBLE_LEN, HEADER_BITS, sps) * rotation
    header_bits = demodulate(header, MODULATION)
    payload_length_bytes = bits_to_int(header_bits)

    if payload_length_bytes > MAX_PAYLOAD_BYTES or payload_length_bytes == 0:
        return None

    payload_length_bits = 8 * payload_length_bytes
    payload_start = PREAMBLE_LEN + HEADER_BITS

    if start + (payload_start + payload_length_bits - 1) * sps >= len(filtered):
        return None

    payload = symbols_samples(filtered, start, payload_start, payload_length_bits, sps) * rotation
    return demodulate(payload, MODULATION)


def process(rx, window):
    filtered = matched_filter(window - np.mean(window), rx.taps)

    if USE_DSSS:
        off, score = find_code(filtered, rx.spc, return_info=True)
        #print(f"code score={score:.1f}  offset={off}")

        if score < DETECT_THRESH:
            return None

        symbols = despread_symbols(filtered[off::rx.spc])
        sps = 1
    else:
        symbols = filtered
        sps = rx.sps

    start = find_preamble(rx, symbols, sps)
    if start is None:
        return None

    return decode_frame(rx, symbols, start, sps)
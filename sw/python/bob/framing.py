import numpy as np

from common.config import HEADER_BITS, MAX_PAYLOAD_BYTES, MODULATION, PREAMBLE_LEN
from common.dsp import bits_to_int
from common.modulation import demodulate


def sample_symbols(filtered, start, first, count, sps):
    indices = start + (first + np.arange(count)) * sps
    if len(indices) == 0 or indices[-1] >= len(filtered):
        return None
    return filtered[indices]


def decode_frame(
    filtered, start, sps, preamble, modulation=MODULATION, available_samples=None
):
    last_header_sample = start + (PREAMBLE_LEN + HEADER_BITS - 1) * sps
    if available_samples is not None and last_header_sample >= available_samples:
        return None

    preamble_symbols = sample_symbols(filtered, start, 0, PREAMBLE_LEN, sps)
    header = sample_symbols(filtered, start, PREAMBLE_LEN, HEADER_BITS, sps)
    if preamble_symbols is None or header is None:
        return None

    phase = np.angle(np.sum(preamble_symbols * np.conj(preamble)))
    rotation = np.exp(-1j * phase)
    payload_length_bytes = bits_to_int(demodulate(header * rotation, modulation))

    if payload_length_bytes == 0 or payload_length_bytes > MAX_PAYLOAD_BYTES:
        return None

    payload_length_bits = 8 * payload_length_bytes
    payload_start = PREAMBLE_LEN + HEADER_BITS
    last_payload_sample = start + (payload_start + payload_length_bits - 1) * sps
    if available_samples is not None and last_payload_sample >= available_samples:
        return None

    payload = sample_symbols(filtered, start, payload_start, payload_length_bits, sps)
    if payload is None:
        return None

    return demodulate(payload * rotation, modulation)
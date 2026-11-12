import numpy as np
from common.config import MAX_PAYLOAD_BYTES, HEADER_BITS
from common.dsp import preamble_bits, int_to_bits

def text_to_bits(message: str) -> np.ndarray:
    """Text -> bit array (8 bits per character)."""
    return np.unpackbits(np.frombuffer(message.encode("utf-8"), dtype=np.uint8)).astype(int)


## Builds packet for sending message
def build_packet(payload_bits: np.ndarray) -> np.ndarray:
    """Pad/truncate to PAYLOAD_BITS, prepend preamble"""
    payload_bits = np.asarray(payload_bits, dtype=int)
    n_bytes = len(payload_bits) // 8
    if n_bytes > MAX_PAYLOAD_BYTES:
        raise ValueError(f"Payload is {len(payload_bits)} bits, max is {MAX_PAYLOAD_BYTES} bytes")
    if len(payload_bits) % 8 != 0:
        raise ValueError(f"Not full bytes, payload length is: {payload_bits} bits")
    header = int_to_bits(n_bytes, HEADER_BITS)
    return np.concatenate([preamble_bits(), header, payload_bits])






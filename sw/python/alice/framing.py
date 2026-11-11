import numpy as np
from common.config import PREAMBLE_LEN, PREAMBLE_SEED, PAYLOAD_BITS

def text_to_bits(message: str) -> np.ndarray:
    """Text -> bit array (8 bits per character)."""
    return np.unpackbits(np.frombuffer(message.encode("utf-8"), dtype=np.uint8)).astype(int)

def build_packet(payload_bits: np.ndarray) -> np.ndarray:
    """Pad/truncate to PAYLOAD_BITS, prepend preamble. Later: add header, CRC, whitening."""
    




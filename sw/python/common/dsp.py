import numpy as np
from common.config import PREAMBLE_LEN, PREAMBLE_SEED

def preamble_bits() -> np.ndarray:
    """Fixed pseudo-random preamble, identical on TX and RX."""
    rng = np.random.default_rng(PREAMBLE_SEED)
    return rng.integers(0, 2, PREAMBLE_LEN)

def int_to_bits(value: int, n: int) -> np.ndarray:
    return ((value >> np.arange(n - 1, -1, -1)) & 1).astype(int)

def bits_to_int(bits) -> int:
    return int("".join(str(int(b)) for b in bits), 2)
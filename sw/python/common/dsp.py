import numpy as np
from common.config import PREAMBLE_LEN, PREAMBLE_SEED

def preamble_bits() -> np.ndarray:
    """Fixed pseudo-random preamble, identical on TX and RX."""
    rng = np.random.default_rng(PREAMBLE_SEED)
    return rng.integers(0, 2, PREAMBLE_LEN)
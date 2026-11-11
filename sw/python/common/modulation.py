import numpy as np


def modulate(bits: np.ndarray, scheme: str) -> np.ndarray:
    """Bits -> complex symbols. BPSK: 0 -> -1, 1 -> 1."""
    bits = np.asarray(bits)
    if scheme == "BPSK":
        return (2 * bits - 1).astype(complex)
    raise ValueError(f"Unknown modulation: {scheme}")

def demodulate(symbols, schema: str) -> np.ndarray:
    if schema == "BPSK":
        return (np.real(symbols) > 0).astype(int)



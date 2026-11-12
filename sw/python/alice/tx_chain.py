import numpy as np
from common.config import SYMBOL_RATE, MODULATION, ROLLOFF
from common.modulation import modulate
from common.rrc import rrc_taps, pulse_shape
from alice.settings import RRC_SPAN, DAC_SCALE, GAP_SYMBOLS

def to_samples(packet_bits: np.ndarray, fs: int, gap_symbols: int = GAP_SYMBOLS) -> np.ndarray:
    """Full chain: modulate -> pulse shaping -> zero gaps -> scale for DAC."""
    if fs % SYMBOL_RATE != 0:
        raise ValueError(f"fs={fs} must be an integer multiple of SYMBOL_RATE={SYMBOL_RATE}")
    sps = fs // SYMBOL_RATE

    symbols = modulate(packet_bits, MODULATION)
    taps    = rrc_taps(beta=ROLLOFF, span=RRC_SPAN, sps=sps)
    shaped  = pulse_shape(symbols, taps, sps)

    gap = np.zeros(gap_symbols * sps, dtype=complex)
    samples = np.concatenate([gap, shaped, gap])

    return samples / np.max(np.abs(samples)) * DAC_SCALE
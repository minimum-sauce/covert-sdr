import numpy as np

from common.config import (
    FS,
    HEADER_BITS,
    MODULATION,
    PREAMBLE_LEN,
    ROLLOFF,
    RRC_SPAN,
    SYMBOL_RATE,
)
from common.dsp import preamble_bits
from common.modulation import modulate
from common.rrc import matched_filter, rrc_taps
from bob.framing import decode_frame, sample_symbols


class RxChain:
    def __init__(self):
        self.sps = FS // SYMBOL_RATE
        self.taps = rrc_taps(ROLLOFF, RRC_SPAN, self.sps)
        self.preamble = modulate(preamble_bits(), MODULATION)
        self.last_metric = 0.0

    def find_preamble(self, filtered):
        best_metric, best_start = 0.0, None
        for phase in range(self.sps):
            symbols = filtered[phase::self.sps]
            if len(symbols) < PREAMBLE_LEN + HEADER_BITS:
                continue

            corr = np.correlate(symbols, self.preamble, mode="valid")
            energy = np.convolve(np.abs(symbols) ** 2, np.ones(PREAMBLE_LEN), mode="valid")
            metric = np.abs(corr) / (np.sqrt(energy) * np.linalg.norm(self.preamble) + 1e-12)
            usable = len(symbols) - PREAMBLE_LEN - HEADER_BITS + 1
            peak = np.argmax(metric[:usable])
            if metric[peak] > best_metric:
                best_metric = metric[peak]
                best_start = phase + peak * self.sps

        self.last_metric = best_metric
        return best_start if best_metric >= 0.6 else None

    def sample_symbols(self, filtered, start, first, count):
        return sample_symbols(filtered, start, first, count, self.sps)

    def process(self, window):
        filtered = matched_filter(window - np.mean(window), self.taps)
        start = self.find_preamble(filtered)
        if start is None:
            return None
        return decode_frame(
            filtered,
            start,
            self.sps,
            self.preamble,
            available_samples=len(window),
        )

import numpy as np
import adi

from common.config import *
from common.rrc import rrc_taps, matched_filter
from common.modulation import modulate, demodulate
from common.dsp import preamble_bits, bits_to_int


class sdrRx:
    def __init__(self, uri=SDR2_IP, buffer_size=65536):
        self.uri = uri
        self.buffer_size = buffer_size
        self.sps = FS // SYMBOL_RATE
        self.taps = rrc_taps(ROLLOFF, RRC_SPAN, self.sps)
        self.preamble = modulate(preamble_bits(), MODULATION)
        self.sdr = None
        self.max_samples = 2 * buffer_size

    def setup(self):
        self.sdr = adi.ad9361(uri=self.uri)
        self.sdr.sample_rate = FS
        self.sdr.rx_lo = FC
        self.sdr.rx_rf_bandwidth = int(2e6)
        self.sdr.rx_enabled_channels = [0]
        self.sdr.rx_buffer_size = self.buffer_size
        self.sdr.rx_cyclic_buffer = False
        return self

    def close(self):
        if self.sdr is not None:
            self.sdr.rx_destroy_buffer()
            self.sdr = None

    def __enter__(self):
        return self.setup()

    def __exit__(self, *exc):
        self.close()

    def _read(self):
        samples = np.asarray(self.sdr.rx(), dtype=complex)
        return samples[0] if samples.ndim > 1 else samples

    def _find_preamble(self, filtered):
        best_metric, best_start = 0, None

        for phase in range(self.sps):
            symbols = filtered[phase::self.sps]

            if len(symbols) < PREAMBLE_LEN:
                continue

            corr = np.correlate(symbols, self.preamble, mode="valid")
            energy = np.convolve(np.abs(symbols) ** 2, np.ones(PREAMBLE_LEN), mode="valid")
            metric = np.abs(corr) / (np.sqrt(energy * PREAMBLE_LEN) + 1e-12)
            peak = np.argmax(metric)

            if metric[peak] > best_metric:
                best_metric = metric[peak]
                best_start = phase + peak * self.sps

        return best_start if best_metric >= 0.6 else None

    def _symbols(self, filtered, start, first, count):
        indices = start + (first + np.arange(count)) * self.sps
        return filtered[indices]

    def _decode_frame(self, filtered, start):
        header_start = start + PREAMBLE_LEN * self.sps
        header_end = header_start + HEADER_BITS * self.sps

        if header_end > len(filtered):
            return None

        preamble = self._symbols(filtered, start, 0, PREAMBLE_LEN)
        phase = np.angle(np.sum(preamble * np.conj(self.preamble)))
        rotation = np.exp(-1j * phase)

        header = self._symbols(filtered, start, PREAMBLE_LEN, HEADER_BITS) * rotation

        header_bits = demodulate(header, MODULATION)
        payload_length_bytes = bits_to_int(header_bits)

        if payload_length_bytes > MAX_PAYLOAD_BYTES or payload_length_bytes == 0:
            return None

        payload_length_bits = 8 * payload_length_bytes
        payload_start = PREAMBLE_LEN + HEADER_BITS

        if start + (payload_start + payload_length_bits - 1) * self.sps >= len(filtered):
            return None

        payload = self._symbols(filtered, start, payload_start, payload_length_bits) * rotation

        return demodulate(payload, MODULATION)

    def _process(self, window):
        filtered = matched_filter(window - np.mean(window), self.taps)
        start = self._find_preamble(filtered)

        if start is None:
            return None
        
        return self._decode_frame(filtered, start)

    def listen(self):
        window = np.array([], dtype=complex)

        while True:
            window = np.concatenate((window, self._read()))[-self.max_samples:]
            bits = self._process(window)
            
            if bits is not None:
                return bits



import numpy as np
import adi

class SdrTx:
    def __init__(self, ip: str, fc: int, fs: int, gain: int):
        """Create adi device, set tx_lo, sample_rate, tx_rf_bandwidth, gain."""
        if gain > 0:
            raise ValueError("TX gain is 0 dB at most (0 = maximum power)")
        self.sdr = adi.Pluto(uri=f"ip:{ip}")      # use adi.ad9361(...) if this fails
        self.sdr.tx_lo = int(fc)
        self.sdr.sample_rate = int(fs)
        self.sdr.tx_rf_bandwidth = int(fs)
        self.sdr.tx_hardwaregain_chan0 = gain
        self._active = False

    def send(self, samples: np.ndarray, cyclic: bool = False):
        """Transmit samples (cyclic for debugging, one-shot for real use)."""
        self.stop()                                # a buffer can't be replaced while active
        self.sdr.tx_cyclic_buffer = cyclic
        self.sdr.tx(np.asarray(samples, dtype=complex))
        self._active = True

    def stop(self):
        """tx_destroy_buffer()."""
        if self._active:
            self.sdr.tx_destroy_buffer()
            self._active = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop()
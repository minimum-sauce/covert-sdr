import numpy as np
import adi


class SdrTx:
    def __init__(self, ip: str, fc: int, fs: int, gain: int, sdr=None):
        if gain > 0:
            raise ValueError("TX gain is 0 dB at most")
        self.sdr = sdr if sdr is not None else adi.Pluto(uri=f"ip:{ip}")
        self.sdr.tx_lo = int(fc)
        self.sdr.sample_rate = int(fs)
        self.sdr.tx_rf_bandwidth = int(fs)
        self.sdr.tx_enabled_channels = [0]
        self.sdr.tx_hardwaregain_chan0 = gain
        self._active = False

    def send(self, samples: np.ndarray, cyclic: bool = False):
        self.stop()
        self.sdr.tx_cyclic_buffer = cyclic
        self.sdr.tx(np.asarray(samples, dtype=complex))
        self._active = True

    def stop(self):
        if self._active:
            self.sdr.tx_destroy_buffer()
            self._active = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop()
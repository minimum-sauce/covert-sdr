
import numpy as np
import adi
import time

from common.config import FC, FS, SDR2_IP
from bob.rx_chain import RxChain


class sdrRx:
    def __init__(self, uri=SDR2_IP, buffer_size=65536, sdr=None):
        self.uri = uri
        self.buffer_size = buffer_size
        self.chain = RxChain()
        self.sdr = None
        self.max_samples = 2 * buffer_size
        self._shared = sdr

    def setup(self):
        self.sdr = self._shared if self._shared is not None else adi.ad9361(uri=self.uri)
        self.sdr.sample_rate = FS
        self.sdr.rx_lo = FC
        self.sdr.rx_rf_bandwidth = int(2e6)
        self.sdr.rx_enabled_channels = [0]
        self.sdr.rx_buffer_size = self.buffer_size
        self.sdr.rx_cyclic_buffer = False
        self.sdr.gain_control_mode_chan0 = "manual"
        self.sdr.rx_hardwaregain_chan0 = 20      # dB, adjust with the probe
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

    def listen(self, timeout_s=10, flush_buffers=0):
        t0 = time.time()
        window = np.array([], dtype=complex)
        for _ in range(flush_buffers):
            self._read()

        while time.time() - t0 < timeout_s:
            window = np.concatenate((window, self._read()))[-self.max_samples:]
            bits = self.chain.process(window)
            if bits is not None:
                return bits
        return None



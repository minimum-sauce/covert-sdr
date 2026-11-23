import numpy as np
import adi

from common.config import *
from common.rrc import rrc_taps
from common.modulation import modulate
from common.dsp import preamble_bits
from bob.rxChain import process
from bob.helper import read_samples

class sdrRx:
    def __init__(self, uri=SDR1_IP, buffer_size=2**19):
        self.uri = uri
        self.buffer_size = buffer_size
        self.sps = SPS
        self.sps = SPS
        self.spc = SPC
        self.taps = rrc_taps(ROLLOFF, RRC_SPAN, self.spc if USE_DSSS else self.sps)
        self.preamble = modulate(preamble_bits(), MODULATION)
        self.sdr = None

    def setup(self):
        self.sdr = adi.Pluto(uri=self.uri)
        self.sdr.sample_rate = FS
        self.sdr.rx_lo = FC
        self.sdr.rx_rf_bandwidth = int(1e6)
        self.sdr.rx_enabled_channels = [0]
        self.sdr.rx_buffer_size = self.buffer_size
        self.sdr.rx_cyclic_buffer = False
        self.sdr.gain_control_mode_chan0 = "manual"
        self.sdr.rx_hardwaregain_chan0 = 30
        return self

    def close(self):
        if self.sdr is not None:
            self.sdr.rx_destroy_buffer()
            self.sdr = None

    def __enter__(self):
        return self.setup()

    def __exit__(self, *exc):
        self.close()


    def listen(self):
        while True:
            window = read_samples(self.sdr)
            bits = process(self, window)
            if bits is not None:
                return bits
import numpy as np
import adi
import iio


def _cyclic_tx_block_size_bytes(sdr):
    components_per_sample = 2 if sdr._complex_data else 1
    return (
        sdr._tx_buffer_size
        * sdr._num_tx_channels_enabled
        * components_per_sample
        * sdr._tx_data_type.itemsize
    )


def _iio_write_buffer(data):
    return bytearray(data.tobytes()) if isinstance(data, np.ndarray) else data


def _send_libiio_v1_cyclic(sdr, samples):
    # The v1 shim uses byte-oriented blocks, but supplies sample counts and ndarrays.
    original_init = sdr._tx_init_channels
    original_push = sdr._tx_buffer_push
    missing = object()
    previous_init = sdr.__dict__.get("_tx_init_channels", missing)
    previous_push = sdr.__dict__.get("_tx_buffer_push", missing)

    def init_with_byte_sized_block():
        original_init()
        block_size = _cyclic_tx_block_size_bytes(sdr)
        if len(sdr._tx_block) == block_size:
            return
        undersized_block = sdr._tx_block
        sdr._tx_block = iio.Block(sdr._tx_buf_stream, block_size)
        del undersized_block

    def push_byte_buffer(data):
        return original_push(_iio_write_buffer(data))

    sdr._tx_init_channels = init_with_byte_sized_block
    sdr._tx_buffer_push = push_byte_buffer
    try:
        sdr.tx(samples)
    finally:
        if previous_init is missing:
            del sdr.__dict__["_tx_init_channels"]
        else:
            sdr._tx_init_channels = previous_init
        if previous_push is missing:
            del sdr.__dict__["_tx_buffer_push"]
        else:
            sdr._tx_buffer_push = previous_push


class SdrTx:
    def __init__(self, ip: str, fc: int, fs: int, gain: int, sdr=None):
        """Create adi device, set tx_lo, sample_rate, tx_rf_bandwidth, gain."""
        if gain > 0:
            raise ValueError("TX gain is 0 dB at most (0 = maximum power)")
        self.sdr = sdr if sdr is not None else adi.Pluto(uri=f"ip:{ip}")      # use adi.ad9361(...) if this fails
        self.sdr.tx_lo = int(fc)
        self.sdr.sample_rate = int(fs)
        self.sdr.tx_rf_bandwidth = int(fs)
        self.sdr.tx_hardwaregain_chan0 = gain
        self._active = False

    def send(self, samples: np.ndarray, cyclic: bool = False):
        """Transmit samples (cyclic for debugging, one-shot for real use)."""
        self.stop()                                # a buffer can't be replaced while active
        self.sdr.tx_cyclic_buffer = cyclic
        samples = np.asarray(samples, dtype=complex)

        uses_libiio_v1 = any(
            cls.__module__ == "adi.compat" and cls.__name__ == "compat_libiio_v1_tx"
            for cls in type(self.sdr).__mro__
        )
        if cyclic and uses_libiio_v1:
            _send_libiio_v1_cyclic(self.sdr, samples)
        else:
            self.sdr.tx(samples)
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
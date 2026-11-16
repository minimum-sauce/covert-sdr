import numpy as np

def read_samples(radio):
    samples = np.asarray(radio.rx(), dtype=complex)
    return samples[0] if samples.ndim > 1 else samples


def symbols_samples(sdr, filtered, start, first, count):
    indices = start + (first + np.arange(count)) * sdr.sps
    return filtered[indices]


def bits_to_text(bits):
    bits = np.asarray(bits, dtype=np.uint8)
    bits = bits[: len(bits) - len(bits) % 8]        
    return np.packbits(bits).tobytes().decode(errors="replace")

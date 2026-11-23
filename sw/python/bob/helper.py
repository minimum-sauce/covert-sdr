import numpy as np

def read_samples(radio):
    samples = np.asarray(radio.rx(), dtype=complex)
    return samples[0] if samples.ndim > 1 else samples


def symbols_samples(filtered, start, first, count, sps):
    indices = start + (first + np.arange(count)) * sps
    return filtered[indices]


def bits_to_text(bits):
    bits = np.asarray(bits, dtype=np.uint8)
    bits = bits[: len(bits) - len(bits) % 8]        
    return np.packbits(bits).tobytes().decode(errors="replace")

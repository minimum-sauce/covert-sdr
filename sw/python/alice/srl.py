from common.srl_config import N_REF, A_REF, K_REF
from common.config import FS
from alice.framing import build_packet
from alice.tx_chain import to_samples
import numpy as np


def build_srl_transmission(n: int, mode: str, seed: int):

    if mode == "srl":
        amp  = A_REF * (N_REF / n) ** 0.25
    elif mode == "constant":
        amp = A_REF
    else:
        raise ValueError("Not valid mode")
    
    bits = int(round(K_REF * np.sqrt(n / N_REF) / 8)) * 8
    
    # 2. Seeded pseudo-random payload bits
    rng = np.random.default_rng(seed)
    payload = rng.integers(0, 2, size=bits)

    # 3. Your existing chain: bits -> packet -> samples
    samples = to_samples(build_packet(payload), FS)

    # 4. Scale to the amplitude (RMS = amp)
    samples = samples / np.sqrt(np.mean(np.abs(samples) ** 2)) * amp

    meta = dict(n=len(samples), mode=mode, amp=amp, bits=bits, seed=seed)

    return samples, payload, meta
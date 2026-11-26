import numpy as np
from alice.srl import build_srl_transmission
from alice.framing import build_packet
from common.srl_config import SEED, N_REF, A_REF, K_REF
from common.config import HEADER_BITS, PREAMBLE_LEN, FS, SYMBOL_RATE
from alice.settings import GAP_SYMBOLS

def test_srl_payload_and_packet_bits():
    _, payload, meta = build_srl_transmission(N_REF, "srl", SEED)
    assert len(payload) == K_REF                       # at n == N_REF, bits == K_REF
    assert len(build_packet(payload)) == PREAMBLE_LEN + HEADER_BITS + K_REF


def test_srl_rms_matches_amp():
    samples, _, meta = build_srl_transmission(N_REF, "srl", SEED)
    rms = np.sqrt(np.mean(np.abs(samples) ** 2))
    assert np.isclose(rms, meta["amp"])

def test_srl_scaling_law():
    _, _, m1 = build_srl_transmission(20_000, "srl", SEED)
    _, _, m2 = build_srl_transmission(320_000, "srl", SEED)    # 16x n
    assert np.isclose(m1["amp"] / m2["amp"], 16 ** 0.25)       # 2.0
    assert m2["bits"] == 4 * m1["bits"]                         # sqrt(16) = 4
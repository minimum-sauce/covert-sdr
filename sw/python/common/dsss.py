import numpy as np

from common.config import (
    STAGES, INITIAL_STATE_1, FEEDBACK_TAPS_1,
    INITIAL_STATE_2, FEEDBACK_TAPS_2
)
from common.gold import gen_gold_codes, gen_mls
from common.modulation import modulate

SEQ1 = gen_mls(STAGES, FEEDBACK_TAPS_1, INITIAL_STATE_1)
SEQ2 = gen_mls(STAGES, FEEDBACK_TAPS_2, INITIAL_STATE_2)

GOLD_CODE = gen_gold_codes(STAGES, SEQ1, SEQ2)[2]
SPREAD_CODE = modulate(GOLD_CODE, "BPSK")


def spread_data(symbols):
    repeated_symbols = np.repeat(symbols, len(SPREAD_CODE))
    return repeated_symbols * np.tile(SPREAD_CODE, len(symbols))


def despread_data(received_chips):
    code_length = len(SPREAD_CODE)
    despread_chips = received_chips * np.tile(SPREAD_CODE, len(received_chips) // code_length)
    symbols = despread_chips.reshape(-1, code_length).sum(axis=1)

    return (symbols > 0).astype(int)
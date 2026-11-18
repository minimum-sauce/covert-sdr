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


def spread_symbols(symbols):
    repeated_symbols = np.repeat(symbols, len(SPREAD_CODE))
    return repeated_symbols * np.tile(SPREAD_CODE, len(symbols))


def despread_symbols(received_chips):
    code_length = len(SPREAD_CODE)
    despread_chips = received_chips * np.tile(SPREAD_CODE, len(received_chips) // code_length)
    symbols = despread_chips.reshape(-1, code_length).sum(axis=1)

    return (symbols > 0).astype(int)


def find_code(filtered, sps=10, return_info=False):
    best_score, best_off = -1.0, 0
    L = len(SPREAD_CODE)

    for p in range(sps):                      
        chips = filtered[p::sps]
        corr = np.correlate(chips, SPREAD_CODE, mode="valid")
        n_periods = len(corr) // L
        if n_periods == 0:
            continue
        metric = np.abs(corr[: n_periods * L]).reshape(n_periods, L).sum(axis=0)
        k = int(np.argmax(metric))
        score = metric[k] / np.mean(metric)
        if score > best_score:
            best_score, best_off = score, p + k * sps   

    if return_info:
        return best_off, 0.0, best_score     
     
    return best_off
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
CODE_LEN = len(SPREAD_CODE)

def spread_symbols(symbols):
    repeated_symbols = np.repeat(symbols, len(SPREAD_CODE))
    return repeated_symbols * np.tile(SPREAD_CODE, len(symbols))


def despread_symbols(received_chips):
    n = len(received_chips) // CODE_LEN
    received_chips = received_chips[: n * CODE_LEN]     

    despread_chips = received_chips * np.tile(SPREAD_CODE, n)
    symbols = despread_chips.reshape(-1, CODE_LEN).sum(axis=1) / CODE_LEN

    return symbols


def find_code(filtered, spc, return_info=False):
    best_score = -1.0 
    best_off = 0
  
    for p in range(spc):                      
        chips = filtered[p::spc]
        corr = np.correlate(chips, SPREAD_CODE, mode="valid")
        n_periods = len(corr) // CODE_LEN
        
        if n_periods == 0:
            continue
        
        metric = np.abs(corr[: n_periods * CODE_LEN]).reshape(n_periods, CODE_LEN).sum(axis=0)
        k = int(np.argmax(metric))
        score = metric[k] / np.mean(metric)
        
        if score > best_score:
            best_score, best_off = score, p + k * spc   

    if return_info:
        return best_off, best_score     
     
    return best_off
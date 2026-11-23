from alice.srl import build_srl_transmission
from common.srl_config import *

def test_srl_samples():
    n = 20000
    samples = build_srl_transmission(n, "srl", SEED)
    
    assert len(samples) == 8


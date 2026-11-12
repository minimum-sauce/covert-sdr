import time
import numpy as np
from common.config import SDR1_IP, FC
from alice.settings import FS, TX_GAIN
from alice.sdr_tx import SdrTx

def transmit(samples: np.ndarray, cyclic: bool = True):
    with SdrTx(SDR1_IP, FC, FS, TX_GAIN) as tx:
        tx.send(samples, cyclic=cyclic)
        if cyclic:
            print("Transmitting, press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            time.sleep(len(samples) / FS + 0.1)
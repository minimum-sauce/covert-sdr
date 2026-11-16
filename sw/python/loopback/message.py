import numpy as np
import adi
from common.config import SDR1_IP, FC
from alice.settings import FS, TX_GAIN
from alice.scenarios.send_message import MESSAGE, build_message_samples
from alice.sdr_tx import SdrTx
from bob.helper import bits_to_text
from bob.sdrRx import sdrRx

def main():
    dev = adi.ad9361(uri=f"ip:{SDR1_IP}")
    dev.tx_enabled_channels = [0]
    dev.rx_enabled_channels = [0]
    dev.loopback = 0

    samples = build_message_samples(MESSAGE)

    rx = sdrRx()
    rx.init(uri=f"ip:{SDR1_IP}", buffer_size=2 * len(samples))
    rx.setup()

    try:
        with SdrTx(SDR1_IP, FC, FS, TX_GAIN, sdr=dev) as tx:
            tx.send(samples, cyclic=True)
            print(
                f"Sending {MESSAGE!r} continuously | TX buffer {getattr(dev, '_tx_buffer_size', '?')} | "
                f"TX gain {dev.tx_hardwaregain_chan0} dB | "
                f"RX gain {rx.sdr.rx_hardwaregain_chan0} dB | "
                f"TX port {dev._get_iio_attr_str('voltage0', 'rf_port_select', True)} | "
                f"RX port {dev._get_iio_attr_str('voltage0', 'rf_port_select', False)}"
            )
            while True:
                out = rx.listen()
                if out is not None:
                    print("Received:", bits_to_text(out), flush=True)
    finally:
        rx.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped")
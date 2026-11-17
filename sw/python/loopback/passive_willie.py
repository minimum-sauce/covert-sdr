import adi
from alice.scenarios.send_message import build_message_samples
from alice.sdr_tx import SdrTx
from alice.settings import FS, TX_GAIN
from alice.tx_chain import to_samples
from common.config import FC, SDR1_IP
from willie.willie_rx import calibrate, measure_power, setup_willie
from bob.sdrRx import sdrRx
from alice.framing import text_to_bits, build_packet


device = adi.ad9361(uri=f"ip:{SDR1_IP}")


willie = setup_willie(sdr=device, rx_gain=40)
alice = SdrTx(SDR1_IP, FC, FS, TX_GAIN, sdr=device)

# Set threshold for detection based on noise measurements
threshold = calibrate(willie, n=100, k=4)

## Message to send
msg = "Hello, Bob!"
bits = text_to_bits(msg)
packet = build_packet(bits)
samples = to_samples(packet, FS)













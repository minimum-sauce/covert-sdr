from common.config import FS
from alice.framing import text_to_bits, build_packet
from alice.tx_chain import to_samples
from alice.runner import transmit

MESSAGE = "FortniteDavis"
CYCLIC  = True

def build_message_samples(message=MESSAGE):
    bits = text_to_bits(message)
    return to_samples(build_packet(bits), FS)


def main():
    transmit(build_message_samples(), cyclic=CYCLIC)

if __name__ == "__main__":
    main()
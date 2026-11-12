from alice.settings import FS
from alice.framing import text_to_bits, build_packet
from alice.tx_chain import to_samples
from alice.runner import transmit

MESSAGE = "hello"
CYCLIC  = True

def main():
    samples = to_samples(build_packet(text_to_bits(MESSAGE)), FS)
    transmit(samples, cyclic=CYCLIC)

if __name__ == "__main__":
    main()
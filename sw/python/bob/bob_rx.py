import numpy as np
from bob.sdrRx import sdrRx


def bits_to_text(bits):
    bits = np.asarray(bits, dtype=np.uint8)
    bits = bits[: len(bits) - len(bits) % 8]        
    return np.packbits(bits).tobytes().decode(errors="replace")


def main():
    with sdrRx() as bob:
        while True:
            bits = bob.listen()
            print("Received message:", bits_to_text(bits))


if __name__ == "__main__":
    main()
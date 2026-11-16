import numpy as np
from bob.sdrRx import sdrRx
from bob.helper import bits_to_text



def main():
    with sdrRx() as bob:
        while True:
            bits = bob.listen()
            if bits is not None:
                print("Received message:", bits_to_text(bits), flush=True)


if __name__ == "__main__":
    main()
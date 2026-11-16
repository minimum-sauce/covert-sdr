import numpy as np
from bob.sdrRx import sdrRx
from bob.helper import bits_to_text



def main():
    with sdrRx() as bob:
        while True:
            bits = bob.listen()
            print("Received message:", bits_to_text(bits))


if __name__ == "__main__":
    main()
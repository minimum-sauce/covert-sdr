import time

from alice.scenarios.send_message import build_message_samples
from alice.sdr_tx import SdrTx
from alice.settings import FS, TX_GAIN
from common.config import FC, MAX_PAYLOAD_BYTES, SDR1_IP

BURSTS = 8
BURST_SECONDS = 0.8
GAP_SECONDS = 2.5
START_DELAY_SECONDS = 1
PAYLOAD_PATTERN = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def build_test_message(sequence):
    prefix = f"WILLIE TEST {sequence:02d}: "
    return prefix + (PAYLOAD_PATTERN * MAX_PAYLOAD_BYTES)[
        : MAX_PAYLOAD_BYTES - len(prefix)
    ]


def main():
    print(
        f"Start Bob and Willie now; first Alice burst starts in "
        f"{START_DELAY_SECONDS}s.",
        flush=True,
    )
    time.sleep(START_DELAY_SECONDS)

    with SdrTx(SDR1_IP, FC, FS, TX_GAIN) as tx:
        for sequence in range(1, BURSTS + 1):
            message = build_test_message(sequence)
            tx.send(build_message_samples(message), cyclic=True)
            print(
                f"Burst {sequence}/{BURSTS}: transmitting {message!r} "
                f"for {BURST_SECONDS}s",
                flush=True,
            )
            time.sleep(BURST_SECONDS)
            tx.stop()
            print(f"Silent gap: {GAP_SECONDS}s", flush=True)
            if sequence < BURSTS:
                time.sleep(GAP_SECONDS)


if __name__ == "__main__":
    main()

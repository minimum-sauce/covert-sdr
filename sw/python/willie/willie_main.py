from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np

from common.config import FS
from willie.willie_rx import N, calibrate, setup_willie

PRE_SECONDS = 0.5
POST_SECONDS = 0.5
CAPTURE_DIR = Path("willie_captures")


def _receive_samples(sdr):
    samples = np.asarray(sdr.rx(), dtype=np.complex64)
    if samples.ndim > 1:
        samples = samples[0]
    return samples


def _save_capture(samples, threshold, peak_power, trigger_index):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = CAPTURE_DIR / f"willie_{timestamp}.npz"
    np.savez_compressed(
        path,
        iq=samples,
        sample_rate=FS,
        threshold=threshold,
        peak_power=peak_power,
        trigger_index=trigger_index,
        measurement_window_samples=N,
    )
    return path


def main():
    sdr = setup_willie()
    measurements = 0
    captures = 0
    pre_sample_count = int(PRE_SECONDS * FS)
    post_sample_count = int(POST_SECONDS * FS)
    pre_buffer = deque(maxlen=(pre_sample_count + N - 1) // N + 1)

    try:
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        threshold = calibrate(sdr)
        print(
            f"Willie listening; threshold: {threshold:.2f}; "
            f"captures will be saved in {CAPTURE_DIR}",
            flush=True,
        )
        armed = True

        while True:
            samples = _receive_samples(sdr)
            power = float(np.mean(np.abs(samples) ** 2))
            measurements += 1
            if power > threshold and armed:
                before = (
                    np.concatenate(pre_buffer)
                    if pre_buffer
                    else np.array([], dtype=np.complex64)
                )
                before = before[-pre_sample_count:] if pre_sample_count else before[:0]
                capture = [before, samples]
                pre_buffer.append(samples)
                remaining = post_sample_count
                peak_power = power
                last_post_power = power

                while remaining > 0:
                    after = _receive_samples(sdr)
                    after_power = float(np.mean(np.abs(after) ** 2))
                    peak_power = max(peak_power, after_power)
                    capture.append(after)
                    remaining -= len(after)
                    last_post_power = after_power
                    pre_buffer.append(after)
                    measurements += 1

                captured_samples = np.concatenate(capture)
                path = _save_capture(
                    captured_samples, threshold, peak_power, len(before)
                )
                captures += 1
                armed = last_post_power <= threshold
                print(
                    f"Willie saved detection {captures}: {path} "
                    f"(peak power {peak_power:.2f})",
                    flush=True,
                )
            else:
                pre_buffer.append(samples)
                if power <= threshold:
                    armed = True
    except KeyboardInterrupt:
        print(
            f"\nWillie stopped after {measurements} measurements; "
            f"{captures} captures",
            flush=True,
        )
    finally:
        sdr.rx_destroy_buffer()


if __name__ == "__main__":
    main()

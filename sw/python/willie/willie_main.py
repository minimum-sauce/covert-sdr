from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np

from common.config import FS
from willie.willie_rx import calibrate, setup_willie

PRE_SECONDS = 0.5
POST_SECONDS = 0.5
MEASUREMENT_SAMPLES = 10_000
AVERAGE_COUNT = 5
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
        measurement_window_samples=MEASUREMENT_SAMPLES,
    )
    return path


def main():
    sdr = setup_willie(buffer_size=MEASUREMENT_SAMPLES)
    measurements = 0
    captures = 0
    pre_sample_count = int(PRE_SECONDS * FS)
    post_sample_count = int(POST_SECONDS * FS)
    pre_buffer = deque(
        maxlen=(pre_sample_count + MEASUREMENT_SAMPLES - 1) // MEASUREMENT_SAMPLES + 1
    )
    power_history = deque(maxlen=AVERAGE_COUNT)

    try:
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        threshold = calibrate(sdr, average=AVERAGE_COUNT)
        print(
            f"Willie listening; threshold: {threshold:.2f}; "
            f"detection averages {AVERAGE_COUNT} x "
            f"{MEASUREMENT_SAMPLES} samples; "
            f"captures will be saved in {CAPTURE_DIR}",
            flush=True,
        )
        armed = True

        while True:
            samples = _receive_samples(sdr)
            block_power = float(np.mean(np.abs(samples) ** 2))
            power_history.append(block_power)
            measurements += 1
            average_power = (
                float(np.mean(power_history))
                if len(power_history) == AVERAGE_COUNT
                else None
            )
            if average_power is not None and average_power > threshold and armed:
                before = (
                    np.concatenate(pre_buffer)
                    if pre_buffer
                    else np.array([], dtype=np.complex64)
                )
                before = before[-pre_sample_count:] if pre_sample_count else before[:0]
                capture = [before, samples]
                pre_buffer.append(samples)
                remaining = post_sample_count
                peak_power = block_power

                while remaining > 0:
                    after = _receive_samples(sdr)
                    after_power = float(np.mean(np.abs(after) ** 2))
                    peak_power = max(peak_power, after_power)
                    capture.append(after)
                    remaining -= len(after)
                    pre_buffer.append(after)
                    power_history.append(after_power)
                    measurements += 1

                captured_samples = np.concatenate(capture)
                path = _save_capture(
                    captured_samples, threshold, peak_power, len(before)
                )
                captures += 1
                armed = (
                    len(power_history) == AVERAGE_COUNT
                    and np.mean(power_history) <= threshold
                )
                print(
                    f"Willie saved detection {captures}: {path} "
                    f"(average power {average_power:.2f}, "
                    f"peak buffer power {peak_power:.2f})",
                    flush=True,
                )
            else:
                pre_buffer.append(samples)
                if average_power is not None and average_power <= threshold:
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

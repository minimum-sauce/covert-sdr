import argparse
import html
from pathlib import Path

import numpy as np


SAMPLES_BEFORE = 500
SAMPLES_AFTER = 500
WIDTH = 1100
HEIGHT = 600
MARGIN_LEFT = 85
MARGIN_RIGHT = 35
MARGIN_TOP = 65
MARGIN_BOTTOM = 65


def _read_peak_spectrum(path):
    with np.load(path, allow_pickle=False) as capture:
        iq = np.asarray(capture["iq"], dtype=np.complex64)
        sample_rate = int(capture["sample_rate"])

    if iq.size == 0 or sample_rate <= 0:
        raise ValueError(f"{path} has invalid IQ data or sample-rate metadata")

    peak_index = int(np.argmax(np.abs(iq)))
    start = max(0, peak_index - SAMPLES_BEFORE)
    end = min(iq.size, peak_index + SAMPLES_AFTER + 1)
    window = iq[start:end]

    taper = np.hanning(window.size)
    spectrum = np.fft.fftshift(np.fft.fft(window * taper))
    power_per_bin = np.abs(spectrum) ** 2 / np.sum(taper**2)
    power_db = 10 * np.log10(np.maximum(power_per_bin, 1e-12))
    frequencies = np.fft.fftshift(np.fft.fftfreq(window.size, d=1 / sample_rate))
    return frequencies, power_db, peak_index, window.size, sample_rate


def _render_svg(path, frequencies, power_db, peak_index, sample_count, sample_rate):
    plot_width = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_height = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    x_min = float(frequencies[0])
    x_max = float(frequencies[-1])
    y_min = float(np.min(power_db))
    y_max = float(np.max(power_db))
    padding = max((y_max - y_min) * 0.1, 1.0)
    y_min -= padding
    y_max += padding

    def x_position(value):
        return MARGIN_LEFT + (value - x_min) / (x_max - x_min) * plot_width

    def y_position(value):
        return MARGIN_TOP + (y_max - value) / (y_max - y_min) * plot_height

    points = " ".join(
        f"{x_position(float(x)):.1f},{y_position(float(y)):.1f}"
        for x, y in zip(frequencies, power_db)
    )
    grid = []
    for index in range(6):
        value = y_min + (y_max - y_min) * index / 5
        y = y_position(value)
        grid.append(
            f'<line x1="{MARGIN_LEFT}" y1="{y:.1f}" '
            f'x2="{WIDTH - MARGIN_RIGHT}" y2="{y:.1f}" stroke="#e2e8f0"/>'
            f'<text x="{MARGIN_LEFT - 12}" y="{y + 4:.1f}" '
            'text-anchor="end" font-size="12" fill="#334155">'
            f"{value:.1f}</text>"
        )

    x_ticks = []
    for index in range(5):
        value = x_min + (x_max - x_min) * index / 4
        x = x_position(value)
        x_ticks.append(
            f'<line x1="{x:.1f}" y1="{HEIGHT - MARGIN_BOTTOM}" '
            f'x2="{x:.1f}" y2="{HEIGHT - MARGIN_BOTTOM + 5}" stroke="#334155"/>'
            f'<text x="{x:.1f}" y="{HEIGHT - MARGIN_BOTTOM + 22}" '
            f'text-anchor="middle" font-size="12" fill="#334155">'
            f"{value / 1e3:.0f}</text>"
        )

    title = html.escape(path.stem)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<rect width="100%" height="100%" fill="white"/>
<text x="{WIDTH / 2}" y="28" text-anchor="middle" font-size="18" font-family="sans-serif" fill="#0f172a">{title}: power spectrum around peak</text>
<text x="{WIDTH / 2}" y="48" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#475569">{sample_count} IQ samples, peak at capture sample {peak_index}, sample rate {sample_rate} samples/s</text>
{''.join(grid)}
<polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="1.5"/>
<line x1="{MARGIN_LEFT}" y1="{MARGIN_TOP}" x2="{MARGIN_LEFT}" y2="{HEIGHT - MARGIN_BOTTOM}" stroke="#334155"/>
<line x1="{MARGIN_LEFT}" y1="{HEIGHT - MARGIN_BOTTOM}" x2="{WIDTH - MARGIN_RIGHT}" y2="{HEIGHT - MARGIN_BOTTOM}" stroke="#334155"/>
{''.join(x_ticks)}
<text x="{WIDTH / 2}" y="{HEIGHT - 18}" text-anchor="middle" font-size="14" font-family="sans-serif" fill="#334155">Frequency offset (kHz)</text>
<text x="22" y="{HEIGHT / 2}" text-anchor="middle" font-size="14" font-family="sans-serif" fill="#334155" transform="rotate(-90 22 {HEIGHT / 2})">Power per FFT bin (dB, relative IQ units)</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def plot_captures(capture_dir, output_dir):
    capture_paths = sorted(Path(capture_dir).glob("*.npz"))
    if not capture_paths:
        raise FileNotFoundError(f"No Willie .npz captures found in {capture_dir}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for capture_path in capture_paths:
        frequencies, power_db, peak_index, sample_count, sample_rate = (
            _read_peak_spectrum(capture_path)
        )
        output_path = output_dir / f"{capture_path.stem}.svg"
        _render_svg(
            output_path,
            frequencies,
            power_db,
            peak_index,
            sample_count,
            sample_rate,
        )
        print(f"Saved {output_path}")


def main():
    package_dir = Path(__file__).resolve().parent
    project_dir = package_dir.parents[2]
    parser = argparse.ArgumentParser(
        description="Plot the power spectrum around the peak in Willie IQ captures."
    )
    parser.add_argument(
        "--captures",
        type=Path,
        default=project_dir / "willie_captures",
        help="Directory containing Willie .npz capture files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=package_dir,
        help="Directory where SVG plots are written.",
    )
    args = parser.parse_args()
    plot_captures(args.captures, args.output)


if __name__ == "__main__":
    main()

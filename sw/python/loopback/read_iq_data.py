from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bob.rx_chain import RxChain
from common.rrc import matched_filter
from common.config import HEADER_BITS, MAX_PAYLOAD_BYTES, PREAMBLE_LEN


def main():
	capture_path = Path(__file__).resolve().parents[3] / "cap.npy"
	capture = np.load(capture_path)
	rx = RxChain()
	filtered = matched_filter(capture - np.mean(capture), rx.taps)
	start = rx.find_preamble(filtered)
	if start is None:
		print(f"No preamble found; metric {rx.last_metric:.2f}")
		return

	available_symbols = (len(capture) - 1 - start) // rx.sps + 1
	symbol_count = min(PREAMBLE_LEN + HEADER_BITS + 8 * MAX_PAYLOAD_BYTES, available_symbols)
	symbols = rx.sample_symbols(filtered, start, 0, symbol_count)
	phase = np.angle(np.sum(symbols[:PREAMBLE_LEN] * np.conj(rx.preamble)))
	symbols *= np.exp(-1j * phase)

	plt.subplot(311)
	plt.plot(np.abs(capture))
	plt.title("Capture magnitude")
	plt.subplot(312)
	plt.plot(filtered[start : start + 1200].real)
	plt.title("Matched filter from detected preamble")
	plt.subplot(313)
	plt.plot(symbols.real, "o-")
	plt.plot(rx.preamble.real, "x")
	plt.title("Received symbols and expected preamble")
	plt.show()


if __name__ == "__main__":
	main()
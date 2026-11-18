import glob, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common.config import FS, FC

os.makedirs("graphs", exist_ok=True)
CH = 4096   # chunk size used to locate the burst

for path in sorted(glob.glob("willie_captures/*.npz")):
    d = np.load(path)
    iq = d["samples"]
    fs = float(d["sample_rate"]) if "sample_rate" in d.files else float(FS)
    fc = float(d["fc"]) if "fc" in d.files else float(FC)

    # locate the strongest chunk (the burst)
    n = len(iq) // CH
    pwr = np.mean(np.abs(iq[: n * CH]).reshape(n, CH) ** 2, axis=1)
    p = int(np.argmax(pwr)) * CH
    burst = iq[max(0, p - 8 * CH): p + 8 * CH]
    noise = iq[:16384]

    fig, ax = plt.subplots(figsize=(9, 5))
    w = np.hanning(256)
    noise = iq[:16384]
    burst = iq[max(0, p - 8 * CH): p + 8 * CH]

  

    ax.psd(noise, NFFT=256, Fs=fs, Fc=fc, window=w, label="noise floor")
    ax.psd(burst, NFFT=256, Fs=fs, Fc=fc, window=w, label="burst")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v/1e6:.2f}")
    ax.set_xlabel("Frequency (MHz)")
    ax.legend()
    ax.set_title(os.path.basename(path))

    out = os.path.join("graphs", os.path.basename(path).replace(".npz", ".svg"))
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved {out}")
import glob, os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]            # covert-sdr/ (adjust if needed)
IN_DIR = ROOT / "willie_captures" / "parameter_sweep"
OUT_DIR = ROOT / "graphs" / "parameter_sweep"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CH = 4096


def load(path):
    d = np.load(path)
    return dict(
        iq=d["samples"], fs=float(d["sample_rate"]), fc=float(d["fc"]),
        thr=float(d["threshold"]), gain=float(d["tx_gain"]),
        msg=str(d["message"]), scale=float(d["amp_scale"]),
        rep=int(d["repeat"]), maxp=float(d["max_power"]),
        det=bool(d["detected"]),
    )


def split(iq):
    """Strongest chunk = burst, weakest chunk = noise (each 4 chunks wide)."""
    n = len(iq) // CH
    pwr = np.mean(np.abs(iq[: n * CH]).reshape(n, CH) ** 2, axis=1)
    pb, pn = int(np.argmax(pwr)) * CH, int(np.argmin(pwr)) * CH
    burst = iq[max(0, pb - 2 * CH): pb + 3 * CH]
    noise = iq[pn: pn + 4 * CH]
    return burst - burst.mean(), noise - noise.mean()


paths = sorted(glob.glob(str(IN_DIR / "*.npz")))
if not paths:
    raise SystemExit(f"No captures in {IN_DIR}")

rows = []
for path in paths:
    c = load(path)
    rows.append(c)
    burst, noise = split(c["iq"])

    fig, ax = plt.subplots(figsize=(9, 5))
    w = np.hanning(256)
    ax.psd(noise, NFFT=256, Fs=c["fs"], Fc=c["fc"], window=w, label="noise floor")
    ax.psd(burst, NFFT=256, Fs=c["fs"], Fc=c["fc"], window=w, label="burst")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v/1e6:.2f}")
    ax.set_xlabel("Frequency (MHz)")
    ax.legend(loc="upper right")
    msg = c["msg"] if len(c["msg"]) <= 25 else c["msg"][:22] + "..."
    ax.set_title(
        f"TX gain {c['gain']:.0f} dB | scale {c['scale']:g} | rep {c['rep']} | msg {msg!r}\n"
        f"max power {c['maxp']:.1f} vs threshold {c['thr']:.1f} | "
        f"{'DETECTED' if c['det'] else 'not detected'}", fontsize=10)
    stem = Path(path).stem
    fig.savefig(OUT_DIR / f"spectrum_{stem}.svg")
    plt.close(fig)
    print(f"Saved spectrum_{stem}.svg")

# ---- summary: max power / threshold vs TX gain, one colour per message ----
fig, ax = plt.subplots(figsize=(9, 5))
for msg in sorted({r["msg"] for r in rows}, key=len):
    sel = [r for r in rows if r["msg"] == msg]
    x = [r["gain"] for r in sel]
    y = [10 * np.log10(r["maxp"] / r["thr"]) for r in sel]
    ax.scatter(x, y, label=f"{len(msg)} chars", alpha=0.7)
ax.axhline(0, color="red", linestyle="--", label="Willie threshold")
ax.set_xlabel("TX gain (dB)")
ax.set_ylabel("Max buffer power / threshold (dB)")
ax.set_title("Willie's received power vs TX gain")
ax.grid(True)
ax.legend()
fig.savefig(OUT_DIR / "summary_power_vs_gain.svg")
plt.close(fig)
print("Saved summary_power_vs_gain.svg")
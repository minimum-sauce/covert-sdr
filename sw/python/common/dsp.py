import numpy as np


def rrc_taps(beta=0.35, span=10, sps=50):
    t = np.arange(-span * sps // 2, span * sps // 2 + 1) / sps

    h = (
        np.sin(np.pi * t * (1 - beta))
        + 4 * beta * t * np.cos(np.pi * t * (1 + beta))
    ) / (
        np.pi * t * (1 - (4 * beta * t) ** 2)
    )

    h[np.isclose(t, 0)] = 1 - beta + 4 * beta / np.pi

    if beta > 0:
        special = np.isclose(np.abs(t), 1 / (4 * beta))

        h[special] = (beta / np.sqrt(2)) * (
            (1 + 2 / np.pi) * np.sin(np.pi / (4 * beta))
            + (1 - 2 / np.pi) * np.cos(np.pi / (4 * beta))
        )

    return h / np.sqrt(np.sum(h**2))


def pulse_shape(symbols, taps, sps):
    upsampled = np.zeros(len(symbols) * sps, dtype=complex)
    upsampled[::sps] = symbols

    return np.convolve(upsampled, taps, mode="same")


def matched_filter(x, taps):
    return np.convolve(x, taps, mode="same")
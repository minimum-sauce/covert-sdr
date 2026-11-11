import numpy as np

def rrc_taps(beta=0.35, span=10, sps=50):
    t = np.arange(-span * sps // 2, span * sps // 2 + 1) / sps
    h = np.zeros_like(t)

    zero = np.isclose(t, 0)
    h[zero] = 1 - beta + 4 * beta / np.pi

    if beta > 0:
        special = np.isclose(np.abs(t), 1 / (4 * beta))

        h[special] = (beta / np.sqrt(2)) * (
            (1 + 2 / np.pi) * np.sin(np.pi / (4 * beta))
            + (1 - 2 / np.pi) * np.cos(np.pi / (4 * beta))
        )
    else:
        special = np.zeros_like(t, dtype=bool)

    regular = ~(zero | special)

    h[regular] = (
        np.sin(np.pi * t[regular] * (1 - beta))
        + 4 * beta * t[regular] * np.cos(np.pi * t[regular] * (1 + beta))
    ) / (
        np.pi * t[regular] * (1 - (4 * beta * t[regular]) ** 2)
    )
    
    return h / np.sqrt(np.sum(h**2))


def pulse_shape(symbols, taps, sps):
    upsampled = np.zeros(len(symbols) * sps, dtype=complex)
    upsampled[::sps] = symbols

    return np.convolve(upsampled, taps, mode="full")


def matched_filter(signal, taps):
    return np.convolve(signal, taps, mode="full")
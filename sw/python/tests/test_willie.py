import numpy as np
import pytest
from willie.willie_rx import measure_power, calibrate, detect


# Fake SDR: rx() returns AWGN with power 1, plus BPSK from Alice when she is on
class FakeSDR:
    def __init__(self, alice_db=None, n=10_000, seed=0):
        self.alice_db = alice_db
        self.n = n
        self.rng = np.random.default_rng(seed)

    def rx(self):
        noise = (self.rng.standard_normal(self.n) + 1j * self.rng.standard_normal(self.n)) / np.sqrt(2)
        if self.alice_db is None:
            return noise
        bits = self.rng.integers(0, 2, self.n)
        return noise + np.sqrt(10 ** (self.alice_db / 10)) * (2 * bits - 1)


# Check the measured power of pure noise is close to 1
def test_measure_noise_power():
    sdr = FakeSDR(seed=0)
    assert measure_power(sdr) == pytest.approx(1.0, rel=0.05)

# Check the threshold ends up just above the noise level
def test_threshold_above_noise():
    sdr = FakeSDR(seed=1)
    thr = calibrate(sdr)
    assert 1.0 < thr < 1.1

# Alice silent, Willie should almost never raise a false alarm
def test_no_false_alarms_when_silent():
    sdr = FakeSDR(seed=2)
    thr = calibrate(sdr)
    alarms = [detect(sdr, thr) for _ in range(200)]
    assert np.mean(alarms) < 0.02

# Alice strong (0 dB), Willie should always detect her
def test_detects_strong_signal():
    sdr = FakeSDR(seed=3)
    thr = calibrate(sdr)
    sdr.alice_db = 0
    assert all(detect(sdr, thr) for _ in range(50))

# Alice very weak (-40 dB), Willie should almost never detect her
def test_misses_weak_signal():
    sdr = FakeSDR(seed=4)
    thr = calibrate(sdr)
    sdr.alice_db = -40
    hits = [detect(sdr, thr) for _ in range(200)]
    assert np.mean(hits) < 0.05
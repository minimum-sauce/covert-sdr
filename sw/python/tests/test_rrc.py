
import numpy as np
import pytest

from common.rrc import rrc_taps, pulse_shape, matched_filter


# --------------------------------------------------
# Tests for rrc_taps()
# --------------------------------------------------

def test_rrc_taps_length():
    taps = rrc_taps(beta=0.35, span=10, sps=50)

    assert len(taps) == 501


def test_rrc_taps_are_symmetric():
    taps = rrc_taps(beta=0.35, span=10, sps=50)

    assert np.allclose(taps, taps[::-1])


def test_rrc_taps_have_unit_energy():
    taps = rrc_taps(beta=0.35, span=10, sps=50)

    assert np.sum(taps**2) == pytest.approx(1.0)


def test_rrc_taps_are_finite():
    taps = rrc_taps(beta=0.35, span=10, sps=50)

    assert np.all(np.isfinite(taps))


# --------------------------------------------------
# Tests for pulse_shape()
# --------------------------------------------------

def test_pulse_shape_upsamples_symbols():
    symbols = np.array([1, -1, 1])
    taps = np.array([1.0])
    sps = 4

    result = pulse_shape(symbols, taps, sps)

    expected = np.array([
        1, 0, 0, 0,
        -1, 0, 0, 0,
        1, 0, 0, 0
    ])

    assert np.allclose(result, expected)


def test_pulse_shape_output_length():
    symbols = np.array([1, -1, 1, 1, -1])
    sps = 50
    taps = rrc_taps(beta=0.35, span=10, sps=sps)

    result = pulse_shape(symbols, taps, sps)

    expected_length = len(symbols) * sps + len(taps) - 1

    assert len(result) == expected_length
    
    
# --------------------------------------------------
# Tests for matched_filter()
# --------------------------------------------------

def test_matched_filter_output():
    signal = np.array([1, 2, 3, 4, 5])
    taps = np.array([1, 2, 1])

    result = matched_filter(signal, taps)
    expected = np.convolve(signal, taps, mode="full")

    assert np.allclose(result, expected)


# --------------------------------------------------
# Test combined TX/RX RRC response
# --------------------------------------------------

def test_rrc_combined_response_has_low_isi():
    sps = 50
    span = 10
    taps = rrc_taps(beta=0.35, span=span, sps=sps)
    
    combined = np.convolve(taps, taps)
    centre = len(combined) // 2

    sample_indices = centre + np.arange(-span, span + 1) * sps
    symbol_samples = combined[sample_indices]

    assert symbol_samples[span] == pytest.approx(1.0)

    isi_samples = np.delete(symbol_samples, span)
    assert np.max(np.abs(isi_samples)) < 0.01


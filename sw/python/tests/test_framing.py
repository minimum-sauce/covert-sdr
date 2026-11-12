import numpy as np
import pytest
from alice.framing import build_packet, text_to_bits
from common.config import PREAMBLE_LEN, HEADER_BITS, MAX_PAYLOAD_BYTES
from common.dsp import preamble_bits, int_to_bits, bits_to_int

HEADER_START = PREAMBLE_LEN
PAYLOAD_START = PREAMBLE_LEN + HEADER_BITS

def test_packet_length():
    p = build_packet(text_to_bits("hello"))
    assert len(p) == PREAMBLE_LEN + HEADER_BITS + 5 * 8

def test_packet_starts_with_preamble():
    p = build_packet(text_to_bits("hello"))
    assert np.array_equal(p[:PREAMBLE_LEN], preamble_bits())

def test_header_contains_payload_length_in_bytes():
    p = build_packet(text_to_bits("hello"))
    assert bits_to_int(p[HEADER_START:PAYLOAD_START]) == 5

def test_payload_follows_header_without_padding():
    bits = text_to_bits("hello")
    p = build_packet(bits)
    assert np.array_equal(p[PAYLOAD_START:], bits)

def test_max_length_payload_is_accepted():
    p = build_packet(np.zeros(MAX_PAYLOAD_BYTES * 8, dtype=int))
    assert bits_to_int(p[HEADER_START:PAYLOAD_START]) == MAX_PAYLOAD_BYTES

def test_too_long_payload_raises():
    with pytest.raises(ValueError):
        build_packet(np.zeros((MAX_PAYLOAD_BYTES + 1) * 8, dtype=int))

def test_payload_not_whole_bytes_raises():
    with pytest.raises(ValueError):
        build_packet(np.array([1, 0, 1]))

def test_text_to_bits():
    expected = np.array([
        0, 1, 1, 1, 0, 1, 0, 0,   # 't' = 0x74
        0, 1, 1, 0, 0, 1, 0, 1,   # 'e' = 0x65
        0, 1, 1, 1, 1, 0, 0, 0,   # 'x' = 0x78
        0, 1, 1, 1, 0, 1, 0, 0,   # 't' = 0x74
    ])
    assert np.array_equal(text_to_bits("text"), expected)

def test_header_roundtrip():
    assert bits_to_int(int_to_bits(5, HEADER_BITS)) == 5
from common.rrc import rrc_taps

## SDR IP addresses
SDR1_IP = "ip:192.168.1.10"
SDR2_IP = "ip:192.168.2.1"

## TX and RX common parameters
FS = int(1e6)
FC = int(868e6)# 868Mhz
SYMBOL_RATE   = 100_000      # symbols/s

HEADER_BITS = 8

MODULATION    = "BPSK"       # "BPSK" or "QPSK"
ROLLOFF       = 0.35         # RRC roll-off
RRC_SPAN      = 10

PREAMBLE_LEN  = 64           # symbols
PREAMBLE_SEED = 1234         # Seed 
MAX_PAYLOAD_BYTES  = 128       
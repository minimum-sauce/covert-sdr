## SDR IP addresses
SDR1_IP = "ip:192.168.1.10"
SDR2_IP = "ip:192.168.2.1"

## TX and RX common parameters
FC = int(868e6)# 868Mhz
FS = int(2e6)
SYMBOL_RATE   = 100_000      # symbols/s
MODULATION    = "BPSK"       # "BPSK" or "QPSK"
ROLLOFF       = 0.35         # RRC roll-off
PREAMBLE_LEN  = 64           # symbols
PREAMBLE_SEED = 1234         # Seed 
PAYLOAD_BITS  = 1024         # Bits to send
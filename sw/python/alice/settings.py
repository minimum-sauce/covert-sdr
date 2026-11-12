FS          = 1_000_000       # Sampling frequency
TX_GAIN     = -40             # Gain when transmitting
RRC_SPAN    = 10              # filter length in symbols
DAC_SCALE   = 2**12 * 0.5     # digital amplitude, headroom below full scale
GAP_SYMBOLS = 10              # default silence around a packet
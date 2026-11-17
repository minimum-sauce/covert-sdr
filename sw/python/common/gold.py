import numpy as np

def gen_mls(n, taps, initial_state):
    state = list(initial_state)
    sequence = []

    for _ in range(2**n - 1):        
        sequence.append(state[-1])

        feedback = 0
        for tap in taps:
            feedback ^= state[tap - 1]

        state = [feedback] + state[:-1]

    return np.array(sequence)


def gen_gold_codes(n, seq1, seq2):
    gold_codes = []

    gold_codes.append(seq1)
    gold_codes.append(seq2)

    for shift in range(2**n - 1):
        shifted_seq2 = np.roll(seq2, shift)
        gold_code = np.bitwise_xor(seq1, shifted_seq2)
        gold_codes.append(gold_code)

    return gold_codes



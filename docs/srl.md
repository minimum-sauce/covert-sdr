# Square root law (SRL) experiment

## Background

The square root law (Bash, Goeckel, Towsley, 2013) states that over an AWGN channel, Alice can communicate covertly only if the average power per channel use falls as 1/√n, where n is the number of channel uses. With that power she can reliably send on the order of √n bits. With constant power, Willie's detection probability approaches 1 as n grows.

The law gives only proportionalities, so the constants are set by anchoring at a reference length `N_REF`:

- amplitude(n) = `A_REF` · (`N_REF` / n)^¼  (power ∝ 1/√n)
- bits(n) = `K_REF` · √(n / `N_REF`)

All parameters live in `common/srl_config.py`.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `N_SWEEP` | `[20_000, 80_000, 320_000, 1_280_000]` | Transmission lengths n (samples) to test |
| `N_REF` | `20_000` | Reference length where the scaling is anchored |
| `A_REF` | `3000` | Baseband amplitude at `N_REF`. Tune together with `TX_GAIN` |
| `K_REF` | `16` | Payload bits at `N_REF` |
| `TRIALS` | `30` | Transmissions per n (plus the same number of silent trials) |
| `INTERVAL` | `3.0` s | Time between transmissions. Must exceed n / `FS` plus capture margin |
| `TX_GAIN` | found by calibration | Alice's hardware gain in dB. Start the search at -50 to -80 |
| `BOB_RX_GAIN` | `30` | Bob's RX gain in dB. Lower it if the receiver clips |
| `WILLIE_RX_GAIN` | `40` | Willie's RX gain in dB. Fixed during a run, recalibrate if changed |
| `MODE` | `"srl"` | `"srl"` scales amplitude and bits with n. `"constant"` keeps the amplitude at `A_REF` (control run) |
| `SEED` | `1234` | Seeds payload generation. Each send uses `SEED + send_id` |

## Setting the operating point

1. Set `TX_GAIN` and `A_REF` so that at the smallest n, Willie's max power is about 1–3× his threshold. Use `srl_calibrate.py` (issue 11) and keep `A_REF` in the hundreds to a few thousand.
2. Run `MODE = "srl"` over `N_SWEEP`. Detection should stay roughly flat while the bits grow as √n.
3. Run `MODE = "constant"` with the same settings as a control. Detection should rise with n.

The result is the pair of curves, not any single value, so keep every other parameter identical between the two runs.
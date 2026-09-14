# Independent hidden-state linear audit — 2026-08-31

## Purpose

Independently reconstruct the frozen hidden-state candidate from the immutable Gate 3C arrays after discovering that the earlier packaged “active execution” bundle did not contain its claimed Gate 4 outputs.

This implementation was written separately from PR #27's compressed source bundle. It uses only:

- the accepted 151-state `A/B` model;
- the reconstructed step-ready `C_RZ` map;
- the frozen preparation inputs, bounds, slew, zero-command tail, alias constraints, target horizon, P6 recovery limits, and delay grid.

## Hidden-state preparation result

The preparation LP uses D1, D2, P4, P5, and P6 for 30 samples at `dt = 100 µs`, with `|ΔV| ≤ 2 V`, `|ΔV_k-ΔV_{k-1}| ≤ 0.5 V/sample`, and the final three commands fixed to zero.

It constructs a reachable half-difference state `h` satisfying:

- `C_RZ h = 0`;
- `C_RZ A_d h = 0`;
- zero dominant unstable left-mode coordinate.

The independently reconstructed optimum is:

| Quantity | Value |
|---|---:|
| Future Z at 3 ms | `2.138027646844e-6 m` |
| Decision R/Z alias residual | `1.36e-19 m` maximum |
| One-step R/Z alias residual | `3.22e-20 m` maximum |
| Dominant left-mode residual | `2.09e-15` |
| Equality residual | `6.88e-15` maximum in unscaled equations |
| Inequality violation | `1.11e-16` |
| Preparation peak voltage | `2.0 V` |
| Preparation peak slew | `0.5 V/sample` |
| Final-three-command maximum | `0 V` |

This exactly reproduces the previously predeclared `2.138 µm` linear hidden transient without relying on the missing historical Gate 4 result files.

## Frozen P6 recovery boundary

The recovery LP minimizes peak absolute Z over 30 samples using only P6, with `|ΔV| ≤ 0.1 V` and `|ΔV_k-ΔV_{k-1}| ≤ 0.05 V/sample`.

| Control delay | Predicted peak Z | Hold / controlled peak reduction |
|---:|---:|---:|
| 0 ms | `8.01e-20 m` | `2.67e13×` |
| 0.2 ms | `9.5833e-8 m` | `22.31×` |
| 0.5 ms | `5.0984e-7 m` | `4.194×` |
| 1.0 ms | `1.1048465e-6 m` | `1.935×` |
| 3.0 ms | `2.1380276e-6 m` | `1.0×` |

The near-zero immediate result is an exact-model linear cancellation and must not be interpreted literally outside the measured model-discrepancy band.

## Sign-specific action separation

The sign-correct immediate P6 waveform suppresses both `+h` and `-h` to numerical precision in the linear model. Assigning the opposite sign's waveform instead produces a peak of:

`4.276055293689e-6 m`

which is twice the no-action peak of:

`2.138027646844e-6 m`.

This verifies a strong sign-specific linear action separation for the frozen candidate. It does not establish that an output-only dynamic observer could not identify the sign from a longer diagnostic history.

## Independent optimum certificate

The hidden-state LP was solved independently with HiGHS dual simplex and interior point.

| Check | Dual simplex | Interior point |
|---|---:|---:|
| Target Z objective | `2.138027646844e-6 m` | `2.138027646844e-6 m` |
| Equality residual | `2.64e-16` | `9.85e-16` |
| Inequality violation | `1.11e-16` | `8.88e-16` |
| Stationarity residual | `6.23e-19` | `5.96e-19` |
| Primal–dual gap | `6.56e-19` | `5.72e-19` |
| Complementarity residual | `0` | `0` |

The two algorithms agree on the hidden state to approximately `2.06e-15` relative L2 and on the future-Z objective to `6.65e-19 m` absolute.

## What this establishes

- The frozen linear hidden-state construction is real, reachable under its stated preparation constraints, and independently reproducible.
- Its optimum has a machine-checkable primal/dual KKT certificate.
- The frozen linear model predicts a material latency boundary and opposite recovery actions for the aliased state pair.

## What remains unestablished

- nonlinear FreeGSNKE recovery;
- aliasing under the nonlinear physical outputs within the frozen tolerances;
- separation from all output-history observers or established reference-governor/MPC baselines;
- experimental MAST-U validation;
- a machine operating limit, reactor-safety claim, net energy, or sustainable fusion.

The next gate remains the predeclared prospective nonlinear experiment. No nonlinear threshold, preparation bound, actuator limit, or latency value is changed by this audit.

# Observer-aware protection redirection — 2026-09-01

## Verdict

**Fusion is not solved.** The prior hidden-state anticipatory-recovery candidate is falsified in its stated form. The surviving result is a corrected, observer-aware set-membership protection method for the accepted 151-state FreeGSNKE public MAST-U-like linear model.

This is a scientific redirection, not an operational checkpoint and not a fusion breakthrough.

## Why the prior candidate fails

The candidate pair was prepared using opposite active PF-coil voltage histories. Those commands would normally be known to the plasma-control system. In addition, before the nominal decision point the pair differed by as much as approximately `31.512 micrometres` in R and `254.152 micrometres` in Z.

The nominal construction predicted a `4.27606 micrometre` pair separation after 3 ms. Requiring the alias to survive recent R/Z history and six output maps calibrated from the frozen Gate 3C held-out checks reduced the future pair separation to:

| Required recent history | Future pair Z after 3 ms |
|---:|---:|
| 0 ms | `0.469713 micrometres` |
| 0.5 ms | `0.00128615 micrometres` |
| 1.0 ms | `0.000053931 micrometres` |
| 3.0 ms | `0 micrometres` |

The original information-separation claim therefore does not survive a fair history-aware, model-discrepancy-aware test.

## Observability consequence

The dominant unstable vertical mode projects directly into R/Z. The difficult uncertainty is instead stable/non-normal passive-current and profile/model-discrepancy structure.

At a 1 ms horizon, the accepted linear model gives the following basis-specific numerical observability results:

| Measurement suite | Machine rank | Effective rank at relative singular threshold 1e-8 |
|---|---:|---:|
| R/Z | 20 | 15 |
| R/Z plus active currents | 138 | 98 |
| R/Z plus active and plasma current | 144 | 102 |
| Previous suite plus 2 selected passive coordinates | 151 | 113 |
| Previous suite plus 32 selected passive coordinates | 151 | 151 |

These passive coordinates are model-basis coordinates, not a claim that two or thirty-two literal sensors solve the physical problem.

## Same-command unknown-profile preflight

A stronger formulation used identical active PF commands for both trajectories and allowed only bounded unknown evolution of `alpha_m`, `alpha_n`, and `paxis` to create state ambiguity. The exact compatible FreeGSNKE export is in a slightly different passive-mode basis, so this remains an engineering preflight rather than a final certificate.

| History | R/Z band | Maximum profile excursion per trajectory | Future pair Z after 3 ms |
|---:|---:|---:|---:|
| 0.6 ms | +/-1 micrometre | +/-0.1% | `0.925413 micrometres` |
| 0.6 ms | +/-1 micrometre | +/-1% | `1.19592 micrometres` |
| 1.0 ms | +/-1 micrometre | +/-0.1% | `0.848825 micrometres` |
| 1.0 ms | +/-1 micrometre | +/-1% | `0.994198 micrometres` |
| 3.0 ms | +/-1 micrometre | +/-0.1% | `0.255579 micrometres` |
| 3.0 ms | +/-1 micrometre | +/-1% | `0.257766 micrometres` |

## Correct set-membership semantics

For an uncertain output-map family, the feasible future-output set is the **union** over admissible maps. The global protection diameter must therefore allow the two endpoint hypotheses to use different admissible maps while sharing overlapping measurement histories. Earlier same-map or map-intersection calculations were not accepted as fail-safe bounds.

The corrected cross-map calculation used:

- 0.6 ms diagnostic cadence;
- 3 ms history;
- R/Z uncertainty of +/-1 micrometre;
- effective-current and plasma-current uncertainty of +/-3 A;
- profile excursions of +/-0.1% and +/-1%;
- every ordered pair of the six Gate 3C-calibrated output maps;
- independent HiGHS dual-simplex and interior-point solutions.

## Held-out synthetic coverage result

| Profile excursion | Cross-map global diameter | Worst ordered map pair | Held-out interval coverage | Median interval width | Maximum interval width |
|---:|---:|---|---:|---:|---:|
| +/-0.1% | `4.20732 micrometres` | deterministic dense direction to P6 coordinate | `100%` | `2.84957 micrometres` | `3.60201 micrometres` |
| +/-1% | `5.68918 micrometres` | dominant unstable direction to deterministic dense direction | `100%` | `5.37154 micrometres` | `5.56367 micrometres` |

All 40 bounded held-out synthetic trajectories were covered. Every interval width remained below its precomputed global diameter. The largest dual-simplex/interior-point diameter disagreement was `4.974e-14 micrometres`.

These numerical widths are controlled by parameterised bands and cannot be used as MAST-U operating limits.

## Prior-art boundary

Passive-current observers, H-infinity eddy-current observers, extended Kalman equilibrium estimators, virtual-circuit inference, maximum-controllable-displacement methods, reference governors, and real-time MAST-U shape control already exist. The surviving increment is not that passive currents matter or that observers are useful.

The research target is now a prospective **protection-level layer** that asks whether the observer, model-discrepancy family, diagnostic cadence, delivered-current uncertainty, profile evolution, voltage/slew limits, latency, and shared PF authority leave too much worst-case vertical ambiguity for a recovery decision.

## Required next gate

1. Replace parameter bands with released MAST-U PCS signal histories, reconstruction residuals, filtering delays, delivered-current uncertainty, and profile-evolution estimates.
2. Replay Kalman, H-infinity, and set-membership estimators on identical held-out shots or redistribution-safe shot exports.
3. Freeze safe/unsafe and recovery predictions before nonlinear FreeGSNKE and experimental outcomes.
4. Measure false-safe, false-unsafe, latency, PF voltage, slew, and retained shape-authority consequences.
5. Carry only a validated engineering change into PROCESS/FUSE availability and power-balance analysis.

## Claim boundary

This is machine-derived linear software-model analysis with parameterised uncertainty and held-out synthetic coverage. It is not experimental MAST-U validation, a controller certification, an ITER result, reactor-safety evidence, net energy, or sustainable fusion.

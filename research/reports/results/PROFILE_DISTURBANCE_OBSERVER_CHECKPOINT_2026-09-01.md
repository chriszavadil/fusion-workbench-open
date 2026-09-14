# Profile-disturbance observer checkpoint — 2026-09-01

## Scientific disposition

The earlier active-coil-history hidden-state candidate is rejected. Its opposite preparation commands were known to the plasma control system, and its recent R/Z history did not remain genuinely aliased under the stronger diagnostic-history and output-map stress tests. It is not a breakthrough candidate.

The replacement branch uses identical commanded PF voltages and bounded, initially unknown plasma-profile evolution through the three profile-rate channels exposed by the accepted FreeGSNKE example10 linearisation.

## Machine-derived linear result

For the exact 151-state public MAST-U-like model and a 3 ms diagnostic history:

- R/Z, all 12 active-coil currents, and plasma current still leave approximately `1.10 micrometres` of future vertical ambiguity at the calibration-scale profile envelope;
- one selected passive-current estimator state reduces that to approximately `0.11 micrometres`;
- two selected passive-current estimator states reduce the exact-model ambiguity to approximately `0.001 micrometres`.

The dominant unstable vertical mode itself is visible in R/Z. The unresolved component is stable or non-normal passive-current structure excited by profile evolution.

## Independent checks completed locally

- exact unknown-input linear-program reconstruction;
- recent-history and diagnostic-noise sweeps;
- prospective nonlinear profile trajectories with identical PF commands;
- a separately frozen held-out recovery contract;
- a second profile-rate waveform replication when permitted by the held-out gate;
- batch unknown-input reconstruction with training-only regularisation selection;
- an independent augmented-process Kalman filter;
- a profile-envelope, output-map-discrepancy, diagnostic-noise, and latency architecture boundary.

The complete numerical artifacts remain claim-bounded. A held-out software-model pass, where present, is not experimental validation. A failed gate rejects its candidate without threshold relaxation.

## Prior-art boundary

The following are treated as established and cannot be claimed as novel:

- vertical-position control;
- passive-vessel or eddy-current modelling;
- state observers and Kalman filtering;
- current-profile estimation and profile-aware VDE avoidance;
- maximum-controllable-displacement and watchdog logic;
- constrained MPC/reference governors;
- the general fact that passive-current state matters beyond instantaneous plasma position.

The potentially useful increment is narrower: a prospectively tested, machine-derived joint boundary among profile evolution, diagnostic history, passive-state estimation, measurement noise, latency, voltage, slew, and shared PF authority that changes a concrete engineering decision.

## Engineering rule under test

For a declared future-Z uncertainty budget `B`, profile envelope `p`, architecture coefficient `k`, and additional latency `L`, the current linear design envelope is

```text
epsilon_remaining = B / (1.15 * exp(277.386313821 * L)) - k * p
```

where `L` is in seconds, Z quantities are in micrometres, and the factor `1.15` carries the Gate 3C engineering-grade output-map discrepancy. A negative result means the architecture cannot meet the declared budget even before adding nonlinear and experimental uncertainty.

## Next gates

1. Import and independently review the complete held-out nonlinear and replication artifacts.
2. Compare the passive-state requirement against established unknown-input/Kalman, watchdog/MCD, PD, and constrained-control baselines on identical cases.
3. Repeat on an independently matched equilibrium or experimental shot.
4. Translate only a surviving requirement into diagnostic latency, PF voltage/slew/shared-authority, disruption avoidance, availability, and plant power-balance consequences.

## Claim boundary

Fusion is not solved. No current result establishes experimental MAST-U performance, controller certification, a machine operating limit, ITER performance, reactor safety, net energy, or sustainable fusion.

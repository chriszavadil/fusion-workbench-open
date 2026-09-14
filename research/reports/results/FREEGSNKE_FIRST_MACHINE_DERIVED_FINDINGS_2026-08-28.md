# First machine-derived FreeGSNKE findings — 2026-08-28

## Evidence source

- Upstream: `FusionComputingLab/freegsnke`
- Tag: `v3.0.1`
- Commit: `f776e908c8c333411f9824cbcfed674fafff8dfd`
- Connected compatibility run: GitHub Actions run `33181821964`
- Rebased confirmation run: GitHub Actions run `33195784629`
- Source notebook: `examples/example10 - growth_rates.ipynb`
- Configuration scope: public FreeGSNKE MAST-U-like configuration

## Reproduction result

Three exact FreeGS4E versions produced a green, unmodified upstream suite and validated export:

| FreeGS4E | Upstream suite | Export | Validation | Dominant growth rate |
|---|---:|---:|---:|---:|
| 0.12.0 | 10 passed, 4 skipped | pass | pass | 277.424209 s^-1 |
| 0.13.0 | 10 passed, 4 skipped | pass | pass | 277.375670 s^-1 |
| 0.13.1 | 10 passed, 4 skipped | pass | pass | 277.386314 s^-1 |
| 0.14.0 | 2 failed, 5 passed, 4 skipped, 3 errors | not run | not run | unavailable |

The 0.14.0 failure is preserved without a source patch. Its repeated upstream error is an `AttributeError` involving `ConstrainPaxisIp.inputs` during profile copying.

## Exported model

The connected artifact contains:

- 151 states;
- 12 active-PF voltage inputs;
- 138 retained passive normal modes;
- one scaled plasma-current state;
- three profile-rate disturbance inputs;
- a two-output current-centre R/Z Jacobian;
- one unstable eigenvalue near 277.4 s^-1.

The exported continuous-time equation is

```text
M x_dot + x = F_voltage u - F_profile theta_dot
A = -M^-1
B = M^-1 F_voltage
E = -M^-1 F_profile
```

The numerical artifacts satisfy the defining identities to floating-point precision, and the exported dominant eigenvalue agrees with the upstream growth-rate calculation.

## Immediate physical timing implication

Using the 0.13.1 result, the open-loop unstable mode has approximately:

- e-folding time: 3.605 ms;
- doubling time: 2.499 ms;
- tenfold-amplification time: 8.301 ms.

Pure open-loop modal amplification is approximately:

| Delay | Amplification |
|---:|---:|
| 1 ms | 1.320x |
| 3 ms | 2.298x |
| 5 ms | 4.003x |
| 10 ms | 16.020x |

These figures describe the exported linear operating point. They are not yet a maximum-controllable-displacement result or a hardware requirement.

## Validation insight: compare physical dynamics, not raw passive coordinates

Raw `A/B/E` matrices differ substantially among the three compatible FreeGS4E versions because the retained passive-mode coordinates change. However, geometry hashes, labels, growth rates and R/Z input-output transfer functions remain close.

Therefore dependency/model-discrepancy audits must prioritize basis-invariant quantities:

- unstable growth rates;
- physical R/Z transfer functions;
- unstable modal residues;
- invariant-subspace alignment;
- matched physical rollouts;
- nonlinear equilibrium outputs.

Raw Frobenius differences between passive-coordinate realizations must not be interpreted directly as physical model uncertainty.

## Hypotheses generated, not conclusions

The linear export indicates that passive-conductor states make large contributions to the unstable mode and that the P6 voltage channel has the strongest projected vertical modal authority at this operating point. These observations justify held-out nonlinear tests; they do not yet justify coil redesign or a controller claim.

## Current evidence level

This result advances the project from surrogate-only work to a reproducible **machine-derived public MAST-U-like linear model**. It does **not** establish:

- experimental MAST-U validation;
- nonlinear recovery performance;
- an ITER engineering prediction;
- reactor safety;
- quantum advantage;
- net-electric or sustainable fusion.

## Next required evidence

1. independent-run repeatability using basis-invariant comparisons;
2. exact comparison with FreeGSNKE's implicit-Euler time stepper;
3. held-out R/Z finite differences;
4. small linear-versus-nonlinear free-boundary rollouts;
5. frozen prospective predictions from prior-art baselines and any candidate monitor;
6. independent TokaMaker/Open FUSION Toolkit cross-check.

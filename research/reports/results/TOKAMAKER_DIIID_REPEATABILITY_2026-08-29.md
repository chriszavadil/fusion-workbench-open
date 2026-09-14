# TokaMaker v26.6 DIII-D repeatability — strict gate result

## Status

**FAIL under the predeclared absolute-output tolerances.**

Both independent runners individually completed the exact official equilibrium, linear-stability calculation and 40-step VDE evolution successfully. Source, wheel, notebook, mesh, input equilibrium, original cell source, array shapes, time-history length and source cleanliness checks passed.

The comparison failed only the two frozen maximum-absolute-output checks:

| Quantity | Observed cross-run difference | Frozen limit | Result |
|---|---:|---:|---|
| Dominant growth rate | `1.7917045625e-10 s^-1` | `1.0e-6 s^-1` | pass |
| Time grid | `8.0664641633e-16 s` | `1.0e-15 s` | pass |
| Official timestep | `2.0017082610e-17 s` | `1.0e-15 s` | pass |
| Relative-axis-Z maximum absolute difference | `1.1635496677e-8 m` | `1.0e-9 m` | **fail** |
| Relative-axis-Z relative L2 difference | `8.1975703256e-9` | `1.0e-8` | pass |
| Unstable-mode maximum absolute difference | `1.0775169201e-8` | `1.0e-8` | **fail** |
| Unstable-mode relative L2 difference | `8.6083590754e-10` | `1.0e-8` | pass |

The maximum magnetic-axis difference is approximately `11.64 nm`. This is tiny relative to the simulated displacement, but the threshold was frozen before execution and is not relaxed afterward.

## Generated equilibrium output

The two generated `g192185_tokamaker` gEQDSK files have different hashes. Direct comparison shows floating numerical field differences rather than a simple timestamp-only difference. Their exact hashes are retained:

- replicate 1: `4484d5f8c2ed39e9a6609f908448b7eb132b8d431565701c86b4a72dff3a7be6`
- replicate 2: `d47365b4de9f2c3f7b611b1e3909666cbd3f19ee9029a834482b470d47edaa07`

## Interpretation

The exact case is highly repeatable in its dominant eigenvalue and physical traces, but it is not byte-identical and did not satisfy the deliberately severe maximum-absolute output thresholds. The observed variation is retained as a measured numerical floor for this runner/package configuration.

This result is useful rather than a dead end:

1. future TokaMaker comparisons must not assume bitwise reproducibility;
2. cross-solver disagreement below this measured floor cannot be treated as physical-model disagreement;
3. the complete first and second artifacts remain available for convergence and CPU/BLAS sensitivity studies;
4. no threshold was loosened and no replica was discarded.

## Next action

Use scale-aware physical quantities and an explicit numerical-error budget for matched FreeGSNKE/TokaMaker comparisons. A new criterion may be designed prospectively for a different benchmark version, but this v1 gate remains failed permanently.

## Claim boundary

This is numerical-repeatability evidence for one official simulated DIII-D case. It is not experimental validation, a matched FreeGSNKE result, controller performance, ITER performance, reactor safety evidence or sustainable fusion.

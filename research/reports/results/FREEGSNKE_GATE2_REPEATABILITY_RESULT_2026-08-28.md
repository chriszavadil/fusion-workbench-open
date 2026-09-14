# FreeGSNKE Gate 2 repeatability and time-step result — 2026-08-28

## Status

**PASS under the predeclared controlled numerical environment.**

This result validates repeatable export and time-discretisation consistency for the public MAST-U-like operating point. It does not validate nonlinear plasma recovery, experimental MAST-U behavior, ITER performance, or reactor safety.

## Frozen source and dependency cell

- FreeGSNKE tag: `v3.0.1`
- FreeGSNKE commit: `f776e908c8c333411f9824cbcfed674fafff8dfd`
- FreeGS4E: `0.13.1`
- h5py: `3.13.0`
- Shapely: `2.0.7`
- Python: `3.10`
- Runner CPU: AMD EPYC 7763
- NumPy: `1.26.4`, OpenBLAS 0.3.23.dev, HASWELL kernel

Controlled environment:

```text
PYTHONHASHSEED=0
OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
MKL_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1
BLIS_NUM_THREADS=1
OMP_DYNAMIC=FALSE
```

## Replication design

- two independent GitHub-hosted runners;
- two complete machine exports per runner;
- thirty held-out state/forcing/timestep trials per export;
- single-step and multi-substep implicit-Euler cases;
- thresholds frozen before execution.

## Result

All four controlled exports were byte-identical:

```text
numeric bundle SHA-256:
c4afba12c2289d99c15b2fad9596b8bb7e5b89a7343f39b332353b5d74737bfa
```

All identity, label, geometry, growth, transfer-function and unstable-residue comparisons were exactly equal across the four exports.

### Growth result

```text
dominant unstable growth rate = 277.46192409096403 s^-1
e-folding time                = 3.604098 ms
```

### Native stepper equivalence

Across each frozen 30-trial suite:

```text
worst FreeGSNKE stepper vs native M/F formula relative L2
= 7.0313e-15

worst FreeGSNKE stepper vs exported A/B/E formulation relative L2
= 1.9522e-14
```

The largest case used a 3 ms full step split into twelve 0.25 ms internal implicit-Euler steps.

## Preserved uncontrolled-run finding

Before numerical thread control was frozen, two otherwise identical runners produced:

```text
277.3756696557428 s^-1
277.3863138206694 s^-1
```

with a 0.0106442 s^-1 cross-run difference and up to 0.5976% difference in the sampled high-frequency R/Z transfer response. Those two outputs were bit-identical to two earlier compatibility-run outputs, supporting a discrete environment/kernel effect rather than stochastic corruption.

The controlled value differs from the two uncontrolled values by approximately 273–311 ppm. Therefore:

> Reproducibility requires preserving the numerical thread/kernel environment, and numerical-environment sensitivity must be included in later model-discrepancy studies rather than silently ignored.

The strict original thresholds were never relaxed. The uncontrolled failure and two intermediate dependency-harness failures remain preserved in PR #16.

## Scientific interpretation

Gate 2 establishes:

1. the exported 151-state equation is internally consistent with FreeGSNKE's own implicit-Euler integrator;
2. the machine export is repeatable across independent runners when the numerical environment is controlled;
3. the earlier cross-run disagreement is environmental numerical sensitivity, not a sign error in `A/B/E`;
4. raw default-run outputs are not sufficiently provenance-complete for safety-critical use.

Gate 2 does **not** establish:

- that the linearisation accurately predicts a nonlinear free-boundary trajectory;
- that the R/Z Jacobian is correct away from the operating point;
- that the public configuration represents a particular MAST-U discharge;
- that any controller can recover the plasma;
- or that the control design is relevant to ITER or a power plant.

## Next gate

Before any new control theorem uses this model:

1. held-out finite-difference validation of the R/Z current-centre Jacobian;
2. small linear-versus-nonlinear free-boundary rollouts;
3. finite-difference, equilibrium-tolerance, grid and numerical-environment sensitivity;
4. independent TokaMaker/Open FUSION Toolkit reproduction;
5. prospective baseline and candidate predictions frozen before nonlinear outcomes.

# Candidate-linked equilibrium and EC interface

Read the dated `EC_EQUILIBRIUM_INTERFACE_2026-09-16.md` report before interpreting any arrays. These are four smooth fixed-boundary constructions, not a matched diverted reactor or experimentally reconstructed equilibrium. The scalar-q compatibility screen fails; no candidate achieved current or power is certified.

## Numerical evidence
`EXACT_INPUT.json` preserves original source hashes, scalars and all201 archived pressure/effective-charge samples. Each `runs/<case>` directory contains the successful numerical record, full finite-element points/connectivity/flux/pressure/F fields in `SOLUTION.npz`, all traced contour vertices, every saved enclosed-volume mapping iteration and the exported gEQDSK. COCOS7 is explicit; do not silently feed another convention into a ray code.

The source parameterization uses thermal-pressure shape with an explicitly assumed isotropic co-shaped fast component, and an iterative normalized-volume profile mapping. Two FF′ exponents and two mesh sizes are construction/refinement sensitivities, not uncertainty distributions. The complete native results are retained; display-only contour sampling does not remove canonical evidence.

## Reproduce a construction
Use a separate copy of this directory without its `equilibria` output directory. The tested Linux environment used Open FUSION Toolkit26.9, NumPy2.5.3 and SciPy1.18.1. The program creates a new case directory and refuses to overwrite an earlier run. For each pair execute a bounded invocation, for example:

```sh
timeout 180 python solve_equilibrium.py 0.18 1
timeout 180 python solve_equilibrium.py 0.18 2
timeout 180 python solve_equilibrium.py 0.09 1
timeout 180 python solve_equilibrium.py 0.09 2
```

The script sets one numerical thread, uses the exact input/admission and preserves all mapping iterations. Check both `numerically_solved` and `export_completed`, target integral errors, mapping convergence and the q compatibility flag. A completed numerical solve is not physical qualification. The current driver uses the installed documented `nl_tol`, equilibrium-returning `solve`, independent contour-volume integration and supported COCOS7 export. Earlier failed API/export attempts are summarized in `IMPLEMENTATION_FAILURES.json`; raw logs remain private.

## Canonical GENRAY reference
`GENRAY_REFERENCE.json` contains all343 recorded points and source-native scalar outputs from the existing ITER EC reference, with full input/NetCDF/binary hashes. It is a different plasma and is not evidence of candidate current drive or agreement with experiment. The original upstream test input is `00_Genray_Regression_Tests/genray.dat_CANONICAL_2004_ITER_TEST_one_ray`, with `g521022.01000`, at pin`ee443d16e5aaf9bc7227fb3e95581e3ba374df89`.

A project-local Giza library required changing only the plotting device fromVCPS toCPS; `GENRAY_GRAPHICS_ADAPTER.json` records this and both source hashes. GENRAY's GPL-3.0-or-later source/binary and graphics libraries are not distributed here. `export_reference_ray.py` documents the extraction but assumes the original local result layout; it is not an installer. New reproduction must verify the upstream input/equilibrium, physics settings and normal ray termination, not just process exit zero.

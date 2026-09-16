# Inverse current-budget diagnostic

Read `research/reports/results/INVERSE_CURRENT_BUDGET_2026-09-16.md` before using the numbers. This is a new current-budget calculation on four previously unqualified fixed-boundary equilibria. It is not a newly optimized reactor, a complete self-consistent current solution, achieved microwave drive or measured electricity.

## Reuse and original authors
Redl, Angioni, Belli, Sauter and collaborators supply the underlying neoclassical model; Open FUSION Toolkit/TokaMaker supplies the implementation, trapped-particle calculation and equilibrium solver. Original candidate profiles and systems equations come from UKAEA PROCESS and its credited contributors, including James Morris for the inherited generic tokamak input. Original Workbench integration code is MIT; no upstream solver/library distribution is bundled or relicensed.

The original systems output already had other correlations that predicted larger bootstrap fractions. `EXISTING_SCALING_COMPARISON.json` retains that fact. The new work is a spatial/current-budget diagnostic on these particular fields, not discovering that correlations disagree or selecting the most favorable one.

## Replay arithmetic without new scientific execution
Run `python verify_budget.py` in this directory with compatible NumPy/SciPy. It checks all four401-point files, their digests, independently recomputed integrals, the complete flux-convention reversal, numerical refinement and retained limits. It does not rerun an equilibrium. `CURRENT_FIELDS.npz` contains every sampled kinetic/geometry/current value used by the visual projection. `PROFILES.json` preserves shell averages and all returned model coefficients. No display subsampling deletes evidence.

`RESULT.json` includes the old field hash, source/kinetic/driver hashes, restored q/current/energy checks, the interior budget and unresolved qualification. The awkward historical boolean `no_countercurrent_profile_possible_on_proxy` means a nonnegative residual exists on the sampled interval; its value is derived from the separately preserved opposing-current integral. It does not prove an actuator can produce that residual. Initial negative sign-diagnostic samples are deliberately retained, not the final physical current estimate.

## Optional new bounded reproduction
Use the recorded Linux environment with `openfusiontoolkit==26.9`, NumPy and SciPy. The parent Workbench checkout must contain the original `ec_equilibrium_2026_09_16` module. Run a single explicitly chosen case into a new output directory:

```sh
python reproduce.py --case dx0.09_ff1_v6 --output NEW_RESULT_DIRECTORY
```

Allowed cases are the two mesh sizes0.18/0.09 and FF-prime exponents1/2. The wrapper refuses an existing output directory, sets a180-second child timeout and uses the unchanged original input/admission. The original exact drivers are `current_budget.py` and `finish_budget.py`; the portable wrapper overrides their local-layout constants rather than modifying scientific inputs. The wrapper itself is new and is not claimed to have undergone an extra full reproduction in this continuation.

No sign, bootstrap amplitude, induction amplitude or plasma target is fitted to the desired result. Restore the original fields to the declared tolerances first; failures remain failures. The forward equilibrium object is reconstructed once to recover required geometry coefficients that the old export did not include; that reconstruction is reuse, not a new design search.

Only flux0.01–0.98 is quantitatively assessed. Bootstrap outside this interval is not filled in. An optimistic lower bound placing all original inductive current inside the interval is not a new full microwave-current target. Plasma-current closure, the diverted boundary, fast-particle current, source deposition, stability and control remain unqualified. The power dashboard does not receive a new MW point from this calculation.

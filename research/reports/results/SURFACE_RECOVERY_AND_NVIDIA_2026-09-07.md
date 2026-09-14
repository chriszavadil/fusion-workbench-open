# Surface release, usable fuel, and the NVIDIA toolkit

## What actually ran

This continuation adds an explicit, finite surface-escape step and a distinct downstream recovery stage to a ceramic diffusion sensitivity. There are 48 declared cases, eight mesh-refinement cases, 12 groups of analytical spectral comparisons, and two adaptive-ODE cross-checks. The local assembled audit suite passed **194 tests: 165 reproduced and 29 new, no failures or skips**. The main study took 0.346 seconds in the recorded single-thread run. This is not every test in the GitHub repository.

No NVIDIA model inference, GPU job, full PROCESS optimization, OpenMC transport or physical experiment ran. No new data arrived in the two original outreach threads checked during this turn. No paid resources or automatic monitoring were created.

## Toolkit assessment

The installed BioNeMo Agent Toolkit's skill resources are visible in this conversation. The cuEquivariance skill was read. The biological folding, docking and sequence-design skills do not directly solve this ceramic-fuel-release problem. cuEquivariance can accelerate supported geometric neural networks, including machine-learning interatomic potentials used for atomistic materials calculations. NVIDIA's documentation and MACE's own integration documentation establish that use case, not performance on this project [1-3].

A meaningful later use would require a validated material model covering the relevant chemistry, defects, surfaces and temperatures, suitable reference data, compatible software and an actual GPU. Installation of agent instructions does not supply those prerequisites. The active execution environment has CPU-only PyTorch, reports zero GPUs, and has no cuEquivariance library installed. PROCESS/OpenMC are also absent; direct DNS queries for GitHub/PyPI/Zenodo still fail. This does not prove anything about the user's other computers or Azure account.

The runtime speedup of a GPU library must not be confused with a physical improvement in a material's diffusion coefficient.

## Physical motivation and the boundary on this calculation

Kulsartov et al. discuss coupled diffusion and surface desorption, and note that several parameter combinations can describe their data. Their effective diffusion law uses an activation energy of 20 kJ/mol, while their desorption fit uses 62 kJ/mol. These are phenomenological fits, not an independently qualified HCPB material model [4]. Another published biphasic-ceramic model already includes interface transfer; generic coupled-release modeling is not novel [5].

The present test is a **different, explicitly linearized model family**: an isotropic sphere with a linear Robin boundary, `-D dc/dr = h c_surface`. Here h has units m/s. It is NOT the paper's nonlinear K, whose units are m2/(mol s). We borrow only the activation-energy contrast to motivate a sensitivity. We do not copy K0 into h, fit the paper's curves, or claim to reproduce the experiment.

At the reference hot temperature, dimensionless surface-to-diffusion ratios (Biot numbers) of 0.1, 1, 10 and 100 are deliberately assumed. Other declared inputs are a 750-micrometre **diameter**, a 90-minute recovery interval, hot/cold levels of 665/100 C, and downstream times 0, 6 minutes or 4 hours. These are scenarios, not measured operating histories or reactor specifications. Extrapolation at the cold endpoint is particularly uncertain.

Initial material inventory is normalized to one unit with each model's fully developed hot uniform-generation concentration profile. Generation then stops. Downstream processing begins empty, so this tracks an isolated material cohort, not an already-operating full fuel loop. Radioactive decay, isotope chemistry, trapping, evolving porosity, permanent recovery loss and plant energy costs are excluded from this short recovery test.

## 1. Fast diffusion alone may be the wrong improvement target

In the stated spherical model, the mean residence time of a uniformly generated atom is

    tau = a^2/(15 D) + a/(3 h).

The first contribution is bulk diffusion, the second surface escape. An independent finite-volume solution reproduces this identity with second-order spatial convergence.

Holding surface behavior fixed, increasing D by tenfold yields the following mean-release speedups at the hot reference temperature:

| Assumed hot Biot number | Actual mean-release speedup for 10x D |
|---:|---:|
| 0.1 | 1.018x |
| 1 | 1.176x |
| 10 | 2.500x |
| 100 | 7.000x |

These are **conditional physical sensitivities**, not achieved materials improvements and not GPU-computing speedups. They explain why an atomistic study should not optimize bulk diffusion alone before the surface bottleneck has been constrained.

## 2. Material release is not fuel ready for reuse

For the assumed Biot-10, held-hot case, approximately **71.17%** of the isolated material inventory leaves the ceramic within 90 minutes. With the assumed 4-hour downstream stage, only **14.32%** has reached the available-fuel state by that time; approximately **56.85%** remains in processing. With an instantaneous stage the full released amount is available; with a 6-minute stage approximately 68.67% is available.

A deliberately declared test that requires half the original cohort to be available would pass an incorrect release-only check and fail the actual availability check. This is a model counterexample, not a real plant reserve limit. Downstream residence time and physical loss/yield must be measured separately.

## 3. The order of temperature exposure matters

Two artificial schedules spend 45 minutes at each temperature, in opposite order. Their total time at each temperature and their integrated diffusion coefficients are identical. The same initial material profile is used for both.

At 256 radial cells, Biot 10 and a 6-minute downstream stage:

| Schedule | Left material by 90 min | Available by 90 min |
|---|---:|---:|
| Hot then cold | 47.4114% | 47.4088% |
| Cold then hot | 47.8202% | 43.1625% |

Thus the schedule with slightly MORE material released has LESS fuel available at the comparison time. The difference in availability is approximately **4.25 percentage points**. This does not show an optimal warm-hold strategy: temperature transitions are imposed and their heating/cooling costs are not modeled.

The earlier diffusion-clock shortcut remains valid for its original perfect-sink, spatially uniform-temperature scope. It cannot be carried over unchanged to this wider model family. Different activation energies make the material operators depend on temperature in different proportions. Even when equal activation energies are imposed as a control, making the material profiles identical between the two orders, downstream timing still changes availability.

## Numerical verification

The largest inventory-conservation error in the 48-case study is 4.73e-14 of initial inventory. Direct matrix exponentials and adaptive Radau integration agree within 5.72e-14 at the same spatial mesh. These are time-integration checks of the same model, not independent physical validation.

An independently assembled analytical Robin-sphere eigenfunction series checks constant-temperature behavior. At 128 cells, the largest discrepancy in material remaining fraction is 1.66e-5 over the checked times and Biot values, decreasing with refinement. For the schedule comparison, refining from 128 to 256 cells changes the release-order difference by less than 4e-6 in fractional units. Equating the activation energies eliminates the material-order effect to numerical precision, as expected.

## Next gate

The missing evidence is still decisive: temperature history, specimen geometry/microstructure, isotope-resolved release and instrument response; then separate collection/processing residence and loss measurements. Received pressure or mass-spectrometer signals must not be labeled immediately available fuel without calibration and a downstream interface. Fit physical models on one interval and evaluate on an untouched shutdown/restart interval. A linear Robin surrogate and the paper's nonlinear desorption model must remain distinct candidates until evidence discriminates them.

For future NVIDIA use, first determine whether better bulk, surface or defect-rate predictions would change a fuel-availability decision. Only then benchmark a material-appropriate interatomic model and accelerator. The current calculation is already subsecond and is not a useful GPU bottleneck. Its critical uncertainty is physical input, not arithmetic speed.

The prior 406.5 MW / 20,000-cycle candidate remains superseded. No integrated fuel/power/lifetime design is validated by this study.

## Outreach and continuity

Both original threads were read: the ceramic request and MAST-U request each contain only the sent request at the time checked. The ceramic request is **sent**, not an unsent draft; the previous handoff's draft status is historical. The user is arranging the scheduled notification themselves. No Make integration, scheduled job or autonomous research team was created in this continuation.

## Reproduction

    OPENBLAS_NUM_THREADS=1 python scripts/surface_recovery_gate.py --output results
    FUSION_POWER_ARCHIVE=inputs/process-power-cycle-33906304781.zip OPENBLAS_NUM_THREADS=1 python -m pytest -q tests

The second command is for the assembled checkpoint. To test only new work in the main repository, run `python -m pytest -q tests/test_surface_recovery_gate.py`. Runtime in the result JSON varies between runs, so its full-file hash can change without a scientific result changing. Inputs are written before evaluating cases. The artifact contains the complete numerical results, inherited sources, new source/tests and SHA-256 manifest.

## Sources inspected

[1] NVIDIA cuEquivariance: https://docs.nvidia.com/cuda/cuequivariance/
[2] NVIDIA application scope: https://developer.nvidia.com/cuequivariance
[3] MACE integration documentation: https://mace-docs.readthedocs.io/en/latest/guide/cuda_acceleration.html
[4] Kulsartov et al., Nuclear Materials and Energy 36 (2023), 101489. DOI 10.1016/j.nme.2023.101489. Author PDF pages 4-5 inspected visually in this turn: https://publikationen.bibliothek.kit.edu/1000161583/151216760
[5] Ran et al., Modeling of tritium release behavior of biphasic Li2TiO3-Li4SiO4 ceramics, Ceramics International 50 (2024), 22421-22429. DOI 10.1016/j.ceramint.2024.03.343. Publisher abstract/sections inspected; full experimental data not downloaded.

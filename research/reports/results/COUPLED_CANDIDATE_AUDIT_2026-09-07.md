# Coupled candidate audit — 7 September 2026

## Disposition

The previous 406.535 MW / 20,000-cycle candidate does not pass its stated gates after heat feedback and numerical-convergence checks. This rejects that numerical claim, not fusion or HCPB technology. Completed local work: **73 tests passed, zero failures, zero skips; 72 electrical cases; 81 steady fuel-budget cases; 12 time-dependent 60-day fuel campaigns.** No full PROCESS optimization, OpenMC transport, qualified magnet experiment, or new hosted job ran here.

## Pump heat feedback

The pinned PROCESS power model includes mechanical coolant-pump work in primary heat. The authenticated baseline has 232.160418 MW FW/blanket mechanical pumping, 266.851055 MW pump electricity (87% motor efficiency), 2890.381072 MW primary heat, and 1156.152429 MW gross electricity at 40% conversion.

The old candidate substituted 97.313864 MW mechanical pump power while retaining gross generation. This leaves recoverable pump heat in the electricity balance after the work supplying it has been removed. With unchanged other heat inputs and temperatures:

`delta P_net = (W_old-W_new) * (1/eta_motor - eta_turbine)`.

The earlier calculation used only the first term. Reducing circulation demand remains beneficial, but its gain was overstated.

| Quantity | Previous calculation reproduced | With pump-heat feedback |
|---|---:|---:|
| Gross electricity during generation | 1156.1524 MW | 1102.2138 MW |
| Average net at assumed 80% availability | 406.5347 MW | **369.6474 MW** |

Both retain 60% EC efficiency, 600 s dwell, 97.313864 MW mechanical pump work and all other archived assumptions. The average penalty is **36.8873 MW**. If the external 90/2400 pump/heat ratio instead applies to the new total FW/blanket heat, its fixed point gives 92.0601 MW mechanical pumping and 372.3400 MW average. That interpretation also remains below target. Both pump targets remain cross-study assumptions, not source-matched hydraulic results.

## Fatigue integration

The native routine uses 0.1 mm crack-advance steps. Its baseline was reproduced exactly, then the same growth law was integrated with adaptive DOP853 and RK45, stopping at the specified event rather than stepping beyond it.

| Case | Native-step reproduction | Adaptive event-located result |
|---|---:|---:|
| Authenticated baseline | 5736.978618 | **5449.014936 cycles** |
| Prior rounded candidate: 293.95 MPa, 9.813 mm conduit | 19999.940961 | **19070.388949 cycles** |

Euler refinement approaches the adaptive value; the two adaptive solvers differ by less than 0.000001 cycle. Termination is the radial-crack safety limit, not the fracture-toughness limit. This establishes numerical convergence of the existing constitutive model, not actual material life or independent experimental validation. The two-load-excursions-per-plant-pulse convention is retained.

At the fixed 9.813 mm conduit thickness, the converged model requires hoop stress <=288.635 MPa for 20,000 cycles. This is a diagnostic requirement, not a complete redesigned magnet. Field, current, flux, quench and structural geometry must still close together.

## Lifetime and revised requirements

The candidate schedule executes 2837.824 cycles per calendar year at assumed 80% additional availability. Thus 20,000 cycles represents 7.05 years, the converged candidate represents 6.72 years, and 30 years without solenoid replacement requires about **85,135 cycles**. Replacement is not proved impossible, but its feasibility/downtime cannot be omitted. A hypothetical 90-day replacement every 19,070 cycles lowers effective availability to 77.1704% and the corrected average power to 356.57 MW.

Conditional routes to 400 MW average, retaining the external pump target and 600 s dwell:

| Changed assumption | Required value |
|---|---:|
| EC efficiency only; turbine 40%, availability 80% | **70.3467%** |
| Turbine efficiency only; EC 60%, availability 80% | **41.6107%** |
| Mechanical pump power only; EC 60%, turbine 40% | **<=38.0908 MW** |
| Turbine efficiency with hypothetical 90-day solenoid replacements, EC 60% | **42.3890%** |
| Also impose a diagnostic 5% reduction of nonpump primary heat | **44.5372%** |

These are accounting roots, not demonstrated equipment performance. Nonpump-primary-heat derating is not automatically a fusion-power derating. At 42% turbine conversion, the candidate gives 407.34 MW before the hypothetical replacement penalty but 392.93 MW after it. Selecting another favorable subsystem value is not integrated closure. KIT's June 2026 gyrotron dissertation describes gyrotron efficiency above 60%, not a full wall-plug-to-injector EC system at the new requirement.

## Fuel-cycle checks

A June 2026 preprint identifies potentially large tritium throughput from divertor gas fueling and its interaction with direct recycling. The new ledger therefore distinguishes effective core burn fraction from all circulating fuel.

For effective core burn fraction b, tritium-puff/core-input ratio g, unrecoverable exhaust fraction l and delivered bred fraction eta_b, a necessary long-run balance before decay/reserves is:

`eta_b*TBR >= 1 + l*((1+g)/b - 1)`.

At the declared assumptions b=2%, eta_b=99%, and l=0.05%, the necessary TBR is 1.034848 with g=0 but **1.287374 with g=10**. A TBR of 1.15 therefore fails the latter scenario. It would permit at most 0.02523% unrecoverable loss per exhaust pass before decay/reserves. These are sensitivity assumptions, not measured PR42 quantities; total D+T puffing is not interchangeable with tritium puffing.

The executed four-inventory model tracks fast/slow recycling, blanket extraction, available storage, permanent loss, radioactive decay, burned mass and bred mass. Each constant-input segment is solved analytically and independently replayed by an augmented matrix exponential. All scenario inputs were saved and hashed before evaluation.

For 80% routing through fast recycling and 0.05% per-pass loss, finite-horizon initial stock is approximately **0.906 kg at g=0**, versus **8.438 kg at g=10**. The latter requirement is still moving toward the end of the 60-day campaign, so providing finite startup stock does not establish self-sufficiency. Reducing the assumed loss to 0.01% gives approximately 6.073 kg at g=10.

Assumptions: 2% effective core burn, TBR1.15, 99% blanket delivery, 6-minute fast recycle, 4-hour slow recycle, 48-hour blanket extraction/residence, 12.32-year half-life, archived DT power 2061.200738 MW, 17.6 MeV/reaction, empty process reservoirs and zero emergency reserve. Rectangular flat-top burn omits ramp fusion consumption. The 60-day campaign has no additional maintenance outages; it is NOT an 80%-availability lifecycle simulation or an operating-stock recommendation. Plasma feedback and real transport/trapping/isotope-separation data remain missing.

Maximum mass-balance residual across 12 campaigns: 1.13e-11 kg. Maximum analytic/matrix final-state difference: 1.19e-11 kg. These certify bookkeeping under the stated assumptions, not their physical accuracy.

## Reproduction and next action

Original power ZIP SHA256: `5aae03f0d4dc4e7eff11b46488f6c3bddc290d29a759cd38712ea79a0b9b627b`. Input artifact ID9949782922, run33906304781. The full numerical outputs are deterministic reproductions via:

```sh
python -m pip install -r requirements-coupled-audit.txt
python scripts/audit_coupled_candidate.py --archive inputs/process-power-cycle-33906304781.zip --output results
python scripts/audit_fuel_campaign.py --archive inputs/process-power-cycle-33906304781.zip --output results
FUSION_POWER_ARCHIVE=inputs/process-power-cycle-33906304781.zip python -m pytest -q tests/test_coupled_candidate.py tests/test_fuel_campaign.py
```

Test environment: Python3.13.5, NumPy2.3.5, SciPy1.17.0, pytest9.0.2. Full outputs/hashes are in the downloadable evidence checkpoint; key results and tested source are committed here. No full PROCESS source could be installed locally because outbound GitHub hostname resolution failed; this is separate from earlier hosted-runner allocation failures.

Next decisive task: a source-matched thermal-hydraulic and magnet-lifecycle PROCESS solve, with pump heat feedback, converged fatigue or justified conservative discretization margin, explicit lifetime/replacement requirements, and unchanged superconducting/flux constraints. Then incorporate the same HCPB geometry's nuclear heating, tritium release and actual core/divertor fuel streams. Do not reuse the superseded 406.5 MW claim or requeue unchanged blocked jobs as a substitute for research.

## Primary sources

- Pinned PROCESS power: https://github.com/ukaea/PROCESS/blob/c0ae5b28649f2b20fb7efc7904628b6defe4151c/process/models/power.py
- Pinned fatigue equations/defaults: `process/models/cs_fatigue.py` and `process/data_structure/cs_fatigue_variables.py` at the same commit. Restricted mathematical reimplementation credits UKAEA PROCESS (MIT).
- HCPB circulating-power study: https://doi.org/10.1080/15361055.2019.1607695
- KIT gyrotron dissertation: https://publikationen.bibliothek.kit.edu/1000190165
- Gyrotrons for Fusion Power Plants: https://doi.org/10.1080/15361055.2025.2523609
- Meschini/Moscheni June2026 preprint: https://arxiv.org/html/2606.28043v1
- Abdou et al. fuel-cycle requirements: https://doi.org/10.1088/1741-4326/abbf35
- Existing multi-fidelity workflow, not reproduced here: https://arxiv.org/html/2603.25751v1

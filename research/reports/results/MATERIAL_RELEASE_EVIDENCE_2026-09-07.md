# Fusion: external material evidence and an independent transport reference

## Disposition

The next model improvement is a temperature-dependent material-release interface, not another assumed faster-recycling success claim. This continuation reproduced an external coupled diffusion reference, extracted published lithium-ceramic measurements, replaced a single residence-time response with a spatial-diffusion response in a declared sensitivity, and then tested a shutdown-temperature issue raised by a separate irradiation experiment.

**165 tests passed with no failures or skips:** 127 inherited checks and 38 new checks. This is the assembled audit suite, not every test in the repository. Both new study scripts executed locally. No full PROCESS optimization, OpenMC transport, PathView/FESTIM binary run, physical experiment, cloud provisioning, or unattended research team is claimed.

## 1. External reference reproduced

Delaporte-Mathurin et al., arXiv:2603.25751v1, section 4.2, uses an established depleted-source diffusion verification problem. A finite gas enclosure feeds an initially empty wall; gas pressure, wall concentration and outward permeation evolve together. The authors supply parameters and analytical expressions in the public PathView_Paper repository at commit `31aedef8aa12205c7ba71fc1b9d80b2ac443e065`.[1,2]

I implemented two separate calculations: a bracketed analytical eigenfunction series and a conservative finite-volume gas-plus-wall model. At the finest tested grid, their maximum normalized-pressure discrepancy was **4.3791e-6** across eight specified times from 1 to 140 seconds, decreasing with mesh refinement.

At 10 seconds, the finite-volume result allocates the original inventory as follows:

| Location | Fraction of initial inventory |
|---|---:|
| Gas enclosure | 0.5353565 |
| Still inside the wall | 0.3727232 |
| Escaped through the outer surface | 0.0919203 |

The distinction matters: gas-pressure depletion is NOT equivalent to recovered fuel outside the wall. An independently assembled matrix exponential checks conservation and the time evolution. This is a reproduction of the published mathematical reference at its supplied parameters, **not** an execution of the authors' software or a new experimental validation.

## 2. Published material evidence, with its limits preserved

Zhao et al. report the following for melt-sprayed lithium orthosilicate. These are the authors' published abstract summaries, not a downloaded dataset of raw time traces or uncertainty bars.[3]

| Temperature | Reported residence time | Measurement/analysis regime |
|---|---:|---|
| 467 C | 23.34 h | In-pile reported residence |
| 525 C | 21.3 h | Post-irradiation diffusion analysis |
| 550 C | 4.7 h | Post-irradiation diffusion analysis |

The latter two reported diffusion coefficients, 1.19e-11 and 5.34e-11 **cm2/s**, convert to 1.19e-15 and 5.34e-15 **m2/s**. The regimes are not pooled into one fitted temperature law. Under the chosen uniform-source sphere interpretation, their time/coefficient pairs imply similar effective lengths, about 37 micrometres. That length is **inferred, not measured**, and the reported time and coefficient may derive from the same fit. Their agreement is only a units/consistency check.

These values concern material specimens. They cannot by themselves replace the complete industrial blanket's release, collection and downstream processing time. The specimen microstructure, temperature field, dose, purge conditions, geometry and uncertainties have not been matched to our conceptual plant.

### Response shape matters, not just its mean

For a uniform source in an ideal diffusion-only sphere with an absorbing surface, the residence-response modes have weights `6/(pi*n)^2` and rates `(pi*n)^2/(15*tau)`. A single exponential with mean tau does not reproduce this spatial response. The finite modal tail is handled conservatively, its missing mean is bounded, and an independent radial finite-volume calculation checks refinement.

At tau=21.3 h, the fraction released over the archived 2.057-hour burn duration is approximately **25.2%** for initially uniform sphere inventory versus **9.20%** for a single exponential. Starting instead from the hot steady-generation concentration profile gives approximately **8.00%** released after shutdown over the same interval. Different initial spatial inventories must not be interchanged.

### Faster material release does not rescue the high-loss scenario

I ran eight declared delay/throughput sensitivities and 16 sphere-mode refinements on the inherited ledger. Other fuel assumptions remain unchanged and uncalibrated. For the previously studied high-throughput, 0.05%-loss-per-pass scenario:

| Material-delay representation | Critical breeding ratio in this model |
|---|---:|
| Old 48 h exponential assumption | 1.2913934 |
| 21.3 h diffusion response | 1.2911720 |
| 4.7 h diffusion response | 1.2910343 |

All remain above 1.29 and fail the assumed 1.15 breeding ratio. Improved release reduces holdup; it does not replenish permanently lost fuel. The research priority therefore remains recovery losses and isotope-specific throughput, alongside release behavior—not merely selecting the fastest reported material number.

## 3. Follow-on: shutdown cooling challenges constant release

Kulsartov et al. examine a **different**, biphasic Li4SiO4/Li2TiO3 material during a 1.5-hour irradiation interruption, with a reported temperature drop from about 665 C to 100 C. Their fitted effective transport law and diffusion/desorption discussion provide a reason to test temperature-dependent release. This is not the same material/calibration as Zhao's specimens.[4]

I used that study's effective diffusion law only in a separate idealized follow-on. With spatially uniform temperature, diffusion during cooling can be calculated through the integrated diffusion clock. I checked that time transformation against a direct non-autonomous diffusion equation solved by an adaptive numerical method.

For a **750-micrometre illustrative sphere**, initially at a hypothetical hot steady-generation profile, the calculated fractions released over 1.5 hours are:

| Declared temperature scenario | Calculated released fraction |
|---|---:|
| Held at 665 C | 78.5% |
| Linear cooling from 665 C to 100 C | 47.3% |
| Instantly at 100 C | 4.02% |

Nine size/temperature scenarios were executed. The hot and cold limits bound only this diffusion-only, zero-surface-concentration model when its temperature stays inside the stated range. They **do not bound the real experiment**: actual cooling, desorption, porosity and trapping are not reproduced. The linear trajectory is a sensitivity, not a digitized measurement. These are calculations using the authors' effective fit, not new experimental release fractions.

The engineering consequence to investigate is specific: crediting fuel release throughout an outage requires the material's temperature history and surface conditions. Holding material warm may affect recovery, but any extra heating, cooling, inventory and restart costs must enter the same net-electric design. No warm-hold strategy has yet been shown beneficial.

## Evidence, limits and next action

The two studies' materials and extraction conditions remain separate. The exact depletion-reference parameters, source Git blob identifiers, reported point summaries, assumptions, outputs and tests are preserved. The KIT article was read as a full PDF, including its temperature and release figures; its numerical raw histories were not obtained. Its data-availability statement offers data on request.[4] The previously identified Zenodo fuel-stream dataset could not be retrieved; it was not used as calibration. A targeted check of existing UKAEA outreach located the sent request but no reply; no new message was sent.

Next decisive task: obtain time-aligned material temperature, neutron/source history and isotope-resolved release with specimen and instrument-response metadata. Fit diffusion/desorption on one interval and test it on an untouched shutdown/restart interval. Then retain a separate downstream processing stage rather than treating material release as immediately available plasma fuel. Recovery loss and fuel throughput still require their own evidence. Same-geometry neutronics, thermal hydraulics, electrical output and magnet life remain outstanding.

No new hosted retries were submitted. The local environment sufficed for these reference and component calculations; it does not establish a working full PROCESS/OpenMC route. The previous pump-heat and fatigue corrections remain in force, and the superseded 406.5 MW / 20,000-cycle claim is not reinstated.

## Reproduction

```sh
python -m pip install -r requirements-material-reference.txt
python scripts/material_release_reference.py --archive inputs/process-power-cycle-33906304781.zip --output results
python scripts/material_cooldown_bounds.py --output results
FUSION_POWER_ARCHIVE=inputs/process-power-cycle-33906304781.zip OPENBLAS_NUM_THREADS=1 python -m pytest -q tests/test_coupled_candidate.py tests/test_fuel_campaign.py tests/test_periodic_fuel.py tests/test_fuel_operating_limits.py tests/test_material_reference.py
```

Verified power archive SHA256: `5aae03f0d4dc4e7eff11b46488f6c3bddc290d29a759cd38712ea79a0b9b627b`. Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, pytest 9.0.2. The final test run completed in 1.81 seconds. Runtime is performance evidence only, not a scientific success criterion. The GitHub source includes the scripts and tests; the reference-result fixture regenerates its study in a temporary directory when FUSION_POWER_ARCHIVE is supplied. Full output files are included in the evidence package.

## Primary references

[1] Delaporte-Mathurin et al., Physics-informed tritium fuel cycle modelling workflow for fusion reactors, 2026, section 4.2: https://arxiv.org/html/2603.25751v1

[2] Public source at commit `31aedef8aa12205c7ba71fc1b9d80b2ac443e065`: https://github.com/rossmacdonald98/PathView_Paper . Parameters: `FESTIM/depleted_source.json`, blob `34b753e4787aea6f5bda74bd031ef5b374101faa`; analytical reference: `FESTIM/analytical_solution_depleted_source.py`, blob `b071d78410cba1f5b60a4e0d389c921a3af82af1`. Source license MIT, copyright 2025 rossmacdonald98. Our solvers are independent mathematical implementations; no PathView/FESTIM binary execution is claimed.

[3] Zhao et al., In-pile tritium release behavior and the post-irradiation experiments of Li4SiO4 fabricated by melting process, Nuclear Engineering and Technology 56 (2024), 106-113. https://doi.org/10.1016/j.net.2023.09.014 . Numerical abstract summaries accessed; no raw experimental dataset.

[4] Kulsartov et al., Investigation of transient processes of tritium release from biphasic lithium ceramics Li4SiO4-Li2TiO3 at negative neutron flux pulse, Nuclear Materials and Energy 36 (2023), 101489. https://doi.org/10.1016/j.nme.2023.101489 . Full author-repository article: https://publikationen.bibliothek.kit.edu/1000161583/151216760 . Figure 6 and Eq.5 inspected; diffusion/desorption limitations preserved. Raw data offered on request, not obtained.

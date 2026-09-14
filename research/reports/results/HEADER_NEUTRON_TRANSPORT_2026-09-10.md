# Header neutron study: candidate-linked transport decision

## What advanced
We completed neutron and photon transport through a representative blanket cell tied to the r838 header/material allocation. Earlier cooling work had not tested this nuclear interaction. The new decision is that a uniformly mixed inventory must not be treated as validation of placing these headers near the front. Rear placement remains a candidate for a complete coupled design; it is not an approved engineering solution.

This is a local computational design test, not a whole-reactor tritium-breeding ratio, an experimental validation or a higher plant-electricity result. Placement-dependent neutron effects are already known; the question was whether they materially affect this particular proposed inventory.

## Existing research and prerequisite check
The HCPB design review by Zhou et al. (2023) and the full-module neutronic/thermal coupling work by Lian et al. (2023) were checked before admitting this calculation. We reused OpenMC, an existing Eurofer material recipe and the published OpenMC-Fusion-Benchmarks infrastructure, not a newly invented transport solver or general blanket optimizer.

The public reference repository did not supply the executable FNG HCPB breeding benchmark at the recorded revision. We reproduced its unchanged OKTAVIAN aluminum source, geometry and neutron/photon leakage tallies as a computational check. Integrated neutron and photon leakage were within 0.036% and 0.007% of its archived OpenMC/ENDF-B-VIII.0 results. That is not validation of lithium/beryllium breeding. We did not claim access to restricted SINBAD data or calibrate the candidate to the reference.

Novais and Peterson's published FNG HCPB comparison reports an average approximately 9% underprediction of experimental tritium production, largely associated with beryllium nuclear data. It illustrates why small Monte Carlo error is not physical accuracy. We did not apply a universal 9% correction to our results.

## The completed experiment
Three layouts each used two separate random streams of one million source histories: six million histories in total. Each run had 40 batches, two CPU threads and a 600-second limit. All six completed. The source, geometry, material parameters, data hashes, layout choices and acceptance rule were fixed before evaluation.

The one-metre-deep repeated cell retains the archived armor, first-wall specification and blanket inventory. Explicit front/rear layouts place three capped helium headers in the cell, subtracting their steel and coolant from the residual mixture. All per-nuclide inventories agree within approximately 2.2e-15 relative numerical difference; no extra material or coolant is created. Side faces reflect and the front/rear boundaries leak to vacuum. Incoming neutrons have 14.1 MeV and the declared cosine-weighted angular law. This omits toroidal return flux and the rest of the reactor.

| Local layout | Tritons / incident neutron | One Monte Carlo standard error | Deposited MeV / incident neutron |
|---|---:|---:|---:|
| Uniform inventory | 0.679755 | 0.000692 | 11.779692 |
| Headers at rear | 0.682932 | 0.000857 | 11.786598 |
| Headers near front | 0.665826 | 0.000778 | 11.706790 |

The front layout produces approximately 2.05% fewer tritons than the uniform reference; the rear layout produces approximately 0.47% more. Total nuclear heating changes by approximately -0.62% for front headers and +0.06% for rear headers. These are predictions per neutron entering the local cell, NOT per fusion neutron born in a complete reactor and NOT recovered reusable fuel.

## What the statistical result permits
The front-minus-uniform difference is -0.013929 tritons per incident neutron, with an approximate 99% Monte Carlo interval [-0.016612,-0.011246]. The rear-minus-uniform difference is +0.003176, with interval [+0.000338,+0.006015]. These intervals describe sampling error only. Nuclear data, material specification, manufacturing, temperature, source and model-form uncertainties are excluded.

The admitted screen flags a difference when its point estimate exceeds 2% and the 99% interval excludes zero. Front placement triggers that screen. However, its effect-size interval spans the 2% threshold: we do NOT claim 99% confidence that the loss exceeds 2%. Rear placement does not trigger the admitted magnitude screen. Its smaller positive difference is not proof of a beneficial complete design.

An exploratory direct comparison of the already-completed front/rear cases gives about 2.50% lower local triton yield for front placement. This was not the preregistered primary comparison. Neither that comparison nor a successful solver run justifies an absolute global TBR claim.

## Physical and numerical limitations
The materials retain the declared 30% lithium-6 enrichment, effective densities, Li4SiO4/TiBe12 fractions and uniform 673.15 K temperature. They are the archived conceptual model's assumptions, not a qualified current DEMO blanket specification. Ceramic and TiBe12 bound-atom scattering kernels are not included. Nuclear heat is tallied with neutron/photon transport, but there is no feedback to temperature, coolant properties, thermal stresses or CFD. The front case is an admitted stress case, not an optimized or certified pressure vessel.

Three spatial models passed sampled point and analytic volume checks. Tally filter IDs are unique in exported XML; cell-resolved heating and triton tallies sum to their global local-model tallies. Repeat-seed differences are recorded, and raw statepoints are hashed. The published computational reference, source files, nuclear-data identifiers, all six results and unsuccessful software-preparation attempts are retained. The first reference postprocessor required a pandas compatibility correction; no reference transport was rerun or tuned for that correction.

No number here has been added to the previous 213.69 MW conditional plant average. Neither r838 nor r900 has a validated whole-device neutron/material model or a closed fuel cycle. In particular, a local triton yield below one does not by itself establish a full-reactor breeding deficit: the source denominator and geometric boundary are different.

## The visual application update
A dedicated Neutron study panel compares the three actual completed layouts, their computed depth profiles and numerical error estimates. The mid-height drawing is the local cell geometry, not a whole-reactor heat map. The new report and source/reproduction notes are searchable in Research library; the evidence dashboard distinguishes local transport from missing whole-device validation. The display does not run code or replace an accepted reactor when changing layouts.

## Next acceptance decision
Before accepting the header proposal, reproduce a compatible lithium/beryllium experimental benchmark or explicitly quantify the applicable nuclear-data/model discrepancy. Then use the actual three-dimensional module and whole-device source/return-flux geometry, with header heating and coolant/steel allocation carried into the thermal and structural calculation. Reuse published HCPB coupled methods; do not silently transfer this cell's yield to the plant or start arbitrary geometry sweeps.

## Primary references and reproduction
- Zhou et al., HCPB design status: https://doi.org/10.3390/en16145377
- Lian et al., existing full-module coupling: https://doi.org/10.1016/j.net.2023.08.005
- Novais and Peterson, FNG HCPB benchmark and uncertainty: https://doi.org/10.1080/15361055.2025.2567167
- Public computational benchmark: https://github.com/eepeterson/openmc_fusion_benchmarks at c47fc573a7e2a9ca11a8958dc67155b1146adf51
The experiment folder `research/source/experiments/header_neutron_placement_2026_09_10` contains frozen inputs, cleared results and reproduction instructions. Full local evidence additionally preserves all statepoints and execution logs. Nuclear-data files are identified by hashes but are not bundled into the application. No private correspondence, local account paths or credentials are part of the reader.

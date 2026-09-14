# Header neutron study: research context and acceptance boundary

## The physical design decision
The previous r838 cooling work proposed additional helium distribution headers and recorded their steel and coolant inventory, but had not transported fusion neutrons through that inventory. Before crediting the cooling proposal, we must test whether treating this material as uniformly mixed conceals a meaningful change in local tritium production or nuclear heating. This campaign compares one uniform reference with the same inventory placed explicitly at the rear or near the front of a representative blanket cell.

The placement effect is established physics, not a novelty claim. The contribution sought here is a falsifiable decision for the archived r838-linked material/header allocation, with identical nuclide totals and explicit computational uncertainty. The front placement is a stress case, not a proposed qualified pressure vessel or an optimized manifold.

## Existing work used rather than rebuilt
Zhou et al. (2023), *The European DEMO Helium Cooled Pebble Bed Breeding Blanket: Design Status at the Conclusion of the Pre-Concept Design Phase*, describes established nuclear, thermal-hydraulic and engineering design work. Its detailed modern design is not our older homogeneous PROCESS material specification; its reported reactor performance cannot simply be transferred. https://doi.org/10.3390/en16145377

Lian et al. (2023) already developed three-dimensional thermal-hydraulic/neutronics coupling for a full-scale CFETR helium-cooled breeder module. A local representative-cell test does not reproduce or supersede that full workflow. https://doi.org/10.1016/j.net.2023.08.005

Novais and Peterson's FNG HCPB study compares OpenMC tritium-production predictions with MCNP and experimental measurements, and propagates nuclear-data uncertainty. It reports approximately 9% mean underprediction of the experimental tritium data, associated largely with beryllium cross-section uncertainty. That is evidence that small Monte Carlo error does not establish physical accuracy; it is NOT a universal 9% adjustment for our calculation. https://doi.org/10.1080/15361055.2025.2567167

The public OpenMC-Fusion-Benchmarks repository at the recorded commit did not include an executable HCPB model. We reproduced its unchanged OKTAVIAN aluminum source, geometry and leakage tallies as a computational transport check. This exercises neutron/photon transport and source normalization, not lithium-ceramic breeding validation. No restricted SINBAD package or unreceived experiment was claimed. https://github.com/eepeterson/openmc_fusion_benchmarks

## Frozen local model
The repeat cell uses the r838 outboard blanket depth, volume allocation and proposed three-header geometry. The first wall and armor are unchanged. Each explicit-header case removes its helium and Eurofer volume from the residual mixed blanket: no free extra coolant or steel is added. All isotope totals match to numerical precision. Side faces reflect; the front and rear are vacuum. An incoming 14.1 MeV source has a cosine-weighted angular distribution. This is not a toroidal source/blanket model, and it excludes neutron return from the rest of a reactor.

The 30% Li-6 enrichment, Li4SiO4/TiBe12 recipe, effective densities and uniform 673.15 K material temperature are recorded assumptions. They are not the current European DEMO material prescription. No ceramic or TiBe12 bound-atom scattering treatment is included. Coupled neutron/photon heating is scored, but no feedback to temperature, coolant density or CFD is applied.

## Admitted computation and test
Three layouts each receive two distinct random streams of one million histories, with 40 batches per run, two CPU threads and a 600-second limit per run. The admission precedes the results. The decision rule flags a geometry sensitivity when the local triton-yield change exceeds 2% of the homogeneous value and the independent-run 99% normal Monte Carlo interval excludes zero. That interval does not contain nuclear-data, model-form, manufacturing, source or operating uncertainty.

No global tritium-breeding ratio, delivered reusable fuel, plant-output increase, experimental validation, or first-of-kind fusion physics is claimed by this local test. The original accepted plant input and power results remain unchanged.

# Source direction and 3D transport: recorded physics in the hardware view

## Decision being tested
The previous local r838 header study assumed diffuse, cosine-weighted neutron incidence. This follow-on asks whether its front/rear placement ranking survives a different incident direction, and records three-dimensional energy-deposition fields and particle tracks for inspection. This is a boundary-assumption test of the existing local representative cell, not a full toroidal reactor, a new blanket optimizer or experimental validation.

Research preceded the calculation. The official FNG HCPB benchmark describes angular variation of both source intensity and energy, detector positions, and material recipes. Those definitions cannot be replaced by an arbitrary isotropic or normal source and still called that benchmark. The underlying compatible experiment and complete reactor source remain unresolved; the present normal and cosine cases are deliberately contrasting hypotheses, NOT measured source distributions or physical uncertainty bounds.

## What was held fixed
All four cases retain the previous material inventory, header dimensions, first wall, armour, nuclear-data files, 673.15 K temperature, 14.1 MeV source energy and reflecting lateral/vacuum front-and-back boundaries. They use either rear or source-facing headers. Within each placement, only source direction and the independent random seed change. Each tally run contains 40 batches of 10,000 primary histories; 1.6 million primary histories were scored in total, with neutron and secondary-photon transport enabled.

The predeclared additional output is a 24 x 16 x 16 mesh: 6,144 three-dimensional scoring voxels. Heating is stored in eV per cubic centimetre per incident source neutron. Tritium production is stored separately. Neither is a temperature field or a complete-plant breeding ratio. The first 16 primary histories of each case, and their moving neutron/photon descendants, were selected before seeing the tracks. There was no selection for visually impressive paths.

## Results
| Incidence assumption | Header placement | Tritons per incident neutron | Monte Carlo standard error | Deposited energy, MeV per incident neutron |
|---|---|---:|---:|---:|
| Cosine weighted | Rear | 0.680709 | 0.001612 | 11.7883 |
| Cosine weighted | Front | 0.666377 | 0.001890 | 11.7173 |
| Normal | Rear | 0.846251 | 0.001828 | 13.4334 |
| Normal | Front | 0.825353 | 0.001748 | 13.3292 |

The front-minus-rear change is -2.105% for cosine incidence and -2.470% for normal incidence. Both 99% normal Monte Carlo intervals for the absolute front-minus-rear difference exclude zero: [-0.020731, -0.007932] and [-0.027414, -0.014383] tritons per incident neutron respectively.

Thus the direction of the local placement penalty survives both tested incident-angle hypotheses. This supports retaining rear placement as the less damaging local option to investigate, not approving a complete rear-header engineering design. The interaction between incidence law and placement is NOT resolved at 99% Monte Carlo confidence: its interval is [-0.015699, +0.002566]. The result key named `source_change_resolved_at99_MC` refers to that interaction, not to the large absolute difference between source laws.

Changing the source law changes absolute local yield by roughly 24% for the rear arrangement. That is not a free performance improvement: it demonstrates dependence on an unvalidated boundary condition. The source law cannot be chosen because its number looks better. A geometry-matched plasma source, return flux and experimental validation are required before promoting any absolute breeding result.

## What the three-dimensional app displays
The native Unreal transport laboratory draws steel header shells, their helium interiors, the armour/first-wall layers and a transparent homogenized breeder envelope from the local model's dimensions. Cutaways remove visible surfaces only; they do not modify the neutron calculation. No unmodeled bolts, pumps, pebbles or external piping are presented as engineering data.

Cyan neutron and gold photon markers move along recorded OpenMC trajectory states with actual positions and times. Their size, brightness and slow-motion/logarithmic playback are display choices. All 16 independent histories are aligned at emission for viewing, not asserted to be a physical source pulse. A sparse demonstration sample cannot represent the reactor's particle flux. Between recorded states, position is interpolated along the straight transport segment; energy data remain in the source packet.

The movable heating slice reads actual three-dimensional mesh scores. One common logarithmic color scale is used across all cases; values with relative statistical standard error above 50%, or no score, are masked. Clicking a voxel displays its physical coordinates, score, units and statistical uncertainty. The field is not an inferred temperature, and there is no computed coolant velocity field. The full-cell heating readout includes armour and first wall, whereas the mesh covers the blanket volume only.

The data path is traceable: approved local input -> OpenMC statepoint and track HDF5 files -> checked JSON projection -> runtime geometry, particle playback and voxel inspection. Opening a report or changing a camera does not execute a solver or modify an accepted reference. The existing full-system reproduction control remains separate.

## Numerical checks and execution recovery
The mesh heating and triton sums agree with the blanket-cell tally sums, including explicitly separated headers, to floating-point precision. All displayed particle states remain in the modeled domain and have monotone nonnegative recorded time. There are 463 moving neutron/photon paths and 4,693 recorded states across the four first-16-history samples. Zero-length paths are not drawn. Original dimensions, seed selection and data hashes are retained.

The initial cosine/rear transport completed but did not write tracks because the installed OpenMC version expects the singular `settings.track` property. Its 400,000-history statepoint was retained unchanged. A one-batch, same-physics, same-seed companion recovered the track sample; remaining cases used the corrected property. The extra 10,000 companion histories are not added to the scored 1.6-million-history comparison. The recovery manifest and original statepoint hash are preserved. No result was tuned or reoptimized after inspection.

Small Monte Carlo error does not bound physical uncertainty. Nuclear cross sections, bound-atom scattering approximations, material composition, source distributions, manufacture, geometry and coupled thermal feedback remain separate. The previous aluminum reference is a computational transport check, not lithium/beryllium breeder validation. No whole-reactor TBR, recovered usable tritium, new electrical output, magnet qualification or fusion breakthrough is claimed.

## Reproduction and remaining gate
The companion experiment directory contains frozen inputs, run manifests, material/model definitions, four safe result projections and recorded tracks. The private evidence package retains the original HDF5 statepoints, raw tracks and diagnostic logs. Nuclear-data files and machine-specific paths are not distributed inside the public-source candidate. An arithmetic replay does not constitute independent neutron transport.

The next physical gate is to replace the hypothetical incident field with a source and return-flux model consistent with the chosen full geometry, then compare a compatible breeder benchmark and carry nuclear heating into thermal and structural checks. The 3D viewer can now expose the spatial data those tasks produce, rather than inventing a field from one component scalar.

## Primary references and reading scope
- OpenMC 0.15.2 execution settings: https://docs.openmc.org/en/v0.15.2/usersguide/settings.html (fixed-source batches, angular and temporal source definitions).
- OpenMC track-source documentation: https://docs.openmc.org/en/stable/_modules/openmc/tracks.html (stored position in cm, time in seconds, energy in eV and particle types; installed 0.15.2 API checked separately).
- Official FNG HCPB benchmark description: https://www.oecd-nea.org/science/wprs/shielding/sinbad/fng_hcpb/fnghcpb-a.htm (source anisotropy, lithium/beryllium/steel material and measurement context; not a reproduction of its full data package).
- Novais and Peterson HCPB uncertainty study: https://doi.org/10.1080/15361055.2025.2567167 (prior-art pointer retained from the preceding study, not new calibration data).
- Epic runtime procedural-mesh API: https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/ProceduralMeshComponent/UProceduralMeshComponent/CreateMeshSectio- (runtime visualization capability, not a scientific solver).

The benchmark abstract was available; attempts to retrieve the linked experimental-description and input-deck resources did not yield usable contents in this continuation. No missing measurement, uncertainty record or simulation input was fabricated. No private correspondence or credentials are included in the reader.

# Plasma source coupling: candidate-linked incidence and header decision

## What was completed
The previously interrupted source-coupling campaign has been recovered, analyzed and checked. Its admission and four completed transport runs retain their 11 September 2026 labels; the analysis, independent result checks and app integration were completed on 13 September. No failed or incomplete run was promoted into a result and the completed statepoints were not rerun to obtain a preferred outcome.

The design question was specific: does the front-versus-rear header penalty survive an incoming source constructed from the r838 candidate's own reproduced density, temperature and geometry, rather than selecting either normal incidence or a cosine distribution? This is a conditional computational design comparison, not a fusion breakthrough or a whole-reactor breeding calculation.

## Research used before calculation
Parameterized tokamak sources and surface-source coupling are established methods. The admission records the Fausser neutron-source work, the Tokamak Neutron Source theory documentation, a source-generation publication and OpenMC FileSource. The package documentation explicitly distinguishes plasma profiles, equilibrium coordinates, reaction rates and neutron energy distributions. We reused the installed PROCESS profile/Bosch-Hale routines and OpenMC local model; we did not claim a new neutron solver or a new source method.

The previous published OKTAVIAN-Al computational replay exercises neutron/photon transport, not lithium/beryllium breeding validation. A compatible experimental breeding benchmark remains necessary. The modern European HCPB design is not identical to our inherited material specification; its published breeding ratio cannot be borrowed for this candidate.

## Candidate-to-source interface
The approved r838 PROCESS input was reproduced with the previously declared runtime modules. Its 201-point profiles were exported and its DT reaction-rate integral evaluated using the existing reactivity function. The geometric source is a self-similar Miller-style torus using the reproduced major radius, minor radius, elongation and triangularity coefficient, with zero Shafranov shift explicitly assumed. The first-wall proxy uses a 0.25 m gap. No experimental equilibrium file was available.

For each volumetric source location and outboard-midplane surface point, the established uncollided kernel weights incidence by local emission, the geometric Jacobian, projected surface area, inverse-square distance and line-of-sight visibility. Surface position and direction are retained jointly. This does not replace them with a single averaged incident angle.

Eight independently scrambled Sobol integrations were used. Two independent 65,536-particle equal-weight banks were then constructed and supplied to OpenMC. Front and rear geometries retain exactly the same material inventory as the prior local-cell study. Each layout was simulated against each bank using distinct random streams: four runs, 200,000 scored histories each, 800,000 total.

The model-derived mean incoming cosine is approximately 0.7873, compared with 2/3 for a diffuse cosine source and 1 for normal incidence. Those previous sources remain comparison hypotheses, not physical uncertainty bounds.

## Completed result
| Local header arrangement | Tritons per incident neutron | Statistical standard error | Deposited energy, MeV per incident neutron |
|---|---:|---:|---:|
| Rear | 0.752802 | 0.001480 | 12.593954 |
| Front | 0.732380 | 0.001814 | 12.483032 |

The front-minus-rear difference is -0.020423 tritons per incident neutron, or -2.713% of the rear result. Its conditional 99% normal Monte Carlo interval is [-0.026454, -0.014392]. The sign is resolved within this calculation. The interval includes reductions both smaller and larger than 2%; it must not be described as proving a loss greater than 2% with 99% confidence.

This strengthens the reason to keep the front-header arrangement unaccepted: the penalty persists when position and direction are derived from the candidate-linked source, rather than only under two chosen angular laws. It does not certify rear headers as optimized, safe or acceptable for a complete reactor.

With the source rate normalized to the reproduced DT reaction rate, the conditional direct-view local nuclear heating is approximately 3.606 MW for rear headers and 3.574 MW for front headers. These are model-specific module loads, not electrical generation and not a measured power forecast. They provide a traceable input for later thermal analysis only after the geometric/source assumptions are accepted. No cooling temperature has been calculated from the new load and no old cooling temperature is silently reused.

## Numerical checks and limitations
The source kernel was checked against an exact rectangular solid angle. The parameterized volume was independently integrated; first-wall visibility was checked at twice the sampling resolution for two scrambles. Source positions, unit directions, positive incidence, sizes and bank moments were checked. Transport statepoint, track and geometry hashes were verified, as were cell-to-total and voxel-to-cell score sums. The two bank results differ by about 1.20 combined Monte Carlo standard errors for rear headers and 0.14 for front headers; that is a consistency check, not a complete finite-source uncertainty analysis.

The parameterized plasma volume is 2.407% larger than the PROCESS volume. Applying the same profile to that different shape gives an unnormalized total DT rate 3.745% larger; the final direct-source normalization explicitly uses the reproduced PROCESS DT rate. Neither discrepancy is hidden or treated as improved reactor performance. The geometry remains a proxy, not transport-ready engineering CAD or a measured magnetic equilibrium.

Source integration scramble error, finite resampled-bank effects, nuclear-data uncertainty, scattering-model uncertainty, geometry, plasma profiles, equilibrium and manufacturing tolerances are not combined into the quoted transport-only interval. The source contains only uncollided DT neutrons at the inherited monoenergetic 14.1 MeV approximation. Plasma energy broadening, DD neutrons, material return flux, surrounding blanket, ports and divertor effects have not been integrated.

The local slab still has reflecting side boundaries and vacuum front/back. Tritons per neutron entering that slab are NOT a global tritium-breeding ratio, and are not recovered reusable fuel. Existing plant geometry, accepted full-system inputs and net electricity remain unchanged.

## What the 3D view now shows
Two new recorded local cases appear beside the four earlier boundary tests. A Source context view connects the parameterized plasma envelope to the sampled outboard wall patch, displaying 64 weighted, uncollided geometric ray samples. These are source-construction samples, not collision-resolved whole-reactor trajectories. Marker size, brightness and animation speed are display conventions. Switching to the module uses the actual OpenMC collision histories from bank 0 and the spatial heating scores averaged over both banks.

Voxel inspection retains the source-normalized score and its transport statistical error. For the new source-linked cases it also reports the conditional DT-rate-scaled nuclear heating density. This is not a temperature field, a coolant-flow field, validated hardware performance or additional net electricity. The model-derived source and old assumed angular sources remain distinguishable.

The source and original local geometry hashes remain linked. The source overview does not redraw the approved reactor or make the parameterized equilibrium its accepted engineering geometry. Reading a report or switching source cases does not execute code or promote a new accepted configuration.

## Reproduction and primary references
The cleared source packet includes the two sampled banks, admitted input, reproduced profile arrays, all four numerical result/track projections and analysis scripts. The separate local evidence archive retains the original HDF5 statepoints and execution logs; private log paths are excluded from the shareable source. No credentials, raw correspondence or private Git history were added to the app.

- Fausser et al., tokamak neutron-source parameterization: https://doi.org/10.1016/j.fusengdes.2010.12.049
- Tokamak Neutron Source theory, including density/temperature/reactivity and equilibrium-coordinate conventions: https://fusion-power-plant-framework.github.io/tokamak-neutron-source/theory/
- Additional source-generation reference in the frozen admission: https://doi.org/10.1080/15361055.2025.2525028
- OpenMC file sources: https://docs.openmc.org/en/v0.15.2/pythonapi/generated/openmc.FileSource.html
- Modern European HCPB prior art and limitations of transplanting another design's results: https://doi.org/10.3390/en16145377

The continuation rechecked the available primary source documentation. Publisher full texts for every reference were not retrieved in this continuation; no full-text or experimental reproduction is claimed from a citation alone.

## Next acceptance decision
The candidate-derived direct source preserves the front-header penalty, but source-linked local transport is not an accepted full blanket. The next gate is a compatible breeding benchmark and a genuinely matched three-dimensional source/material/return-flux model, followed by thermal and structural checks using those nuclear loads. Keep the nuclear geometry and material inventories consistent with the cooling design; do not add the most favorable results from unrelated configurations.

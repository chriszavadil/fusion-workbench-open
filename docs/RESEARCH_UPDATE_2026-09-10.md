# Research update - 10 September 2026: neutron transport added

The previous release improved evidence access and confinement interpretation. This release adds a physical transport calculation that was missing from the cooling/header proposal: six completed neutron/photon runs through three candidate-linked local blanket layouts, two million source histories per layout. This advances the component feasibility assessment, not proof of a working fusion power plant.

## The design finding
With exactly matched nuclide inventories, placing the headers near the source-facing side gives a local triton yield about 2.05% below the uniformly mixed reference. Rear placement differs by about +0.47%. The front result triggers the predeclared sensitivity screen, but its statistical effect-size interval spans the 2% threshold: the data do not establish 99% confidence that the reduction exceeds 2%. The matched-mass uniform material model therefore cannot substitute for evaluating an actual front-header arrangement. No geometry is accepted as a complete engineered cooling or breeding system.

The tallied 0.68-or-less tritons per neutron are normalized to neutrons entering a local rectangular cell, not to fusion neutrons born in a complete tokamak. This is NOT the plant breeding ratio, and it does not establish fuel self-sufficiency or its failure. Nuclear-data uncertainty, whole-device return flux and thermal feedback remain outside this test. The previous plant electrical outputs are unchanged.

## The visual app
Open Neutron study in the native app or browser. Switch between Uniform inventory, Headers at rear and Headers near front. The panel displays the actual local mid-height geometry, recorded tritium-production depth profiles, source-history counts and Monte Carlo standard errors. Its plot is not an invented reactor heat map. Changing the comparison leaves the accepted reactor configuration untouched.

Open Research library and search 'header neutron' for the full report, prior-art review, numerical results and reproduction instructions. The dashboard now distinguishes completed local neutron transport from missing whole-reactor breeding validation. Older studies and unsuccessful/superseded conclusions remain readable with their original scope.

## Research-first and validation
Existing HCPB design/coupling studies and OpenMC benchmark work were reviewed before the calculation. The exact public OKTAVIAN-Al source/geometry/tallies were reproduced as a computational transport check. That is not the unavailable FNG HCPB lithium/beryllium validation. No prior-art mechanism is claimed as new, and no empirical correction factor was invented.

The run inputs, material inventory, library identities and independent seeds were frozen before evaluation. All six runs, cell-to-total tally checks, repeated-stream uncertainty and source/data hashes are preserved. Full local evidence includes raw statepoints and logs; the app's shareable source includes cleared numeric summaries and reproducibility code but not nuclear-data files or private diagnostics.

The native UI and source remain local preview work. Public publication still requires the fresh repository requested earlier; the withdrawn repository is not reopened. No unattended team, cloud simulation endpoint or experimental reactor result is claimed. Work continues from the explicit remaining geometry, nuclear-data and thermal-coupling requirements rather than another arbitrary sweep.

# Source-to-blanket research and visualization update

## Scientific result
The interrupted candidate-source study is now analyzed and checked. Four completed OpenMC runs, 800,000 scored histories total, use two joint position/direction banks generated from the reproduced r838 density and temperature profiles and a declared toroidal geometry proxy. The local front-header yield is 0.732380 tritons per entering neutron, versus 0.752802 for rear headers: a 2.713% reduction under this model-derived direct source. The transport-only 99% interval resolves the sign, not a guaranteed minimum 2% physical loss.

This removes the previous need to select either a normal or cosine incidence assumption for this specific direct-source comparison. It does not remove uncertainties in plasma geometry, profiles, nuclear data or reactor return flux, and does not calculate global breeding or new electrical output. The parameterized plasma volume differs by 2.407% from the reproduced systems geometry and is explicitly not an experimentally reconstructed equilibrium.

## What to open
In the native Unreal application choose **3D transport**. Six completed local cases are available: the four previous angular stress cases and two new plasma-linked cases. Choose **Source context / module** to switch between the parameterized plasma-to-wall direct-ray view and the local header/blanket transport view.

The overview displays the sampled source geometry and wall patch with animated geometric ray samples. The module displays recorded OpenMC neutron/photon histories, score slices, source rate where applicable, and voxel inspection. The overview animation is NOT physical time; the local track replay retains its stated log-time mapping. Nuclear heating is not temperature. No visual control silently changes an accepted reactor input.

The full source-coupling report, admitted assumptions, benchmark scope, numerical comparison, prior-art links and reproduction instructions are readable in Research library. Earlier work and rejections remain present. Source-code and experiment packets are separate from the local raw logs and nuclear-data installation.

## Scope and publishing
The existing repositories remain the project repositories; creating another repository is not a prerequisite for research. This continuation makes no public visibility change and does not republish previously withdrawn history. The updated native application, clean source and raw evidence are saved locally, with distinct publication scopes. No remote backup operation previously blocked by a safety check is retried.

The next scientific acceptance gate is compatible breeder-benchmark evidence and a full chosen-geometry source/material/return-flux model, then thermal/structural checks using the same nuclear loads. The app is a way to inspect those calculations, not a substitute for them. No autonomous off-session research worker or public live-compute service is established by this update.

## Complete data versus display limits
The canonical app export retains all 131,072 source-bank particles with stable bank/particle identifiers, positions, directions, statistical weights and joint sampling probabilities. It also retains the full source integration observations and angular histograms, plasma profiles, local-input definition, both banks' run records, geometry metadata and recorded track data. The original 64-ray preview is retained only as historical metadata, not as a replacement for the source banks.

Unreal loads the full canonical binary. A separately declared display budget selects a manageable number of rays for drawing; it does not remove particles from the exported dataset or change any analysis. The default is 64 sites and is declared in the packet's visualization metadata, with a `SourceRenderBudget` runtime override. The viewer labels the displayed count and the complete count. Source case names, source-count limits for display and the geometric volume discrepancy come from loaded data rather than fixed scientific labels in the executable.

The export round-trip checks compare every source record with the original banks, verify unique identifiers, weights, probability sums, angular-bin counts, profiles, observations and both recorded track banks. The viewer still intentionally uses selected diagnostic collision histories for animation; this does not imply that every scored OpenMC history was tracked.

# 3D transport laboratory - research and visualization update

The visual app now goes beyond charts and documents. The native Unreal laboratory contains a three-dimensional, dimension-linked local blanket module, cutaway steel headers and helium domains, replayed neutron/photon trajectories, a movable computed heating slice, voxel inspection and a physical-time scrubber. The browser companion uses the same checked data packet for its own orbitable 3D view.

## What is physically computed
Four new OpenMC runs scored 1.6 million incident-neutron histories in the inherited r838-linked local geometry, testing rear and front headers under cosine and normal incidence. Each run produced a 6,144-voxel heating/production mesh. The first 16 primary histories in each case supplied the displayed trajectories, including moving neutron and photon descendants: 463 paths and 4,693 recorded states in total. The report documents a track-file API recovery and excludes its companion histories from the scored total.

Front-header local triton yield is lower than rear-header yield in both tests, by about 2.11% and 2.47%. Both differences are statistically resolved under the stated Monte Carlo analysis; the change in the placement penalty between source laws is not resolved at 99%. Absolute yield depends strongly on source direction. No global tritium-breeding ratio, additional plant output, operating temperature or coolant velocity is inferred.

## What is a display choice
Particle markers are enlarged and time is slowed on a logarithmic slider so trajectories can be inspected. They are not a literal view of particle sizes, a physical simultaneous pulse or source flux. The transparent breeder envelope represents the modeled homogenized material, not individual ceramic pebbles. Cutaways alter visible surfaces only. The heating palette uses one common logarithmic scale with units and a mask for low-statistics cells. Clicking a voxel shows the actual score, coordinates and statistical error, not an interpolated temperature.

## Inspect it
Open 3D transport in the native toolbar, choose a recorded case, right-drag to orbit and scroll to zoom. Toggle the hardware cutaway, track trails and heating slice independently. Move the slice height to inspect other physical regions. Play/pause or scrub physical track time. Read study and limits opens the new scientific report in the searchable Research library. Return to reactor restores the original device view and configuration without promoting any new result.

## How updates flow
The source model runs in OpenMC; HDF5 results are checked and projected into the shared data packet; Unreal and the browser draw those same arrays and coordinates. The approved full-system reproduction controls remain separate. This release plays completed transport runs, not an always-on public neutron worker. New externally supplied data or code still needs review before execution or publication.

## Remaining scientific obligations
The local header ranking survived these two boundary hypotheses, but neither source law is validated for the reactor. The next integration needs a physically matched source/return flux and compatible breeder benchmark, then nuclear-heating feedback into thermal and structural calculations. We reused published model/track APIs and reference methods; source sensitivity itself is not claimed as new physics.

This is a local 0.4.0-preview update. The previous public repository remains withdrawn and must not be reopened. Public publication still requires the fresh project repository. Private logs, credentials, machine details and correspondence are excluded from the shareable source candidate. No autonomous off-session research service is claimed.

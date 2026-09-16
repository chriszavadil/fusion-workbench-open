# Start here: what the models and particle animations do—and do not—show

## Correction to the presentation
This project has not produced physical fusion, built a working reactor or generated electricity. The existing power estimates are conditional outputs of systems calculations. They assume plasma conditions and component capabilities that have not been demonstrated as one working design. We have not shown a design can ignite and sustain fusion simply because an optimizer reports positive hypothetical net power.

The previous homepage made the largest theoretical electrical-output estimate dominant. Even with qualification labels, that invited a reader to mistake it for achieved output. The revised default page leads with the actual project stage: computer research. Numerical estimates, records and source links are preserved under an advanced-data section and in the Power progress dashboard, not deleted or promoted.

## The whole design and the particles are different views
The default page loads the existing r838 GLB reference-concept mesh through the existing DeviceViewer. It is interactive 3D, not a screenshot or live Unreal stream. Orbiting is camera motion; the glow is illustrative. Cutaway and component selection show the same saved geometry and plain-language descriptions. Reduced-motion preference disables automatic rotation. This does not create particle or ignition physics inside the whole-device drawing.

The prominent **Watch our calculated particle paths** link opens `#watch`. It selects the existing plasma-linked rear-header case from the recorded transport dataset, starts playback, enables the cutaway, and initially hides the heating slice so it does not obscure the particles. A closer camera and enlarged display markers make the paths easier to see; no stored positions, energies, times, counts or results are changed.

Cyan markers represent neutrons and yellow markers represent photons. The animation interpolates the original OpenMC histories, not invented decorative sparks. It is a small modeled cooling/blanket section linked to the r838 reference, not the higher-power alternative and not a whole-reactor transient simulation. The calculation starts from an assumed source of fusion neutrons and follows them through material. It does not simulate achieving ignition or prove that the source can be maintained.

The playback clock remains a logarithmic display of saved track times; independent histories are aligned at emission. Pause/scrub controls are placed before the viewport. Timing conventions and numerical values remain available in expandable technical details. Color, marker enlargement and display speed are not measurements of particle size or intensity. The optional heating slice is deposited-energy data, not coolant motion or measured temperature.

## Progress for a general audience
The new entry distinguishes (a) software and models that exist, (b) unresolved integration of plasma/magnets/heating/cooling/fuel, and (c) physical fusion/electricity that this project has not demonstrated. It explains an existing useful local layout result and the later equilibrium discrepancy without representing either as a fusion breakthrough. Other laboratories' physical results are explicitly separate from our modeled results.

No new scientific solver run, physical experiment, improved power result or native Unreal build is part of this interface change. Existing full datasets and exact recorded geometry are preserved. `#design` opens the detailed whole-device view; `#watch` starts the actual saved particle replay. The code reuses the existing Three.js rendering/OrbitControls and established OpenMC result projection, with original attribution retained.

## Verification and references
A fresh unsigned-in installed-Edge context checks the actual GLB canvas, hidden-by-default advanced scoreboard, direct links, recorded-case selection, playback controls, two different rendered particle frames and a narrow viewport. Browser sandboxing and TLS protections remain unchanged; no policy bypass, proxy, signed-in profile or scientific submission is used. Exact results and screenshots are recorded separately; a local preview pass is not a claim of successful public deployment until the deployed revision is checked.

Sources: existing `app/web/viewer.js`, `app/web/transport-lab.js`, immutable `app/data/transport_lab.json`, `app/data/catalog.json` and the dated source-coupling/power/equilibrium studies. The original particle transport solver is OpenMC; original systems model is UKAEA PROCESS. Three.js OrbitControls documentation: https://archive.threejs.org/docs/examples/en/controls/OrbitControls.html . ITER's explanation of fusion power versus electricity is background context, not a performance claim for this project: https://www.iter.org/fusion-energy/what-will-iter-do . Original interface changes remain MIT licensed.

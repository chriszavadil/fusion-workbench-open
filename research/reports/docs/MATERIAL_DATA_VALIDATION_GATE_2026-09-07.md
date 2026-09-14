# Prospective material-data validation gate

Status: planned before receiving raw data. The author's publication has been read, so this is not a blinded replication of the published findings. No received experimental dataset or completed calibration is claimed.

## Requested evidence

The public corresponding-author address and data-on-request statement were verified in Kulsartov et al., Nuclear Materials and Energy 36 (2023), 101489, DOI 10.1016/j.nme.2023.101489, pages 1 and 6. An unsent Gmail draft requests a publication-safe numerical subset of the shutdown/restart experiment. It requests sample temperature, the irradiation/source history underlying the published figures, release channels, common timing, units, instrument/background response, uncertainty, and specimen-size information. It does not request material samples, access to the reactor, or restricted operating details. Sending awaits the user's authorization; no new email was sent.

## Acceptance checks before fitting

Preserve original files, checksums, version, authorship, units and permitted uses. A publicly readable paper is not by itself permission to redistribute the underlying files. Record whether each channel is a calibrated rate, pressure, detector reading, or computed quantity. Do not substitute chamber pressure depletion for recovered tritium flux. Preserve absolute-temperature conversion, isotope counting, time origin, source history, and instrument delay. A mass-number-four signal must not automatically be labelled HT: the paper discusses its helium contribution. A reported total tritium signal requires its definition and calibration, not an assumed HT + 2T2 conversion from unseparated raw channels.

Use the actual specimen composition and size distribution; do not combine pure orthosilicate and biphasic-material fits. Do not insert effective diffusion lengths inferred from a previous fit as independently measured radii. Record missing uncertainty, extraction conditions, porosity, dose and temperature-distribution information explicitly.

## Calibration and evaluation separation

Freeze permitted model classes and parameters before opening response values. Candidate classes are constant-property diffusion, temperature-dependent diffusion, and diffusion plus an explicitly represented surface-release stage. Include the measurement-response model when it is identifiable. The thermal/source inputs may be used as forcing, not release outcomes disguised as model inputs.

Preferred split: identify parameters from an earlier non-evaluation transient, then predict an untouched shutdown and restart. If only one shutdown/restart is provided, prespecify a calibration interval and reserve the other interval for conditional prediction, and label this as within-experiment evaluation rather than independent validation. The source paper already used these events; matching its published fitted curve is not a new held-out result. If the calibration interval does not contain enough independent temperature or transient variation to distinguish parameters, report non-identifiability and request a second transient instead of forcing a fit. In particular, one constant temperature cannot separately identify an Arrhenius prefactor and activation energy.

## Numerical and scientific acceptance

Keep sample timestamps rather than interpolating response data to manufacture temporal resolution. Weight residuals using supplied measurement errors; without errors, report descriptive residuals and sensitivity ranges rather than confidence claims. Preserve cumulative release, timing, species balance and residual structure separately. Freeze fit ranges and validation metrics before evaluation. A prediction that misses its declared uncertainty range is a failed model test even when the trend looks plausible. Mesh and integration refinement must make numerical error small relative to measurement uncertainty; solver agreement is not evidence of correct material physics.

A validated specimen release model still needs a separate downstream extraction/processing stage. No raw specimen result can establish industrial blanket delivery, a plant tritium-breeding ratio, qualified storage, or net electric output. The next plant-level test must couple the same geometry's temperature history, release response, recovery losses and energy costs.

## Available while awaiting data

The existing numerical reference, material-unit checks, cooling envelopes and conditional fuel-loss requirements remain reproducible locally. The new empirical calibration and an independent experimental prediction remain unexecuted. This data-access dependency does not mean that every possible research branch is blocked.

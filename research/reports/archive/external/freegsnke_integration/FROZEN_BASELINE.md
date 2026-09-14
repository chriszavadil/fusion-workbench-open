# Frozen FreeGSNKE reproduction baseline

## Purpose

This branch establishes an independently reproducible, upstream-first validation gate before any new plasma-control or safety claim is evaluated.

## Pinned source

- Repository: `FusionComputingLab/freegsnke`
- Tag: `v3.0.1`
- Expected commit prefix: `f776e90`

The workflow refuses to continue if the checked-out tag does not resolve to the expected commit prefix.

## Required sequence

1. Clone the official upstream repository.
2. Check out the frozen tag and record the complete commit SHA.
3. Record operating-system, Python, compiler and package provenance.
4. Install the upstream package without modifying its source.
5. Run the upstream test suite.
6. Inventory the upstream notebooks, examples and machine configurations.
7. Preserve the complete logs and machine-readable test results as immutable workflow artifacts.
8. Only after the upstream suite passes may a separate workflow execute selected examples or export a state-space model.

## Evidence boundary

Passing this workflow means only that the pinned upstream software can be reproduced in the GitHub runner environment. It is not evidence that:

- a MAST-U discharge has been reproduced;
- an ITER scenario has been validated;
- a proposed recovery monitor is correct;
- a reactor is safe;
- or fusion power is commercially sustainable.

## Stop conditions

The branch must stop and report rather than silently patch upstream behavior if:

- the tag resolves to a different commit;
- installation requires an undocumented dependency;
- upstream tests fail;
- a required example relies on restricted data;
- or the runner cannot establish sufficient numerical provenance.

Any compatibility patch must be proposed separately, with the unmodified failure retained as evidence.
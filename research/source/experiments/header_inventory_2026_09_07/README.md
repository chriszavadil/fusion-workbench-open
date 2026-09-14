# Header inventory and fair-baseline replay

This packet contains a completed, candidate-specific numerical comparison. It is not a qualified header layout or a new general manifold solver. Read `DECISION.md`, `ADMISSION.json`, and `FOLLOWON_ADMISSION.json` before using the numbers.

The exact native state and inherited branch/thermal wrappers are preserved in `dependencies/`. The original pre-follow-on source and outputs are retained in `initial_prescribed_flow/`. The two new calculation modules and focused tests are in this directory. `MANIFEST.json` checks bytes and relevant pinned upstream source files.

## Reproduce in the already installed reference environment
Run from any directory using the pinned PROCESS Python environment:

```powershell
& "$env:USERPROFILE\FusionResearch\.venv-process-310\Scripts\python.exe" replay.py
```

The replay creates a fresh temporary directory, rebuilds the historical directory layout, checks input/source hashes, runs the two bounded calculations and 19 focused tests, and compares results. It does not install anything, access the network, alter the upstream source, or overwrite the packet. `--output` can specify a new empty replay directory. `requirements-observed.txt` records the executed environment; the editable PROCESS reference is c0ae5b28649f2b20fb7efc7904628b6defe4151c.

The numerical repeat tolerances are0.1Pa for selected pressures and1e-5K for selected temperatures; these are not physical uncertainty bounds. A different dependency/platform combination may require independent numerical assessment rather than pretending it reproduces these exact byte-level results.

## Interpretation
The circular three-header envelope, native computational-module mapping and wall thickness rule are declared choices. Header coolant and steel are deducted from their existing inventories, but remaining structural adequacy and spatial fit are not established. Known friction is included; junction/distribution losses and external-system pressure losses remain budgeted requirements. The balanced split has more known-loss headroom than the stronger unsplit redistribution reference, but this alone does not validate the split as a complete cooling design.

No TBR/neutron calculation, real material-life result, extra electrical generation or autonomous research service is supplied. Source-derived portions use the UKAEA MIT license included in `UPSTREAM_LICENSE.txt`.
